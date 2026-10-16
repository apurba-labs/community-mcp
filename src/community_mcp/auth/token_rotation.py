#!/usr/bin/env python3
"""Rotate the short-lived production MCP token for the public simulator."""

from __future__ import annotations

import argparse
import os
import tempfile
import time
from pathlib import Path

import jwt

ISSUER = "https://mcp.gotihub.com"
AUDIENCE = "https://mcp.gotihub.com"
KEY_ID = "community-mcp-2026-01"
CLIENT_ID = "community-public-simulator"


def rotate_token(private_key_path: Path, output_path: Path) -> None:
    now = int(time.time())

    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + 300,
        "client_id": CLIENT_ID,
        "sub": CLIENT_ID,
        "scope": "community.read",
    }

    private_key = private_key_path.read_bytes()

    token = jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
        headers={"kid": KEY_ID},
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=".simulator-jwt-",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            os.fchmod(temporary.fileno(), 0o640)
            temporary.write(token)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())

        os.replace(temporary_path, output_path)

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--private-key",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    rotate_token(args.private_key, args.output)

    print("Simulator MCP token rotated successfully.")


if __name__ == "__main__":
    main()
