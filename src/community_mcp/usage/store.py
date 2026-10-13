from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from community_mcp.agent.usage import BedrockUsage


@dataclass(frozen=True)
class UsageBudget:
    daily_requests: int
    concurrent_requests: int
    daily_tokens: int
    reserved_tokens_per_request: int = 1024
    reservation_timeout_seconds: int = 60

    def __post_init__(self) -> None:
        if (
            min(
                self.daily_requests,
                self.concurrent_requests,
                self.daily_tokens,
                self.reserved_tokens_per_request,
                self.reservation_timeout_seconds,
            )
            <= 0
        ):
            raise ValueError("Budget limits must be positive.")


class UsageBudgetExceeded(Exception):
    pass


class SQLiteUsageStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=10,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    @staticmethod
    def _migrate_unknown_status(connection: sqlite3.Connection) -> None:
        row = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table' AND name = 'usage_records'
            """
        ).fetchone()

        if row is None or "'unknown'" in row["sql"]:
            return

        connection.execute(
            """
            CREATE TABLE usage_records_new (
                id TEXT PRIMARY KEY,
                channel TEXT NOT NULL
                    CHECK (channel IN ('public', 'alumni')),
                organization_id TEXT,
                model_id TEXT NOT NULL,
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                total_tokens INTEGER NOT NULL DEFAULT 0,
                reserved_tokens INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL
                    CHECK (status IN (
                        'reserved', 'completed', 'failed', 'unknown'
                    )),
                created_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            INSERT INTO usage_records_new (
                id, channel, organization_id, model_id,
                input_tokens, output_tokens, total_tokens,
                reserved_tokens, status, created_at
            )
            SELECT
                id, channel, organization_id, model_id,
                input_tokens, output_tokens, total_tokens,
                reserved_tokens, status, created_at
            FROM usage_records
            """
        )

        connection.execute("DROP TABLE usage_records")
        connection.execute(
            "ALTER TABLE usage_records_new RENAME TO usage_records"
        )

    @staticmethod
    def _expire_reservations(
        connection: sqlite3.Connection,
        *,
        now: datetime,
        timeout_seconds: int,
    ) -> None:
        cutoff = now - timedelta(seconds=timeout_seconds)

        connection.execute(
            """
            UPDATE usage_records
            SET status = 'unknown'
            WHERE status = 'reserved'
              AND created_at < ?
            """,
            (cutoff.isoformat(),),
        )

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_records (
                    id TEXT PRIMARY KEY,
                    channel TEXT NOT NULL
                        CHECK (channel IN ('public', 'alumni')),
                    organization_id TEXT,
                    model_id TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL DEFAULT 0,
                    output_tokens INTEGER NOT NULL DEFAULT 0,
                    total_tokens INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL
                        CHECK (status IN ('reserved', 'completed', 'failed')),
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_usage_channel_created
                ON usage_records (channel, created_at)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_usage_organization_created
                ON usage_records (organization_id, created_at)
                """
            )

            columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(usage_records)")
            }

            if "reserved_tokens" not in columns:
                connection.execute(
                    "ALTER TABLE usage_records "
                    "ADD COLUMN reserved_tokens INTEGER NOT NULL DEFAULT 0"
                )

            self._migrate_unknown_status(connection)

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_usage_channel_created
                ON usage_records (channel, created_at)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_usage_organization_created
                ON usage_records (organization_id, created_at)
                """
            )

    def reserve(
        self,
        *,
        channel: str,
        model_id: str,
        organization_id: str | None = None,
        budget: UsageBudget | None = None,
    ) -> str:
        if channel not in {"public", "alumni"}:
            raise ValueError("Invalid usage channel.")

        if channel == "alumni" and not organization_id:
            raise ValueError("Alumni usage requires an organization ID.")

        if channel == "public" and organization_id is not None:
            raise ValueError("Public usage cannot have an organization ID.")

        record_id = str(uuid4())
        now = datetime.now(UTC)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        scope_sql = "channel = ?"
        scope_params: list[str] = [channel]

        if channel == "alumni":
            scope_sql += " AND organization_id = ?"
            scope_params.append(organization_id)

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")

            if budget is not None:
                self._expire_reservations(
                    connection,
                    now=now,
                    timeout_seconds=budget.reservation_timeout_seconds,
                )

            if budget is not None:
                row = connection.execute(
                    f"""
                    SELECT
                        COUNT(*) AS daily_requests,
                        COALESCE(SUM(
                            CASE WHEN status = 'reserved' THEN 1 ELSE 0 END
                        ), 0) AS active_requests,
                        COALESCE(SUM(
                            CASE
                                WHEN status IN ('reserved', 'unknown') THEN reserved_tokens
                                ELSE total_tokens
                            END
                        ), 0) AS allocated_tokens
                    FROM usage_records
                    WHERE {scope_sql}
                    AND created_at >= ?
                    AND created_at < ?
                    """,
                    [
                        *scope_params,
                        day_start.isoformat(),
                        day_end.isoformat(),
                    ],
                ).fetchone()

                if row["daily_requests"] >= budget.daily_requests:
                    raise UsageBudgetExceeded("Daily request budget exhausted.")

                if row["active_requests"] >= budget.concurrent_requests:
                    raise UsageBudgetExceeded("Concurrent request limit reached.")

                if (
                    row["allocated_tokens"] + budget.reserved_tokens_per_request
                    > budget.daily_tokens
                ):
                    raise UsageBudgetExceeded("Daily token budget exhausted.")

            connection.execute(
                """
                INSERT INTO usage_records (
                    id,
                    channel,
                    organization_id,
                    model_id,
                    reserved_tokens,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, 'reserved', ?)
                """,
                (
                    record_id,
                    channel,
                    organization_id,
                    model_id,
                    budget.reserved_tokens_per_request if budget else 0,
                    now.isoformat(),
                ),
            )

        return record_id

    def complete(
        self,
        record_id: str,
        usage: BedrockUsage,
    ) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE usage_records
                SET
                    input_tokens = ?,
                    output_tokens = ?,
                    total_tokens = ?,
                    status = 'completed'
                WHERE id = ? AND status IN ('reserved', 'unknown')
                """,
                (
                    usage.input_tokens,
                    usage.output_tokens,
                    usage.total_tokens,
                    record_id,
                ),
            )

            if cursor.rowcount != 1:
                raise ValueError("Usage reservation not found or already finalized.")

    def fail(self, record_id: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE usage_records
                SET status = 'failed'
                WHERE id = ? AND status = 'reserved'
                """,
                (record_id,),
            )

            if cursor.rowcount != 1:
                raise ValueError("Usage reservation not found or already finalized.")

    def summary(
        self,
        *,
        channel: str,
        organization_id: str | None = None,
    ) -> dict[str, int]:
        if channel not in {"public", "alumni"}:
            raise ValueError("Invalid usage channel.")

        if channel == "alumni" and not organization_id:
            raise ValueError("Alumni summary requires an organization ID.")

        if channel == "public" and organization_id is not None:
            raise ValueError("Public summary cannot have an organization ID.")

        query = """
            SELECT
                COUNT(*) AS total_requests,
                COALESCE(SUM(
                    CASE WHEN status = 'completed' THEN 1 ELSE 0 END
                ), 0) AS completed_requests,
                COALESCE(SUM(
                    CASE WHEN status = 'reserved' THEN 1 ELSE 0 END
                ), 0) AS reserved_requests,
                COALESCE(SUM(input_tokens), 0) AS input_tokens,
                COALESCE(SUM(output_tokens), 0) AS output_tokens,
                COALESCE(SUM(total_tokens), 0) AS total_tokens
            FROM usage_records
            WHERE channel = ?
        """

        parameters: list[str] = [channel]

        if channel == "alumni":
            query += " AND organization_id = ?"
            parameters.append(organization_id)

        with self._connect() as connection:
            row = connection.execute(query, parameters).fetchone()

        return dict(row)
