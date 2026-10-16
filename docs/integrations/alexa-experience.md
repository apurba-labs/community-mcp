# Alexa+ Experience Architecture

## Overview

Community MCP was developed for the Amazon Build, Ship, Shape Developer Hackathon 2026.

It explores how AI assistants can help trusted communities discover events and access approved assistance information.

## Implemented capabilities

- Authenticated Streamable HTTP MCP server.
- Community event and assistance tools.
- Browser-based conversational simulator.
- Amazon Nova Micro through Amazon Bedrock.
- Synthetic demonstration data.
- JWT authentication and authorization.
- AI usage accounting and request budgets.
- GotiHub Alumni application integration.

## Experience flow

1. A visitor sends a message to the public simulator.
2. The simulator processes the conversation using Amazon Bedrock.
3. An authenticated MCP client retrieves community context.
4. MCP tools return approved event or assistance information.
5. The simulator generates a response for the visitor.
6. Usage accounting records the request.

## Governance principles

- Authoritative community data over model memory.
- Deterministic authorization before AI reasoning.
- Least-privilege access to tools and data.
- Explicit confirmation before consequential actions.
- Auditable records for supported actions.

## Alexa+ integration status

The browser simulator demonstrates the intended conversational MCP experience.

It is not an officially verified Alexa+ integration.

The project does not claim a deployed Alexa+ skill or certification.

## Future roadmap

- Multi-community and multi-organization support.
- Permissioned third-party API connectivity.
- Published developer integration documentation.
- Planned API portal: https://mcp.gotihub.com/api
- Future integration with supported voice-assistant platforms.

The API portal is planned and is not currently claimed as live.

## Related documentation

- [Architecture](../architecture/overview.md)
- [Security](../architecture/security.md)
- [Alumni integration](gotihub-alumni.md)
