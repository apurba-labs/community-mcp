# Operations Guide

This guide covers monitoring, maintenance, and incident response for the Community MCP public simulator deployment.

## Services

The public simulator Docker Compose stack contains:

- `demo-mcp`: authenticated MCP server using synthetic data.
- `public-simulator`: browser-facing simulator with Amazon Bedrock reasoning.

The production GotiHub MCP service and Alumni platform are operated separately.

## Service status

Run from the repository root:

    docker compose -f infra/public-simulator/compose.yml ps

View recent logs:

    docker compose -f infra/public-simulator/compose.yml logs --tail=100

Follow simulator logs:

    docker compose -f infra/public-simulator/compose.yml logs -f public-simulator

Avoid printing credentials, access tokens, or private user information in logs.

## Restart services

Restart the simulator:

    docker compose -f infra/public-simulator/compose.yml restart public-simulator

Restart the demonstration MCP server:

    docker compose -f infra/public-simulator/compose.yml restart demo-mcp

A restart does not rebuild the image or apply changes to environment files.

## AI usage accounting

The simulator maintains separate usage accounting for:

- Public demonstration traffic.
- Authenticated Alumni traffic.

Configured daily limits:

| Limit | Public demo | Alumni |
| --- | ---: | ---: |
| Requests per day | 300 | 200 |
| Concurrent requests | 5 | 3 |
| Tokens per day | 150,000 | 100,000 |

These values reflect the application configuration documented at the time of writing. Verify them against the current deployment before changing operational limits.

Usage reservations help prevent concurrent requests from exceeding configured budgets.

When a daily budget is exhausted, the application should return a clear limit message rather than silently continue making model calls.

## Persistent storage

The public simulator uses SQLite for usage accounting.

The Docker named volume `public_simulator_data` persists the database.

Do not run `docker compose down -v` during normal maintenance.

Back up persistent data before changing storage configuration or performing destructive maintenance.

## MCP authentication

MCP requests require valid JWT authentication with the configured issuer, audience, and `community.read` scope.

The public simulator reads its JWT from a protected, read-only token file.

JWT issuance and renewal are external operational responsibilities; the provided Compose stack does not implement token renewal.

Never place JWT values in Git, browser JavaScript, screenshots, or public documentation.

## AWS Bedrock

The public simulator uses Amazon Nova Micro through Amazon Bedrock.

AWS credentials must remain server-side.

Use least-privilege permissions and monitor Bedrock usage and AWS billing.

The application-level usage budget is not a substitute for AWS billing alerts.

## Troubleshooting

### Simulator is unavailable

1. Check container status.
2. Inspect simulator logs.
3. Verify the local port binding.
4. Check the external HTTPS reverse proxy.

### MCP authentication fails

1. Verify token expiry.
2. Check issuer and audience configuration.
3. Confirm JWKS availability.
4. Verify the required scope.
5. Check the protected token-file mount.

Do not disable authentication to work around token failures.

### Bedrock requests fail

1. Verify AWS credentials are available to the container.
2. Confirm the configured AWS region and model.
3. Check IAM permissions and Bedrock model access.
4. Inspect application logs without exposing secrets.

### Usage database errors

1. Check the SQLite database path.
2. Verify volume availability and file permissions.
3. Check available disk space.
4. Preserve the database before attempting repairs.

## Incident response

If credentials or tokens are exposed:

1. Revoke or rotate the affected credentials.
2. Check access logs for suspicious activity.
3. Restrict access while investigating.
4. Restore service only after validating authentication and permissions.

If the public simulator must be stopped:

    docker compose -f infra/public-simulator/compose.yml stop public-simulator

This stops the simulator without deleting its persistent volume.

## Release verification

Before releasing changes:

    uv run ruff check .
    uv run pytest -q
    git diff --check

After deployment, verify authenticated MCP communication, simulator responses, usage accounting, and the public HTTPS route.

## Related documentation

- [Getting started](getting-started.md)
- [Deployment](deployment.md)
- [Security](../architecture/security.md)
