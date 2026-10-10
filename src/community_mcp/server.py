from pathlib import Path
from uuid import UUID

from mcp.server import MCPServer

from community_mcp.assistance.action_service import (
    ActorMismatchError,
    AssistanceActionService,
    ConfirmationRequiredError,
)
from community_mcp.assistance.preparation_store import (
    AssistancePreparationStore,
    PreparationAlreadyConsumedError,
    PreparationNotFoundError,
)
from community_mcp.assistance.service import (
    AssistanceNotFoundError,
    AssistanceService,
    AssistanceUnavailableError,
)
from community_mcp.assistance.sqlite_store import SQLiteAssistanceStore
from community_mcp.config import get_settings
from community_mcp.policy.assistance import AssistancePolicy
from community_mcp.providers.assistance import AssistanceContextProvider
from community_mcp.providers.assistance_factory import (
    create_assistance_provider,
)
from community_mcp.providers.base import (
    CommunityDataProvider,
    EventNotFoundError,
)
from community_mcp.providers.factory import create_provider
from community_mcp.schemas.action import (
    ConfirmedAssistanceResponse,
    PreparedAssistanceResponse,
)
from community_mcp.schemas.assistance import (
    AssistanceAction,
    AssistanceRequest,
)
from community_mcp.schemas.event import EventDetail


def create_mcp_server(
    provider: CommunityDataProvider | None = None,
    assistance_provider: AssistanceContextProvider | None = None,
) -> MCPServer:
    settings = get_settings()
    data_provider = provider or create_provider(settings)
    resolved_assistance_provider = assistance_provider or create_assistance_provider(settings)

    assistance_service = AssistanceService(resolved_assistance_provider)
    assistance_policy = AssistancePolicy()
    preparation_store = AssistancePreparationStore()

    durable_store = None

    if settings.demo_ledger_enabled:
        if settings.data_provider != "demo":
            raise ValueError("Durable demo assistance ledger requires DATA_PROVIDER=demo.")

        ledger_path = Path(settings.demo_ledger_path)
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        durable_store = SQLiteAssistanceStore(ledger_path)

    assistance_action_service = AssistanceActionService(
        preparation_store,
        durable_store=durable_store,
    )

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
            raise ValueError(f"No public event was found with slug '{event_slug}'.") from exc

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
            raise ValueError(f"No assistance request was found for '{public_reference}'.") from exc
        except AssistanceUnavailableError as exc:
            raise ValueError(f"Assistance request '{public_reference}' is not available.") from exc

    @mcp.tool()
    async def prepare_assistance_response(
        public_reference: str,
        actor_id: str,
        action: AssistanceAction,
    ) -> PreparedAssistanceResponse:
        """Prepare a community assistance response for user confirmation.

        This capability evaluates deterministic policy and prepares an
        intended response. It does not record, send, notify, or execute
        the response.

        Args:
            public_reference: Public assistance request reference.
            actor_id: Authenticated actor identifier supplied by the caller.
            action: Assistance action the actor intends to perform.
        """
        if settings.data_provider != "demo":
            raise ValueError(
                "Assistance response actions are disabled outside synthetic demo mode."
            )
        try:
            request = await assistance_service.get_public_context(public_reference)
        except AssistanceNotFoundError as exc:
            raise ValueError(f"No assistance request was found for '{public_reference}'.") from exc
        except AssistanceUnavailableError as exc:
            raise ValueError(f"Assistance request '{public_reference}' is not available.") from exc

        prepared = assistance_policy.prepare_response(
            request,
            actor_id=actor_id,
            action=action,
        )

        if prepared.confirmation_required:
            if durable_store is not None:
                durable_store.save(prepared)
            else:
                preparation_store.save(prepared)

        return prepared

    @mcp.tool()
    async def confirm_assistance_response(
        preparation_id: UUID,
        actor_id: str,
        confirmed: bool,
    ) -> ConfirmedAssistanceResponse:
        """Confirm and record a previously prepared assistance response.

        This is a consequential capability. It succeeds only for a preparation
        previously issued by the policy engine, for the same actor, after
        explicit confirmation. A preparation can be consumed only once.

        Args:
            preparation_id: Identifier returned by prepare_assistance_response.
            actor_id: Authenticated actor identifier supplied by the caller.
            confirmed: Explicit confirmation of the prepared action.
        """
        if settings.data_provider != "demo":
            raise ValueError(
                "Assistance response actions are disabled outside synthetic demo mode."
            )
        try:
            return assistance_action_service.confirm_response(
                preparation_id,
                actor_id=actor_id,
                confirmed=confirmed,
            )
        except PreparationNotFoundError as exc:
            raise ValueError("The prepared assistance response does not exist.") from exc
        except PreparationAlreadyConsumedError as exc:
            raise ValueError("The prepared assistance response has already been used.") from exc
        except ConfirmationRequiredError as exc:
            raise ValueError("Explicit confirmation is required.") from exc
        except ActorMismatchError as exc:
            raise ValueError("The confirming actor does not match the prepared response.") from exc

    return mcp


mcp = create_mcp_server()


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        json_response=True,
    )
