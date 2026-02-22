# Eight Guardrails Reconciliation

Last updated: 2026-02-22

## Purpose

This document reconciles the repo's actual state against the Three-Layer
Guardrail Architecture and Eight Guardrails Framework described in
`docs/WALKTHROUGH.md`. The goal: identify what's implemented, what's missing,
and what to do about it.

---

## The Three Layers — Status at a Glance

| Layer | Description | Status | Coverage |
|-------|-------------|--------|----------|
| **Layer 1: Git Hooks** | Deterministic, local, pre-cluster | **IMPLEMENTED** (2026-02-22) | 8/8 guardrails |
| **Layer 2: Claude Code Hooks** | Mix of deterministic + probabilistic | **IMPLEMENTED** (2026-02-22) | 7/8 guardrails |
| **Layer 3: Kubernetes Infrastructure** | Deterministic, cluster-enforced | **FULLY IMPLEMENTED** | 8/8 guardrails |

---

## Layer 3: Kubernetes Infrastructure (COMPLETE)

All eight guardrails are implemented at the cluster level. This is the
production-grade layer that the IDP delivers.

| # | Guardrail | Implementation | Files |
|---|-----------|---------------|-------|
| 1 | Propose-Approve-Execute | ArgoCD GitOps delivery, app-of-apps, sync waves | `gitops/bootstrap/`, `gitops/apps/` |
| 2 | Blast Radius Limits | Namespace RBAC, ResourceQuotas, NetworkPolicies | `security/rbac/`, `security/network-policies/`, `security/quotas-pdbs/` |
| 3 | Stop Hooks & Circuit Breakers | Kyverno admission webhooks (6 policies), Falco runtime | `policies/kyverno/`, `security/falco/` |
| 4 | Assume Misunderstanding | Schema validation at admission, Kyverno validate rules | `policies/kyverno/` |
| 5 | Immutable Audit Trail | Prometheus metrics, Grafana dashboards, OTel traces, K8s audit | `monitoring/`, `security/falco/` |
| 6 | Automated Rollback | ArgoCD self-heal + GitOps revert, PDBs | `gitops/apps/`, `security/quotas-pdbs/` |
| 7 | Secrets & Credential Isolation | ESO + AWS Secrets Manager, Pod Identity (no static creds) | `security/eso/`, `infrastructure/terraform/` |
| 8 | Supply Chain Validation | Kyverno restrict-image-registries (ECR + GHCR + registry.k8s.io) | `policies/kyverno/restrict-image-registries.yaml` |

**Verdict: Layer 3 exceeds minimum requirements.** 27 ArgoCD applications,
6 Kyverno policies, 5 Falco rules, RBAC, NetworkPolicies, ESO, PDBs, quotas,
cert-manager, OIDC — all working, all tested (59 tests passing).

---

## Layer 2: Claude Code Hooks (MINIMAL)

### What Exists

| File | Purpose | Status |
|------|---------|--------|
| `.claude/hooks/stop-hook.sh` | Ralph Wiggum pattern — blocks exit without phase promise | EXISTS, functional |
| `.claude/commands/build-phase.md` | Slash command for phase execution | EXISTS, no guardrail checklist |
| `.claude/commands/validate-phase.md` | Slash command for phase validation | EXISTS, no guardrail validation |
| `.claude/commands/score-component.md` | Slash command for scoring | EXISTS, no guardrail column |
| `.claude/skills/*.md` (6 files) | Component knowledge injection | EXISTS, no guardrail sections |

### What's Missing (per WALKTHROUGH.md)

| File | Purpose | Guardrails | Priority |
|------|---------|------------|----------|
| `.claude/settings.json` | Hook registration (PreToolUse, PostToolUse, Stop, SessionStart) | ALL | High |
| `.claude/hooks/cc-pretool-guard.sh` | Block kubectl apply after Phase 2, block terraform destroy, block secret dumps | #1, #2, #7 | High |
| `.claude/hooks/cc-posttool-audit.sh` | Scorecard reminders after deploys, verify-after-apply reminders, rollback suggestions | #4, #5, #6 | Medium |
| `.claude/hooks/cc-stop-deterministic.sh` | Enhanced stop hook with guardrail-aware messaging | #3 | Low (existing stop-hook.sh covers core behavior) |
| "Guardrail Integration" section in each skill file | Cross-reference which guardrails each component implements | Documentation | Low |

### What Actually Happened During the Build

The build used the global `llm_coding_workflow` hooks (lint, type-check,
secret scan, AI-reference blocking) instead of IDP-specific Claude Code hooks.
This worked — the build completed successfully — but it means:

- `kubectl apply` was used in some cases where ArgoCD-only was specified
- No automatic scorecard reminders after deployments
- No PreToolUse blocking of dangerous commands
- The build process didn't demonstrate defense-in-depth at Layer 2

---

## Layer 1: Git Hooks (NOT IMPLEMENTED)

### What Exists

| Component | Status |
|-----------|--------|
| `.git/hooks/` | Only stock `.sample` files — no active hooks |
| `.pre-commit-config.yaml` | **Does not exist** |
| `.yamllint.yml` | **Does not exist** |
| `policies/allowed-images.txt` | **Does not exist** (image restriction is via Kyverno policy, not file) |
| `.gitleaks.toml` | EXISTS — allowlist for known test secrets |
| `pre-commit` framework | NOT in pyproject.toml, not installed |

### What's Missing (per WALKTHROUGH.md)

