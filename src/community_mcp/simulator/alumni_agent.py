from __future__ import annotations

from typing import Any

from community_mcp.agent.schemas import AgentIntent, SupportedLocale
from community_mcp.providers.assistance import (
    AssistanceContextNotFoundError,
    AssistanceContextUnavailableError,
)
from community_mcp.providers.gotihub import GotiHubProvider
from community_mcp.providers.gotihub_assistance import GotiHubAssistanceProvider
from community_mcp.simulator.assistance import (
    extract_public_reference,
    render_assistance_context,
    render_reference_required,
)
from community_mcp.simulator.event_renderer import (
    detect_event_topic,
    render_event_answer,
)


class AlumniAgent:
    EVENT_SLUG = "centenary-celebration"

    def __init__(
        self,
        *,
        provider: GotiHubProvider,
        assistance_provider: GotiHubAssistanceProvider | None = None,
    ) -> None:
        self.provider = provider
        self.assistance_provider = assistance_provider

    @staticmethod
    def _is_assistance_question(message: str) -> bool:
        text = message.casefold()

        keywords = (
            "assistance",
            "need help",
            "needs help",
            "help request",
            "blood donation",
            "blood donor",
            "সাহায্য",
            "সহায়তা",
            "সহায়তা",
            "রক্ত",
            "অনুদান",
        )

        return any(keyword in text for keyword in keywords)

    async def _handle_assistance(
        self,
        *,
        message: str,
        locale: SupportedLocale,
        reference: str | None,
    ) -> dict[str, Any]:
        intent = AgentIntent.ASSISTANCE_CONTEXT.value

        if reference is None:
            return {
                "message": render_reference_required(locale),
                "intent": intent,
                "tool": None,
            }

        unavailable_message = (
            "এই রেফারেন্সের অনুমোদিত সহায়তার তথ্য এখন যাচাই করা যাচ্ছে না।"
            if locale == SupportedLocale.BN
            else "Approved assistance information for this reference is currently unavailable."
        )

        if self.assistance_provider is None:
            return {
                "message": unavailable_message,
                "intent": intent,
                "tool": None,
            }

        try:
            request = await self.assistance_provider.get_public_context(reference)

            if (
                request.public_reference != reference
                or not request.verified
                or not request.approved
                or request.status.value not in {"OPEN", "ACTIVE"}
            ):
                raise ValueError("Assistance request is not publicly available.")

            response = render_assistance_context(
                request.model_dump(mode="json"),
                locale=locale,
            )

        except (
            AssistanceContextNotFoundError,
            AssistanceContextUnavailableError,
            ValueError,
        ):
            return {
                "message": unavailable_message,
                "intent": intent,
                "tool": None,
            }

        return {
            "message": response,
            "intent": intent,
            "tool": "get_assistance_context",
        }

    async def handle(
        self,
        *,
        message: str,
        locale: SupportedLocale = SupportedLocale.EN,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        reference = extract_public_reference(message)

        if reference is not None or self._is_assistance_question(message):
            return await self._handle_assistance(
                message=message,
                locale=locale,
                reference=reference,
            )

        events = await self.provider.list_events()

        event = next(
            (item for item in events if item.slug == self.EVENT_SLUG),
            None,
        )

        if event is None:
            return {
                "message": (
                    "এই অনুষ্ঠানের কোনো প্রকাশিত তথ্য পাওয়া যায়নি।"
                    if locale == SupportedLocale.BN
                    else "No published information is available for this event."
                ),
                "intent": AgentIntent.EVENT_CONTEXT.value,
                "tool": None,
            }

        event_data = event.model_dump(mode="json")

        return {
            "message": render_event_answer(
                event_data,
                topic=detect_event_topic(message),
                locale=locale,
            ),
            "intent": AgentIntent.EVENT_CONTEXT.value,
            "tool": "list_events",
        }
