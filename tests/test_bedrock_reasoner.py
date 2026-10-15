import pytest

from community_mcp.agent.bedrock import BedrockReasoner
from community_mcp.agent.schemas import AgentIntent, SupportedLocale
from community_mcp.agent.usage import BedrockUsage
from community_mcp.schemas.assistance import AssistanceAction


class FakeBedrockClient:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[dict] = []

    def converse(self, **kwargs: object) -> dict:
        self.calls.append(kwargs)

        return {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": self.text,
                        }
                    ]
                }
            }
        }


@pytest.mark.asyncio
async def test_bedrock_reasoner_returns_donation_decision() -> None:
    client = FakeBedrockClient('{"intent":"ASSISTANCE_RESPONSE","action":"DONATE_BLOOD"}')
    reasoner = BedrockReasoner(client=client)

    decision = await reasoner.reason(
        message="I'm B positive and would be happy to help.",
        locale=SupportedLocale.EN,
    )

    assert decision.intent == AgentIntent.ASSISTANCE_RESPONSE
    assert decision.action == AssistanceAction.DONATE_BLOOD
    assert decision.locale == SupportedLocale.EN
    assert len(client.calls) == 1


@pytest.mark.asyncio
async def test_bedrock_reasoner_preserves_bangla_locale() -> None:
    client = FakeBedrockClient('{"intent":"ASSISTANCE_RESPONSE","action":"DONATE_BLOOD"}')
    reasoner = BedrockReasoner(client=client)

    decision = await reasoner.reason(
        message="আমার রক্তের গ্রুপ B+। প্রয়োজন হলে আমি রক্ত দিতে পারি।",
        locale=SupportedLocale.BN,
    )

    assert decision.locale == SupportedLocale.BN
    assert decision.action == AssistanceAction.DONATE_BLOOD


@pytest.mark.asyncio
async def test_bedrock_reasoner_rejects_invalid_json() -> None:
    reasoner = BedrockReasoner(client=FakeBedrockClient("ASSISTANCE_RESPONSE"))

    with pytest.raises(
        ValueError,
        match="invalid agent decision",
    ):
        await reasoner.reason(
            message="I can help.",
            locale=SupportedLocale.EN,
        )


@pytest.mark.asyncio
async def test_bedrock_reasoner_rejects_action_on_context_intent() -> None:
    reasoner = BedrockReasoner(
        client=FakeBedrockClient('{"intent":"ASSISTANCE_CONTEXT","action":"DONATE_BLOOD"}')
    )

    with pytest.raises(
        ValueError,
        match="Only assistance responses",
    ):
        await reasoner.reason(
            message="Does anyone need blood?",
            locale=SupportedLocale.EN,
        )


@pytest.mark.asyncio
async def test_bedrock_reasoner_requires_action_for_response() -> None:
    reasoner = BedrockReasoner(
        client=FakeBedrockClient('{"intent":"ASSISTANCE_RESPONSE","action":null}')
    )

    with pytest.raises(
        ValueError,
        match="requires a canonical action",
    ):
        await reasoner.reason(
            message="I can donate blood.",
            locale=SupportedLocale.EN,
        )


@pytest.mark.asyncio
async def test_bedrock_reasoner_records_token_usage() -> None:
    client = FakeBedrockClient('{"intent":"EVENT_CONTEXT","action":null}')
    original_converse = client.converse

    def converse_with_usage(**kwargs):
        response = original_converse(**kwargs)
        response["usage"] = {
            "inputTokens": 120,
            "outputTokens": 18,
            "totalTokens": 138,
        }
        return response

    client.converse = converse_with_usage

    recorded: list[BedrockUsage] = []

    reasoner = BedrockReasoner(
        client=client,
        usage_recorder=recorded.append,
    )

    decision = await reasoner.reason(
        message="When is the centenary celebration?",
        locale=SupportedLocale.EN,
    )

    assert decision.intent == AgentIntent.EVENT_CONTEXT
    assert recorded == [
        BedrockUsage(
            model_id="amazon.nova-micro-v1:0",
            input_tokens=120,
            output_tokens=18,
            total_tokens=138,
        )
    ]


@pytest.mark.asyncio
async def test_bedrock_reasoner_records_usage_before_invalid_decision() -> None:
    class InvalidResponseClient:
        def converse(self, **kwargs):
            return {
                "output": {"message": {"content": [{"text": "not valid JSON"}]}},
                "usage": {
                    "inputTokens": 90,
                    "outputTokens": 12,
                    "totalTokens": 102,
                },
            }

    recorded: list[BedrockUsage] = []

    reasoner = BedrockReasoner(
        client=InvalidResponseClient(),
        usage_recorder=recorded.append,
    )

    with pytest.raises(ValueError, match="invalid agent decision"):
        await reasoner.reason(
            message="Can I help?",
            locale=SupportedLocale.EN,
        )

    assert len(recorded) == 1
    assert recorded[0].total_tokens == 102


@pytest.mark.asyncio
async def test_bedrock_reasoner_handles_missing_usage_metadata() -> None:
    recorded: list[BedrockUsage] = []

    reasoner = BedrockReasoner(
        client=FakeBedrockClient('{"intent":"EVENT_CONTEXT","action":null}'),
        usage_recorder=recorded.append,
    )

    decision = await reasoner.reason(
        message="When is the event?",
        locale=SupportedLocale.EN,
    )

    assert decision.intent == AgentIntent.EVENT_CONTEXT
    assert recorded == []
