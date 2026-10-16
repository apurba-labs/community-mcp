import pytest

from community_mcp.simulator.mcp_client import (
    CommunityMCPClient,
    CommunityMCPClientError,
)


def test_mcp_client_reads_rotated_token(tmp_path):
    token_file = tmp_path / "mcp.jwt"
    token_file.write_text("first-token")

    client = CommunityMCPClient(
        server_url="https://mcp.example.test/mcp",
        token_file=token_file,
    )

    assert client._get_access_token() == "first-token"

    token_file.write_text("second-token")

    assert client._get_access_token() == "second-token"


def test_mcp_client_rejects_missing_token_file(tmp_path):
    client = CommunityMCPClient(
        server_url="https://mcp.example.test/mcp",
        token_file=tmp_path / "missing.jwt",
    )

    with pytest.raises(
        CommunityMCPClientError,
        match="authentication is temporarily unavailable",
    ):
        client._get_access_token()


def test_mcp_client_requires_exactly_one_token_source(tmp_path):
    with pytest.raises(ValueError):
        CommunityMCPClient(
            server_url="https://mcp.example.test/mcp",
        )

    with pytest.raises(ValueError):
        CommunityMCPClient(
            server_url="https://mcp.example.test/mcp",
            access_token="static-token",
            token_file=tmp_path / "mcp.jwt",
        )
