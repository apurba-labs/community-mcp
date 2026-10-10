import httpx
import pytest

from community_mcp.providers.assistance import (
    AssistanceContextNotFoundError,
    AssistanceContextUnavailableError,
)
from community_mcp.providers.credentials import (
    AccessTokenProvider,
    AccessTokenUnavailableError,
)
from community_mcp.providers.gotihub_assistance import (
    GotiHubAssistanceProvider,
)
from community_mcp.schemas.assistance import (
    AssistanceAction,
    AssistanceStatus,
    AssistanceType,
)


class StubAccessTokenProvider(AccessTokenProvider):
    def __init__(
        self,
        tokens: dict[str, str] | None = None,
    ) -> None:
        self.tokens = tokens or {}

    async def get_access_token(self, actor_id: str) -> str:
        try:
            return self.tokens[actor_id]
        except KeyError as exc:
            raise AccessTokenUnavailableError(actor_id) from exc


def discovery_payload(
    *,
    public_reference: str = "HELP-2026-001",
    assistance_type: str = "BLOOD",
) -> dict:
    return {
        "items": [
            {
                "public_reference": public_reference,
                "assistance_type": assistance_type,
                "audience_scope": "PUBLIC",
                "audience_batch_year": None,
                "visibility": "PUBLIC",
                "urgency": "URGENT",
                "blood_group": "B+" if assistance_type == "BLOOD" else None,
                "units_needed": 2 if assistance_type == "BLOOD" else None,
                "location_label": "Community Hospital",
                "public_context": "Safe assistance discovery context.",
                "created_at": "2026-10-04T12:00:00+06:00",
            }
        ]
    }


@pytest.mark.asyncio
async def test_public_context_uses_public_endpoint_without_authorization() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/assistance/public/requests"
        assert "Authorization" not in request.headers

        return httpx.Response(
            200,
            json=discovery_payload(),
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://community.example.org",
    ) as client:
        provider = GotiHubAssistanceProvider(
            "https://community.example.org",
            client=client,
        )

        result = await provider.get_public_context("HELP-2026-001")

    assert result.public_reference == "HELP-2026-001"
    assert result.assistance_type == AssistanceType.BLOOD
    assert result.status == AssistanceStatus.ACTIVE
    assert result.summary == "Safe assistance discovery context."
    assert result.location_text == "Community Hospital"
    assert result.blood_group == "B+"
    assert result.units_needed == 2
    assert result.verified is True
    assert result.approved is True
    assert result.allowed_actions == [
        AssistanceAction.DONATE_BLOOD,
        AssistanceAction.VOLUNTEER,
        AssistanceAction.SHARE,
    ]


@pytest.mark.asyncio
async def test_unknown_public_reference_is_not_found() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json=discovery_payload(
                public_reference="HELP-OTHER",
            ),
        )
    )

    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://community.example.org",
    ) as client:
        provider = GotiHubAssistanceProvider(
            "https://community.example.org",
            client=client,
        )

        with pytest.raises(AssistanceContextNotFoundError):
            await provider.get_public_context("HELP-UNKNOWN")


@pytest.mark.asyncio
async def test_invalid_public_payload_fails_closed() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"items": [{"unexpected": "payload"}]},
        )
    )

    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://community.example.org",
    ) as client:
        provider = GotiHubAssistanceProvider(
            "https://community.example.org",
            client=client,
        )

        with pytest.raises(AssistanceContextUnavailableError):
            await provider.get_public_context("HELP-2026-001")


@pytest.mark.asyncio
async def test_member_context_uses_actor_scoped_bearer_token() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/assistance/requests"
        assert request.headers["Authorization"] == "Bearer actor-token-001"

        return httpx.Response(
            200,
            json=discovery_payload(),
        )

    transport = httpx.MockTransport(handler)
    credentials = StubAccessTokenProvider({"demo-member-001": "actor-token-001"})

    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://community.example.org",
    ) as client:
        provider = GotiHubAssistanceProvider(
            "https://community.example.org",
            credentials,
            client=client,
        )

        result = await provider.get_member_context(
            "HELP-2026-001",
            actor_id="demo-member-001",
        )

    assert result.public_reference == "HELP-2026-001"


@pytest.mark.asyncio
async def test_missing_actor_credential_fails_closed_without_http_call() -> None:
    called = False

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(500)

    transport = httpx.MockTransport(handler)
    credentials = StubAccessTokenProvider()

    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://community.example.org",
    ) as client:
        provider = GotiHubAssistanceProvider(
            "https://community.example.org",
            credentials,
            client=client,
        )

        with pytest.raises(AssistanceContextUnavailableError):
            await provider.get_member_context(
                "HELP-2026-001",
                actor_id="unknown-member",
            )

    assert called is False


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [401, 403])
async def test_member_authorization_failure_fails_closed(
    status_code: int,
) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(status_code))
    credentials = StubAccessTokenProvider({"demo-member-001": "actor-token-001"})

    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://community.example.org",
    ) as client:
        provider = GotiHubAssistanceProvider(
            "https://community.example.org",
            credentials,
            client=client,
        )

        with pytest.raises(AssistanceContextUnavailableError):
            await provider.get_member_context(
                "HELP-2026-001",
                actor_id="demo-member-001",
            )


@pytest.mark.asyncio
async def test_financial_support_has_deterministic_contribute_action() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json=discovery_payload(
                assistance_type="FINANCIAL_SUPPORT",
            ),
        )
    )

    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://community.example.org",
    ) as client:
        provider = GotiHubAssistanceProvider(
            "https://community.example.org",
            client=client,
        )

        result = await provider.get_public_context("HELP-2026-001")

    assert result.assistance_type == AssistanceType.FINANCIAL_SUPPORT
    assert result.allowed_actions == [
        AssistanceAction.CONTRIBUTE,
        AssistanceAction.VOLUNTEER,
        AssistanceAction.SHARE,
    ]


@pytest.mark.asyncio
async def test_service_token_sent_to_protected_assistance_endpoint() -> None:
    from community_mcp.providers.assistance import (
        AssistanceContextNotFoundError,
    )

    requests_seen = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests_seen.append(request)
        return httpx.Response(200, json={"items": []})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://community.example.org",
    ) as client:
        provider = GotiHubAssistanceProvider(
            "https://community.example.org",
            organization_slug="test-school",
            service_token="synthetic-test-token",
            client=client,
        )

        with pytest.raises(AssistanceContextNotFoundError):
            await provider.get_public_context("missing-reference")

    assert len(requests_seen) == 1
    assert requests_seen[0].url.path == (
        "/api/v1/integrations/community/organizations/test-school/assistance"
    )
    assert requests_seen[0].headers["Authorization"] == ("Bearer synthetic-test-token")
