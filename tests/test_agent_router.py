import pytest

from community_mcp.agent.router import IntentRouter
from community_mcp.agent.schemas import AgentIntent


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        (
            "What is the centenary event schedule?",
            AgentIntent.EVENT_CONTEXT,
        ),
        (
            "শতবর্ষ অনুষ্ঠানের সময়সূচি কী?",
            AgentIntent.EVENT_CONTEXT,
        ),
        (
            "Is there an urgent blood request?",
            AgentIntent.ASSISTANCE_CONTEXT,
        ),
        (
            "কোনো জরুরি রক্তের অনুরোধ আছে?",
            AgentIntent.ASSISTANCE_CONTEXT,
        ),
        (
            "I can donate blood",
            AgentIntent.ASSISTANCE_RESPONSE,
        ),
        (
            "আমি রক্ত দিতে পারি",
            AgentIntent.ASSISTANCE_RESPONSE,
        ),
        (
            "Yes confirm",
            AgentIntent.CONFIRM_ACTION,
        ),
        (
            "হ্যাঁ নিশ্চিত করুন",
            AgentIntent.CONFIRM_ACTION,
        ),
    ],
)
def test_bilingual_intent_routing(
    message: str,
    expected: AgentIntent,
) -> None:
    assert IntentRouter().classify(message) == expected


def test_unknown_message_is_not_invented_as_an_intent() -> None:
    assert (
        IntentRouter().classify("Tell me something interesting")
        == AgentIntent.UNKNOWN
    )
