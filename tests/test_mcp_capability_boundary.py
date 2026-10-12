import pytest

from community_mcp.providers.demo import DemoProvider
from community_mcp.server import create_mcp_server


@pytest.mark.asyncio
async def test_public_mode_registers_only_public_tools():
    server = create_mcp_server(
        DemoProvider(),
        capability_mode="public",
    )

    tools = await server.list_tools()
    names = {tool.name for tool in tools}

    assert names == {
        "get_event_context",
        "get_assistance_context",
    }


@pytest.mark.asyncio
async def test_demo_mode_registers_action_tools():
    server = create_mcp_server(
        DemoProvider(),
        capability_mode="demo",
    )

    tools = await server.list_tools()
    names = {tool.name for tool in tools}

    assert names == {
        "get_event_context",
        "get_assistance_context",
        "prepare_assistance_response",
        "confirm_assistance_response",
    }


def test_production_rejects_demo_capabilities(monkeypatch):
    from community_mcp.config import Settings

    settings = Settings(
        app_env="production",
        data_provider="gotihub",
        mcp_capability_mode="public",
    )

    monkeypatch.setattr(
        "community_mcp.server.get_settings",
        lambda: settings,
    )

    with pytest.raises(
        ValueError,
        match="Production MCP server must use public capability mode",
    ):
        create_mcp_server(
            DemoProvider(),
            capability_mode="demo",
        )
