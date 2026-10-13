"""Safe, read-only rendering of public assistance context."""

from __future__ import annotations

import re
from typing import Any

from community_mcp.agent.schemas import SupportedLocale

REFERENCE_PATTERN = re.compile(r"\bHELP-\d{4}-\d{3,6}\b", re.IGNORECASE)


def extract_public_reference(message: str) -> str | None:
    """Extract an explicit public assistance reference from user input."""
    match = REFERENCE_PATTERN.search(message)
    return match.group(0).upper() if match else None


def render_reference_required(locale: SupportedLocale) -> str:
    if locale == SupportedLocale.BN:
        return (
            "আমি অনুমোদিত সহায়তার অনুরোধ যাচাই করতে পারি। "
            "অনুগ্রহ করে প্রকাশিত রেফারেন্স নম্বর দিন, যেমন HELP-2026-001। "
            "রেফারেন্স ছাড়া সব অনুরোধ অনুসন্ধান করার সুবিধা এখনো নেই।"
        )

    return (
        "I can check an approved public assistance request. "
        "Please provide its published reference, such as HELP-2026-001. "
        "Searching all assistance requests is not currently supported."
    )


def render_assistance_context(
    request: dict[str, Any],
    *,
    locale: SupportedLocale,
) -> str:
    """Render only explicitly allowlisted public fields."""

    reference = request.get("public_reference")
    status = request.get("status")
    assistance_type = request.get("assistance_type")
    urgency = request.get("urgency")
    summary = request.get("summary")

    if not isinstance(reference, str) or not isinstance(summary, str):
        raise ValueError("Incomplete public assistance context.")

    if locale == SupportedLocale.BN:
        return (
            f"সহায়তার রেফারেন্স: {reference}\n"
            f"ধরন: {assistance_type or 'প্রকাশিত নয়'}\n"
            f"অবস্থা: {status or 'প্রকাশিত নয়'}\n"
            f"জরুরি মাত্রা: {urgency or 'প্রকাশিত নয়'}\n"
            f"বিবরণ: {summary}\n\n"
            "এটি প্রকাশের জন্য অনুমোদিত তথ্য। "
            "ব্যক্তিগত যোগাযোগের তথ্য এখানে দেখানো হয় না।"
        )

    return (
        f"Assistance reference: {reference}\n"
        f"Type: {assistance_type or 'Not published'}\n"
        f"Status: {status or 'Not published'}\n"
        f"Urgency: {urgency or 'Not published'}\n"
        f"Summary: {summary}\n\n"
        "This is approved public information. "
        "Private contact details are not displayed."
    )
