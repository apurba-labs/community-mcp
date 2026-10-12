import asyncio
from uuid import uuid4

from community_mcp.agent.bedrock import BedrockReasoner
from community_mcp.agent.community import CommunityAgent
from community_mcp.agent.reasoning import (
    DeterministicReasoner,
    ReasoningProvider,
)
from community_mcp.agent.safe_reasoning import SafeReasoner
from community_mcp.agent.schemas import AgentRequest, SupportedLocale
from community_mcp.assistance.sqlite_store import SQLiteAssistanceStore
from community_mcp.config import Settings, get_settings
from community_mcp.providers.demo import DemoProvider
from community_mcp.providers.demo_member_context import (
    DemoMemberContextProvider,
)


def detect_locale(message: str) -> SupportedLocale:
    if any("\u0980" <= char <= "\u09ff" for char in message):
        return SupportedLocale.BN

    return SupportedLocale.EN


def build_reasoner(settings: Settings) -> ReasoningProvider:
    if settings.reasoning_provider == "bedrock":
        delegate = BedrockReasoner(
            profile_name=settings.aws_profile,
            region_name=settings.bedrock_region,
            model_id=settings.bedrock_model_id,
        )
    else:
        delegate = DeterministicReasoner()

    return SafeReasoner(delegate)


async def run_demo() -> None:
    settings = get_settings()
    reasoner = build_reasoner(settings)
    if settings.data_provider != "demo":
        raise RuntimeError("Interactive synthetic actions require DATA_PROVIDER=demo.")

    durable_store = (
        SQLiteAssistanceStore(settings.demo_ledger_path) if settings.demo_ledger_enabled else None
    )

    agent = CommunityAgent(
        DemoProvider(),
        reasoner=reasoner,
        member_context_provider=DemoMemberContextProvider(),
        durable_store=durable_store,
        allow_demo_actions=True,
    )

    session_id = f"demo-{uuid4()}"
    actor_id = "demo-member-001"

    print()
    print("Community MCP")
    print("Trusted community context and permissioned actions")
    print("English + বাংলা")
    print(f"Reasoning: {settings.reasoning_provider}")
    print()
    print("Type 'exit' to finish.")
    print()

    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not message:
            continue

        if message.casefold() in {"exit", "quit"}:
            break

        locale = detect_locale(message)

        response = await agent.handle(
            AgentRequest(
                message=message,
                locale=locale,
                actor_id=actor_id,
                session_id=session_id,
            )
        )

        print()
        print(f"Agent: {response.message}")

        if response.requires_confirmation:
            print("[confirmation required]")

        print()

    print("Demo finished.")


def main() -> None:
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
