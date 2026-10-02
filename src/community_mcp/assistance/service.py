import json
from pathlib import Path

from community_mcp.schemas.assistance import (
    AssistanceRequest,
    AssistanceStatus,
)


class AssistanceNotFoundError(Exception):
    pass


class AssistanceUnavailableError(Exception):
    pass


class AssistanceService:
    def __init__(self, fixture_path: Path | None = None) -> None:
        self.fixture_path = fixture_path or (
            Path(__file__).parents[3]
            / "demo"
            / "fixtures"
            / "assistance.json"
        )

    async def get_public_context(
        self,
        public_reference: str,
    ) -> AssistanceRequest:
        payload = json.loads(self.fixture_path.read_text())

        request = next(
            (
                AssistanceRequest.model_validate(item)
                for item in payload
                if item["public_reference"] == public_reference
            ),
            None,
        )

        if request is None:
            raise AssistanceNotFoundError(public_reference)

        if not request.verified or not request.approved:
            raise AssistanceUnavailableError(public_reference)

        if request.status not in {
            AssistanceStatus.OPEN,
            AssistanceStatus.ACTIVE,
        }:
            raise AssistanceUnavailableError(public_reference)

        return request
