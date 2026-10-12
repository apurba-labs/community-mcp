import time
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from community_mcp.auth.verifier import JWTTokenVerifier

ISSUER = "https://auth.example.test"
AUDIENCE = "https://mcp.example.test/mcp"


@pytest.fixture
def keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    return private_key, private_key.public_key()


@pytest.fixture
def verifier(keys):
    instance = JWTTokenVerifier(
        issuer=ISSUER,
        audience=AUDIENCE,
        jwks_url=f"{ISSUER}/.well-known/jwks.json",
    )

    with patch.object(
        instance.jwks_client,
        "get_signing_key_from_jwt",
    ) as signing_key:
        signing_key.return_value.key = keys[1]
        yield instance


def make_token(private_key, **overrides):
    now = int(time.time())

    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + 3600,
        "client_id": "test-client",
        "scope": "community.read",
    }

    claims.update(overrides)

    return jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
    )


@pytest.mark.asyncio
async def test_valid_token(verifier, keys):
    token = make_token(keys[0])

    result = await verifier.verify_token(token)

    assert result is not None
    assert result.client_id == "test-client"
    assert result.scopes == ["community.read"]
    assert result.resource == AUDIENCE


@pytest.mark.asyncio
async def test_expired_token(verifier, keys):
    token = make_token(keys[0], exp=int(time.time()) - 3600)

    assert await verifier.verify_token(token) is None


@pytest.mark.asyncio
async def test_wrong_issuer(verifier, keys):
    token = make_token(keys[0], iss="https://wrong.example.test")

    assert await verifier.verify_token(token) is None


@pytest.mark.asyncio
async def test_wrong_audience(verifier, keys):
    token = make_token(keys[0], aud="https://other.example.test/mcp")

    assert await verifier.verify_token(token) is None


@pytest.mark.asyncio
async def test_invalid_signature(verifier, keys):
    different_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    token = make_token(different_private_key)

    assert await verifier.verify_token(token) is None


@pytest.mark.asyncio
async def test_missing_client_id(verifier, keys):
    token = make_token(keys[0], client_id=None)

    assert await verifier.verify_token(token) is None


@pytest.mark.asyncio
async def test_missing_scope(verifier, keys):
    token = make_token(keys[0], scope="")

    result = await verifier.verify_token(token)

    assert result is not None
    assert result.scopes == []
