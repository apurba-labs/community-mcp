from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi.testclient import TestClient

from community_mcp.simulator.api import create_simulator_app
from community_mcp.usage.store import SQLiteUsageStore, UsageBudget

ORGANIZATION_ID = str(uuid4())
OTHER_ORGANIZATION_ID = str(uuid4())
SERVICE_TOKEN = "test-internal-service-token"


def create_test_client(tmp_path):
    store = SQLiteUsageStore(tmp_path / "usage.sqlite3")

    budget = UsageBudget(
        daily_requests=10,
        concurrent_requests=3,
        daily_tokens=1000,
        reserved_tokens_per_request=100,
    )

    agent = AsyncMock()

    app = create_simulator_app(
        agent_factory=lambda: agent,
        internal_agent_factory=lambda: agent,
        internal_organization_id=ORGANIZATION_ID,
        internal_api_token=SERVICE_TOKEN,
        usage_store=store,
        alumni_budget=budget,
        public_budget=budget,
    )

    return TestClient(app), store


def test_internal_usage_requires_service_token(tmp_path):
    client, _ = create_test_client(tmp_path)

    response = client.get("/simulator/api/internal/usage")

    assert response.status_code == 401

    response = client.get(
        "/simulator/api/internal/usage",
        headers={"Authorization": "Bearer incorrect-token"},
    )

    assert response.status_code == 401


def test_internal_usage_reports_daily_budget(tmp_path):
    client, store = create_test_client(tmp_path)

    store.reserve(
        channel="alumni",
        organization_id=ORGANIZATION_ID,
        model_id="test-model",
    )

    response = client.get(
        "/simulator/api/internal/usage",
        headers={"Authorization": f"Bearer {SERVICE_TOKEN}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["organization_id"] == ORGANIZATION_ID
    assert data["period"] == "today_utc"

    assert data["requests"]["used"] == 1
    assert data["requests"]["limit"] == 10
    assert data["requests"]["remaining"] == 9


def test_internal_usage_isolates_organizations(tmp_path):
    client, store = create_test_client(tmp_path)

    store.reserve(
        channel="alumni",
        organization_id=ORGANIZATION_ID,
        model_id="test-model",
    )

    store.reserve(
        channel="alumni",
        organization_id=OTHER_ORGANIZATION_ID,
        model_id="test-model",
    )

    response = client.get(
        "/simulator/api/internal/usage",
        headers={"Authorization": f"Bearer {SERVICE_TOKEN}"},
    )

    assert response.status_code == 200
    assert response.json()["requests"]["used"] == 1


def test_internal_usage_reports_allocated_tokens(tmp_path):
    client, store = create_test_client(tmp_path)

    store.reserve(
        channel="alumni",
        organization_id=ORGANIZATION_ID,
        model_id="test-model",
        budget=UsageBudget(
            daily_requests=10,
            concurrent_requests=3,
            daily_tokens=1000,
            reserved_tokens_per_request=100,
        ),
    )

    response = client.get(
        "/simulator/api/internal/usage",
        headers={"Authorization": f"Bearer {SERVICE_TOKEN}"},
    )

    assert response.status_code == 200

    tokens = response.json()["tokens"]

    assert tokens["allocated"] == 100
    assert tokens["recorded"] == 0
    assert tokens["remaining"] == 900
