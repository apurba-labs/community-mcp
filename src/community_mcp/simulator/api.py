import secrets
import time
from collections import defaultdict, deque
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
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
    internal_api_token: str | None = None,
    internal_rate_limiter: ChatRateLimiter | None = None,
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
    internal_limiter = internal_rate_limiter or ChatRateLimiter(
        max_requests=30,
        window_seconds=60,
    )

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

    @app.post("/simulator/api/internal/chat", response_model=ChatResponse)
    async def internal_chat(
        payload: ChatRequest,
        request: Request,
        agent: Annotated[Any, Depends(get_agent)],
        authorization: Annotated[str | None, Header()] = None,
    ) -> ChatResponse:
        if not internal_api_token:
            raise HTTPException(
                status_code=503,
                detail="Internal chat is not configured.",
            )

        scheme, _, supplied_token = (authorization or "").partition(" ")

        if scheme.lower() != "bearer" or not secrets.compare_digest(
            supplied_token,
            internal_api_token,
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid service credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Never accept a channel name from the browser.
        # This endpoint is reserved for the Alumni backend.
        client_key = "alumni"

        if not internal_limiter.allow(client_key):
            raise HTTPException(
                status_code=429,
                detail="Alumni assistant request limit exceeded.",
            )

        try:
            result = await agent.handle(
                message=payload.message,
                locale=SupportedLocale(payload.locale),
                session_id=str(payload.session_id),
            )
        except (ValueError, ValidationError) as exc:
            raise HTTPException(
                status_code=422,
                detail="Invalid conversation request.",
            ) from exc

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
