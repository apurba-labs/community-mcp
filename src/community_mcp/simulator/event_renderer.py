from __future__ import annotations

from datetime import datetime
from typing import Any

from community_mcp.agent.schemas import SupportedLocale


def detect_event_topic(message: str) -> str | None:
    text = message.casefold()

    topics = {
        "registration": (
            "registration",
            "register",
            "sign up",
            "নিবন্ধন",
            "রেজিস্ট্রেশন",
        ),
        "venue": (
            "where",
            "venue",
            "location",
            "place",
            "কোথায়",
            "কোথায়",
            "স্থান",
        ),
        "date": (
            "when",
            "date",
            "time",
            "কবে",
            "তারিখ",
            "কখন",
        ),
        "program": (
            "program",
            "schedule",
            "activities",
            "অনুষ্ঠানসূচি",
            "কর্মসূচি",
        ),
        "guests": (
            "guest",
            "guests",
            "chief guest",
            "অতিথি",
        ),
    }

    for topic, keywords in topics.items():
        if any(keyword in text for keyword in keywords):
            return topic

    return None


def render_event_answer(
    event: dict[str, Any],
    *,
    topic: str | None,
    locale: SupportedLocale,
) -> str:
    bn = locale == SupportedLocale.BN
    title = event.get("title") or ("শতবর্ষ উদ্‌যাপন" if bn else "Centenary Celebration")

    if topic == "date":
        starts_at = event.get("starts_at")

        if not starts_at:
            return (
                "শতবর্ষ উদযাপনের তারিখ এখনো আনুষ্ঠানিকভাবে ঘোষণা করা হয়নি। "
                "তারিখ ঘোষণা করা হলে বিদ্যালয়ের ওয়েবসাইটের সংবাদ বিভাগে "
                "প্রকাশ করা হবে। বিস্তারিত: /news"
                if bn
                else "The centenary celebration date has not been officially announced yet. "
                "Please check the school's news section for official updates: /news"
            )

        try:
            date = datetime.fromisoformat(str(starts_at).replace("Z", "+00:00"))
            formatted = date.strftime("%d %B %Y, %H:%M")
        except ValueError:
            return (
                "অনুষ্ঠানের তারিখের তথ্য এখন যাচাই করা যাচ্ছে না।"
                if bn
                else "The event date could not be verified."
            )

        return f"অনুষ্ঠান শুরু হবে {formatted}।" if bn else f"The event starts on {formatted}."

    if topic == "registration":
        if event.get("registration_enabled") is True:
            return (
                "অনুষ্ঠানের নিবন্ধন বর্তমানে চালু আছে।"
                if bn
                else "Event registration is currently enabled."
            )

        return (
            "অনুষ্ঠানের নিবন্ধন বর্তমানে চালু নেই।"
            if bn
            else "Event registration is not currently enabled."
        )

    if topic == "venue":
        venue = event.get("primary_venue")

        if not isinstance(venue, dict) or not venue.get("name"):
            return (
                "অনুষ্ঠানের স্থান এখনো প্রকাশ করা হয়নি।"
                if bn
                else "The event venue has not been published yet."
            )

        name = venue["name"]
        return f"প্রকাশিত স্থান: {name}।" if bn else f"The listed venue is {name}."

    if topic == "program":
        program = event.get("program") or []

        if not program:
            return (
                "অনুষ্ঠানের বিস্তারিত কর্মসূচি এখনো প্রকাশ করা হয়নি।"
                if bn
                else "The detailed event program has not been published yet."
            )

        titles = [item["title"] for item in program if isinstance(item, dict) and item.get("title")]

        if not titles:
            return (
                "অনুষ্ঠানের বিস্তারিত কর্মসূচি এখনো প্রকাশ করা হয়নি।"
                if bn
                else "The detailed event program has not been published yet."
            )

        return (
            f"প্রকাশিত কর্মসূচি: {', '.join(titles)}।"
            if bn
            else f"Published activities: {', '.join(titles)}."
        )

    if topic == "guests":
        guests = event.get("guests") or []

        names = [item["name"] for item in guests if isinstance(item, dict) and item.get("name")]

        if not names:
            return (
                "অতিথিদের বিস্তারিত তালিকা এখনো প্রকাশ করা হয়নি।"
                if bn
                else "The guest list has not been published yet."
            )

        return f"প্রকাশিত অতিথি: {', '.join(names)}।" if bn else f"Listed guests: {', '.join(names)}."

    return (
        f"{title} সম্পর্কে আপনি তারিখ, নিবন্ধন, স্থান, অতিথি বা কর্মসূচি জানতে পারেন।"
        if bn
        else f"You can ask about {title}: dates, registration, venue, guests or program."
    )
