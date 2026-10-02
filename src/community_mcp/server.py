from mcp.server import MCPServer

from community_mcp.assistance.service import (
    AssistanceNotFoundError,
    AssistanceService,
    AssistanceUnavailableError,
)
from community_mcp.config import get_settings
from community_mcp.providers.base import (
    CommunityDataProvider,
    EventNotFoundError,
)
from community_mcp.providers.factory import create_provider
from community_mcp.schemas.assistance import AssistanceRequest
from community_mcp.schemas.event import EventDetail


def create_mcp_server(
    provider: CommunityDataProvider | None = None,
) -> MCPServer:
    data_provider = provider or create_provider(get_settings())
    assistance_service = AssistanceService()

    mcp = MCPServer(
        "Community MCP",
        instructions=(
            "Use Community MCP for authoritative community information and "
            "permissioned community actions. Do not invent institutional facts "
            "when a Community MCP capability can provide them."
        ),
    )

    @mcp.tool()
    async def get_event_context(event_slug: str) -> EventDetail:
        """Get authoritative public context for a community event.

        Use this when reasoning about an event's schedule, program, venue,
        registration requirements, guests, sponsors, or event team.

        Args:
            event_slug: Stable public slug identifying the event.
        """
        try:
            return await data_provider.get_event_by_slug(event_slug)
        except EventNotFoundError as exc:
            raise ValueError(
                f"No public event was found with slug '{event_slug}'."
            ) from exc

    @mcp.tool()
    async def get_assistance_context(
        public_reference: str,
    ) -> AssistanceRequest:
        """Get safe public context for a verified community assistance request.

        Use this before reasoning about how someone may help with a community
        assistance need. This capability is read-only and performs no action.

        Args:
            public_reference: Public reference identifying the assistance request.
        """
        try:
            return await assistance_service.get_public_context(public_reference)
        except AssistanceNotFoundError as exc:
            raise ValueError(
                f"No assistance request was found for '{public_reference}'."
            ) from exc
        except AssistanceUnavailableError as exc:
            raise ValueError(
                f"Assistance request '{public_reference}' is not available."
            ) from exc

    return mcp


mcp = create_mcp_server()


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        json_response=True,
    )
