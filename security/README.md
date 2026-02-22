# Security

Kubernetes security resources organized by concern. All deployed via ArgoCD.

## Directory Structure

```
rbac/
  cluster-roles.yaml     # platform-admin, app-deployer, app-viewer ClusterRoles
  role-bindings.yaml     # Namespace-scoped RoleBindings (apps, monitoring)

network-policies/
  → see ../policies/network-policies/

eso/
  cluster-secret-store.yaml   # ClusterSecretStore pointing to AWS Secrets Manager
  test-external-secret.yaml   # ExternalSecret syncing a test secret

falco/
  custom-rules.yaml      # 3 general rules (write to /etc, shell spawn, sensitive mount)
  eks-aware-rules.yaml   # 2 EKS-specific rules (IMDS access, NodePort creation)

quotas-pdbs/
  resource-quota.yaml    # Apps namespace: 10 pods, 4 CPU, 8Gi memory
  pdbs.yaml              # PodDisruptionBudgets for 5 critical services

cert-manager/
  cluster-issuers.yaml   # Let's Encrypt staging + production ClusterIssuers
```

## Security Posture Summary

| Concern | Implementation | Guardrail |
|---------|---------------|-----------|
| Admission control | Kyverno (6 policies in `policies/kyverno/`) | #3, #4, #8 |
| Runtime detection | Falco eBPF + 5 custom rules | #3, #5 |
| Secret management | ESO + AWS Secrets Manager (no static creds) | #7 |
| Access control | RBAC (least-privilege, namespace-scoped) | #2 |
| Network isolation | NetworkPolicies (default-deny + allow rules) | #2 |
| Resource limits | ResourceQuotas on apps namespace | #2 |
| Availability | PDBs on ArgoCD, Kyverno, Prometheus, Grafana, Falco | #6 |
| TLS | cert-manager + Let's Encrypt (HTTP-01) | #7 |
| Auth | GitHub OIDC via ArgoCD Dex (no static passwords) | #7 |

See [docs/SECURITY.md](../docs/SECURITY.md) for the full security architecture.

See [docs/EIGHT-GUARDRAILS.md](../docs/EIGHT-GUARDRAILS.md) for guardrail framework details.
