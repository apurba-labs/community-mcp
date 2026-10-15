"""Local-only simulator with a real MCP transport and Bedrock reasoning.

Development utility. Never deploy this module as a production service.
"""

from __future__ import annotations

import asyncio
import socket
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import uvicorn
from mcp.server.auth.provider import AccessToken

from community_mcp.agent.bedrock import BedrockReasoner
from community_mcp.config import Settings
from community_mcp.providers.demo import DemoProvider
from community_mcp.providers.gotihub import GotiHubProvider
from community_mcp.server import create_mcp_server
from community_mcp.simulator.agent import SimulatorAgent
from community_mcp.simulator.alumni_agent import AlumniAgent
from community_mcp.simulator.api import create_simulator_app
from community_mcp.simulator.mcp_client import CommunityMCPClient
from community_mcp.usage.context import record_bedrock_usage
from community_mcp.usage.store import SQLiteUsageStore, UsageBudget

LOCAL_TOKEN = "local-simulator-test-token"


def create_local_mcp_app():
    settings = Settings(
        app_env="development",
        data_provider="demo",
        mcp_capability_mode="public",
        mcp_auth_enabled=True,
        mcp_auth_issuer_url="https://auth.example.test",
        mcp_auth_audience="https://mcp.example.test/mcp",
        mcp_auth_jwks_url="https://auth.example.test/jwks.json",
        mcp_auth_required_scope="community.read",
    )

    # Keep the local MCP server isolated from production settings.
    import community_mcp.server as server_module

    original_get_settings = server_module.get_settings
    server_module.get_settings = lambda: settings

    try:
        server = create_mcp_server(
            DemoProvider(),
            capability_mode="public",
        )
    finally:
        server_module.get_settings = original_get_settings

    async def verify_token(token):
        if token != LOCAL_TOKEN:
            return None

        return AccessToken(
            token=token,
            client_id="local-simulator",
            scopes=["community.read"],
            resource="https://mcp.example.test/mcp",
        )

    server._token_verifier.verify_token = AsyncMock(
        side_effect=verify_token,
    )

    return server.streamable_http_app(
        json_response=True,
        stateless_http=True,
        host="127.0.0.1",
    )


@asynccontextmanager
async def local_mcp_server():
    app = create_local_mcp_app()

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="error",
        lifespan="on",
    )

    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())

    try:
        for _ in range(100):
            if server.started:
                break

            if task.done():
                raise RuntimeError("Local MCP server exited unexpectedly.")

            await asyncio.sleep(0.05)
        else:
            raise RuntimeError("Local MCP server failed to start.")

        yield f"http://127.0.0.1:{port}/mcp"

    finally:
        server.should_exit = True
        await asyncio.wait_for(task, timeout=10)


async def main():
    from community_mcp.config import Settings

    async with local_mcp_server() as mcp_url:
        settings = Settings()
        model_id = "amazon.nova-micro-v1:0"

        reasoner = BedrockReasoner(
            profile_name="community-mcp",
            region_name="us-east-1",
            model_id=model_id,
            usage_recorder=record_bedrock_usage,
        )

        client = CommunityMCPClient(
            server_url=mcp_url,
            access_token=LOCAL_TOKEN,
        )

        agent = SimulatorAgent(
            mcp_client=client,
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

        internal_api_token = settings.simulator_internal_api_token

        if not internal_api_token:
            raise RuntimeError("SIMULATOR_INTERNAL_API_TOKEN is required.")

        if not all(
            (
                settings.gotihub_base_url,
                settings.gotihub_organization_slug,
                settings.gotihub_service_token,
                settings.gotihub_organization_id,
            )
        ):
            raise RuntimeError("GotiHub Alumni integration settings are incomplete.")

        alumni_agent = AlumniAgent(
            provider=GotiHubProvider(
                base_url=str(settings.gotihub_base_url),
                organization_slug=settings.gotihub_organization_slug,
                service_token=settings.gotihub_service_token,
            )
        )

        app = create_simulator_app(
            agent_factory=lambda: agent,
            internal_agent_factory=lambda: alumni_agent,
            internal_organization_id=settings.gotihub_organization_id,
            internal_api_token=internal_api_token,
            usage_store=usage_store,
            public_budget=public_budget,
            alumni_budget=alumni_budget,
            model_id=model_id,
        )

        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=8080,
            log_level="info",
        )

        server = uvicorn.Server(config)

        print()
        print("Community MCP — Alexa+ Experience Simulator")
        print("Browser: http://127.0.0.1:8080/simulator")
        print("MCP:     Local authenticated demo server")
        print("Bedrock: Amazon Nova Micro")
        print()

        await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
