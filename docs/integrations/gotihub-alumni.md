# GotiHub Alumni Integration

## Overview

GotiHub Alumni is a real community platform for Chandaikona M. L. High School.

Community MCP connects AI assistants to approved community information through authenticated interfaces.

The Alumni application and Community MCP maintain separate authentication and authorization boundaries.

## Architecture

The integration follows this flow:

1. A visitor or member uses the Alumni website.
2. The Alumni gateway authenticates and establishes user context.
3. The gateway communicates with Community MCP.
4. MCP retrieves approved information through its data provider.
5. The response returns through the Alumni gateway.

Browser clients must never receive internal MCP credentials.

## Authorization

The Alumni application controls user identity, organization context, and permissions.

Community MCP must not infer membership from a user's message.

Registration is limited to eligible former students of Chandaikona M. L. High School.

Eligibility and verification are separate requirements.

## Data privacy

Public visitors can access approved public information.

Authenticated members may access additional approved information according to their permissions.

Sensitive assistance requests, including blood donation, require appropriate authorization.

The public simulator uses synthetic data and must remain separate from private Alumni records.

## Usage accounting

Public simulator and authenticated Alumni requests have separate usage accounting and limits.

Organization-level reporting must preserve tenant isolation.

## Future integrations

Community MCP is designed to support multiple trusted organizations through permissioned APIs.

A developer API and documentation portal is planned at:

https://mcp.gotihub.com/api

This portal is planned, not an existing public API.

## Related documentation

- [Architecture](../architecture/overview.md)
- [Security](../architecture/security.md)
- [Data providers](../architecture/data-providers.md)
