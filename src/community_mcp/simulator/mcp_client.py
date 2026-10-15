from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


class CommunityMCPClientError(Exception):
    """Raised when the Community MCP server cannot complete a request."""


@dataclass(frozen=True)
class MCPToolInfo:
    name: str
    description: str


class CommunityMCPClient:
    """Authenticated Streamable HTTP client for Community MCP."""

    ALLOWED_TOOLS = frozenset(
        {
            "get_event_context",
            "get_assistance_context",
        }
    )

    def __init__(
        self,
        *,
        server_url: str,
        access_token: str | None = None,
        token_file: str | Path | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        if not server_url.startswith(("https://", "http://127.0.0.1:", "http://localhost:")):
            raise ValueError("MCP server must use HTTPS outside localhost.")

        if bool(access_token) == bool(token_file):
            raise ValueError("Exactly one of access_token or token_file is required.")

        self.server_url = server_url
        self.access_token = access_token
        self.token_file = Path(token_file) if token_file else None
        self.timeout_seconds = timeout_seconds

    def _get_access_token(self) -> str:
        if self.token_file is None:
            assert self.access_token is not None
            return self.access_token

        try:
            token = self.token_file.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise CommunityMCPClientError("MCP authentication is temporarily unavailable.") from exc

        if not token:
            raise CommunityMCPClientError("MCP authentication is temporarily unavailable.")

        return token

    async def _execute(
        self,
        *,
        tool_name: str | None = None,
        arguments: dict[str, Any] | None = None,
    ) -> list[MCPToolInfo] | Any:
        try:
            async with httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self._get_access_token()}"},
                timeout=self.timeout_seconds,
                follow_redirects=False,
            ) as http_client:
                async with streamable_http_client(
                    self.server_url,
                    http_client=http_client,
                ) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()

                        if tool_name is None:
                            response = await session.list_tools()
                            return [
                                MCPToolInfo(
                                    name=tool.name,
                                    description=tool.description or "",
                                )
                                for tool in response.tools
                            ]

                        response = await session.call_tool(
                            tool_name,
                            arguments=arguments or {},
                        )

                        if response.is_error:
                            raise CommunityMCPClientError(
                                f"MCP tool {tool_name} returned an error."
                            )

                        return response

        except CommunityMCPClientError:
            raise
        except Exception as exc:
            raise CommunityMCPClientError(
                "Unable to complete the authenticated MCP request."
            ) from exc

    async def list_tools(self) -> list[MCPToolInfo]:
        result = await self._execute()
        return result

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        if name not in self.ALLOWED_TOOLS:
            raise ValueError(f"Tool is not permitted: {name}")

        return await self._execute(
            tool_name=name,
            arguments=arguments,
        )
