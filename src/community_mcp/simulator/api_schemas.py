from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    locale: Literal["en", "bn"] = "en"
    session_id: UUID = Field(default_factory=uuid4)


class MCPTrace(BaseModel):
    transport: str = "streamable_http"
    tool: str | None = None
    authenticated: bool = False


class ChatResponse(BaseModel):
    session_id: UUID
    message: str
    intent: str
    trace: MCPTrace


class InternalChatRequest(ChatRequest):
    organization_id: UUID
