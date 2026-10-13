import pytest

from community_mcp.agent.usage import BedrockUsage
from community_mcp.usage.store import SQLiteUsageStore


def test_usage_store_persists_completed_usage(tmp_path):
    database_path = tmp_path / "usage.sqlite3"

    store = SQLiteUsageStore(database_path)

    record_id = store.reserve(
        channel="public",
        model_id="amazon.nova-micro-v1:0",
    )

    store.complete(
        record_id,
        BedrockUsage(
            model_id="amazon.nova-micro-v1:0",
            input_tokens=100,
            output_tokens=20,
            total_tokens=120,
        ),
    )

    reopened_store = SQLiteUsageStore(database_path)

    summary = reopened_store.summary(channel="public")

    assert summary["total_requests"] == 1
    assert summary["completed_requests"] == 1
    assert summary["total_tokens"] == 120


def test_public_and_alumni_usage_are_isolated(tmp_path):
    store = SQLiteUsageStore(tmp_path / "usage.sqlite3")

    public_id = store.reserve(
        channel="public",
        model_id="amazon.nova-micro-v1:0",
    )

    alumni_id = store.reserve(
        channel="alumni",
        organization_id="school-1",
        model_id="amazon.nova-micro-v1:0",
    )

    store.complete(
        public_id,
        BedrockUsage(
            model_id="amazon.nova-micro-v1:0",
            input_tokens=100,
            output_tokens=10,
            total_tokens=110,
        ),
    )

    store.complete(
        alumni_id,
        BedrockUsage(
            model_id="amazon.nova-micro-v1:0",
            input_tokens=200,
            output_tokens=20,
            total_tokens=220,
        ),
    )

    assert store.summary(channel="public")["total_tokens"] == 110

    assert (
        store.summary(
            channel="alumni",
            organization_id="school-1",
        )["total_tokens"]
        == 220
    )


def test_alumni_requires_organization(tmp_path):
    store = SQLiteUsageStore(tmp_path / "usage.sqlite3")

    with pytest.raises(ValueError, match="organization"):
        store.reserve(
            channel="alumni",
            model_id="amazon.nova-micro-v1:0",
        )


def test_usage_cannot_be_completed_twice(tmp_path):
    store = SQLiteUsageStore(tmp_path / "usage.sqlite3")

    record_id = store.reserve(
        channel="public",
        model_id="amazon.nova-micro-v1:0",
    )

    usage = BedrockUsage(
        model_id="amazon.nova-micro-v1:0",
        input_tokens=50,
        output_tokens=10,
        total_tokens=60,
    )

    store.complete(record_id, usage)

    with pytest.raises(ValueError, match="already finalized"):
        store.complete(record_id, usage)


def test_failed_reservation_does_not_count_as_completed(tmp_path):
    store = SQLiteUsageStore(tmp_path / "usage.sqlite3")

    record_id = store.reserve(
        channel="public",
        model_id="amazon.nova-micro-v1:0",
    )

    store.fail(record_id)

    summary = store.summary(channel="public")

    assert summary["total_requests"] == 1
    assert summary["completed_requests"] == 0
    assert summary["total_tokens"] == 0