| Hook | Guardrail | What It Does | Priority |
|------|-----------|-------------|----------|
| gitleaks | #7 | Scan commits for leaked secrets | High |
| yamllint | #4 | Validate YAML syntax | Medium |
| kubeconform | #4 | Kubernetes schema validation | Medium |
| kyverno CLI dry-run | #3 | Pre-commit policy validation | Medium |
| terraform validate | #4 | Terraform syntax + provider validation | Medium |
| helm lint | #4 | Helm chart validation | Low |
| trivy dockerfile | #8 | Image vulnerability scanning | Low |
| image-allowlist | #8 | Registry allowlist enforcement | Low |
| namespace-scope-check | #2 | Phase-scoped namespace enforcement | Low |
| commit-msg-validate | #5 | Conventional commit format enforcement | Low |
| pre-push-tests | #1, #3 | Block push if tests fail | Medium |
| GPG signing | #5 | Commit signing verification | Low |

### What Actually Happened During the Build

The `llm_coding_workflow` hooks provided:
- Pre-commit: ruff lint, ruff format check, type checking on staged files
- Pre-commit: debug artifact check (no pdb, breakpoint, console.log)
- Pre-push: gitleaks secret scanning on staged files

This covered basic code quality and secret scanning, but NOT:
- Kubernetes-specific validation (kubeconform, kyverno CLI)
- Helm/Terraform validation
- Image allowlist enforcement
- Phase-scoped namespace checking
- Conventional commit format

---

## Gap Analysis: What the Repo Needs

### Option A: "Document the Gap" (Minimal Effort)

Add the guardrail gap to the talk narrative: "We implemented all eight
guardrails at the Kubernetes layer. Layers 1 and 2 are where the rebuild
story gets interesting." This is honest and creates a clear call-to-action
for the audience.

**Work required:**
1. This document (already done)
2. Update `REMAINING-ITEMS.md` (already done)
3. Maybe add a slide about the three-layer gap

### Option B: "Implement Layers 1-2" (Full Reconciliation)

Add all missing hooks and configurations so the repo demonstrates
defense-in-depth at all three layers.

**Work required:**

#### Layer 1 (estimate: 30-45 min)
1. Create `.pre-commit-config.yaml` with all hooks from WALKTHROUGH.md
2. Create `.yamllint.yml` for YAML validation config
3. Create helper scripts: `check-image-allowlist.sh`, `check-namespace-scope.sh`
4. Create `commit-msg-validate.sh` and install as `.git/hooks/commit-msg`
5. Create `pre-push-tests.sh` and install as `.git/hooks/pre-push`
6. Create `.current-phase` file (set to "7" since all phases complete)
7. Add `pre-commit` to pyproject.toml dev dependencies
8. Run `pre-commit install` to activate

#### Layer 2 (estimate: 20-30 min)
1. Create `.claude/settings.json` with all hook registrations
2. Create `.claude/hooks/cc-pretool-guard.sh`
3. Create `.claude/hooks/cc-posttool-audit.sh`
4. Upgrade `.claude/hooks/stop-hook.sh` → `cc-stop-deterministic.sh`
5. Add "Guardrail Integration" section to each of the 6 skill files

#### Documentation (estimate: 15-20 min)
1. Create standalone `docs/EIGHT-GUARDRAILS.md` (extract from WALKTHROUGH.md)
2. Add guardrail cross-references to `docs/SECURITY.md`
3. Optionally add "Guardrails Implemented" column to `spec/SCORECARD.md`
4. Update `collateral/slide-outline.md` with guardrail layer slides

### Option C: "Hybrid — Document + Key Hooks Only" (Recommended)

Implement the high-value hooks that actually prevent mistakes, skip the
low-priority ceremony. Keep the gap documented for the talk narrative.

**Work required:**

#### Must-have hooks (estimate: 20-30 min)
1. `.claude/settings.json` — Register PreToolUse and Stop hooks
2. `.claude/hooks/cc-pretool-guard.sh` — Block dangerous commands
3. `.pre-commit-config.yaml` — gitleaks + yamllint + kubeconform (the ones
   that catch real problems)
4. `.current-phase` — Set to "7"

#### Documentation (estimate: 10-15 min)
1. Standalone `docs/EIGHT-GUARDRAILS.md`
2. This reconciliation document (already done)

#### Skip (document as future work)
- GPG signing, conventional commits, namespace-scope checks
- PostToolUse audit hook, SessionStart hook
- Guardrail column in scorecard
- Guardrail sections in skill files
- trivy, helm lint, terraform validate hooks (these tools aren't installed
  in the local environment anyway)

---

## Recommendation

**Option C (Hybrid)** gives the best talk-to-effort ratio:

- The `.claude/settings.json` + `cc-pretool-guard.sh` are genuinely useful
  safety nets for any future work on this repo
- The `.pre-commit-config.yaml` with gitleaks + yamllint is standard practice
  and costs nothing to add
- The `docs/EIGHT-GUARDRAILS.md` standalone doc makes the framework easily
  referenceable from the talk
- The gap between "what we built" and "what we'd add" is itself a talk point
  about iterative guardrail adoption

The talk narrative becomes: "Layer 3 is complete. Layers 1 and 2 are where
you start on Day 2. Here's the playbook."

---

## Cross-Reference

- Full Three-Layer architecture: `docs/WALKTHROUGH.md`
- Current scorecard: `spec/SCORECARD.md`
- Security posture: `docs/SECURITY.md`
- Remaining items: `REMAINING-ITEMS.md`
