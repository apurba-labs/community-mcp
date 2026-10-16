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
                "শতবর্ষ উদ্‌যাপনের মূল অনুষ্ঠানের তারিখ এখনো আনুষ্ঠানিকভাবে "
                "ঘোষণা করা হয়নি। আগামী ২২ অক্টোবর ২০২৬ তারিখে আয়োজক "
                "কমিটির সভায় অনুষ্ঠানের নিবন্ধন শুরুর সম্ভাব্য তারিখ "
                "এবং মূল অনুষ্ঠানের সম্ভাব্য তারিখ নিয়ে আলোচনা করার "
                "পরিকল্পনা রয়েছে। "
                "চূড়ান্ত সিদ্ধান্ত ও সর্বশেষ তথ্য জানতে বিদ্যালয়ের "
                "অফিসিয়াল ফেসবুক পেজ, হোয়াটসঅ্যাপ গ্রুপ এবং "
                "ওয়েবসাইটের সংবাদ বিভাগে নজর রাখুন। "
                "বিস্তারিত: https://chandaikonamlhs.org/news"
                if bn
                else "The centenary celebration date has not yet been "
                "officially announced. The organizing committee plans "
                "to discuss possible dates for opening event registration "
                "and holding the main celebration at its meeting on "
                "22 October 2026. Please follow the school's official "
                "Facebook page, WhatsApp group, and news section "
                "for confirmed announcements: "
                "https://chandaikonamlhs.org/news"
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
            "শতবর্ষ উদ্‌যাপনের অনুষ্ঠানের নিবন্ধন এখনো আনুষ্ঠানিকভাবে "
            "শুরু হয়নি। নিবন্ধন শুরুর তারিখ, পদ্ধতি এবং প্রয়োজনীয় "
            "নির্দেশনা আয়োজক কমিটির সিদ্ধান্ত অনুযায়ী জানানো হবে। "
            "আপনার যদি বিদ্যালয়ের Alumni প্ল্যাটফর্মে অ্যাকাউন্ট "
            "না থাকে, তাহলে এখনই একটি অ্যাকাউন্ট তৈরি করে "
            "আপনার প্রোফাইলের তথ্য সম্পূর্ণ রাখতে পারেন। "
            "এতে ভবিষ্যতে বিদ্যালয়ের গুরুত্বপূর্ণ ঘোষণা এবং "
            "নিবন্ধনসংক্রান্ত আপডেট সহজে জানতে পারবেন। "
            "মনে রাখবেন, Alumni প্ল্যাটফর্মে অ্যাকাউন্ট তৈরি করা "
            "এবং শতবর্ষ উদ্‌যাপনের অনুষ্ঠানে নিবন্ধন করা "
            "দুটি আলাদা প্রক্রিয়া। "
            "ওয়েবসাইট: https://chandaikonamlhs.org "
            "সর্বশেষ সংবাদ: https://chandaikonamlhs.org/news"
            if bn
            else "Centenary event registration has not officially opened. "
            "The organizing committee will announce the registration "
            "dates, process, and instructions. "
            "If you do not have an Alumni platform account, you can "
            "create one now and complete your profile to make it "
            "easier to follow school announcements and registration "
            "updates. Creating an Alumni account and registering "
            "for the centenary event are two separate processes. "
            "Website: https://chandaikonamlhs.org "
            "News: https://chandaikonamlhs.org/news"
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
