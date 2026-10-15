"""Production-only Alumni API security tests."""

from fastapi.testclient import TestClient

from community_mcp.simulator.api import create_simulator_app
from community_mcp.usage.store import SQLiteUsageStore, UsageBudget


class DummyAgent:
    async def handle(self, **kwargs):
        raise AssertionError("Agent must not run for unauthorized requests")


def create_test_app(tmp_path):
    return create_simulator_app(
        agent_factory=lambda: DummyAgent(),
        internal_only=True,
        internal_api_token="test-secret",
        internal_organization_id="09aa0633-6469-4155-87ee-762b81cc0695",
        usage_store=SQLiteUsageStore(tmp_path / "usage.sqlite3"),
        alumni_budget=UsageBudget(
            daily_requests=200,
            concurrent_requests=3,
            daily_tokens=100_000,
        ),
    )


def test_internal_only_hides_public_routes():
    app = create_simulator_app(
        agent_factory=lambda: DummyAgent(),
        internal_only=True,
        internal_api_token="test-secret",
    )

    client = TestClient(app)

    for path in (
        "/simulator",
        "/simulator/api/health",
        "/simulator/api/chat",
        "/simulator/static/index.html",
        "/docs",
        "/redoc",
        "/openapi.json",
    ):
        assert client.get(path).status_code == 404, path

    assert (
        client.post(
            "/simulator/api/chat",
            json={"message": "Hello"},
        ).status_code
        == 404
    )


def test_internal_endpoints_require_authentication(tmp_path):
    app = create_test_app(tmp_path)
    client = TestClient(app)

    assert (
        client.get(
            "/simulator/api/internal/usage",
        ).status_code
        == 401
    )

    assert (
        client.post(
            "/simulator/api/internal/chat",
            json={
                "message": "Hello",
                "organization_id": "09aa0633-6469-4155-87ee-762b81cc0695",
            },
        ).status_code
        == 401
    )


def test_internal_endpoints_reject_invalid_token(tmp_path):
    app = create_test_app(tmp_path)
    client = TestClient(app)

    assert (
        client.get(
            "/simulator/api/internal/usage",
            headers={"Authorization": "Bearer wrong-token"},
        ).status_code
        == 401
    )
