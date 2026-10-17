# Community MCP Documentation

**Community MCP — Trusted AI for Real Communities**

*Trusted AI for real communities, governed by people.*

Community MCP connects AI assistants to trusted community information and permissioned capabilities through authenticated Model Context Protocol (MCP) interfaces.

Built for the Amazon Build, Ship, Shape Developer Hackathon 2026, the project combines Amazon Bedrock reasoning, secure MCP tools, deterministic authorization, and human-governed community workflows.

## Live Project

- [Community MCP Website](https://mcp.gotihub.com/)
- [Interactive Simulator](https://mcp.gotihub.com/simulator)
- [GotiHub Alumni — Real Community Platform](https://chandaikonamlhs.org/)
- [Source Code](https://github.com/apurba-labs/community-mcp)

The public simulator uses synthetic community data. The independently deployed GotiHub Alumni platform provides a real-world integration scenario.

## Architecture

- [Architecture Overview](architecture/overview.md)
- [Security and Trust Boundaries](architecture/security.md)
- [Community Data Providers](architecture/data-providers.md)

The architecture separates AI reasoning from application authority.

Amazon Bedrock interprets conversational requests, while authenticated MCP tools retrieve permitted information. Authorization, confirmation, and business rules remain under application control.

## Developer Guides

- [Getting Started](guides/getting-started.md)
- [Deployment](guides/deployment.md)
- [Operations](guides/operations.md)

These guides cover local development, service deployment, and operational considerations.

## Integrations

- [GotiHub Alumni Integration](integrations/gotihub-alumni.md)
- [Alexa+ Experience Architecture](integrations/alexa-experience.md)

The Alexa+ track submission demonstrates a simulated conversational experience using Amazon Bedrock and authenticated MCP.

Direct Alexa+ integration is a future direction, not a completed feature.

## Security and Governance

Community MCP is designed around six principles:

1. Authoritative information over model-generated assumptions.
2. Authentication and authorization before protected capabilities.
3. Separation of synthetic demo data and production information.
4. Deterministic rules for sensitive operations.
5. Explicit human confirmation for consequential actions.
6. Auditable operations and controlled AI usage.

The production MCP service uses JWT/JWKS authentication, while the public simulator operates through an isolated demonstration environment.

## Hackathon Submission

- [Engineering Friction Log](submission/friction-log.md)
- [GitHub Development History](https://github.com/apurba-labs/community-mcp/commits/main)

The friction log documents authentication, credential renewal, deployment, and usage-accounting challenges encountered during development.

Each entry includes the task attempted, expected and actual behavior, resolution, and actionable recommendations.

## Design Decisions

Architecture decisions are maintained in the [decisions directory](decisions/).

## Project Status

### Implemented

- Authenticated MCP server using Streamable HTTP.
- Community event and approved-assistance context tools.
- Amazon Bedrock / Nova Micro reasoning integration.
- English and Bengali conversational experiences.
- Public browser simulator with synthetic community data.
- Separate authenticated GotiHub Alumni assistant integration.
- JWT/JWKS authentication and scoped MCP access.
- Persistent AI usage accounting and budget controls.
- Automated tests and containerized deployment.

### Planned

- Direct Alexa+ integration.
- Support for additional community organizations.
- Developer API and documentation portal.
- Expanded operational reporting and governance capabilities.

---

**Community MCP — Trusted AI for Real Communities**

*Built for one real community. Designed with the potential to serve many.*