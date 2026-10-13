from __future__ import annotations

import os

from community_mcp.agent.bedrock import BedrockReasoner
from community_mcp.config import get_settings
from community_mcp.simulator.agent import SimulatorAgent
from community_mcp.simulator.api import create_simulator_app
from community_mcp.simulator.mcp_client import CommunityMCPClient


def create_app():
    settings = get_settings()

    mcp_url = os.environ.get("SIMULATOR_MCP_URL")
    mcp_token = os.environ.get("SIMULATOR_MCP_ACCESS_TOKEN")
    internal_api_token = os.environ.get("SIMULATOR_INTERNAL_API_TOKEN")

    if not mcp_url:
        raise RuntimeError("SIMULATOR_MCP_URL is required.")

    if not mcp_token:
        raise RuntimeError("SIMULATOR_MCP_ACCESS_TOKEN is required.")

    reasoner = BedrockReasoner(
        model_id=settings.bedrock_model_id,
        region_name=settings.bedrock_region,
        profile_name=settings.aws_profile,
    )

    mcp_client = CommunityMCPClient(
        server_url=mcp_url,
        access_token=mcp_token,
    )

    # One shared agent preserves temporary conversation context.
    agent = SimulatorAgent(
        mcp_client=mcp_client,
        reasoner=reasoner,
    )

    return create_simulator_app(
        agent_factory=lambda: agent,
        internal_api_token=internal_api_token,
    )
