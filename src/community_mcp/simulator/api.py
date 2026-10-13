import time
from collections import defaultdict, deque
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from community_mcp.agent.schemas import SupportedLocale
from community_mcp.simulator.api_schemas import ChatRequest, ChatResponse, MCPTrace


class ChatRateLimiter:
    """Simple in-memory per-client request limiter for local development."""

    def __init__(self, *, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, client_key: str) -> bool:
        now = time.monotonic()
        timestamps = self._requests[client_key]

        while timestamps and now - timestamps[0] >= self.window_seconds:
            timestamps.popleft()

        if len(timestamps) >= self.max_requests:
            return False

        timestamps.append(now)
        return True


def create_simulator_app(
    *,
    agent_factory: Callable[[], Any],
    rate_limiter: ChatRateLimiter | None = None,
) -> FastAPI:
    app = FastAPI(title="Community MCP Experience Simulator")

    static_dir = Path(__file__).resolve().parent / "static"

    app.mount(
        "/simulator/static",
        StaticFiles(directory=static_dir),
        name="simulator-static",
    )

    @app.get("/simulator", include_in_schema=False)
    async def simulator_home():
        return FileResponse(static_dir / "index.html")

    limiter = rate_limiter or ChatRateLimiter()

    def get_agent() -> Any:
        return agent_factory()

    @app.get("/simulator/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/simulator/api/chat", response_model=ChatResponse)
    async def chat(
        payload: ChatRequest,
        request: Request,
        agent: Annotated[Any, Depends(get_agent)],
    ) -> ChatResponse:
        # Use the actual TCP peer, not untrusted forwarded headers.
        client_key = request.client.host if request.client else "unknown"

        if not limiter.allow(client_key):
            raise HTTPException(status_code=429, detail="Too many requests.")

        try:
            result = await agent.handle(
                message=payload.message,
                locale=SupportedLocale(payload.locale),
                session_id=str(payload.session_id),
            )
        except (ValueError, ValidationError) as exc:
            raise HTTPException(status_code=422, detail="Invalid conversation request.") from exc

        return ChatResponse(
            session_id=payload.session_id,
            message=result["message"],
            intent=result["intent"],
            trace=MCPTrace(
                tool=result.get("tool"),
                authenticated=result.get("tool") is not None,
            ),
        )

    return app
