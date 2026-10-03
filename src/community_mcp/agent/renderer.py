from community_mcp.agent.schemas import SupportedLocale
from community_mcp.schemas.action import ConfirmedAssistanceResponse
from community_mcp.schemas.assistance import AssistanceRequest
from community_mcp.schemas.event import EventDetail


class BilingualRenderer:
    def event_context(
        self,
        event: EventDetail,
        locale: SupportedLocale,
    ) -> str:
        schedules = ", ".join(
            schedule.title for schedule in event.schedules
        )

        if locale == SupportedLocale.BN:
            return (
                f"{event.title} অনুষ্ঠানের প্রধান কার্যক্রম: "
                f"{schedules}।"
            )

        return (
            f"The main activities for {event.title} are: "
            f"{schedules}."
        )

    def assistance_context(
        self,
        request: AssistanceRequest,
        locale: SupportedLocale,
    ) -> str:
        blood_group = request.blood_group or "N/A"

        if locale == SupportedLocale.BN:
            return (
                f"একটি যাচাইকৃত {blood_group} রক্তের অনুরোধ রয়েছে। "
                f"স্থান: {request.location_text}।"
            )

        return (
            f"There is a verified {blood_group} blood request. "
            f"Location: {request.location_text}."
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
            return (
                "আমি এই অনুরোধটি এখনো বুঝতে পারিনি। "
                "অনুষ্ঠান বা কমিউনিটি সহায়তা সম্পর্কে জিজ্ঞাসা করতে পারেন।"
            )

        return (
            "I couldn't understand that request yet. "
            "You can ask about events or community assistance."
        )
