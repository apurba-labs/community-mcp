# Getting Started

This guide explains how to run Community MCP locally.

## Requirements

- Python 3.12
- uv package manager
- Git
- AWS credentials only when using Amazon Bedrock

## Installation

Clone the repository:

    git clone https://github.com/apurba-labs/community-mcp.git
    cd community-mcp

Install dependencies:

    uv sync --dev

Copy the example configuration:

    cp .env.example .env

The default configuration uses synthetic demonstration data and deterministic reasoning.

## Run the Local Demo

    uv run python -m community_mcp.demo

The interactive CLI supports English and Bangla.

Type `exit` to stop.

This mode does not require AWS credentials or a running MCP HTTP server.

## Run Tests

    uv run ruff check .
    uv run pytest -q

## Configuration

Important settings:

| Variable | Purpose |
| --- | --- |
| APP_ENV | Runtime environment |
| DATA_PROVIDER | demo or gotihub |
| REASONING_PROVIDER | deterministic or bedrock |
| BEDROCK_REGION | AWS region |
| BEDROCK_MODEL_ID | Bedrock model identifier |
| MCP_AUTH_ENABLED | Enable MCP authentication |
| SIMULATOR_MCP_URL | MCP server URL |
| SIMULATOR_MCP_TOKEN_FILE | Protected JWT file |
| SIMULATOR_USAGE_DB_PATH | Persistent usage database |

## Security

Never commit real credentials, JWTs, or institutional private data.

Use synthetic data for public demonstrations.

See the security and deployment guides for production considerations.
