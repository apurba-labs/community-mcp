from community_mcp.agent.schemas import AgentIntent


class IntentRouter:
    def classify(self, message: str) -> AgentIntent:
        normalized = message.casefold().strip()

        confirmation_phrases = {
            "yes",
            "yes confirm",
            "confirm",
            "হ্যাঁ",
            "হ্যাঁ নিশ্চিত করুন",
            "নিশ্চিত করুন",
        }

        if normalized in confirmation_phrases:
            return AgentIntent.CONFIRM_ACTION

        assistance_response_terms = (
            "i can donate",
            "i want to donate",
            "donate blood",
            "give blood",
            "আমি রক্ত দিতে পারি",
            "আমি রক্ত দিতে চাই",
            "রক্ত দিতে চাই",
        )

        if any(term in normalized for term in assistance_response_terms):
            return AgentIntent.ASSISTANCE_RESPONSE

        assistance_terms = (
            "blood",
            "assistance",
            "help request",
            "রক্ত",
            "সহায়তা",
            "সাহায্য",
        )

        if any(term in normalized for term in assistance_terms):
            return AgentIntent.ASSISTANCE_CONTEXT

        event_terms = (
            "event",
            "program",
            "schedule",
            "centenary",
            "celebration",
            "অনুষ্ঠান",
            "সময়সূচি",
            "শতবর্ষ",
        )

        if any(term in normalized for term in event_terms):
            return AgentIntent.EVENT_CONTEXT

        return AgentIntent.UNKNOWN
