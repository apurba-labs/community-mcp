from community_mcp.agent.schemas import SupportedLocale
from community_mcp.schemas.action import ConfirmedAssistanceResponse
from community_mcp.schemas.assistance import AssistanceRequest
from community_mcp.schemas.community import MyBatchContext
from community_mcp.schemas.event import EventDetail


class BilingualRenderer:
    def event_context(
        self,
        event: EventDetail,
        locale: SupportedLocale,
    ) -> str:
        program = ", ".join(item.title for item in event.program)

        if locale == SupportedLocale.BN:
            return f"{event.title} অনুষ্ঠানের প্রধান কার্যক্রম: {program}।"

        return f"The main activities for {event.title} are: {program}."

    def community_context(
        self,
        context: MyBatchContext,
        locale: SupportedLocale,
    ) -> str:
        if locale == SupportedLocale.BN:
            return (
                f"আপনার {context.batch_year} ব্যাচের "
                f"{context.registered_alumni_count} জন অ্যালামনাই "
                "প্ল্যাটফর্মে নিবন্ধিত আছেন।"
            )

        return (
            f"There are {context.registered_alumni_count} registered alumni "
            f"from your {context.batch_year} batch on the platform."
        )

    def community_context_unavailable(
        self,
        locale: SupportedLocale,
    ) -> str:
        if locale == SupportedLocale.BN:
            return "আপনার অ্যালামনাই ব্যাচের তথ্য এখন নিরাপদভাবে যাচাই করা যাচ্ছে না।"

        return "Your alumni batch context cannot be securely resolved right now."

    def assistance_context(
        self,
        request: AssistanceRequest,
        locale: SupportedLocale,
    ) -> str:
        blood_group = request.blood_group or "N/A"

        if locale == SupportedLocale.BN:
            return f"একটি যাচাইকৃত {blood_group} রক্তের অনুরোধ রয়েছে। স্থান: {request.location_text}।"

        return (
            f"There is a verified {blood_group} blood request. Location: {request.location_text}."
        )

    def confirmation_required(
        self,
        locale: SupportedLocale,
    ) -> str:
        if locale == SupportedLocale.BN:
            return (
                "আপনার রক্তদানের সাড়া প্রস্তুত করা হয়েছে। "
                "এটি রেকর্ড করার আগে আপনার নিশ্চিতকরণ প্রয়োজন। "
                "আপনি কি নিশ্চিত করতে চান?"
            )

        return (
            "Your blood donation response has been prepared. "
            "Your confirmation is required before it is recorded. "
            "Would you like to confirm?"
        )

    def action_confirmed(
        self,
        result: ConfirmedAssistanceResponse,
        locale: SupportedLocale,
    ) -> str:
        if locale == SupportedLocale.BN:
            return "আপনার সাহায্যের সাড়া সফলভাবে রেকর্ড করা হয়েছে। ধন্যবাদ।"

        return "Your assistance response has been recorded. Thank you."

    def unknown(self, locale: SupportedLocale) -> str:
        if locale == SupportedLocale.BN:
            return "আমি এই অনুরোধটি এখনো বুঝতে পারিনি। অনুষ্ঠান বা কমিউনিটি সহায়তা সম্পর্কে জিজ্ঞাসা করতে পারেন।"

        return (
            "I couldn't understand that request yet. "
            "You can ask about events or community assistance."
        )

    def no_pending_action(
        self,
        locale: SupportedLocale,
    ) -> str:
        if locale == SupportedLocale.BN:
            return "নিশ্চিত করার মতো কোনো প্রস্তুত কার্যক্রম নেই। প্রথমে আপনি কীভাবে সাহায্য করতে চান তা জানান।"

        return "There is no pending action to confirm. First tell me how you'd like to help."
