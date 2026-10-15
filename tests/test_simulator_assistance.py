from __future__ import annotations

from community_mcp.agent.schemas import SupportedLocale
from community_mcp.simulator.assistance import (
    extract_public_reference,
    render_assistance_context,
    render_reference_required,
)


def test_extract_assistance_reference():
    assert extract_public_reference("Please check help-2026-001") == "HELP-2026-001"


def test_missing_reference():
    assert extract_public_reference("Does anyone need blood?") is None


def test_bangla_reference_required():
    response = render_reference_required(SupportedLocale.BN)

    assert "রেফারেন্স" in response
    assert "HELP-2026-001" in response


def test_public_assistance_renderer_excludes_private_fields():
    request = {
        "public_reference": "HELP-2026-001",
        "assistance_type": "BLOOD",
        "status": "ACTIVE",
        "urgency": "URGENT",
        "summary": "A verified community member needs blood support.",
        "phone_number": "PRIVATE-PHONE-123",
        "requester_name": "PRIVATE-NAME-123",
        "internal_notes": "PRIVATE-NOTES-123",
    }

    response = render_assistance_context(
        request,
        locale=SupportedLocale.EN,
    )

    assert "HELP-2026-001" in response
    assert "blood support" in response

    assert "PRIVATE-PHONE-123" not in response
    assert "PRIVATE-NAME-123" not in response
    assert "PRIVATE-NOTES-123" not in response


def test_bangla_assistance_labels():
    response = render_assistance_context(
        {
            "public_reference": "HELP-2026-001",
            "assistance_type": "BLOOD",
            "status": "ACTIVE",
            "urgency": "URGENT",
            "summary": "A verified community member needs blood support.",
        },
        locale=SupportedLocale.BN,
    )

    assert "ধরন: রক্ত সহায়তা" in response
    assert "অবস্থা: সক্রিয়" in response
    assert "জরুরি মাত্রা: জরুরি" in response
