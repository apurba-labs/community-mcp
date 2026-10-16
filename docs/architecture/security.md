# Security and Trust Boundaries

Community MCP follows a governance-first approach to AI-assisted community interactions.

The model is not an authorization authority.

## MCP authentication

The production MCP HTTP transport uses signed JWT access tokens.

The authentication implementation validates:

- Token signatures using configured JWKS.
- Expected issuer.
- Expected audience.
- Required access scopes.
- Token validity and expiration.

Production configuration requires inbound authentication.

The default required scope is `community.read`.

## Service-to-service authentication

The Alumni application communicates with the assistant backend through a server-side authenticated integration.

The assistant backend connects to the MCP server using protected credentials.

Credentials must not be embedded in browser JavaScript or committed to source control.

## Token lifecycle

The simulator supports reading an MCP access token from a protected file.

This allows the runtime to consume a renewed token without storing a permanent JWT in frontend code.

Token issuance and rotation remain responsibilities of the deployment environment.

## Data authorization

Authentication does not automatically authorize access to every community record.

Institutional information is retrieved through configured providers.

Providers and application policies determine which information is permitted.

Private membership records are not exposed merely because a user asks for them.

## Action governance

The assistant may interpret a request or propose an action.

It cannot grant itself permission to perform consequential operations.

Supported action workflows enforce deterministic application rules and explicit confirmation.

Demonstration action storage remains separate from production institutional data.

## Production safeguards

Production MCP configuration rejects:

- Disabled inbound authentication.
- Demo capability mode.
- Enabled demonstration ledger.
- Non-GotiHub data providers.

These checks reduce the risk of accidentally exposing demonstration capabilities in production.

## AI usage protection

The simulator supports persistent usage accounting and configured request, token, and concurrency limits.

Public simulator and Alumni assistant consumption have separate budgets.

Budget enforcement is an operational safeguard, not a substitute for AWS account-level spending controls.

## Security limitations

Community MCP should not be described as providing unrestricted multi-tenant authorization, complete OAuth infrastructure, or automatic authorization of arbitrary external actions.

New integrations must implement their own institutional authorization and data-access boundaries.