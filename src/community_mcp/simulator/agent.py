from __future__ import annotations

from typing import Any

from community_mcp.agent.bedrock import BedrockReasoner
from community_mcp.agent.schemas import AgentIntent, SupportedLocale
from community_mcp.simulator.assistance import (
    extract_public_reference,
    render_assistance_context,
    render_reference_required,
)
from community_mcp.simulator.event_renderer import (
    detect_event_topic,
    render_event_answer,
)
from community_mcp.simulator.mcp_client import CommunityMCPClient, CommunityMCPClientError
from community_mcp.simulator.session import SimulatorSessionStore


class SimulatorAgent:
    """Read-only conversational agent backed by actual MCP tool calls."""

    EVENT_SLUG = "centenary-celebration"

    def __init__(
        self,
        *,
        mcp_client: CommunityMCPClient,
        reasoner: BedrockReasoner,
    ) -> None:
        self.mcp_client = mcp_client
        self.reasoner = reasoner
        self.sessions = SimulatorSessionStore()

    async def handle(
        self,
        *,
        message: str,
        locale: SupportedLocale = SupportedLocale.EN,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        if not message.strip():
            raise ValueError("Message cannot be empty.")

        decision = await self.reasoner.reason(
            message=message,
            locale=locale,
        )

        reference = extract_public_reference(message)

        previous_reference = (
            self.sessions.get_assistance_reference(session_id) if session_id is not None else None
        )

        is_assistance = decision.intent == AgentIntent.ASSISTANCE_CONTEXT

        is_assistance_followup = (
            previous_reference is not None
            and decision.intent == AgentIntent.UNKNOWN
            and any(
                phrase in message.casefold()
                for phrase in (
                    "still active",
                    "still needed",
                    "that request",
                    "এই অনুরোধ",
                    "এখনো প্রয়োজন",
                    "এখনও প্রয়োজন",
                    "সক্রিয়",
                    "সক্রিয়",
                )
            )
        )

        if (
            is_assistance
            or (reference is not None and decision.intent == AgentIntent.UNKNOWN)
            or is_assistance_followup
        ):
            reference = reference or previous_reference

            if reference is None:
                return {
                    "message": render_reference_required(locale),
                    "intent": decision.intent.value,
                    "tool": None,
                }

            try:
                result = await self.mcp_client.call_tool(
                    "get_assistance_context",
                    {"public_reference": reference},
                )

                if result.is_error:
                    raise ValueError("Assistance lookup failed.")

                request = result.structured_content

                if not isinstance(request, dict):
                    raise ValueError("Invalid assistance context.")

                if (
                    request.get("public_reference") != reference
                    or request.get("verified") is not True
                    or request.get("approved") is not True
                    or request.get("status") not in {"OPEN", "ACTIVE"}
                ):
                    raise ValueError("Assistance request is unavailable.")

                response = render_assistance_context(
                    request,
                    locale=locale,
                )

            except (CommunityMCPClientError, ValueError, RuntimeError):
                return {
                    "message": (
                        "এই রেফারেন্সের অনুমোদিত সহায়তার তথ্য এখন যাচাই করা যাচ্ছে না।"
                        if locale == SupportedLocale.BN
                        else "Approved assistance information for \
                            this reference is currently unavailable."
                    ),
                    "intent": decision.intent.value,
                    "tool": None,
                }

            if session_id is not None:
                self.sessions.remember_assistance(session_id, reference)

            return {
                "message": response,
                "intent": decision.intent.value,
                "tool": "get_assistance_context",
            }

        topic = detect_event_topic(message)
        has_context = session_id is not None and self.sessions.has_event_context(session_id)

        is_event_question = decision.intent == AgentIntent.EVENT_CONTEXT
        is_event_followup = (
            has_context
            and topic is not None
            and decision.intent in {AgentIntent.EVENT_CONTEXT, AgentIntent.UNKNOWN}
        )

        if not (is_event_question or is_event_followup):
            return {
                "message": (
                    "For now, I can answer questions about our centenary celebration."
                    if locale == SupportedLocale.EN
                    else "আপাতত আমি আমাদের শতবর্ষ উদ্‌যাপন সম্পর্কে তথ্য দিতে পারি।"
                ),
                "intent": decision.intent.value,
                "tool": None,
            }

        result = await self.mcp_client.call_tool(
            "get_event_context",
            {"event_slug": self.EVENT_SLUG},
        )

        event = result.structured_content

        if not isinstance(event, dict):
            raise ValueError("MCP did not return structured event data.")

        if session_id is not None:
            self.sessions.remember_event(session_id, self.EVENT_SLUG)

        return {
            "message": render_event_answer(event, topic=topic, locale=locale),
            "intent": decision.intent.value,
            "tool": "get_event_context",
            "event": event,
        }

    @staticmethod
    def _render_event(
        event: dict[str, Any],
        locale: SupportedLocale,
    ) -> str:
        title = event.get("title") or "Centenary Celebration"
        starts_at = event.get("starts_at")
        registration_enabled = event.get("registration_enabled") is True

        if locale == SupportedLocale.BN:
            date_text = (
                f"অনুষ্ঠানের নির্ধারিত শুরুর সময়: {starts_at}।"
                if starts_at
                else "অনুষ্ঠানের তারিখ এখনো প্রকাশ করা হয়নি।"
            )

            registration_text = "নিবন্ধন চালু আছে।" if registration_enabled else "নিবন্ধন এখনো চালু হয়নি।"

            return f"{title}\n{date_text}\n{registration_text}"

        date_text = (
            f"The event starts at {starts_at}."
            if starts_at
            else "The event date has not been announced yet."
        )

        registration_text = (
            "Registration is currently enabled."
            if registration_enabled
            else "Registration is not currently enabled."
        )

        return f"{title}\n{date_text}\n{registration_text}"
