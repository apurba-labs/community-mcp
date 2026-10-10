import pytest
from mcp import Client

from community_mcp.providers.demo import DemoProvider
from community_mcp.server import create_mcp_server


@pytest.mark.asyncio
async def test_assistance_response_requires_prepare_then_confirm() -> None:
    mcp = create_mcp_server(
        DemoProvider(),
        capability_mode="demo",
    )

    async with Client(mcp, raise_exceptions=True) as client:
        prepared_result = await client.call_tool(
            "prepare_assistance_response",
            {
                "public_reference": "HELP-2026-001",
                "actor_id": "demo-member-001",
                "action": "DONATE_BLOOD",
            },
        )

        prepared = prepared_result.structured_content

        assert prepared["decision"] == "REQUIRES_CONFIRMATION"
        assert prepared["confirmation_required"] is True

        confirmed_result = await client.call_tool(
            "confirm_assistance_response",
            {
                "preparation_id": prepared["preparation_id"],
                "actor_id": "demo-member-001",
                "confirmed": True,
            },
        )

    assert confirmed_result.is_error is False

    result = confirmed_result.structured_content

    assert result["response"]["public_reference"] == "HELP-2026-001"
    assert result["response"]["actor_id"] == "demo-member-001"
    assert result["response"]["action"] == "DONATE_BLOOD"

    assert result["audit"]["event_type"] == ("ASSISTANCE_RESPONSE_RECORDED")
    assert result["audit"]["actor_id"] == "demo-member-001"


@pytest.mark.asyncio
async def test_mcp_rejects_replay_of_confirmed_response() -> None:
    mcp = create_mcp_server(
        DemoProvider(),
        capability_mode="demo",
    )

    async with Client(mcp) as client:
        prepared_result = await client.call_tool(
            "prepare_assistance_response",
            {
                "public_reference": "HELP-2026-001",
                "actor_id": "demo-member-001",
                "action": "DONATE_BLOOD",
            },
        )

        preparation_id = prepared_result.structured_content["preparation_id"]

        first = await client.call_tool(
            "confirm_assistance_response",
            {
                "preparation_id": preparation_id,
                "actor_id": "demo-member-001",
                "confirmed": True,
            },
        )

        second = await client.call_tool(
            "confirm_assistance_response",
            {
                "preparation_id": preparation_id,
                "actor_id": "demo-member-001",
                "confirmed": True,
            },
        )

    assert first.is_error is False
    assert second.is_error is True
