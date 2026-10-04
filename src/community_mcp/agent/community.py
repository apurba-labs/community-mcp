from community_mcp.agent.reasoning import (
    DeterministicReasoner,
    ReasoningProvider,
)
from community_mcp.agent.renderer import BilingualRenderer
from community_mcp.agent.schemas import (
    AgentIntent,
    AgentRequest,
    AgentResponse,
)
from community_mcp.agent.session import AgentSessionStore
from community_mcp.assistance.action_service import AssistanceActionService
from community_mcp.assistance.preparation_store import AssistancePreparationStore
from community_mcp.assistance.service import AssistanceService
from community_mcp.policy.assistance import AssistancePolicy
from community_mcp.providers.base import CommunityDataProvider
from community_mcp.providers.member_context import (
    MemberContextProvider,
    MemberContextUnavailableError,
)
from community_mcp.schemas.action import PolicyDecision


class CommunityAgent:
    def __init__(
        self,
        provider: CommunityDataProvider,
        *,
        reasoner: ReasoningProvider | None = None,
        member_context_provider: MemberContextProvider | None = None,
        event_slug: str = "centenary-celebration",
        assistance_reference: str = "HELP-2026-001",
    ) -> None:
        self.provider = provider
        self.event_slug = event_slug
        self.assistance_reference = assistance_reference

        self.reasoner = reasoner or DeterministicReasoner()
        self.member_context_provider = member_context_provider
        self.renderer = BilingualRenderer()
        self.sessions = AgentSessionStore()

        self.assistance_service = AssistanceService()
        self.assistance_policy = AssistancePolicy()
        self.preparation_store = AssistancePreparationStore()
        self.action_service = AssistanceActionService(
            self.preparation_store
        )

    async def handle(
        self,
        request: AgentRequest,
    ) -> AgentResponse:
        session = self.sessions.get_or_create(
            session_id=request.session_id,
            locale=request.locale,
            actor_id=request.actor_id,
        )

        decision = await self.reasoner.reason(
            message=request.message,
            locale=request.locale,
        )
        intent = decision.intent

        if intent == AgentIntent.EVENT_CONTEXT:
            event = await self.provider.get_event_by_slug(
                self.event_slug
            )

            self.sessions.set_event_context(
                request.session_id,
                event.slug,
            )

            return AgentResponse(
                locale=request.locale,
                intent=intent,
                message=self.renderer.event_context(
                    event,
                    request.locale,
                ),
            )

        if intent == AgentIntent.COMMUNITY_CONTEXT:
            if not session.actor_id or self.member_context_provider is None:
                return AgentResponse(
                    locale=request.locale,
                    intent=intent,
                    message=self.renderer.community_context_unavailable(
                        request.locale
                    ),
                )

            try:
                context = await self.member_context_provider.get_my_batch_context(
                    session.actor_id
                )
            except MemberContextUnavailableError:
                return AgentResponse(
                    locale=request.locale,
                    intent=intent,
                    message=self.renderer.community_context_unavailable(
                        request.locale
                    ),
                )

            return AgentResponse(
                locale=request.locale,
                intent=intent,
                message=self.renderer.community_context(
                    context,
                    request.locale,
                ),
            )

        if intent == AgentIntent.ASSISTANCE_CONTEXT:
            assistance = (
                await self.assistance_service.get_public_context(
                    self.assistance_reference
                )
            )

            self.sessions.set_assistance_context(
                request.session_id,
                assistance.public_reference,
            )

            return AgentResponse(
                locale=request.locale,
                intent=intent,
                message=self.renderer.assistance_context(
                    assistance,
                    request.locale,
                ),
            )

        if intent == AgentIntent.ASSISTANCE_RESPONSE:
            if not session.actor_id:
                return AgentResponse(
                    locale=request.locale,
                    intent=intent,
                    message=self.renderer.no_pending_action(
                        request.locale
                    ),
                )

            if decision.action is None:
                return AgentResponse(
                    locale=request.locale,
                    intent=intent,
                    message=self.renderer.unknown(
                        request.locale
                    ),
                )

            public_reference = (
                session.current_assistance_reference
                or self.assistance_reference
            )

            assistance = (
                await self.assistance_service.get_public_context(
                    public_reference
                )
            )

            prepared = self.assistance_policy.prepare_response(
                assistance,
                actor_id=session.actor_id,
                action=decision.action,
            )
            if (
                prepared.decision
                == PolicyDecision.REQUIRES_CONFIRMATION
            ):
                self.preparation_store.save(prepared)
                self.sessions.set_pending_preparation(
                    request.session_id,
                    prepared.preparation_id,
                )

            return AgentResponse(
                locale=request.locale,
                intent=intent,
                message=self.renderer.confirmation_required(
                    request.locale
                ),
                requires_confirmation=(
                    prepared.confirmation_required
                ),
                preparation_id=str(
                    prepared.preparation_id
                ),
            )

        if intent == AgentIntent.CONFIRM_ACTION:
            if (
                not session.actor_id
                or session.pending_preparation_id is None
            ):
                return AgentResponse(
                    locale=request.locale,
                    intent=intent,
                    message=self.renderer.no_pending_action(
                        request.locale
                    ),
                )

            result = self.action_service.confirm_response(
                session.pending_preparation_id,
                actor_id=session.actor_id,
                confirmed=True,
            )

            self.sessions.clear_pending_preparation(
                request.session_id
            )

            return AgentResponse(
                locale=request.locale,
                intent=intent,
                message=self.renderer.action_confirmed(
                    result,
                    request.locale,
                ),
            )

        return AgentResponse(
            locale=request.locale,
            intent=AgentIntent.UNKNOWN,
            message=self.renderer.no_pending_action(
                request.locale
            ),
        )
