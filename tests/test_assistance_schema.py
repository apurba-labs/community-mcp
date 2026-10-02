import json
from pathlib import Path

from community_mcp.schemas.assistance import (
    AssistanceAction,
    AssistanceRequest,
    AssistanceStatus,
    AssistanceType,
)


def test_demo_blood_assistance_is_public_safe() -> None:
    fixture = (
        Path(__file__).parents[1]
        / "demo"
        / "fixtures"
        / "assistance.json"
    )

    payload = json.loads(fixture.read_text())[0]
    request = AssistanceRequest.model_validate(payload)

    assert request.assistance_type == AssistanceType.BLOOD
    assert request.status == AssistanceStatus.ACTIVE
    assert request.blood_group == "B+"
    assert request.units_needed == 2
    assert request.verified is True
    assert request.approved is True

    assert AssistanceAction.DONATE_BLOOD in request.allowed_actions


def test_public_assistance_contract_contains_no_private_person_data() -> None:
    fields = set(AssistanceRequest.model_fields)

    forbidden_fields = {
        "patient_name",
        "patient_phone",
        "phone",
        "email",
        "donors",
        "donor_ids",
        "medical_history",
        "diagnosis",
        "payment_details",
    }

    assert fields.isdisjoint(forbidden_fields)
