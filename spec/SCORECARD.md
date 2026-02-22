# AI Platform Building Scorecard

## Methodology

Each component is scored on six dimensions during the AI-assisted build.
Scores are updated per-component (not per-phase) as each component passes tests.

See `scorecard/methodology.md` (created in Phase 8) for full methodology.

## Scorecard

| Component | Toil Reduced (1-10) | Correction Cycles | AI Time | Est. Manual Time | Toil Shifted? | Notes |
|---|---|---|---|---|---|---|
| VPC + Networking | 7 | 1 | 5 min | 30 min | No | VPC module config straightforward; NAT gateway + subnet tagging correct first try |
| EKS Cluster | 6 | 3 | 25 min | 45 min | Partial | Module v21.15 variable renames caused 2 correction cycles; AWS provider 6.x dependency; addon bootstrap chicken-and-egg required manual intervention |
| IAM Roles + Pod Identity | 7 | 1 | 5 min | 25 min | No | IRSA roles for EBS CSI + LB Controller correct; Helm release for LB Controller wired properly |
| Namespace Structure | 9 | 0 | 2 min | 10 min | No | PSS labels on apps namespace correct first try; clean YAML |
| ArgoCD Install + Config | 8 | 1 | 8 min | 40 min | No | Helm chart version mapping (9.x not 7.x) needed correction from skill file; ArgoCD 3.2.6 installed cleanly; RBAC + values correct first try |
| App-of-Apps Pattern | 9 | 1 | 5 min | 20 min | No | Root app + namespace child app correct; needed repo secret for private GitHub access |
| Sync Waves + Ordering | 8 | 1 | 3 min | 15 min | No | Wave -10 for namespaces works; drift detection test needed fix (annotation tracking only monitors managed fields, not new labels) |
| Kyverno Install | 6 | 3 | 15 min | 35 min | Partial | Skill file webhook config was wrong (list vs map for chart 3.7.0); CRD annotation too large required ServerSideApply; clean reinstall after stale sync; 3 correction cycles total |
| Kyverno Policies (6 policies) | 8 | 0 | 5 min | 25 min | No | All 6 ClusterPolicies correct first try; enforce in apps namespace only; audit mode for NetworkPolicy check |
| Kyverno Policy Interactions | 9 | 0 | 2 min | 15 min | No | Pod rejection tested via dry-run; 5 policies fire correctly on non-compliant pod; no false positives in system namespaces |
| Falco Install | 7 | 2 | 10 min | 30 min | Partial | Skill file had wrong chart version (4.x vs 7.x); write_etc_common macro removed in 0.42.x; DaemonSet + eBPF correct first try |
| Falco Custom Rules | 8 | 1 | 5 min | 20 min | No | 5 custom rules (3 general + 2 EKS-aware) correct; one macro fix needed; Falcosidekick with Prometheus metrics working |
| ESO + Secrets Manager | 7 | 2 | 12 min | 40 min | Partial | ESO 1.3.2 API version v1 (not v1beta1); ArgoCD sync cache stale after API fix; IRSA + ClusterSecretStore correct; secret synced successfully |
| RBAC | 9 | 0 | 3 min | 10 min | No | ClusterRoles + namespace-scoped RoleBindings correct first try; cross-namespace denial verified |
| NetworkPolicies | 9 | 0 | 3 min | 15 min | No | Default deny + DNS allow + ingress allow correct first try; pod-selector matching verified |
| Prometheus + Grafana | 8 | 1 | 8 min | 40 min | No | kube-prometheus-stack 82.1.0 deployed cleanly; remote write receiver enabled; 1 correction for kubectl run stdout noise in tests (pod deleted message appended to JSON) |
| OTel Collector Config | 6 | 3 | 15 min | 35 min | Partial | Chart 0.145.0 requires explicit image.repository (breaking change from 0.89+); k8s image lacks prometheusremotewrite exporter, needed contrib; DaemonSet mode disables service by default |
| Grafana Dashboards | 9 | 0 | 3 min | 20 min | No | Platform Overview dashboard with 8 panels correct first try; ConfigMap sidecar provisioning worked immediately |
| Alert Rules | 9 | 0 | 2 min | 15 min | No | 4 custom PrometheusRules (NodeNotReady, PodCrashLoop, ArgoCDAppDegraded, FalcoCriticalAlert) correct first try via additionalPrometheusRulesMap |
| Backstage Install | 8 | 1 | 10 min | 45 min | No | Helm chart 2.6.3 (image 1.9.1) deployed cleanly; 1 correction for Kyverno livenessProbe in test dry-run; catalog ConfigMap approach for private repo; Synced+Healthy in 40s |
| Software Templates | 9 | 0 | 5 min | 20 min | No | deploy-service and create-namespace templates correct first try; skeleton produces Kyverno-compliant resources verified by dry-run and live deployment |
| Backstage Plugin Wiring | 8 | 0 | 3 min | 25 min | No | Static file catalog via ConfigMap mount; 4 catalog entities (System, Component, 2 Templates) loaded; ArgoCD/K8s annotations on sample-app correct |
| E2E Integration | 7 | 2 | 12 min | 30 min | No | 7 cross-component tests; 2 fixes needed: NetworkPolicy blocks pod-to-service egress (used localhost), Falco non-interactive exec not logged (switched to /etc write marker); ArgoCD 30s reconciliation for demo |
| TLS + cert-manager | 8 | 1 | 5 min | 25 min | No | cert-manager 1.19.1 deployed cleanly; 1 fix for Application YAML in subdirectory (app-of-apps doesn't recurse); HTTP-01 ClusterIssuers Ready; namespace ordering required force refresh |
| Resource Quotas + PDBs | 9 | 0 | 3 min | 15 min | No | ResourceQuota and 5 PDBs correct first try; ArgoCD Application pattern reused cleanly |
| OIDC Authentication | 8 | 1 | 8 min | 35 min | No | GitHub OIDC via ArgoCD Dex connector; manual prerequisite (OAuth App creation) completed; Backstage GitHub auth integrated; 1 correction for callback URL config |
| Documentation | 9 | 0 | 5 min | 30 min | No | SECURITY.md (8 sections), COST.md, ADR-007 all correct first try; gitleaks allowlist for known test secret |
| Architecture Decision Records | 9 | 0 | 3 min | 15 min | No | 9 ADRs written across all phases (000-007 + 003b); MADR format consistent; ADR-007 auth strategy completed |

## Totals

- **Total AI-assisted build time: 3 hours 10 min** (190 min across 27 scored components)
- **Estimated manual build time: 12 hours 5 min** (725 min)
- **Net toil reduction: 73.8%** (535 min saved)
- **Total correction cycles: 25** (avg 0.93 per component)
- **Average toil-reduced score: 8.0/10**
- Components where AI genuinely reduced toil (No shift): **22/27**
- Components where AI partially shifted toil: **5/27** (EKS, Kyverno Install, Falco Install, ESO, OTel)
- Components where AI fully shifted toil: **0/27**
- Components where starting from scratch would have been faster: **0/27**
- Components with zero corrections: **13/27** (48%)
- Components deferred: **0/27**

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
