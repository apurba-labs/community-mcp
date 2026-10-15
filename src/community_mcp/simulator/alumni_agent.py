from __future__ import annotations

from typing import Any

from community_mcp.agent.schemas import AgentIntent, SupportedLocale
from community_mcp.providers.gotihub import GotiHubProvider
from community_mcp.simulator.event_renderer import (
    detect_event_topic,
    render_event_answer,
)


class AlumniAgent:
    EVENT_SLUG = "centenary-celebration"

    def __init__(self, *, provider: GotiHubProvider) -> None:
        self.provider = provider

    async def handle(
        self,
        *,
        message: str,
        locale: SupportedLocale = SupportedLocale.EN,
        session_id: str | None = None,
    ) -> dict[str, Any]:
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
