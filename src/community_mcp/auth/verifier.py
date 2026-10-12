from __future__ import annotations

import asyncio
import time

import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError
from mcp.server.auth.provider import AccessToken


class JWTTokenVerifier:
    """Verify OAuth access tokens issued for Community MCP."""

    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        jwks_url: str,
        algorithms: tuple[str, ...] = ("RS256",),
    ) -> None:
        if not issuer or not audience or not jwks_url:
            raise ValueError("JWT issuer, audience and JWKS URL are required.")

        self.issuer = issuer.rstrip("/")
        self.audience = audience
        self.algorithms = algorithms
        self.jwks_client = PyJWKClient(
            jwks_url,
            cache_jwk_set=True,
            lifespan=300,
            timeout=5,
        )

    def _verify(self, token: str) -> AccessToken | None:
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(self.algorithms),
                audience=self.audience,
                issuer=self.issuer,
                options={
                    "require": ["exp", "iat", "iss", "aud"],
                },
                leeway=30,
            )

            expires_at = int(claims["exp"])

            if expires_at <= time.time():
                return None

            scopes_value = claims.get("scope", "")
            if isinstance(scopes_value, str):
                scopes = scopes_value.split()
            elif isinstance(claims.get("scp"), list):
                scopes = claims["scp"]
            else:
                scopes = []

            client_id = claims.get("client_id") or claims.get("azp")

            if not isinstance(client_id, str) or not client_id:
                return None

            return AccessToken(
                token=token,
                client_id=client_id,
                scopes=scopes,
                expires_at=expires_at,
                resource=self.audience,
                subject=claims.get("sub"),
            )

        except (PyJWTError, ValueError, TypeError, KeyError):
            return None

    async def verify_token(self, token: str) -> AccessToken | None:
        return await asyncio.to_thread(self._verify, token)
