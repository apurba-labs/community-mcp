from __future__ import annotations

import secrets
import time
from collections import defaultdict, deque
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from community_mcp.agent.schemas import SupportedLocale
from community_mcp.simulator.api_schemas import (
    ChatRequest,
    ChatResponse,
    InternalChatRequest,
    MCPTrace,
)
from community_mcp.usage.context import (
    UsageContext,
    activate_usage,
    reset_usage,
)
from community_mcp.usage.store import (
    SQLiteUsageStore,
    UsageBudget,
    UsageBudgetExceeded,
)

UsageChannel = Literal["public", "alumni"]


class ChatRateLimiter:
    """Simple in-memory per-client request limiter for local development."""

    def __init__(
        self,
        *,
        max_requests: int = 10,
        window_seconds: int = 60,
    ) -> None:
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
    internal_agent_factory: Callable[[], Any] | None = None,
    internal_organization_id: str | None = None,
    internal_api_token: str | None = None,
    rate_limiter: ChatRateLimiter | None = None,
    internal_rate_limiter: ChatRateLimiter | None = None,
    usage_store: SQLiteUsageStore | None = None,
    public_budget: UsageBudget | None = None,
    alumni_budget: UsageBudget | None = None,
    model_id: str = "amazon.nova-micro-v1:0",
    internal_only: bool = False,
) -> FastAPI:
    app = FastAPI(
        title="Community MCP Experience Simulator",
        docs_url=None if internal_only else "/docs",
        redoc_url=None if internal_only else "/redoc",
        openapi_url=None if internal_only else "/openapi.json",
    )

    static_dir = Path(__file__).resolve().parent / "static"

    if not internal_only:
        app.mount(
            "/simulator/static",
            StaticFiles(directory=static_dir),
            name="simulator-static",
        )

    limiter = rate_limiter or ChatRateLimiter()

    internal_limiter = internal_rate_limiter or ChatRateLimiter(
        max_requests=30,
        window_seconds=60,
    )

    async def handle_budgeted_chat(
        *,
        agent: Any,
        payload: ChatRequest,
        channel: UsageChannel,
        organization_id: str | None = None,
    ) -> ChatResponse:
        """
        Execute a chat request with persistent usage accounting.

        Each request receives its own reservation and ContextVar scope.
        No request-specific state is stored on the shared agent.
        """
        budget = public_budget if channel == "public" else alumni_budget

        if usage_store is None or budget is None:
            raise HTTPException(
                status_code=503,
                detail="AI usage controls are not configured.",
            )

        try:
            reservation_id = usage_store.reserve(
                channel=channel,
                organization_id=organization_id,
                model_id=model_id,
                budget=budget,
            )
        except UsageBudgetExceeded as exc:
            raise HTTPException(
                status_code=429,
                detail=str(exc),
            ) from exc

        context_token = activate_usage(
            UsageContext(
                store=usage_store,
                reservation_id=reservation_id,
            )
        )

        try:
            result = await agent.handle(
                message=payload.message,
                locale=SupportedLocale(payload.locale),
                session_id=str(payload.session_id),
            )

            response = ChatResponse(
                session_id=payload.session_id,
                message=result["message"],
                intent=result["intent"],
                trace=MCPTrace(
                    tool=result.get("tool"),
                    authenticated=result.get("tool") is not None,
                ),
            )

            return response

        except (ValueError, ValidationError) as exc:
            raise HTTPException(
                status_code=422,
                detail="Invalid conversation request.",
            ) from exc

        finally:
            try:
                # Bedrock's usage callback marks the reservation completed.
                #
                # If no usage was recorded, preserve the estimated allocation
                # rather than incorrectly reporting zero token consumption.
                if usage_store.reservation_status(reservation_id) == "reserved":
                    usage_store.mark_unknown(reservation_id)
            finally:
                reset_usage(context_token)

    async def simulator_home():
        return FileResponse(static_dir / "index.html")

    async def health() -> dict[str, str]:
        return {"status": "ok"}

    async def chat(
        payload: ChatRequest,
        request: Request,
    ) -> ChatResponse:
        # Do not trust caller-supplied X-Forwarded-For headers.
        client_key = request.client.host if request.client else "unknown"

        if not limiter.allow(client_key):
            raise HTTPException(
                status_code=429,
                detail="Too many requests.",
            )

        return await handle_budgeted_chat(
            agent=agent_factory(),
            payload=payload,
            channel="public",
        )

    # Register public simulator routes only when enabled.
    if not internal_only:
        app.add_api_route(
            "/simulator",
            simulator_home,
            methods=["GET"],
            include_in_schema=False,
        )
        app.add_api_route(
            "/simulator/api/health",
            health,
            methods=["GET"],
        )
        app.add_api_route(
            "/simulator/api/chat",
            chat,
            methods=["POST"],
            response_model=ChatResponse,
        )

    @app.post("/simulator/api/internal/chat", response_model=ChatResponse)
    async def internal_chat(
        payload: InternalChatRequest,
        request: Request,
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

        if (
            internal_organization_id is not None
            and str(payload.organization_id) != internal_organization_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Organization is not authorized for this assistant.",
            )

        # This endpoint is reserved for the authenticated Alumni backend.
        # The organization UUID must come from its resolved organization
        # context, never from an end-user-controlled channel selector.

        client_key = "alumni"

        if not internal_limiter.allow(client_key):
            raise HTTPException(
                status_code=429,
                detail="Alumni assistant request limit exceeded.",
            )

        return await handle_budgeted_chat(
            agent=(internal_agent_factory or agent_factory)(),
            payload=payload,
            channel="alumni",
            organization_id=str(payload.organization_id),
        )

    @app.get("/simulator/api/internal/usage")
    async def internal_usage(
        authorization: Annotated[str | None, Header()] = None,
    ):
        if not internal_api_token or not internal_organization_id:
            raise HTTPException(
                status_code=503,
                detail="Internal usage reporting is not configured.",
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

        if usage_store is None or alumni_budget is None:
            raise HTTPException(
                status_code=503,
                detail="AI usage controls are not configured.",
            )

        usage = usage_store.daily_summary(
            channel="alumni",
            organization_id=internal_organization_id,
        )

        return {
            "organization_id": internal_organization_id,
            "period": "today_utc",
            "requests": {
                "used": usage["requests_used"],
                "limit": alumni_budget.daily_requests,
                "remaining": max(
                    0,
                    alumni_budget.daily_requests - usage["requests_used"],
                ),
                "active": usage["active_requests"],
                "concurrent_limit": alumni_budget.concurrent_requests,
            },
            "tokens": {
                "recorded": usage["recorded_tokens"],
                "allocated": usage["allocated_tokens"],
                "limit": alumni_budget.daily_tokens,
                "remaining": max(
                    0,
                    alumni_budget.daily_tokens - usage["allocated_tokens"],
                ),
                "input": usage["input_tokens"],
                "output": usage["output_tokens"],
            },
        }

    return app
