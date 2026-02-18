# ABOUTME: ADR for authentication strategy across platform services.
# ABOUTME: Documents choice of GitHub OIDC over alternatives for demo platform.

# ADR-007: Authentication Strategy

## Status

Accepted

## Context

The IDP has three user-facing services that need authentication:
ArgoCD, Backstage, and Grafana. For KubeAuto Day, we need an auth
solution that is:
- Easy for attendees to use (most have GitHub accounts)
- Quick to set up (within the 60-minute hardening phase)
- Demonstrably production-grade (not basic auth)
- Consistent across all services

## Decision

Use **GitHub OIDC via OAuth App** for all platform UIs.

ArgoCD uses its built-in Dex connector for GitHub OIDC. Backstage uses
the GitHub auth provider. Grafana uses GitHub OAuth configuration.

OAuth credentials are stored in AWS Secrets Manager and synced to
Kubernetes via External Secrets Operator. No credentials in Git.

RBAC mapping:
- OIDC-authenticated users receive read-only access in ArgoCD
- Admin access retained via local admin accounts for all services
- Backstage catalog access is unauthenticated (read-only data)

## Alternatives Considered

### AWS Cognito
- Heavier setup (user pool, app client, domain)
- More appropriate for customer-facing apps
- Overkill for a demo with known audience

### Dex with LDAP
- Requires running an LDAP server
- No existing directory to connect to
- Added complexity with no benefit for demo

### Basic Auth (username/password)
- Insecure for production demonstration
- No SSO experience
- Poor impression at a CNCF conference

### Keycloak
- Full-featured IAM server
- Significant operational overhead
- Would consume too much of the 60-minute budget

## Consequences

- Attendees must have GitHub accounts to authenticate
- OAuth App callback URLs must match the domain configuration
- GitHub OAuth Apps are organization-scoped or user-scoped (not
  enterprise-grade), which is appropriate for a demo
- Rate limits on GitHub OAuth token validation are generous (~5000/hr)
  and not a concern for demo traffic
