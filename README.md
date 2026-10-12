# Community MCP

> An Alexa+ agent that connects trusted communities to what’s happening and helps them respond when someone needs support through permissioned, auditable actions.

Community MCP is an open-source project for the **Amazon Build, Ship, Shape Developer Hackathon 2026**.

It explores a simple question:

**What if a community agent could do more than answer questions — and safely help people act?**

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

Community MCP connects an Alexa+ experience to authoritative community capabilities through the Model Context Protocol (MCP).

The agent can understand natural-language intent and decide which capability is relevant.

Deterministic services remain responsible for identity, permissions, eligibility, confirmation, and the final action.

```text
Natural language
      |
      v
Alexa+ / Agent
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
Alexa+ / agent experience
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
- Alexa+ agent experience;
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

🚧 **Active hackathon development — October 2026**

The project is currently establishing its MCP foundation and controlled integration boundaries.

Architecture, setup instructions, demo scenarios, evaluation results, and AWS deployment documentation will evolve alongside the implementation.

## License

MIT