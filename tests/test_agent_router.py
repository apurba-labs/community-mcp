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
        (
            "How many alumni from my batch have registered?",
            AgentIntent.COMMUNITY_CONTEXT,
        ),
        (
            "আমার ব্যাচের কতজন অ্যালামনাই রেজিস্ট্রেশন করেছে?",
            AgentIntent.COMMUNITY_CONTEXT,
        ),
        (
            "How many people from my batch registered for the centenary event?",
            AgentIntent.EVENT_CONTEXT,
        ),
        (
            "আমার ব্যাচ থেকে কতজন শতবর্ষ অনুষ্ঠানে রেজিস্ট্রেশন করেছে?",
            AgentIntent.EVENT_CONTEXT,
        ),
    ],
)
def test_bilingual_intent_routing(
    message: str,
    expected: AgentIntent,
) -> None:
    assert IntentRouter().classify(message) == expected


def test_unknown_message_is_not_invented_as_an_intent() -> None:
    assert IntentRouter().classify("Tell me something interesting") == AgentIntent.UNKNOWN


@pytest.mark.parametrize(
    "message",
    [
        "yes",
        "হ্যাঁ",
        "okay",
        "ঠিক আছে",
    ],
)
def test_generic_affirmative_is_not_confirmation(
    message: str,
) -> None:
    assert IntentRouter().classify(message) != AgentIntent.CONFIRM_ACTION
