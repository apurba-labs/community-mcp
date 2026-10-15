from datetime import UTC, datetime, timedelta

import pytest

from community_mcp.agent.usage import BedrockUsage
from community_mcp.usage.store import (
    SQLiteUsageStore,
    UsageBudget,
    UsageBudgetExceeded,
)

MODEL = "amazon.nova-micro-v1:0"


def test_expired_reservation_releases_concurrency_but_retains_tokens(tmp_path):
    store = SQLiteUsageStore(tmp_path / "usage.sqlite3")

    budget = UsageBudget(
        daily_requests=10,
        concurrent_requests=1,
        daily_tokens=3000,
        reserved_tokens_per_request=1024,
        reservation_timeout_seconds=60,
    )

    first = store.reserve(
        channel="public",
        model_id=MODEL,
        budget=budget,
    )

    old_time = datetime.now(UTC) - timedelta(minutes=2)

    with store._connect() as connection:
        connection.execute(
            "UPDATE usage_records SET created_at = ? WHERE id = ?",
            (old_time.isoformat(), first),
        )

    second = store.reserve(
        channel="public",
        model_id=MODEL,
        budget=budget,
    )

    assert second != first

    with store._connect() as connection:
        first_row = connection.execute(
            "SELECT status, reserved_tokens FROM usage_records WHERE id = ?",
            (first,),
        ).fetchone()

    assert first_row["status"] == "unknown"
    assert first_row["reserved_tokens"] == 1024

    with pytest.raises(UsageBudgetExceeded, match="Concurrent"):
        store.reserve(
            channel="public",
            model_id=MODEL,
            budget=budget,
        )


def test_late_usage_reconciles_unknown_reservation(tmp_path):
    store = SQLiteUsageStore(tmp_path / "usage.sqlite3")

    budget = UsageBudget(
        daily_requests=10,
        concurrent_requests=1,
        daily_tokens=5000,
        reservation_timeout_seconds=60,
    )

    record_id = store.reserve(
        channel="public",
        model_id=MODEL,
        budget=budget,
    )

    old_time = datetime.now(UTC) - timedelta(minutes=2)

    with store._connect() as connection:
        connection.execute(
            "UPDATE usage_records SET created_at = ? WHERE id = ?",
            (old_time.isoformat(), record_id),
        )

    store.reserve(
        channel="public",
        model_id=MODEL,
        budget=budget,
    )

    store.complete(
        record_id,
        BedrockUsage(
            model_id=MODEL,
            input_tokens=120,
            output_tokens=20,
            total_tokens=140,
        ),
    )

    with store._connect() as connection:
        row = connection.execute(
            "SELECT status, total_tokens FROM usage_records WHERE id = ?",
            (record_id,),
        ).fetchone()

    assert row["status"] == "completed"
    assert row["total_tokens"] == 140


def test_existing_database_migrates_without_losing_records(tmp_path):
    database_path = tmp_path / "usage.sqlite3"

    store = SQLiteUsageStore(database_path)
    record_id = store.reserve(
        channel="public",
        model_id=MODEL,
    )

    reopened = SQLiteUsageStore(database_path)

    with reopened._connect() as connection:
        row = connection.execute(
            "SELECT id, status FROM usage_records WHERE id = ?",
            (record_id,),
        ).fetchone()

    assert row["id"] == record_id
    assert row["status"] == "reserved"
