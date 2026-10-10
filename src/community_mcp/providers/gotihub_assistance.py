import httpx
from pydantic import BaseModel, ValidationError

from community_mcp.providers.assistance import (
    AssistanceContextNotFoundError,
    AssistanceContextProvider,
    AssistanceContextUnavailableError,
)
from community_mcp.providers.credentials import (
    AccessTokenProvider,
    AccessTokenUnavailableError,
)
from community_mcp.schemas.assistance import (
    AssistanceAction,
    AssistanceRequest,
    AssistanceStatus,
    AssistanceType,
    AssistanceUrgency,
)


class _GotiHubDiscoveryItem(BaseModel):
    public_reference: str
    assistance_type: AssistanceType
    audience_scope: str
    audience_batch_year: int | None
    visibility: str
    urgency: AssistanceUrgency
    blood_group: str | None
    units_needed: int | None
    location_label: str | None
    public_context: str | None
    created_at: str


class _GotiHubDiscoveryResponse(BaseModel):
    items: list[_GotiHubDiscoveryItem]


def _allowed_actions(
    assistance_type: AssistanceType,
) -> list[AssistanceAction]:
    if assistance_type == AssistanceType.BLOOD:
        return [
            AssistanceAction.DONATE_BLOOD,
            AssistanceAction.VOLUNTEER,
            AssistanceAction.SHARE,
        ]

    if assistance_type == AssistanceType.FINANCIAL_SUPPORT:
        return [
            AssistanceAction.CONTRIBUTE,
            AssistanceAction.VOLUNTEER,
            AssistanceAction.SHARE,
        ]

    return [
        AssistanceAction.VOLUNTEER,
        AssistanceAction.SHARE,
    ]


class GotiHubAssistanceProvider(AssistanceContextProvider):
    def __init__(
        self,
        base_url: str,
        credential_provider: AccessTokenProvider | None = None,
        *,
        client: httpx.AsyncClient | None = None,
        organization_slug: str | None = None,
        service_token: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._credential_provider = credential_provider
        self._client = client
        self._organization_slug = organization_slug
        self._service_token = service_token

    async def _get(
        self,
        path: str,
        *,
        access_token: str | None = None,
    ) -> httpx.Response:
        headers = {}

        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        try:
            if self._client is not None:
                return await self._client.get(path, headers=headers)

            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=10.0,
            ) as client:
                return await client.get(path, headers=headers)
        except httpx.HTTPError as exc:
            raise AssistanceContextUnavailableError("Unable to reach community platform") from exc

    @staticmethod
    def _to_request(
        item: _GotiHubDiscoveryItem,
    ) -> AssistanceRequest:
        return AssistanceRequest(
            public_reference=item.public_reference,
            assistance_type=item.assistance_type,
            status=AssistanceStatus.ACTIVE,
            summary=item.public_context,
            urgency=item.urgency,
            location_text=item.location_label,
            blood_group=item.blood_group,
            units_needed=item.units_needed,
            verified=True,
            approved=True,
            allowed_actions=_allowed_actions(item.assistance_type),
        )

    async def get_public_context(
        self,
        public_reference: str,
    ) -> AssistanceRequest:
        if self._organization_slug:
            if not self._service_token:
                raise AssistanceContextUnavailableError(
                    "Community service credentials are unavailable"
                )

            response = await self._get(
                f"/api/v1/integrations/community/organizations/"
                f"{self._organization_slug}/assistance",
                access_token=self._service_token,
            )
        else:
            response = await self._get("/api/v1/assistance/public/requests")

        if response.is_error:
            raise AssistanceContextUnavailableError(
                f"Community platform returned HTTP {response.status_code}"
            )

        try:
            payload = _GotiHubDiscoveryResponse.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise AssistanceContextUnavailableError(
                "Community platform returned invalid assistance context"
            ) from exc

        item = next(
            (item for item in payload.items if item.public_reference == public_reference),
            None,
        )

        if item is None:
            raise AssistanceContextNotFoundError(public_reference)

        return self._to_request(item)

    async def get_member_context(
        self,
        public_reference: str,
        *,
        actor_id: str,
    ) -> AssistanceRequest:
        if self._credential_provider is None:
            raise AssistanceContextUnavailableError(actor_id)

        try:
            access_token = await self._credential_provider.get_access_token(actor_id)
        except AccessTokenUnavailableError as exc:
            raise AssistanceContextUnavailableError(actor_id) from exc

        if not access_token.strip():
            raise AssistanceContextUnavailableError(actor_id)

        response = await self._get(
            "/api/v1/assistance/requests",
            access_token=access_token,
        )

        if response.status_code in {401, 403}:
            raise AssistanceContextUnavailableError(actor_id)

        if response.is_error:
            raise AssistanceContextUnavailableError(
                f"Community platform returned HTTP {response.status_code}"
            )

        try:
            payload = _GotiHubDiscoveryResponse.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise AssistanceContextUnavailableError(
                "Community platform returned invalid assistance context"
            ) from exc

        item = next(
            (item for item in payload.items if item.public_reference == public_reference),
            None,
        )

        if item is None:
            raise AssistanceContextNotFoundError(public_reference)

        return self._to_request(item)
