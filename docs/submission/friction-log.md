# Community MCP — Engineering Friction Log

**Project:** Community MCP — Trusted AI for Real Communities
**Hackathon:** Amazon Build, Ship, Shape Developer Hackathon 2026
**Primary Track:** Alexa+ (Simulated Experience)
**Mini Challenges:** AWS Builder, Open Source
**Repository:** https://github.com/apurba-labs/community-mcp
**Public Demo:** https://mcp.gotihub.com/simulator

## Overview

Community MCP is an open-source project connecting conversational AI to trusted community information through authenticated Model Context Protocol (MCP) tools, Amazon Bedrock, and human-governed workflows.

The project was developed around the practical needs of a real school alumni community in Bangladesh.

During development, we encountered challenges involving MCP authentication, credential renewal, container deployment, and AI usage management.

This document records those challenges, how we addressed them, and improvements that could help other developers.

The observations below describe our integration experience. They should not be interpreted as confirmed defects in Amazon services or the MCP specification.

---

## 1. MCP Authentication and JWT Audience Validation

**Severity:** High
**Category:** Authentication / MCP Integration
**Date:** October 12, 2026

### Task Attempted

Deploy a self-hosted MCP server using Streamable HTTP with secure JWT authentication.

The server needed to expose community event and approved-assistance capabilities while validating token issuer, audience, and authorization scope.

### Steps Taken

1. Implemented MCP tools for community information.
2. Configured RS256 JWT authentication through JWKS.
3. Added issuer, audience, and scope validation.
4. Connected an authenticated MCP client.
5. Tested authorized and unauthorized HTTP requests.

### Expected Result

Valid credentials should permit access to authorized MCP capabilities.

Invalid credentials, incorrect audiences, and insufficient scopes should be rejected consistently.

### Actual Result

During integration, we encountered an audience-validation compatibility issue between the MCP authentication configuration and the application's JWT verification layer.

The initial configuration required adjustment to avoid overlapping validation responsibilities.

### Workaround / Resolution

We delegated audience validation to the JWT verifier while retaining the MCP authentication configuration and required scope checks.

We also added HTTP authentication integration tests.

**Relevant commits:**

