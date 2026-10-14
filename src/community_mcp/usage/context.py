from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass

from community_mcp.agent.usage import BedrockUsage
from community_mcp.usage.store import SQLiteUsageStore


@dataclass(frozen=True)
class UsageContext:
    store: SQLiteUsageStore
    reservation_id: str


_current_usage: ContextVar[UsageContext | None] = ContextVar(
    "community_mcp_usage",
    default=None,
)


def activate_usage(context: UsageContext) -> Token:
    return _current_usage.set(context)


def reset_usage(token: Token) -> None:
    _current_usage.reset(token)


def record_bedrock_usage(usage: BedrockUsage) -> None:
    context = _current_usage.get()

    if context is not None:
        context.store.complete(context.reservation_id, usage)
