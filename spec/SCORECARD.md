# AI Platform Building Scorecard

## Methodology

Each component is scored on six dimensions during the AI-assisted build.
Scores are updated per-component (not per-phase) as each component passes tests.

See `scorecard/methodology.md` (created in Phase 8) for full methodology.

## Scorecard

| Component | Toil Reduced (1-10) | Correction Cycles | AI Time | Est. Manual Time | Toil Shifted? | Notes |
|---|---|---|---|---|---|---|
| VPC + Networking | | | | | | |
| EKS Cluster | | | | | | |
| IAM Roles + Pod Identity | | | | | | |
| Namespace Structure | | | | | | |
| ArgoCD Install + Config | | | | | | |
| App-of-Apps Pattern | | | | | | |
| Sync Waves + Ordering | | | | | | |
| Kyverno Install | | | | | | |
| Kyverno Policies (individual) | | | | | | |
| Kyverno Policy Interactions | | | | | | |
| Falco Install | | | | | | |
| Falco Custom Rules | | | | | | |
| ESO + Secrets Manager | | | | | | |
| RBAC | | | | | | |
| NetworkPolicies | | | | | | |
| Prometheus + Grafana | | | | | | |
| OTel Collector Config | | | | | | |
| Grafana Dashboards | | | | | | |
| Alert Rules | | | | | | |
| Backstage Install | | | | | | |
| Software Templates | | | | | | |
| Backstage Plugin Wiring | | | | | | |
| E2E Integration | | | | | | |
| TLS + cert-manager | | | | | | |
| OIDC Authentication | | | | | | |
| Documentation | | | | | | |
| Architecture Decision Records | | | | | | |

## Totals

- Total AI-assisted build time: ___ hours
- Total human correction time: ___ hours
- Estimated manual build time: ___ hours
- Net toil reduction: ___%
- Components where AI genuinely reduced toil: ___/27
- Components where AI shifted toil without reducing it: ___/27
- Components where starting from scratch would have been faster: ___/27

## Scoring Key

**Toil Reduced (1-10):**
- 10 = Would have taken hours manually, AI did it in minutes with no corrections
- 5 = AI produced a starting point, but required significant human correction
- 1 = AI output was wrong enough that starting from scratch would have been faster

**Correction Cycles:** Number of times AI output needed human intervention.

**Toil Shifted?:**
- Yes = AI converted "writing YAML" toil into "reviewing and debugging AI YAML" toil
- No = AI genuinely reduced total effort
- Partial = Some reduction, some shift