- [Secure MCP HTTP transport with JWT authentication](https://github.com/apurba-labs/community-mcp/commit/8bddf31)
- [Verify signed JWT authentication through MCP HTTP](https://github.com/apurba-labs/community-mcp/commit/128318d)
- [Delegate MCP audience validation to JWT verifier](https://github.com/apurba-labs/community-mcp/commit/ff12486)

### Actionable Suggestion

Provide an end-to-end reference implementation for authenticated Streamable HTTP MCP services that demonstrates:

- JWT/JWKS validation.
- Issuer and resource-audience configuration.
- Required authorization scopes.
- Clear separation of transport and application validation responsibilities.
- Negative authentication and authorization tests.

Such guidance would help developers implement secure MCP integrations with fewer configuration mistakes.

---

## 2. Renewable Authentication for Long-Running MCP Sessions

**Severity:** Medium
**Category:** Authentication / Production Reliability
**Date:** October 16, 2026

### Task Attempted

Operate a publicly accessible conversational simulator that communicates with an authenticated MCP server using short-lived credentials.

### Steps Taken

1. Implemented an authenticated MCP client.
2. Connected the browser simulator through a server-side backend.
3. Configured JWT-based MCP authentication.
4. Tested repeated requests and credential handling.
5. Introduced a renewable credential mechanism.

### Expected Result

The simulator should maintain secure access to MCP tools without exposing service credentials to browser users.

Credential renewal should not require rebuilding or restarting the application.

### Actual Result

A static access-token configuration was insufficient for a continuously available public simulator using short-lived MCP credentials.

The integration needed a secure way to consume renewed credentials while keeping token management outside the browser.

### Workaround / Resolution

We implemented support for reading the current MCP credential from a protected server-side token file.

This allows the backend to use renewed credentials without exposing them through the public browser interface.

Authentication behavior was covered by additional tests.

**Relevant commits:**

- [Support renewable MCP authentication](https://github.com/apurba-labs/community-mcp/commit/5a0434f)
- [Align simulator tests with renewable MCP authentication](https://github.com/apurba-labs/community-mcp/commit/6ccf80e)
- [Validate isolated demo MCP endpoint and authentication tests](https://github.com/apurba-labs/community-mcp/commit/176242b)

### Actionable Suggestion

Publish practical examples for long-running MCP clients that cover:

- Short-lived JWT credentials.
- Server-side credential renewal.
- Secure token storage.
- Expiration and retry handling.
- Browser-to-backend credential isolation.

This would be especially valuable for developers building hosted AI assistants rather than short-lived local demonstrations.

---

## 3. Synthetic Demo Data Packaging in Docker

**Severity:** Medium
**Category:** Deployment / Reproducibility
**Date:** October 16, 2026

### Task Attempted

Deploy a public Alexa+-oriented conversational simulator using synthetic community information.

The public demo needed to operate independently of the private production Alumni database.

### Steps Taken

1. Created a separate public simulator deployment.
2. Configured an isolated demo MCP service.
3. Built the application using Docker.
4. Deployed the simulator and MCP services.
5. Tested synthetic data retrieval in the container environment.

### Expected Result

The deployed application should load its bundled synthetic community fixtures consistently.

The public simulator should function without requiring access to private production data.

### Actual Result

The initial container build required additional changes to package synthetic fixture files and resolve their runtime locations correctly.

Local source-tree assumptions did not fully match the packaged container environment.

### Workaround / Resolution

We updated the Docker packaging and fixture-path resolution so the application could locate the synthetic data at runtime.

The public simulator was subsequently deployed and verified.

**Relevant commits:**

- [Package synthetic demo fixtures in container image](https://github.com/apurba-labs/community-mcp/commit/bb52ccd)
- [Resolve synthetic demo fixtures in Docker runtime](https://github.com/apurba-labs/community-mcp/commit/ea72a85)

### Actionable Suggestion

Provide container-oriented examples for AI agent projects that include:

- Packaging non-Python resources.
- Resolving fixture paths in installed packages.
- Separating public demo data from private integrations.
- Testing container images independently of the development source tree.

This would improve reproducibility for projects submitted to hackathons and deployed for public evaluation.

---

## 4. Amazon Bedrock Usage Accounting and Budget Management

**Severity:** Medium
**Category:** AI Operations / Cost Management
**Date:** October 14, 2026

### Task Attempted

Implement predictable AI usage limits for two separate Community MCP experiences:

1. A public conversational simulator.
2. An authenticated institutional assistant.

Both use Amazon Bedrock reasoning, but they require independent usage accounting and operational limits.

### Steps Taken

1. Integrated Amazon Nova Micro through Amazon Bedrock.
2. Added model usage recording.
3. Implemented persistent request accounting.
4. Added daily request and token budgets.
5. Introduced concurrency limits and usage reservations.
6. Added reservation reconciliation and expiry tests.

### Expected Result

The application should enforce usage limits before starting a model request and reconcile actual consumption afterward.

Public simulator usage should not consume the institutional assistant's allocated budget.

### Actual Result

Bedrock model invocation provides the reasoning capability, but the application also needed its own persistent budget reservation and reconciliation mechanism.

Handling concurrent requests, incomplete operations, and reservation expiry required additional application-level engineering.

This was an architectural challenge rather than a confirmed Bedrock service defect.

### Workaround / Resolution

We implemented SQLite-backed usage accounting with:

- Separate public and institutional usage contexts.
- Daily request limits.
- Token budgets.
- Concurrent request limits.
- Budget reservations.
- Reservation expiry and reconciliation.
- Automated tests.

**Relevant commits:**

- [Persistent AI usage accounting and budget reservations](https://github.com/apurba-labs/community-mcp/commit/400a482)
- [Enforce persistent usage budgets across simulator channels](https://github.com/apurba-labs/community-mcp/commit/3b929d0)
- [Fix usage indexes after schema migration](https://github.com/apurba-labs/community-mcp/commit/eefce73)

### Actionable Suggestion

Provide a reference architecture for cost-aware Amazon Bedrock agents covering:

- Pre-request budget reservations.
- Token usage reconciliation.
- Concurrent invocation limits.
- Recovery from failed or incomplete requests.
- Organization-level usage accounting.
- Practical patterns for controlling costs in shared AI services.

This would help developers build economically sustainable AI applications for smaller organizations and community platforms.

---

## Summary

| Challenge | Severity | Resolution |
|---|---|---|
| MCP JWT audience validation | High | Explicit JWT verifier responsibility and integration tests |
| Renewable MCP authentication | Medium | Protected server-side token file and authentication tests |
| Synthetic fixture packaging | Medium | Docker resource packaging and runtime path fixes |
| Bedrock usage accounting | Medium | Persistent SQLite budgets, reservations, and reconciliation |

## Key Learning

Building a conversational AI prototype is relatively straightforward.

Making that experience secure, reproducible, continuously available, and operationally sustainable requires additional engineering.

For Community MCP, the most important lesson was that AI reasoning and application authority must remain separate.

The model can interpret requests and help users navigate community information, but authentication, authorization, approval, privacy, and resource limits must remain under deterministic application control.

These challenges shaped the project's architecture and helped turn an initial demonstration into a publicly accessible, testable system.

---

**Project Repository:** https://github.com/apurba-labs/community-mcp
**Live Simulator:** https://mcp.gotihub.com/simulator
**Project Website:** https://mcp.gotihub.com/
