# Community MCP

> Governed AI for trusted communities — authoritative answers, permissioned actions, and auditable outcomes.

**Community MCP** is an open-source Model Context Protocol (MCP) integration layer developed for the Amazon Build, Ship, Shape Developer Hackathon 2026.

It connects conversational AI to trusted community information and governed capabilities.

### Live experiences

- [Community MCP website](https://mcp.gotihub.com/)
- [Public AI simulator](https://mcp.gotihub.com/simulator)
- [GotiHub Alumni platform](https://chandaikonamlhs.org/)

The public simulator uses synthetic community data and Amazon Nova Micro through Amazon Bedrock.

GotiHub Alumni is an independently developed production platform with a separate authenticated AI integration.

**Alexa+ status:** The browser simulator demonstrates the intended conversational MCP experience. An end-to-end Alexa+ integration has not been independently verified.

## The Problem

Schools, alumni associations, clubs, and other trusted communities already have people, events, committees, schedules, and support networks.

But when someone asks:

- "What's happening at our centenary celebration?"
- "I'm attending Saturday afternoon. What should I join?"
- "Has the venue been confirmed?"
- "Does anyone in our community urgently need help?"
- "How can I support this medical assistance request?"

the answer is usually fragmented across websites, social posts, messaging groups, spreadsheets, and individual organizers.

A conversational agent can make this information easier to reach.

The harder problem is allowing that agent to **take useful action without giving the model uncontrolled authority**.

Community MCP is built around that boundary.

## What We're Building

Community MCP connects conversational AI to authoritative community capabilities through the Model Context Protocol (MCP).

The agent can understand natural-language intent and decide which capability is relevant.

Deterministic services remain responsible for identity, permissions, eligibility, confirmation, and the final action.

```text
Natural language
      |
      v
Conversational AI / Simulator
      |
      | reasoning
      v
Community MCP
      |
      | permissioned capabilities
      v
Policy + Community APIs
      |
      | deterministic rules
      v
Real-world action
      |
      v
Audit trail
```

The model can **request** an action.

It does not grant itself permission to perform one.

## Core Experiences

### Know and Participate

Community MCP can expose authoritative institutional information such as:

- upcoming events;
- event schedules and sessions;
- event teams;
- awards and institutional context;
- current event updates.

The project uses a real centenary-event journey as one integration scenario rather than relying entirely on an invented hackathon domain.

### Respond and Help

The primary new workflow explores governed community assistance.

A person may ask whether someone in the community needs support, understand a verified assistance request, discover safe ways to respond, and explicitly confirm an action.

Example:

```text
Person expresses a need
        |
        v
Agent understands intent and constraints
        |
        v
Community MCP retrieves authoritative context
        |
        v
Policy determines available actions
        |
        v
Agent proposes a safe action
        |
        v
Human confirms
        |
        v
Action is coordinated
        |
        v
Result is auditable
```

Medical assistance and blood coordination are initial scenarios for demonstrating this workflow.

## Safety and Authority

Community MCP deliberately separates **reasoning** from **authority**.

The agent may:

- interpret conversational intent;
- retrieve permitted information;
- compare available options;
- propose an action;
- ask for confirmation.

The agent may not:

- bypass authorization;
- expose private community data;
- invent institutional state;
- grant itself additional permissions;
- silently perform consequential actions.

Authorization and business rules remain deterministic.

## Real Platform, Public Project

Community MCP is a standalone public project.

It does not connect directly to the private GotiHub Alumni database or import its internal models.

```text
GotiHub Alumni
private production platform
        |
        | controlled APIs
        v
Community MCP
public hackathon project
        |
        | MCP
        v
Authenticated AI experience
```

The production platform provides real institutional foundations including organizations, people, committees, events, schedules, awards, and public-safe community information.

Private alumni data is never required by the public repository.

## Provider Boundary

Community MCP is designed to run independently.

```text
CommunityDataProvider
        |
        +-- DemoProvider
        |     synthetic, reproducible hackathon data
        |
        +-- GotiHubProvider
              controlled GotiHub APIs
```

This allows contributors and judges to run the project without access to private production infrastructure while preserving a path to demonstrate integration with a real deployed community platform.

## Hackathon Scope

This repository contains the work being developed for the Amazon Build, Ship, Shape Developer Hackathon:

- MCP transport and tools;
- browser-based conversational experience simulator;
- community assistance workflow;
- deterministic policy and confirmation boundaries;
- AWS integration;
- auditability and observability;
- synthetic demo scenarios;
- evaluation and reproducible tests.

The existing GotiHub Alumni production platform is separate and is not presented as hackathon-built work.

## Engineering Principles

1. **Authoritative data over model memory**
2. **Deterministic rules before AI judgment**
3. **Least privilege for agent capabilities**
4. **Explicit confirmation for consequential actions**
5. **No private production data in the public demo**
6. **Every important action should be traceable**
7. **AWS services must have an architectural reason to exist**
8. **Build one convincing workflow before adding breadth**

## Status

**Active development — October 2026**

Implemented capabilities include:

- Authenticated Streamable HTTP MCP server.
- Event and approved assistance context tools.
- Amazon Bedrock reasoning with Nova Micro.
- Public conversational simulator using synthetic data.
- JWT/JWKS authentication and authorization.
- Deterministic policy and confirmation boundaries.
- Persistent AI usage accounting and request budgets.
- Authenticated integration with GotiHub Alumni.
- Automated tests and deployment configuration.

The browser simulator is not a verified Alexa+ deployment.

## Developer Quick Start

Requirements: Python 3.12 and uv.

```bash
git clone https://github.com/apurba-labs/community-mcp.git
cd community-mcp
uv sync --dev
uv run python -m community_mcp.demo
```

Run automated checks:
```
uv run ruff check .
uv run pytest -q
```
The CLI demo uses synthetic data and deterministic reasoning.
AWS credentials are not required.

## Documentation

- [Documentation index](docs/README.md)
- [Architecture](docs/architecture/overview.md)
- [Security](docs/architecture/security.md)
- [Data providers](docs/architecture/data-providers.md)
- [Getting started](docs/guides/getting-started.md)
- [Deployment](docs/guides/deployment.md)
- [Operations](docs/guides/operations.md)
- [Alumni integration](docs/integrations/gotihub-alumni.md)
- [Alexa+ experience](docs/integrations/alexa-experience.md)

## Roadmap

Community MCP aims to support multiple trusted communities through permissioned, documented integrations.

Planned capabilities include:

- Multi-community and multi-organization support.
- Permissioned external API connectivity.
- Developer integration documentation.
- A developer API portal at https://mcp.gotihub.com/api.

The API portal is planned and is not currently claimed as live.


## License

MIT