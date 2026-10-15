from __future__ import annotations

from community_mcp.agent.bedrock import BedrockReasoner
from community_mcp.config import get_settings
from community_mcp.simulator.agent import SimulatorAgent
from community_mcp.simulator.api import create_simulator_app
from community_mcp.simulator.mcp_client import CommunityMCPClient
from community_mcp.usage.context import record_bedrock_usage
from community_mcp.usage.store import SQLiteUsageStore, UsageBudget


def create_app():
    settings = get_settings()

    if not settings.simulator_mcp_url:
        raise RuntimeError("SIMULATOR_MCP_URL is required.")

    if bool(settings.simulator_mcp_access_token) == bool(settings.simulator_mcp_token_file):
        raise RuntimeError(
            "Exactly one of SIMULATOR_MCP_ACCESS_TOKEN or SIMULATOR_MCP_TOKEN_FILE is required."
        )

    reasoner = BedrockReasoner(
        model_id=settings.bedrock_model_id,
        region_name=settings.bedrock_region,
        profile_name=settings.aws_profile,
        usage_recorder=record_bedrock_usage,
    )

    mcp_client = CommunityMCPClient(
        server_url=settings.simulator_mcp_url,
        access_token=settings.simulator_mcp_access_token,
        token_file=settings.simulator_mcp_token_file,
    )

    # Shared agent preserves temporary conversation context.
    agent = SimulatorAgent(
        mcp_client=mcp_client,
        reasoner=reasoner,
    )

    usage_store = SQLiteUsageStore(settings.simulator_usage_db_path)

    public_budget = UsageBudget(
        daily_requests=300,
        concurrent_requests=5,
        daily_tokens=150_000,
    )

    alumni_budget = UsageBudget(
        daily_requests=200,
        concurrent_requests=3,
        daily_tokens=100_000,
    )

    return create_simulator_app(
        agent_factory=lambda: agent,
        internal_api_token=settings.simulator_internal_api_token,
        usage_store=usage_store,
        public_budget=public_budget,
        alumni_budget=alumni_budget,
        model_id=settings.bedrock_model_id,
    )
