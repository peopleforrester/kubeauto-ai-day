# ADR-006: Developer Portal

## Status

Accepted

## Context

The IDP needs a developer portal for service catalog, software templates,
and integration with ArgoCD and Kubernetes. The portal must support
self-service workflows for deploying new services.

## Decision

Use **Backstage** (CNCF Incubating) as the developer portal.

- Deploy via official Backstage Helm chart (v2.6.3, image 1.9.1)
- Use **static file catalog locations** initially (no GitHub token needed)
- Configure ArgoCD and Kubernetes plugin annotations on catalog entities
- Software templates use `scaffolder.backstage.io/v1beta3` API
- New backend system (`createBackend()` API) is the only supported path
- SQLite in-memory database (acceptable for demo, not production)

## Alternatives Considered

| Tool | Reason for Rejection |
|------|---------------------|
| Port (getport.io) | Commercial, vendor lock-in |
| Humanitec | Commercial, different scope |
| Custom UI | Too much build time for a 10-hour demo |
| No portal | Missing a key IDP component |

## Consequences

- Plugin wiring is fragile; annotations must match exactly
- All Backstage tutorials written before mid-2024 are outdated
- Static catalog locations avoid GitHub token dependency during build
- Template execution requires Git credentials for full E2E (Phase 7)
- SQLite means catalog state is lost on pod restart (acceptable for demo)
