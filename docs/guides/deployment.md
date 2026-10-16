# Deployment Guide

Community MCP supports an authenticated MCP service and a separately deployed browser simulator.

This guide describes the Docker configuration included in the repository.

## Deployment architecture

The public demonstration stack contains two services:

| Service | Purpose |
| --- | --- |
| demo-mcp | Authenticated MCP server using synthetic data |
| public-simulator | Browser-facing AI experience using Amazon Bedrock |

Both services communicate over the private `demo_internal` Docker network.

Only the simulator publishes a host port, bound to `127.0.0.1:8090`.

The production GotiHub MCP service and Alumni application are separate deployments.

## Requirements

- Docker Engine and Docker Compose
- AWS credentials with appropriate Bedrock permissions
- JWT signing and renewal infrastructure
- A reverse proxy for public HTTPS access
- Protected configuration and credential storage

## Build the image

From the repository root:

    docker build -t community-mcp:public-demo .

The Dockerfile uses Python 3.12 and installs dependencies using uv.

The runtime container executes as a non-root user.

## Configuration

The public simulator deployment files are located in:

    infra/public-simulator/

Configuration examples:

    demo-mcp.env.example
    public-simulator.env.example

Create deployment-specific environment files from these examples.

Do not commit production credentials.

## Demo MCP configuration

The demo MCP server uses:

    DATA_PROVIDER=demo
    MCP_CAPABILITY_MODE=public
    MCP_AUTH_ENABLED=true
    DEMO_LEDGER_ENABLED=false

Authentication requires configured issuer, audience, JWKS URL, and scope.

The default required scope is `community.read`.

## Public simulator configuration

The simulator connects to the demo MCP service using:

    SIMULATOR_MCP_URL=http://community-demo-mcp:8000/mcp

The deployment reads its MCP JWT from:

    /run/mcp-tokens/simulator.jwt

The token is mounted read-only from the host.

The simulator uses Amazon Nova Micro through Bedrock.

AWS credentials are mounted read-only rather than embedded in the image.

## Start the services

From the repository root:

    docker compose -f infra/public-simulator/compose.yml up -d

The required environment files, token mount, AWS credential mount, and image must exist before starting.

## Verify containers

    docker compose -f infra/public-simulator/compose.yml ps

Check recent logs:

    docker compose -f infra/public-simulator/compose.yml logs --tail=100

The simulator is bound locally to port 8090.

External HTTPS routing is managed outside this Compose file.

## Persistent storage

The named Docker volume `public_simulator_data` stores the simulator SQLite usage database.

Do not delete this volume during ordinary deployments.

## Security boundaries

The demo MCP server is not directly published to the host.

The simulator uses authenticated MCP communication.

The browser must never receive MCP JWTs, AWS credentials, or internal service tokens.

The demo stack uses synthetic information and must remain separate from production Alumni data.

## Production considerations

The example demo configuration uses `APP_ENV=development`.

This does not disable MCP authentication because `MCP_AUTH_ENABLED=true` is explicitly configured.

However, production-specific startup restrictions apply only when the application runs with `APP_ENV=production`.

The synthetic demonstration stack must not be confused with the separate production GotiHub MCP deployment.

## Related documentation

- [Architecture](../architecture/overview.md)
- [Security](../architecture/security.md)
- [Operations](operations.md)
