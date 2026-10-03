from typing import Any

import boto3
from pydantic import BaseModel, ValidationError

from community_mcp.agent.reasoning import AgentDecision, ReasoningProvider
from community_mcp.agent.schemas import AgentIntent, SupportedLocale
from community_mcp.schemas.assistance import AssistanceAction

SYSTEM_PROMPT = """
You interpret messages for a trusted community assistant.

Return JSON only with this shape:
{"intent":"<intent>","action":null}

Allowed intents:
EVENT_CONTEXT
ASSISTANCE_CONTEXT
ASSISTANCE_RESPONSE
CONFIRM_ACTION
UNKNOWN

Allowed actions:
DONATE_BLOOD
VOLUNTEER
SHARE

Rules:
- EVENT_CONTEXT: user asks about an event, program, schedule, venue,
  guest, or event information.
- ASSISTANCE_CONTEXT: user asks whether someone needs help or asks for
  information about an assistance request.
- ASSISTANCE_RESPONSE: user personally offers to help, donate blood,
  volunteer, or share an assistance request.
- CONFIRM_ACTION: user explicitly confirms a previously prepared action.
- UNKNOWN: none of the above.

Action rules:
- Use DONATE_BLOOD only when the user offers to donate blood.
- Use VOLUNTEER only when the user offers to volunteer.
- Use SHARE only when the user offers to share the request.
- Otherwise action must be null.

Important:
- Asking about a blood request is ASSISTANCE_CONTEXT.
- Offering to donate blood is ASSISTANCE_RESPONSE with DONATE_BLOOD.
- Never authorize, approve, confirm, or execute an action.
- Do not include explanations or markdown.
""".strip()


class BedrockDecision(BaseModel):
    intent: AgentIntent
    action: AssistanceAction | None = None


class BedrockReasoner(ReasoningProvider):
    def __init__(
        self,
        *,
        client: Any | None = None,
        model_id: str = "amazon.nova-micro-v1:0",
        region_name: str = "us-east-1",
        profile_name: str | None = None,
    ) -> None:
        if client is not None:
            self.client = client
        else:
            session = boto3.Session(
                profile_name=profile_name,
                region_name=region_name,
            )
            self.client = session.client("bedrock-runtime")

        self.model_id = model_id

    async def reason(
        self,
        *,
        message: str,
        locale: SupportedLocale,
    ) -> AgentDecision:
        response = self.client.converse(
            modelId=self.model_id,
            system=[{"text": SYSTEM_PROMPT}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": message}],
                }
            ],
            inferenceConfig={
                "maxTokens": 64,
                "temperature": 0,
            },
        )

        text = self._extract_text(response)

        try:
            parsed = BedrockDecision.model_validate_json(text)
        except ValidationError as exc:
            raise ValueError(
                "Bedrock returned an invalid agent decision"
            ) from exc

        self._validate_decision(parsed)

        return AgentDecision(
            intent=parsed.intent,
            locale=locale,
            action=parsed.action,
            confidence=1.0,
        )

    @staticmethod
    def _extract_text(response: dict[str, Any]) -> str:
        try:
            return response["output"]["message"]["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(
                "Bedrock response did not contain text output"
            ) from exc

    @staticmethod
    def _validate_decision(decision: BedrockDecision) -> None:
        if (
            decision.intent == AgentIntent.ASSISTANCE_RESPONSE
            and decision.action is None
        ):
            raise ValueError(
                "Assistance response requires a canonical action"
            )

        if (
            decision.intent != AgentIntent.ASSISTANCE_RESPONSE
            and decision.action is not None
        ):
            raise ValueError(
                "Only assistance responses may contain an action"
            )
