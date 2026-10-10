from community_mcp.agent.schemas import AgentIntent


class IntentRouter:
    def classify(self, message: str) -> AgentIntent:
        normalized = message.casefold().strip()

        confirmation_phrases = {
            "yes confirm",
            "confirm",
            "yes, confirm it",
            "i confirm",
            "হ্যাঁ নিশ্চিত করুন",
            "হ্যাঁ, নিশ্চিত করুন",
            "হ্যাঁ, আমি নিশ্চিত করছি",
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
            "attending",
            "attend",
            "event registration",
            "registered for the centenary",
            "অনুষ্ঠান",
            "সময়সূচি",
            "শতবর্ষ",
            "ইভেন্ট",
            "অনুষ্ঠানে রেজিস্ট্রেশন",
            "অনুষ্ঠানে আসছে",
        )

        if any(term in normalized for term in event_terms):
            return AgentIntent.EVENT_CONTEXT

        community_terms = (
            "alumni",
            "alumni platform",
            "alumni community",
            "my batch",
            "batchmates",
            "registered alumni",
            "অ্যালামনাই",
            "আমার ব্যাচ",
            "ব্যাচের কতজন",
            "অ্যালামনাই কমিউনিটি",
            "অ্যালামনাই প্ল্যাটফর্ম",
            "রেজিস্টার্ড অ্যালামনাই",
        )

        if any(term in normalized for term in community_terms):
            return AgentIntent.COMMUNITY_CONTEXT

        return AgentIntent.UNKNOWN
