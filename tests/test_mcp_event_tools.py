import pytest
from mcp import Client

from community_mcp.providers.demo import DemoProvider
from community_mcp.server import create_mcp_server


@pytest.mark.asyncio
async def test_event_context_is_exposed_through_mcp() -> None:
    mcp = create_mcp_server(DemoProvider())

    async with Client(mcp, raise_exceptions=True) as client:
        tools = await client.list_tools()

        assert [tool.name for tool in tools.tools] == ["get_event_context"]

        result = await client.call_tool(
            "get_event_context",
            {"event_slug": "centenary-celebration"},
        )

    assert result.is_error is False
    assert result.structured_content is not None

    event = result.structured_content

    assert event["slug"] == "centenary-celebration"
    assert event["event_type"] == "CENTENARY"
    assert len(event["program"]) == 3
    assert event["program"][0]["title"] == "Alumni Gathering"


@pytest.mark.asyncio
async def test_missing_event_returns_mcp_tool_error() -> None:
    mcp = create_mcp_server(DemoProvider())

    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_event_context",
            {"event_slug": "does-not-exist"},
        )

    assert result.is_error is True
