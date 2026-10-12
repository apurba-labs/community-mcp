import pytest

from community_mcp.assistance.service import (
    AssistanceNotFoundError,
    AssistanceService,
)


@pytest.mark.asyncio
async def test_returns_verified_public_assistance_context() -> None:
    service = AssistanceService()

    request = await service.get_public_context("HELP-2026-001")

    assert request.public_reference == "HELP-2026-001"
    assert request.blood_group == "B+"
    assert request.verified is True
    assert request.approved is True


@pytest.mark.asyncio
async def test_unknown_assistance_request_is_not_found() -> None:
    service = AssistanceService()

    with pytest.raises(AssistanceNotFoundError):
        await service.get_public_context("HELP-DOES-NOT-EXIST")
