from __future__ import annotations

from typing import Any

from community_mcp.agent.bedrock import BedrockReasoner
from community_mcp.agent.schemas import AgentIntent, SupportedLocale
from community_mcp.simulator.mcp_client import CommunityMCPClient


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

    async def handle(
        self,
        *,
        message: str,
        locale: SupportedLocale = SupportedLocale.EN,
    ) -> dict[str, Any]:
        if not message.strip():
            raise ValueError("Message cannot be empty.")

        decision = await self.reasoner.reason(
            message=message,
            locale=locale,
        )

        if decision.intent != AgentIntent.EVENT_CONTEXT:
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

        return {
            "message": self._render_event(event, locale),
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
