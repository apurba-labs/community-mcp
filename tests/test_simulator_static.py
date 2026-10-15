from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from community_mcp.simulator.api import create_simulator_app


@pytest.mark.asyncio
async def test_simulator_home_serves_html():
    app = create_simulator_app(agent_factory=lambda: AsyncMock())

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/simulator")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Community MCP" in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "content_type"),
    [
        ("/simulator/static/style.css", "text/css"),
        ("/simulator/static/app.js", "javascript"),
    ],
)
async def test_simulator_static_assets(path, content_type):
    app = create_simulator_app(agent_factory=lambda: AsyncMock())

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get(path)

    assert response.status_code == 200
    assert content_type in response.headers["content-type"]
