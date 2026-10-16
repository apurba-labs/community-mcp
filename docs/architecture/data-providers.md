# Community Data Providers

Community MCP uses provider abstractions to separate institutional information from AI reasoning.

## Why providers matter

A language model should not invent official event dates, registration status, or verified assistance details.

Providers supply authoritative application context through explicit interfaces.

## Demo provider

The demo provider supplies synthetic records.

It is intended for:

- Local development.
- Automated testing.
- Public demonstration scenarios.
- Reproducible conversational experiences.

Synthetic information must not be presented as an official announcement from a real institution.

## GotiHub provider

The GotiHub provider retrieves permitted institutional context through controlled application APIs.

The provider is separate from the private GotiHub Alumni database and application implementation.

Available information depends on the configured integration and authorization context.

## Event information

Event capabilities provide structured context such as event identity, published details, registration information, and related institutional information where available.

An unannounced date must remain unannounced in assistant responses.

## Assistance information

Assistance capabilities retrieve approved public context for verified assistance references.

These capabilities are not an unrestricted search interface for private assistance requests.

## Adding another provider

The architecture supports additional providers, but a generic public developer onboarding API is not yet established.

A future provider integration should define:

1. Its supported capabilities.
2. Its authorization requirements.
3. Its institutional data boundaries.
4. Its failure and error behavior.
5. Its audit requirements.
6. Its integration tests.

Future multi-community API documentation is planned for https://mcp.gotihub.com/api.

That URL is a roadmap destination, not a claim that the developer API is currently available.