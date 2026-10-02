import pytest
from mcp import Client

from community_mcp.providers.demo import DemoProvider
from community_mcp.server import create_mcp_server


@pytest.mark.asyncio
async def test_mcp_prepares_response_but_requires_confirmation() -> None:
    mcp = create_mcp_server(DemoProvider())

    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.call_tool(
            "prepare_assistance_response",
            {
                "public_reference": "HELP-2026-001",
                "actor_id": "demo-member-001",
                "action": "DONATE_BLOOD",
            },
        )

    assert result.is_error is False
    assert result.structured_content is not None

    prepared = result.structured_content

    assert prepared["public_reference"] == "HELP-2026-001"
    assert prepared["actor_id"] == "demo-member-001"
    assert prepared["action"] == "DONATE_BLOOD"
    assert prepared["decision"] == "REQUIRES_CONFIRMATION"
    assert prepared["confirmation_required"] is True
    assert prepared["preparation_id"]


@pytest.mark.asyncio
async def test_mcp_denies_response_without_actor_identity() -> None:
    mcp = create_mcp_server(DemoProvider())

    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.call_tool(
            "prepare_assistance_response",
            {
                "public_reference": "HELP-2026-001",
                "actor_id": "",
                "action": "DONATE_BLOOD",
            },
        )

    assert result.is_error is False

    prepared = result.structured_content

    assert prepared["decision"] == "DENIED"
    assert prepared["confirmation_required"] is False
