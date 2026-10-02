import pytest
from mcp import Client

from community_mcp.providers.demo import DemoProvider
from community_mcp.server import create_mcp_server


@pytest.mark.asyncio
async def test_assistance_context_is_exposed_through_mcp() -> None:
    mcp = create_mcp_server(DemoProvider())

    async with Client(mcp, raise_exceptions=True) as client:
        tools = await client.list_tools()

        assert {
            tool.name for tool in tools.tools
        } == {
            "get_event_context",
            "get_assistance_context",
        }

        result = await client.call_tool(
            "get_assistance_context",
            {"public_reference": "HELP-2026-001"},
        )

    assert result.is_error is False
    assert result.structured_content is not None

    request = result.structured_content

    assert request["public_reference"] == "HELP-2026-001"
    assert request["assistance_type"] == "BLOOD"
    assert request["blood_group"] == "B+"
    assert request["verified"] is True
    assert request["approved"] is True


@pytest.mark.asyncio
async def test_unknown_assistance_is_mcp_tool_error() -> None:
    mcp = create_mcp_server(DemoProvider())

    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_assistance_context",
            {"public_reference": "HELP-DOES-NOT-EXIST"},
        )

    assert result.is_error is True
