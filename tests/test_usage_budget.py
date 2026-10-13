from concurrent.futures import ThreadPoolExecutor

import pytest

from community_mcp.agent.usage import BedrockUsage
from community_mcp.usage.store import (
    SQLiteUsageStore,
    UsageBudget,
    UsageBudgetExceeded,
)

MODEL = "amazon.nova-micro-v1:0"


def test_daily_request_budget(tmp_path):
    store = SQLiteUsageStore(tmp_path / "usage.sqlite3")
    budget = UsageBudget(
        daily_requests=1,
        concurrent_requests=2,
        daily_tokens=10000,
    )

    record_id = store.reserve(channel="public", model_id=MODEL, budget=budget)
    store.complete(
        record_id,
        BedrockUsage(
            model_id=MODEL,
            input_tokens=100,
            output_tokens=10,
            total_tokens=110,
        ),
    )

    with pytest.raises(UsageBudgetExceeded, match="Daily request"):
        store.reserve(channel="public", model_id=MODEL, budget=budget)


def test_concurrent_budget_is_atomic(tmp_path):
    database_path = tmp_path / "usage.sqlite3"

    budget = UsageBudget(
        daily_requests=100,
        concurrent_requests=1,
        daily_tokens=10000,
    )

    def reserve():
        store = SQLiteUsageStore(database_path)
        try:
            return store.reserve(
                channel="public",
                model_id=MODEL,
                budget=budget,
            )
        except UsageBudgetExceeded:
            return None

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: reserve(), range(8)))

    assert sum(result is not None for result in results) == 1


def test_alumni_organization_budgets_are_isolated(tmp_path):
    store = SQLiteUsageStore(tmp_path / "usage.sqlite3")

    budget = UsageBudget(
        daily_requests=1,
        concurrent_requests=1,
        daily_tokens=10000,
    )

    store.reserve(
        channel="alumni",
        organization_id="school-1",
        model_id=MODEL,
        budget=budget,
    )

    with pytest.raises(UsageBudgetExceeded):
        store.reserve(
            channel="alumni",
            organization_id="school-1",
            model_id=MODEL,
            budget=budget,
        )

    other = store.reserve(
        channel="alumni",
        organization_id="school-2",
        model_id=MODEL,
        budget=budget,
    )

    public = store.reserve(
        channel="public",
        model_id=MODEL,
        budget=budget,
    )

    assert other != public


def test_token_reservations_enforce_daily_ceiling(tmp_path):
    store = SQLiteUsageStore(tmp_path / "usage.sqlite3")

    budget = UsageBudget(
        daily_requests=10,
        concurrent_requests=10,
        daily_tokens=1500,
        reserved_tokens_per_request=1024,
    )

    store.reserve(channel="public", model_id=MODEL, budget=budget)

    with pytest.raises(UsageBudgetExceeded, match="token budget"):
        store.reserve(channel="public", model_id=MODEL, budget=budget)
