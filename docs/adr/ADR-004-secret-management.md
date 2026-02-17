# ADR-004: Secret Management

## Status

Accepted

## Context

The IDP needs to deliver secrets from a centralized store to Kubernetes
workloads without storing sensitive values in Git. The solution must
integrate with AWS Secrets Manager and work within the GitOps workflow.

## Decision

Use **External Secrets Operator (ESO)** with **AWS Secrets Manager** as
the backend, authenticated via **IRSA** (IAM Roles for Service Accounts).

ESO reconciles ExternalSecret custom resources into native Kubernetes
Secrets, keeping the secret store as the single source of truth.

## Alternatives Considered

| Tool | Reason for Rejection |
|------|---------------------|
| HashiCorp Vault | Heavier operational overhead, separate HA cluster required |
| Sealed Secrets | Encryption in Git; no centralized rotation or audit trail |
| Secrets Store CSI Driver | Volume-mount only; less GitOps-friendly than ESO |

## Consequences

- IRSA trust policy must be correctly configured (common debugging target)
- ClusterSecretStore allows any namespace to reference AWS SM secrets
- ExternalSecret refresh interval controls sync frequency
- Secret values never appear in Git manifests
- AWS SM costs per-secret per-month (~$0.40/secret)
