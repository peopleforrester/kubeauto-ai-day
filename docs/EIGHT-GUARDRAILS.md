# Eight Guardrails Framework

## Overview

The Eight Guardrails Framework governs how the KubeAuto Day IDP was built and
how the platform itself enforces safety. Each guardrail is implemented across
three defensive layers, with problems caught at the cheapest possible point.

```
Cost to fix:  $        $$              $$$
              |         |                |
              v         v                v
         Git Hooks → Claude Code → Kubernetes
         (local)     (pre-exec)    (cluster)

Determinism:  100%      ~80%            100%
Latency:      <1s       1-30s           1-5s
Bypass risk:  None      Low*            None

* Prompt-based hooks are probabilistic. Bash-based hooks are deterministic.
```

---

## The Eight Guardrails

### 1. Propose-Approve-Execute

Every change follows a structured workflow: propose (Git commit), approve
(test gate), execute (ArgoCD sync).

| Layer | Implementation |
|-------|---------------|
| **Layer 1: Git** | Pre-push hook blocks push if phase tests fail |
| **Layer 2: Claude Code** | PreToolUse blocks `kubectl apply` in production namespaces after Phase 2 |
| **Layer 3: Kubernetes** | ArgoCD GitOps-only delivery. Backstage templates enforce structured service creation |

### 2. Blast Radius Limits

Contain the impact of any single change to the smallest possible scope.

| Layer | Implementation |
|-------|---------------|
| **Layer 1: Git** | Namespace scope check validates manifests target only phase-appropriate namespaces |
| **Layer 2: Claude Code** | PreToolUse blocks `kubectl delete namespace`, `terraform destroy`, operations on `kube-system` |
| **Layer 3: Kubernetes** | Namespace-scoped RBAC, ResourceQuotas (10 pods, 4 CPU, 8Gi in apps), NetworkPolicies (default-deny), VPC isolation |

### 3. Stop Hooks & Circuit Breakers

Automated mechanisms that halt progress when something is wrong.

| Layer | Implementation |
|-------|---------------|
| **Layer 1: Git** | Kubeconform schema validation, Kyverno CLI dry-run (pre-commit), full test suite (pre-push) |
| **Layer 2: Claude Code** | Ralph Wiggum Stop hook blocks exit without phase completion promise. Prompt-based evaluator verifies test criteria actually pass |
| **Layer 3: Kubernetes** | Kyverno admission webhooks reject non-compliant pods. Falco runtime rules detect anomalous behavior |

### 4. Assume Misunderstanding

Validate everything. Never trust that output is correct without verification.

| Layer | Implementation |
|-------|---------------|
| **Layer 1: Git** | yamllint, kubeconform, `terraform validate`, `helm lint` (pre-commit) |
| **Layer 2: Claude Code** | PostToolUse reminds to verify after `kubectl apply` and `terraform apply` |
| **Layer 3: Kubernetes** | Schema validation at admission. Kyverno validate rules enforce structural requirements |

### 5. Immutable Audit Trail

Every action is recorded. Nothing can be silently changed.

| Layer | Implementation |
|-------|---------------|
| **Layer 1: Git** | Conventional commit format with phase/component tags. Prompt logs in `prompts/`. Git history as timeline |
| **Layer 2: Claude Code** | PostToolUse reminders for scorecard updates after deployments. Session logging |
| **Layer 3: Kubernetes** | Prometheus metrics, Grafana dashboards, OTel distributed traces, Falco syscall logging, K8s audit logs |

### 6. Automated Rollback

When something fails, provide a fast path back to the last known-good state.

| Layer | Implementation |
|-------|---------------|
| **Layer 1: Git** | `git revert` is the cheapest rollback. Tagged commits at phase completion |
| **Layer 2: Claude Code** | PostToolUse suggests rollback options after failed terraform/helm/kubectl commands |
| **Layer 3: Kubernetes** | ArgoCD self-heal reverts drift. `argocd app rollback` for instant revision rollback. PDBs protect availability during changes |

### 7. Secrets & Credential Isolation

No secrets in code. No long-lived credentials. No accidental exposure.

| Layer | Implementation |
|-------|---------------|
| **Layer 1: Git** | gitleaks scans every commit. `.gitignore` excludes `*.pem`, `*.key`, `terraform.tfstate`. `.gitleaks.toml` allowlist for known test secrets |
| **Layer 2: Claude Code** | PreToolUse blocks `kubectl get secret -o yaml/json` and `cat` of secret files |
| **Layer 3: Kubernetes** | External Secrets Operator pulls from AWS Secrets Manager. Pod Identity (no static IAM keys). KMS encryption at rest |

### 8. Supply Chain Validation

Trust but verify. Only allow known-good artifacts.

| Layer | Implementation |
|-------|---------------|
| **Layer 1: Git** | Trivy Dockerfile scanning. Image registry allowlist check (pre-commit) |
| **Layer 2: Claude Code** | (Potential: block Helm installs from unapproved repos) |
| **Layer 3: Kubernetes** | Kyverno `restrict-image-registries` policy enforces ECR + GHCR + docker.io/library + registry.k8s.io |

---

## Coverage Summary

| Phase | Guardrails Active at Layer 3 |
|-------|------------------------------|
| After Phase 1 (Foundation) | #2 (VPC/SG), #7 (Pod Identity) |
| After Phase 2 (GitOps) | + #1 (ArgoCD), #6 (self-heal) |
| After Phase 3 (Security) | + #3 (Kyverno/Falco), #4 (admission), #7 (ESO), #8 (image policy) |
| After Phase 4 (Observability) | + #5 (Prometheus/OTel/Grafana) |
| After Phase 7 (Hardening) | All 8 guardrails at all 3 layers |

---

## Files

| Layer | Files |
|-------|-------|
| **Layer 1** | `.pre-commit-config.yaml`, `.yamllint.yml`, `.gitleaks.toml`, `.current-phase`, `.claude/hooks/check-image-allowlist.sh`, `.claude/hooks/check-namespace-scope.sh`, `.claude/hooks/commit-msg-validate.sh`, `.claude/hooks/pre-push-tests.sh` |
| **Layer 2** | `.claude/settings.json`, `.claude/hooks/cc-pretool-guard.sh`, `.claude/hooks/cc-posttool-audit.sh`, `.claude/hooks/cc-stop-deterministic.sh` |
| **Layer 3** | `policies/kyverno/`, `security/falco/`, `security/rbac/`, `security/network-policies/`, `security/eso/`, `security/quotas-pdbs/`, `gitops/`, `monitoring/`, `backstage/` |

---

## Cross-References

- Three-Layer architecture detail: `docs/WALKTHROUGH.md`
- Security posture: `docs/SECURITY.md`
- Reconciliation status: `docs/EIGHT-GUARDRAILS-RECONCILIATION.md`
- Scorecard: `spec/SCORECARD.md`
- Skill file guardrail mappings: `.claude/skills/*.md` (each has a "Guardrail Integration" section)
