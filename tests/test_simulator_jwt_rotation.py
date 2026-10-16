import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from community_mcp.auth.token_rotation import rotate_token


def test_rotated_jwt_contains_expected_claims(tmp_path):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    private_key_path = tmp_path / "private.pem"

    private_key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    output_path = tmp_path / "simulator.jwt"

    rotate_token(private_key_path, output_path)

    token = output_path.read_text().strip()

    claims = jwt.decode(
        token,
        private_key.public_key(),
        algorithms=["RS256"],
        audience="https://mcp.gotihub.com",
        issuer="https://mcp.gotihub.com",
    )

    assert claims["client_id"] == "community-public-simulator"
    assert claims["scope"] == "community.read"
    assert claims["exp"] - claims["iat"] == 300

    assert jwt.get_unverified_header(token)["kid"] == ("community-mcp-2026-01")


def test_rotation_replaces_existing_token(tmp_path):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    private_key_path = tmp_path / "private.pem"

    private_key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    output_path = tmp_path / "simulator.jwt"
    output_path.write_text("expired-token")

    rotate_token(private_key_path, output_path)

    assert output_path.read_text().strip() != "expired-token"
    assert output_path.stat().st_mode & 0o777 == 0o640
