import pytest

from community_mcp.agent.bedrock import BedrockReasoner
from community_mcp.agent.reasoning import DeterministicReasoner
from community_mcp.agent.schemas import SupportedLocale
from community_mcp.config import Settings
from community_mcp.demo import build_reasoner, detect_locale


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        (
            "What is happening at the centenary event?",
            SupportedLocale.EN,
        ),
        (
            "শতবর্ষ অনুষ্ঠানের সময়সূচি কী?",
            SupportedLocale.BN,
        ),
        (
            "I can donate blood",
            SupportedLocale.EN,
        ),
        (
            "আমি রক্ত দিতে পারি",
            SupportedLocale.BN,
        ),
    ],
)
def test_detect_locale(
    message: str,
    expected: SupportedLocale,
) -> None:
    assert detect_locale(message) == expected


def test_demo_uses_deterministic_reasoning_by_default() -> None:
    settings = Settings(
        _env_file=None,
    )

    reasoner = build_reasoner(settings)

    assert isinstance(reasoner, DeterministicReasoner)


def test_demo_builds_bedrock_reasoner_when_configured() -> None:
    settings = Settings(
        _env_file=None,
        reasoning_provider="bedrock",
        aws_profile="community-mcp",
        bedrock_region="us-east-1",
        bedrock_model_id="amazon.nova-micro-v1:0",
    )

    reasoner = build_reasoner(settings)

    assert isinstance(reasoner, BedrockReasoner)
    assert reasoner.model_id == "amazon.nova-micro-v1:0"