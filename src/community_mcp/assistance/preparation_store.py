from dataclasses import dataclass
from uuid import UUID

from community_mcp.schemas.action import PreparedAssistanceResponse


class PreparationNotFoundError(Exception):
    pass


class PreparationAlreadyConsumedError(Exception):
    pass


@dataclass
class StoredPreparation:
    response: PreparedAssistanceResponse
    consumed: bool = False


class AssistancePreparationStore:
    def __init__(self) -> None:
        self._items: dict[UUID, StoredPreparation] = {}

    def save(
        self,
        response: PreparedAssistanceResponse,
    ) -> PreparedAssistanceResponse:
        self._items[response.preparation_id] = StoredPreparation(
            response=response
        )
        return response

    def get(self, preparation_id: UUID) -> PreparedAssistanceResponse:
        stored = self._items.get(preparation_id)

        if stored is None:
            raise PreparationNotFoundError(str(preparation_id))

        if stored.consumed:
            raise PreparationAlreadyConsumedError(str(preparation_id))

        return stored.response

    def consume(self, preparation_id: UUID) -> None:
        stored = self._items.get(preparation_id)

        if stored is None:
            raise PreparationNotFoundError(str(preparation_id))

        if stored.consumed:
            raise PreparationAlreadyConsumedError(str(preparation_id))

        stored.consumed = True
