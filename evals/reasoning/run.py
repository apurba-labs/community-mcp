import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from community_mcp.agent.bedrock import BedrockReasoner
from community_mcp.agent.reasoning import (
    DeterministicReasoner,
    ReasoningProvider,
)
from community_mcp.agent.safe_reasoning import SafeReasoner
from community_mcp.agent.schemas import (
    AgentIntent,
    SupportedLocale,
)

CASES_PATH = Path(__file__).with_name("cases.json")


@dataclass
class EvalResult:
    case_id: str
    locale: str
    message: str
    expected_intent: str
    predicted_intent: str | None
    expected_action: str | None
    predicted_action: str | None
    valid: bool
    intent_correct: bool
    action_correct: bool
    false_action: bool
    false_confirmation: bool
    error: str | None = None


def load_cases() -> list[dict[str, object]]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


async def evaluate_case(
    reasoner: ReasoningProvider,
    case: dict[str, object],
) -> EvalResult:
    case_id = str(case["id"])
    locale = str(case["locale"])
    message = str(case["message"])
    expected_intent = str(case["expected_intent"])

    raw_expected_action = case.get("expected_action")
    expected_action = (
        str(raw_expected_action)
        if raw_expected_action is not None
        else None
    )

    try:
        decision = await reasoner.reason(
            message=message,
            locale=SupportedLocale(locale),
        )
    except Exception as exc:
        return EvalResult(
            case_id=case_id,
            locale=locale,
            message=message,
            expected_intent=expected_intent,
            predicted_intent=None,
            expected_action=expected_action,
            predicted_action=None,
            valid=False,
            intent_correct=False,
            action_correct=False,
            false_action=False,
            false_confirmation=False,
            error=f"{type(exc).__name__}: {exc}",
        )

    predicted_intent = decision.intent.value
    predicted_action = (
        decision.action.value
        if decision.action is not None
        else None
    )

    false_action = (
        (
            expected_intent
            != AgentIntent.ASSISTANCE_RESPONSE.value
            and predicted_intent
            == AgentIntent.ASSISTANCE_RESPONSE.value
        )
        or (
            expected_action is None
            and predicted_action is not None
        )
    )

    false_confirmation = (
        expected_intent != AgentIntent.CONFIRM_ACTION.value
        and predicted_intent == AgentIntent.CONFIRM_ACTION.value
    )

    return EvalResult(
        case_id=case_id,
        locale=locale,
        message=message,
        expected_intent=expected_intent,
        predicted_intent=predicted_intent,
        expected_action=expected_action,
        predicted_action=predicted_action,
        valid=True,
        intent_correct=predicted_intent == expected_intent,
        action_correct=predicted_action == expected_action,
        false_action=false_action,
        false_confirmation=false_confirmation,
    )


async def run(
    reasoner: ReasoningProvider,
) -> list[EvalResult]:
    results = []

    for case in load_cases():
        result = await evaluate_case(reasoner, case)
        results.append(result)

    return results


def percentage(correct: int, total: int) -> float:
    if total == 0:
        return 0.0

    return correct / total * 100


def print_summary(
    provider_name: str,
    results: list[EvalResult],
) -> None:
    total = len(results)
    valid = sum(result.valid for result in results)
    intent_correct = sum(
        result.intent_correct for result in results
    )
    action_correct = sum(
        result.action_correct for result in results
    )

    english = [
        result for result in results if result.locale == "en"
    ]
    bangla = [
        result for result in results if result.locale == "bn"
    ]

    english_correct = sum(
        result.intent_correct for result in english
    )
    bangla_correct = sum(
        result.intent_correct for result in bangla
    )

    false_actions = sum(
        result.false_action for result in results
    )
    false_confirmations = sum(
        result.false_confirmation for result in results
    )

    print()
    print(f"Reasoner: {provider_name}")
    print("=" * 52)
    print(f"Cases:               {total}")
    print(
        "Intent accuracy:     "
        f"{intent_correct}/{total} "
        f"({percentage(intent_correct, total):.1f}%)"
    )
    print(
        "Action accuracy:     "
        f"{action_correct}/{total} "
        f"({percentage(action_correct, total):.1f}%)"
    )
    print(
        "English accuracy:    "
        f"{english_correct}/{len(english)} "
        f"({percentage(english_correct, len(english)):.1f}%)"
    )
    print(
        "Bangla accuracy:     "
        f"{bangla_correct}/{len(bangla)} "
        f"({percentage(bangla_correct, len(bangla)):.1f}%)"
    )
    print(f"Invalid outputs:      {total - valid}")
    print(f"False actions:        {false_actions}")
    print(f"False confirmations:  {false_confirmations}")

    failures = [
        result
        for result in results
        if (
            not result.valid
            or not result.intent_correct
            or not result.action_correct
        )
    ]

    if not failures:
        print()
        print("No mismatches.")
        return

    print()
    print("Mismatches")
    print("-" * 52)

    for result in failures:
        print(f"[{result.case_id}] {result.message}")
        print(
            f"  expected: {result.expected_intent}"
            f" / {result.expected_action}"
        )
        print(
            f"  predicted: {result.predicted_intent}"
            f" / {result.predicted_action}"
        )

        if result.error:
            print(f"  error: {result.error}")


def build_reasoner(
    provider_name: str,
) -> ReasoningProvider:
    if provider_name == "deterministic":
        return DeterministicReasoner()

    if provider_name == "bedrock":
        return BedrockReasoner(
            profile_name="community-mcp",
            region_name="us-east-1",
        )
    if provider_name == "safe-bedrock":
        return SafeReasoner(
            BedrockReasoner(
                profile_name="community-mcp",
                region_name="us-east-1",
            )
        )

    raise ValueError(
        f"Unsupported reasoning provider: {provider_name}"
    )


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider",
        choices=(
            "deterministic",
            "bedrock",
            "safe-bedrock",
        ),
        required=True,
    )
    args = parser.parse_args()

    reasoner = build_reasoner(args.provider)
    results = await run(reasoner)

    print_summary(args.provider, results)


if __name__ == "__main__":
    asyncio.run(main())