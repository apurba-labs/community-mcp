import pytest

from community_mcp.providers.assistance import (
    AssistanceContextNotFoundError,
)
from community_mcp.providers.demo_assistance import DemoAssistanceProvider
from community_mcp.schemas.assistance import AssistanceStatus


@pytest.mark.asyncio
async def test_demo_assistance_returns_safe_synthetic_context() -> None:
    provider = DemoAssistanceProvider()

    request = await provider.get_public_context("HELP-2026-001")

    assert request.public_reference == "HELP-2026-001"
    assert request.status == AssistanceStatus.ACTIVE
    assert request.verified is True
    assert request.approved is True


@pytest.mark.asyncio
async def test_demo_assistance_rejects_unknown_reference() -> None:
    provider = DemoAssistanceProvider()

    with pytest.raises(AssistanceContextNotFoundError):
        await provider.get_public_context("HELP-UNKNOWN")
