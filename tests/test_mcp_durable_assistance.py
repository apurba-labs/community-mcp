from uuid import UUID

import pytest
from mcp import Client

from community_mcp.config import Settings
from community_mcp.providers.demo import DemoProvider
from community_mcp.server import create_mcp_server


@pytest.mark.asyncio
async def test_mcp_confirmation_survives_server_restart(
    tmp_path,
    monkeypatch,
):
    database = tmp_path / "assistance.sqlite3"

    settings = Settings(
        data_provider="demo",
        demo_ledger_enabled=True,
        demo_ledger_path=str(database),
    )

    monkeypatch.setattr(
        "community_mcp.server.get_settings",
        lambda: settings,
    )

    first_server = create_mcp_server(
        DemoProvider(),
        capability_mode="demo",
    )
    async with Client(first_server, raise_exceptions=True) as client:
        prepared_result = await client.call_tool(
            "prepare_assistance_response",
            {
                "public_reference": "HELP-2026-001",
                "actor_id": "demo-member-001",
                "action": "DONATE_BLOOD",
            },
        )

    preparation_id = prepared_result.structured_content["preparation_id"]

    restarted_server = create_mcp_server(
        DemoProvider(),
        capability_mode="demo",
    )
    async with Client(restarted_server, raise_exceptions=True) as client:
        confirmed_result = await client.call_tool(
            "confirm_assistance_response",
            {
                "preparation_id": preparation_id,
                "actor_id": "demo-member-001",
                "confirmed": True,
            },
        )

    assert confirmed_result.is_error is False
    assert UUID(confirmed_result.structured_content["response"]["preparation_id"]) == UUID(
        preparation_id
    )

    another_server = create_mcp_server(
        DemoProvider(),
        capability_mode="demo",
    )
    async with Client(another_server, raise_exceptions=False) as client:
        replay = await client.call_tool(
            "confirm_assistance_response",
            {
                "preparation_id": preparation_id,
                "actor_id": "demo-member-001",
                "confirmed": True,
            },
        )

    assert replay.is_error is True


@pytest.mark.asyncio
async def test_gotihub_mode_rejects_action_tools(monkeypatch):
    settings = Settings(
        data_provider="gotihub",
        gotihub_base_url="https://example.org",
        demo_ledger_enabled=False,
    )

    monkeypatch.setattr(
        "community_mcp.server.get_settings",
        lambda: settings,
    )

    # Explicit demo providers prevent external network access in this test.
    from community_mcp.providers.demo_assistance import DemoAssistanceProvider

    mcp = create_mcp_server(
        DemoProvider(),
        DemoAssistanceProvider(),
    )

    async with Client(mcp, raise_exceptions=False) as client:
        result = await client.call_tool(
            "prepare_assistance_response",
            {
                "public_reference": "HELP-2026-001",
                "actor_id": "demo-member-001",
                "action": "DONATE_BLOOD",
            },
        )

    assert result.is_error is True
