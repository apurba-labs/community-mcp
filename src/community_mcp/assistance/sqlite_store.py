import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from community_mcp.assistance.action_service import (
    ActorMismatchError,
    ConfirmationRequiredError,
)
from community_mcp.assistance.preparation_store import (
    PreparationAlreadyConsumedError,
    PreparationNotFoundError,
)
from community_mcp.schemas.action import (
    AssistanceResponseRecord,
    AuditReceipt,
    ConfirmedAssistanceResponse,
    PolicyDecision,
    PreparedAssistanceResponse,
)


class SQLiteAssistanceStore:
    """Durable preparation and confirmation ledger for synthetic demo actions."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)

        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS preparations (
                    preparation_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    consumed INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS responses (
                    response_id TEXT PRIMARY KEY,
                    preparation_id TEXT NOT NULL UNIQUE,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_receipts (
                    audit_id TEXT PRIMARY KEY,
                    preparation_id TEXT NOT NULL UNIQUE,
                    payload TEXT NOT NULL
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=10,
        )
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def save(
        self,
        response: PreparedAssistanceResponse,
    ) -> PreparedAssistanceResponse:
        if response.decision != PolicyDecision.REQUIRES_CONFIRMATION:
            raise ValueError("Only confirmable preparations can be stored.")

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO preparations (preparation_id, payload)
                VALUES (?, ?)
                """,
                (
                    str(response.preparation_id),
                    response.model_dump_json(),
                ),
            )

        return response

    def get(self, preparation_id: UUID) -> PreparedAssistanceResponse:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT payload, consumed
                FROM preparations
                WHERE preparation_id = ?
                """,
                (str(preparation_id),),
            ).fetchone()

        if row is None:
            raise PreparationNotFoundError(str(preparation_id))

        if row[1]:
            raise PreparationAlreadyConsumedError(str(preparation_id))

        return PreparedAssistanceResponse.model_validate_json(row[0])

    def confirm_response(
        self,
        preparation_id: UUID,
        *,
        actor_id: str,
        confirmed: bool,
    ) -> ConfirmedAssistanceResponse:
        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            row = connection.execute(
                """
                SELECT payload, consumed
                FROM preparations
                WHERE preparation_id = ?
                """,
                (str(preparation_id),),
            ).fetchone()

            if row is None:
                raise PreparationNotFoundError(str(preparation_id))

            if row[1]:
                raise PreparationAlreadyConsumedError(str(preparation_id))

            prepared = PreparedAssistanceResponse.model_validate_json(row[0])

            if prepared.decision != PolicyDecision.REQUIRES_CONFIRMATION:
                raise ConfirmationRequiredError(str(preparation_id))

            if not confirmed:
                raise ConfirmationRequiredError(str(preparation_id))

            if prepared.actor_id != actor_id:
                raise ActorMismatchError(actor_id)

            now = datetime.now(UTC)

            response = AssistanceResponseRecord(
                response_id=uuid4(),
                preparation_id=preparation_id,
                public_reference=prepared.public_reference,
                actor_id=actor_id,
                action=prepared.action,
                recorded_at=now,
            )

            audit = AuditReceipt(
                audit_id=uuid4(),
                event_type="ASSISTANCE_RESPONSE_RECORDED",
                actor_id=actor_id,
                public_reference=prepared.public_reference,
                action=prepared.action,
                occurred_at=now,
            )

            connection.execute(
                """
                INSERT INTO responses
                    (response_id, preparation_id, payload)
                VALUES (?, ?, ?)
                """,
                (
                    str(response.response_id),
                    str(preparation_id),
                    response.model_dump_json(),
                ),
            )

            connection.execute(
                """
                INSERT INTO audit_receipts
                    (audit_id, preparation_id, payload)
                VALUES (?, ?, ?)
                """,
                (
                    str(audit.audit_id),
                    str(preparation_id),
                    audit.model_dump_json(),
                ),
            )

            connection.execute(
                """
                UPDATE preparations
                SET consumed = 1
                WHERE preparation_id = ? AND consumed = 0
                """,
                (str(preparation_id),),
            )

            connection.commit()

            return ConfirmedAssistanceResponse(
                response=response,
                audit=audit,
            )

        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get_confirmed_response(
        self,
        preparation_id: UUID,
    ) -> ConfirmedAssistanceResponse | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT responses.payload, audit_receipts.payload
                FROM responses
                JOIN audit_receipts
                  ON responses.preparation_id = audit_receipts.preparation_id
                WHERE responses.preparation_id = ?
                """,
                (str(preparation_id),),
            ).fetchone()

        if row is None:
            return None

        return ConfirmedAssistanceResponse(
            response=AssistanceResponseRecord.model_validate_json(row[0]),
            audit=AuditReceipt.model_validate_json(row[1]),
        )
