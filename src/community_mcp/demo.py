import asyncio
from uuid import uuid4

from community_mcp.agent.community import CommunityAgent
from community_mcp.agent.schemas import AgentRequest, SupportedLocale
from community_mcp.providers.demo import DemoProvider


def detect_locale(message: str) -> SupportedLocale:
    if any("\u0980" <= char <= "\u09ff" for char in message):
        return SupportedLocale.BN

    return SupportedLocale.EN


async def run_demo() -> None:
    agent = CommunityAgent(DemoProvider())

    session_id = f"demo-{uuid4()}"
    actor_id = "demo-member-001"

    print()
    print("Community MCP")
    print("Trusted community context and permissioned actions")
    print("English + বাংলা")
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
