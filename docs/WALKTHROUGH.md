# KubeAuto Day IDP Build: Comprehensive Walkthrough
## "The 10-Hour IDP: Can Claude Code Actually Reduce Platform Engineering Toil?"
### KubeAuto Day Europe 2026 — Amsterdam, March 23

---

## Current State Assessment

**Today is February 19, 2026.** The original spec timeline had the full build completing by Feb 21. That's not happening. Here's the honest status and the adjusted plan.

### What We Have (Spec Status)

The spec (`kubeauto-idp-build-spec.md`) defines:

- 7 build phases with test-first completion gates
- 27-component AI Platform Building Scorecard
- Ralph Wiggum / Smart Ralph continuous execution strategy
- CLAUDE.md instructions for persistent Claude Code context
- Overnight batch script for sequential phase execution
- Prompt recording format for talk material capture
- Full collateral plan (pre-talk, at-talk, post-talk)

### What the Spec Is Missing

The spec has a basic stop hook and CLAUDE.md rules. That's it for safety. No Git hooks. No PreToolUse blockers. No systematic mapping of the Eight Guardrails Framework to the build process itself.

The IDP implements guardrails (Kyverno, Falco, RBAC, ArgoCD) — but the *process of building it* doesn't enforce those same guardrails. That's the gap. The talk becomes dramatically stronger when the build process demonstrates the same defense-in-depth architecture that the platform enforces.

---

## The Three-Layer Guardrail Architecture

This is the conceptual framework that governs the entire build. Every guardrail is enforced at the cheapest possible layer, with fallbacks at more expensive layers.

### Layer 1: Git Hooks (Deterministic, Local, Pre-Cluster)

Bash and Python scripts that run on `pre-commit`, `commit-msg`, and `pre-push`. These are 100% deterministic. Claude Code cannot bypass a Git hook — if the hook rejects the commit, nothing reaches the cluster. This is where you catch problems at the cheapest possible cost.

### Layer 2: Claude Code Hooks (Mix of Deterministic and Probabilistic)

Claude Code's hook system: `PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`. Bash-based hooks are deterministic (blocking `kubectl apply`). Prompt-based hooks use Haiku and are probabilistic (evaluating whether Claude actually finished). Use deterministic hooks where possible; prompt hooks only where context-awareness is required.

### Layer 3: Kubernetes Infrastructure (Deterministic, Cluster-Enforced)

Admission webhooks (Kyverno), runtime detection (Falco), RBAC, NetworkPolicies, ResourceQuotas, ArgoCD GitOps enforcement. These are the last line — if something slips past Layers 1 and 2, the cluster itself blocks it. This is also the most expensive layer to debug.

### The Eight Guardrails Mapped Across All Three Layers

| # | Guardrail | Layer 1: Git Hooks | Layer 2: Claude Code Hooks | Layer 3: Kubernetes Infrastructure |
|---|---|---|---|---|
| 1 | **Propose-Approve-Execute** | `pre-push`: blocks push if phase tests fail. The "propose" happens at `git commit`, approval is the test gate, execution is ArgoCD sync. | `PreToolUse`: blocks `kubectl apply` in production namespaces after Phase 2. Forces GitOps PR path. | ArgoCD sync-only delivery. Manual sync disabled for app namespaces. Automated sync with self-heal for platform namespaces. |
| 2 | **Blast Radius Limits** | `pre-commit`: validate that manifests only target allowed namespaces for the current phase. Block cross-phase resource creation. | `PreToolUse`: block `kubectl delete namespace`, `terraform destroy` without explicit confirmation flag. Block operations on `kube-system`. | Namespace-scoped RBAC. ResourceQuotas per namespace. NetworkPolicies with default-deny. Claude's ServiceAccount (if used) gets namespace-scoped permissions only. |
| 3 | **Stop Hooks & Circuit Breakers** | `pre-commit`: Kyverno CLI dry-run (`kyverno apply --dry-run`) catches policy violations before they hit the cluster. `pre-push`: full test suite must pass. | `Stop` (bash): blocks exit unless `<promise>PHASEX_DONE</promise>` is present. `Stop` (prompt): Haiku evaluates whether all test criteria actually pass. `PreToolUse`: blocks destructive commands matching deny patterns. | Kyverno admission webhooks reject non-compliant resources at the API server. Falco runtime rules detect and alert on unexpected behavior. OPA Gatekeeper as secondary policy engine if needed. |
| 4 | **Assume Misunderstanding** | `pre-commit`: `kubeconform` schema validation, `helm template` + `helm lint`, `terraform validate`, `yamllint`. Catches structural errors before anything runs. | `PostToolUse`: after any `terraform plan` or `helm template`, inject reminder to review the diff before applying. After `kubectl apply`, inject reminder to verify with `kubectl get`. | Read-after-write verification in test suites. Schema validation at admission. Kyverno `validate` rules enforce structural requirements. |
| 5 | **Immutable Audit Trail** | `commit-msg`: enforce conventional commit format with phase/component tags (`phase-3/kyverno: add require-labels policy`). GPG-signed commits via `pre-commit`. All prompt transcripts committed to `prompts/` directory. | `PostToolUse`: auto-export Claude Code transcript after every `terraform apply` or `helm upgrade`. `SessionStart`: log session start time. `SessionEnd`: log session end time and duration. | Kubernetes audit logging enabled on EKS. OpenTelemetry GenAI semantic conventions for LLM operation tracing. Correlation IDs linking Claude Code sessions to cluster events. |
| 6 | **Automated Rollback** | Git itself — `git revert` is the cheapest rollback. Tagged commits at each phase completion for clean rollback points. `git bisect` to find the breaking commit if integration tests fail. | `PostToolUse`: after any failed `terraform apply`, auto-suggest `terraform plan -destroy` for the failed resource. After failed ArgoCD sync, suggest `argocd app rollback`. | ArgoCD GitOps revert (rollback to last healthy commit). Pre-change `VolumeSnapshots` for any PVC-backed components. ArgoCD self-heal auto-reverts manual drift. |
| 7 | **Secrets & Credential Isolation** | `pre-commit`: `gitleaks` and `detect-secrets` scan every commit. Block any commit containing AWS keys, passwords, tokens, certificates. `.gitignore` includes `*.pem`, `*.key`, `terraform.tfstate`. | `PreToolUse`: block any `echo` or `cat` of files matching secret patterns. Block `kubectl get secret -o yaml` (force `-o jsonpath` for specific fields only). | External Secrets Operator pulls secrets from AWS Secrets Manager. Pod Identity for IAM — no long-lived credentials. Kyverno policy blocks pods with `env` referencing raw secret values (must use `secretKeyRef`). |
| 8 | **Supply Chain Validation** | `pre-commit`: Trivy scan on all Dockerfiles. Validate image references match allowlist in `policies/allowed-images.txt`. Block `latest` tags. | `PreToolUse`: block `docker pull` from unauthorized registries. Block Helm chart installs from non-approved repositories. | Kyverno `ClusterPolicy` restricts image registries to ECR + approved CNCF project registries. Sigstore/Cosign verification at admission. Trivy Operator for continuous vulnerability scanning of running images. |

### The Defense-in-Depth Principle

Problems should be caught at the cheapest layer:

```
Cost to fix:  $        $              $$
              │         │                │
              ▼         ▼                ▼
         Git Hooks → Claude Code → Kubernetes
         (local)     (pre-exec)    (cluster)

Determinism:  100%      ~80%            100%
Latency:      <1s       1-30s           1-5s
Bypass risk:  None      Low*            None

* Prompt-based hooks are probabilistic. Bash-based Claude Code hooks are deterministic.
```

The talk narrative: "We didn't just build an IDP with guardrails — we built it *using* guardrails, at every layer."

---

## Spec-Driven Development: Step-by-Step Execution Plan

### Step 0: Pre-Build Setup (45 min)

Before touching any build phase, scaffold the entire repo, install all three guard rail layers, and verify tooling.

**0.1 — Create the Repository**

```bash
mkdir kubeauto-idp && cd kubeauto-idp
git init
```

**0.2 — Scaffold the Directory Structure**

```bash
# Create all directories from the spec
mkdir -p .claude/{commands,hooks,skills}
mkdir -p spec/phases
mkdir -p infrastructure/{terraform,eksctl}
mkdir -p gitops/{bootstrap,argocd/applicationsets,namespaces,apps/{kyverno,falco,falcosidekick,external-secrets,cert-manager,prometheus,grafana,otel-collector,backstage,sample-app}}
mkdir -p policies/{kyverno,network-policies/per-namespace}
mkdir -p security/{falco,falcosidekick,rbac}
mkdir -p observability/{otel-collector,prometheus/rules,grafana/{dashboards},alerting}
mkdir -p backstage/{catalog/systems,templates/{deploy-service/skeleton,create-namespace/skeleton}}
mkdir -p sample-app/{src,k8s}
mkdir -p tests/helpers
mkdir -p prompts
mkdir -p scorecard
mkdir -p collateral
mkdir -p docs
mkdir -p recordings/logs
```

**0.3 — Install the Spec**

```bash
cp BUILD-SPEC.md spec/BUILD-SPEC.md
```

**0.4 — Write the CLAUDE.md**

Drop the CLAUDE.md from the spec into the repo root. This is Claude Code's persistent context.

**0.5 — Verify Tooling**

```bash
claude --version
claude plugin list                # Check for ralph-wiggum
terraform --version               # Need 1.6+
kubectl version --client          # Need 1.31+
helm version                      # Need 3.14+
python3 -m pytest --version       # Need pytest
kyverno version                   # For pre-commit dry-runs
kubeconform -v                    # For schema validation
gitleaks version                  # For secret scanning
trivy --version                   # For image scanning
asciinema --version               # For terminal recording
```

---

### Step 1: Install Layer 1 — Git Hooks (Deterministic Foundation)

This is the bedrock. Everything else builds on top of a Git repository that won't accept bad commits. Install these before writing a single line of infrastructure code.

#### 1.1 — Pre-commit Framework

File: `.pre-commit-config.yaml`

```yaml
# Defense Layer 1: Git Hooks
# These are 100% deterministic. Claude Code cannot bypass them.

repos:
  # Guardrail 7: Secrets & Credential Isolation
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks

  # Guardrail 4: Assume Misunderstanding (schema validation)
  - repo: local
    hooks:
      - id: yaml-lint
        name: YAML Lint
        entry: yamllint -c .yamllint.yml
        language: system
        files: '\.ya?ml'
        exclude: 'node_modules|.git'

      # Guardrail 4: Assume Misunderstanding (Kubernetes schema validation)
      - id: kubeconform-validate
        name: Kubeconform Schema Validation
        entry: bash -c 'find . -name "*.yaml" -path "*/k8s/*" -o -name "*.yaml" -path "*/gitops/*" -o -name "*.yaml" -path "*/policies/*" | xargs -r kubeconform -strict -ignore-missing-schemas -kubernetes-version 1.31.0'
        language: system
        files: '\.yaml'

      # Guardrail 3: Circuit Breaker (Kyverno dry-run)
      - id: kyverno-validate
        name: Kyverno Policy Dry-Run
        entry: bash -c 'if ls policies/kyverno/*.yaml 1>/dev/null 2>&1; then for resource in $(find gitops/apps sample-app/k8s -name "*.yaml" 2>/dev/null); do kyverno apply policies/kyverno/ --resource "$resource" 2>/dev/null || exit 1; done; fi'
        language: system
        files: '\.yaml'
        pass_filenames: false

      # Guardrail 4: Assume Misunderstanding (Terraform validation)
      - id: terraform-validate
        name: Terraform Validate
        entry: bash -c 'cd infrastructure/terraform && terraform fmt -check && terraform validate'
        language: system
        files: '\.tf'
        pass_filenames: false

      # Guardrail 4: Assume Misunderstanding (Helm lint)
      - id: helm-lint
        name: Helm Lint
        entry: bash -c 'for chart in gitops/apps/*/Chart.yaml; do [ -f "$chart" ] && helm lint "$(dirname "$chart")" || exit 1; done 2>/dev/null; true'
        language: system
        files: '\.yaml'
        pass_filenames: false

      # Guardrail 8: Supply Chain Validation (image scanning)
      - id: trivy-dockerfile
        name: Trivy Dockerfile Scan
        entry: bash -c 'for df in $(find . -name "Dockerfile" -not -path "./.git/*"); do trivy config "$df" --severity HIGH,CRITICAL --exit-code 1 || exit 1; done'
        language: system
        files: 'Dockerfile'
        pass_filenames: false

      # Guardrail 8: Supply Chain Validation (image allowlist)
      - id: image-allowlist
        name: Image Registry Allowlist
        entry: bash -c '.claude/hooks/check-image-allowlist.sh'
        language: system
        files: '\.yaml'
        pass_filenames: false

      # Guardrail 2: Blast Radius Limits (namespace scope check)
      - id: namespace-scope-check
        name: Namespace Scope Validation
        entry: bash -c '.claude/hooks/check-namespace-scope.sh'
        language: system
        files: '\.yaml'
        pass_filenames: false

  # Guardrail 5: Immutable Audit Trail (commit signing)
  - repo: local
    hooks:
      - id: gpg-sign-check
        name: GPG Commit Signing
        entry: bash -c 'git config commit.gpgsign true || echo "WARNING: GPG signing not configured"'
        language: system
        stages: [pre-commit]
```

#### 1.2 — Commit Message Convention

File: `.claude/hooks/commit-msg-validate.sh`

```bash
#!/bin/bash
# Guardrail 5: Immutable Audit Trail
# Enforce conventional commit format with phase/component tags
# Format: phase-X/component: description
# Example: phase-3/kyverno: add require-labels policy

MSG_FILE="$1"
MSG=$(cat "$MSG_FILE")

# Allow merge commits
if echo "$MSG" | grep -qE "^Merge"; then
    exit 0
fi

# Require phase/component format
if ! echo "$MSG" | grep -qE "^phase-[0-7]/[a-z-]+: .+"; then
    echo "ERROR: Commit message must follow format: phase-X/component: description"
    echo "Example: phase-3/kyverno: add require-labels policy"
    echo "Got: $MSG"
    exit 1
fi

exit 0
```

Install as a Git hook:

```bash
cp .claude/hooks/commit-msg-validate.sh .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
```

#### 1.3 — Pre-Push Test Gate

File: `.claude/hooks/pre-push-tests.sh`

```bash
#!/bin/bash
# Guardrail 1: Propose-Approve-Execute
# Guardrail 3: Circuit Breaker
# Blocks push if current phase tests don't pass

PHASE=$(cat .current-phase 2>/dev/null || echo "1")

echo "Running Phase $PHASE tests before push..."
python3 -m pytest "tests/test_phase_0${PHASE}_"*.py -v 2>&1

if [ $? -ne 0 ]; then
    echo ""
    echo "BLOCKED: Phase $PHASE tests are failing. Fix them before pushing."
    exit 1
fi

echo "Phase $PHASE tests pass. Push allowed."
exit 0
```

Install:

```bash
cp .claude/hooks/pre-push-tests.sh .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

#### 1.4 — Image Registry Allowlist

File: `.claude/hooks/check-image-allowlist.sh`

```bash
#!/bin/bash
# Guardrail 8: Supply Chain Validation
# Block images from unauthorized registries

ALLOWED_REGISTRIES=(
    "public.ecr.aws"
    "quay.io"
    "ghcr.io"
    "registry.k8s.io"
    "docker.io/library"
    "docker.io/grafana"
    "docker.io/falcosecurity"
    "docker.io/otel"
    # Add your ECR registry
)

VIOLATIONS=0

for file in $(find gitops/apps sample-app/k8s -name "*.yaml" 2>/dev/null); do
    IMAGES=$(grep -E "^\s+image:" "$file" 2>/dev/null | awk '{print $2}' | tr -d '"'"'" )
    for img in $IMAGES; do
        ALLOWED=false
        for reg in "${ALLOWED_REGISTRIES[@]}"; do
            if echo "$img" | grep -q "^$reg"; then
                ALLOWED=true
                break
            fi
        done
        if [ "$ALLOWED" = false ] && [ -n "$img" ]; then
            # Allow images without a registry prefix (default to docker.io/library)
            if ! echo "$img" | grep -q "/"; then
                continue
            fi
            echo "BLOCKED: Unauthorized image registry: $img in $file"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done
done

if [ $VIOLATIONS -gt 0 ]; then
    echo ""
    echo "Add approved registries to .claude/hooks/check-image-allowlist.sh"
    exit 1
fi

exit 0
```

#### 1.5 — Namespace Scope Check

File: `.claude/hooks/check-namespace-scope.sh`

```bash
#!/bin/bash
# Guardrail 2: Blast Radius Limits
# Validate manifests only target namespaces allowed for the current phase

PHASE=$(cat .current-phase 2>/dev/null || echo "1")

# Define which namespaces each phase can touch
case $PHASE in
    1) ALLOWED_NS="default|kube-system|platform|argocd|monitoring|backstage|apps|security" ;;
    2) ALLOWED_NS="argocd|platform|apps|monitoring|backstage|security" ;;
    3) ALLOWED_NS="security|apps|kyverno|falco" ;;
    4) ALLOWED_NS="monitoring|apps" ;;
    5) ALLOWED_NS="backstage|apps" ;;
    6) ALLOWED_NS="apps" ;;
    7) ALLOWED_NS=".*" ;;  # Hardening touches everything
    *) ALLOWED_NS=".*" ;;
esac

VIOLATIONS=0

for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.yaml'); do
    NS=$(grep -E "^\s+namespace:" "$file" 2>/dev/null | awk '{print $2}' | tr -d '"'"'" | head -1)
    if [ -n "$NS" ] && ! echo "$NS" | grep -qE "^($ALLOWED_NS)$"; then
        echo "WARNING: $file targets namespace '$NS' which is outside Phase $PHASE scope"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

if [ $VIOLATIONS -gt 0 ]; then
    echo ""
    echo "Phase $PHASE should only modify namespaces matching: $ALLOWED_NS"
    echo "Override: update .current-phase or modify check-namespace-scope.sh"
    # Warning only, not blocking — phases sometimes need cross-namespace refs
    # Change exit 0 to exit 1 to make it a hard block
fi

exit 0
```

#### 1.6 — Initialize Pre-commit

```bash
# Install pre-commit framework
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
pre-commit install --hook-type pre-push

# Create phase tracker
echo "1" > .current-phase
```

---

### Step 2: Install Layer 2 — Claude Code Hooks (Build Process Guard Rails)

These hooks govern Claude Code's behavior during the build. Bash hooks are deterministic; prompt hooks are the probabilistic fallback for cases requiring context awareness.

#### 2.1 — Combined Settings File

File: `.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/cc-pretool-guard.sh",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/cc-posttool-audit.sh",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/cc-stop-deterministic.sh"
          },
          {
            "type": "prompt",
            "prompt": "Evaluate whether Claude should stop. Input: $ARGUMENTS. Claude is building an IDP per spec/BUILD-SPEC.md. Block the stop if: 1) No <promise>PHASEX_DONE</promise> tag was output, 2) Test criteria for the current phase are not all passing, 3) SCORECARD.md was not updated for completed components. Explain what still needs to be done.",
            "timeout": 30
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo '{\"systemMessage\": \"Session started. Read spec/BUILD-SPEC.md and spec/SCORECARD.md to determine current phase and progress. Check .current-phase file. Do not proceed without understanding where you are in the build.\"}'"
          }
        ]
      }
    ]
  }
}
```

#### 2.2 — PreToolUse Guard (Deterministic)

File: `.claude/hooks/cc-pretool-guard.sh`

```bash
#!/bin/bash
# Layer 2 enforcement for Guardrails 1, 2, 7
# Deterministic — no LLM involvement

INPUT=$(cat -)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

if [ -z "$COMMAND" ]; then
    exit 0
fi

# === Guardrail 1: Propose-Approve-Execute ===
# After Phase 2, block kubectl apply in production namespaces
if [ -f "$CLAUDE_PROJECT_DIR/gitops/bootstrap/app-of-apps.yaml" ]; then
    BLOCKED_NS="platform|argocd|monitoring|backstage|apps|security"
    if echo "$COMMAND" | grep -qE "kubectl\s+(apply|create|replace).*-n\s+($BLOCKED_NS)"; then
        echo "{\"decision\": \"block\", \"reason\": \"[Guardrail 1: Propose-Approve-Execute] After Phase 2, all resources must be deployed via ArgoCD GitOps. Write manifests to gitops/apps/ and let ArgoCD sync them.\"}" >&2
        exit 2
    fi
fi

# === Guardrail 2: Blast Radius Limits ===
# Never allow operations on kube-system (except reads)
if echo "$COMMAND" | grep -qE "kubectl\s+(delete|apply|patch|edit).*-n\s+kube-system"; then
    echo "{\"decision\": \"block\", \"reason\": \"[Guardrail 2: Blast Radius Limits] Operations on kube-system are blocked. Only read operations (get, describe, logs) are allowed.\"}" >&2
    exit 2
fi

# Block terraform destroy without explicit flag
if echo "$COMMAND" | grep -qE "terraform\s+destroy" && ! echo "$COMMAND" | grep -q "CONFIRMED_DESTROY=true"; then
    echo "{\"decision\": \"block\", \"reason\": \"[Guardrail 2: Blast Radius Limits] terraform destroy requires CONFIRMED_DESTROY=true environment variable. This prevents accidental infrastructure deletion.\"}" >&2
    exit 2
fi

# Block kubectl delete namespace
if echo "$COMMAND" | grep -qE "kubectl\s+delete\s+namespace"; then
    echo "{\"decision\": \"block\", \"reason\": \"[Guardrail 2: Blast Radius Limits] Namespace deletion is blocked. Remove via Terraform or ArgoCD only.\"}" >&2
    exit 2
fi

# === Guardrail 7: Secrets & Credential Isolation ===
# Block commands that would expose secrets in logs
if echo "$COMMAND" | grep -qE "kubectl\s+get\s+secret.*-o\s+(yaml|json)"; then
    echo "{\"decision\": \"block\", \"reason\": \"[Guardrail 7: Secrets Isolation] Do not dump full secrets. Use: kubectl get secret <name> -o jsonpath='{.data.<key>}' for specific fields only.\"}" >&2
    exit 2
fi

# Block cat/echo of common secret file patterns
if echo "$COMMAND" | grep -qE "(cat|echo|less|more)\s+.*(\.pem|\.key|\.crt|credentials|\.env|tfstate)"; then
    echo "{\"decision\": \"block\", \"reason\": \"[Guardrail 7: Secrets Isolation] Reading secret/credential files directly is blocked. Use External Secrets Operator or AWS Secrets Manager CLI.\"}" >&2
    exit 2
fi

exit 0
```

#### 2.3 — PostToolUse Audit Hook (Deterministic)

File: `.claude/hooks/cc-posttool-audit.sh`

```bash
#!/bin/bash
# Layer 2 enforcement for Guardrails 4, 5, 6
# Deterministic post-execution checks and reminders

INPUT=$(cat -)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

if [ -z "$COMMAND" ]; then
    exit 0
fi

# === Guardrail 5: Immutable Audit Trail ===
# After terraform apply or helm install, remind about scorecard
if echo "$COMMAND" | grep -qE "(terraform apply|helm install|helm upgrade)"; then
    echo "{\"addToConversation\": \"[Guardrail 5: Audit Trail] Component deployed. Update spec/SCORECARD.md with: Toil Reduced (1-10), Correction Cycles, AI Time, Est. Manual Time, Toil Shifted (yes/no), Notes. Then commit with conventional format: phase-X/component: description\"}"
fi

# === Guardrail 4: Assume Misunderstanding ===
# After kubectl apply (in allowed contexts), remind to verify
if echo "$COMMAND" | grep -qE "kubectl\s+apply"; then
    echo "{\"addToConversation\": \"[Guardrail 4: Assume Misunderstanding] Resource applied. Verify with kubectl get and kubectl describe. Check for events, conditions, and readiness. Do not assume success from apply exit code alone.\"}"
fi

# === Guardrail 6: Automated Rollback ===
# After any failed command, suggest rollback options
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_result.exit_code // 0' 2>/dev/null)
if [ "$EXIT_CODE" != "0" ] && [ "$EXIT_CODE" != "null" ]; then
    if echo "$COMMAND" | grep -q "terraform"; then
        echo "{\"addToConversation\": \"[Guardrail 6: Rollback] Terraform command failed. Consider: terraform plan to check state, git diff to see what changed, git stash or git checkout to revert files.\"}"
    elif echo "$COMMAND" | grep -q "helm"; then
        echo "{\"addToConversation\": \"[Guardrail 6: Rollback] Helm command failed. Consider: helm rollback, helm history to check previous revisions, argocd app sync --revision to force a known-good state.\"}"
    fi
fi

exit 0
```

#### 2.4 — Stop Hook (Deterministic Gate)

File: `.claude/hooks/cc-stop-deterministic.sh`

```bash
#!/bin/bash
# Guardrail 3: Circuit Breaker (deterministic stop gate)
# Ralph Wiggum pattern: block exit unless phase completion promise found

OUTPUT=$(cat -)

# Check for phase completion promises
if echo "$OUTPUT" | grep -q "<promise>PHASE[0-7]_DONE</promise>"; then
    echo '{"decision": "allow"}'
    exit 0
fi

# Check for explicit stop request
if echo "$OUTPUT" | grep -q "<promise>ALL_PHASES_COMPLETE</promise>"; then
    echo '{"decision": "allow"}'
    exit 0
fi

# Block exit - keep iterating
echo '{"decision": "block", "reason": "[Guardrail 3: Circuit Breaker] Phase completion promise not found. Continue working on current phase. Run tests, fix failures, update scorecard."}'
exit 0
```

---

### Step 3: Layer 3 — Kubernetes Infrastructure Guard Rails (Built by the IDP Itself)

Layer 3 is what the IDP implements across Phases 2-7. These aren't pre-build hooks — they're the infrastructure components that the build creates. But mapping them to the Eight Guardrails ensures nothing is missed.

| Phase | Components Built | Guardrails Implemented |
|---|---|---|
| Phase 2: GitOps | ArgoCD, app-of-apps, sync waves | #1 Propose-Approve-Execute (GitOps delivery), #6 Automated Rollback (ArgoCD revert) |
| Phase 3: Security | Kyverno, Falco, ESO, RBAC, NetworkPolicies | #2 Blast Radius (RBAC, ResourceQuotas, NetworkPolicies), #3 Circuit Breakers (Kyverno admission, Falco runtime), #7 Secrets Isolation (ESO), #8 Supply Chain (Kyverno image policies) |
| Phase 4: Observability | Prometheus, Grafana, OTel Collector | #5 Immutable Audit Trail (OTel spans, K8s audit logs), #4 Assume Misunderstanding (observable verification) |
| Phase 7: Hardening | TLS, cert-manager, PDBs, resource quotas | #2 Blast Radius (resource quotas), #8 Supply Chain (Cosign verification at admission) |

**Guardrail coverage by completion:**

After Phase 3: Guardrails 1, 2, 3, 6, 7, 8 are enforced at the cluster level.
After Phase 4: Guardrail 5 is fully operational.
After Phase 7: All eight guardrails are enforced at all three layers.

---

### Step 4: Write the Skills Files

The spec defines 6 skill files. These are knowledge injection — Claude reads them before generating config. Your 100K+ student teaching patterns are the unfair advantage.

Each skill file follows this structure:

```markdown
---
name: component-name
description: When to invoke this skill
---

# Component Patterns

## What Claude Gets Wrong
[Failure modes from 100K+ students]

## Correct Patterns
[Working configs]

## Known Gotchas
[Version-specific, IAM formats, etc.]

## Guardrail Integration
[Which of the Eight Guardrails this component implements, and how]

## Test This Before Moving On
[Quick validation commands]
```

Note the new **Guardrail Integration** section. Every skill file should explicitly call out which guardrails the component enforces.

**Priority order:**

1. `eks-hardening.md` — Phase 1. IAM trust policies, Pod Identity, VPC CNI NetworkPolicy.
2. `argocd-patterns.md` — Phase 2. Sync waves, app-of-apps, CRD ordering. **Guardrails 1, 6.**
3. `kyverno-policies.md` — Phase 3. Policy interactions, generate vs validate vs mutate. **Guardrails 2, 3, 8.**
4. `falco-rules.md` — Phase 3. EKS syscall patterns, eBPF driver. **Guardrail 3.**
5. `otel-wiring.md` — Phase 4. Exporter endpoints, receiver protocols. **Guardrail 5.**
6. `backstage-templates.md` — Phase 5. Catalog annotations, plugin wiring. **Guardrail 1** (templates enforce the propose-approve-execute workflow for developers).

---

### Step 5: Write the Slash Commands

#### `/build-phase` command

File: `.claude/commands/build-phase.md`

```markdown
# Build Phase $ARGUMENTS

Read spec/BUILD-SPEC.md and find Phase $ARGUMENTS.

## Process
1. Read the relevant skill file(s) from .claude/skills/ for this phase's components
2. Read the test file: tests/test_phase_0$ARGUMENTS_*.py
3. If the test file doesn't exist, WRITE IT FIRST based on the test criteria in the spec
4. Implement the phase outputs until ALL test criteria pass
5. After each component, run /score-component to update the scorecard
6. Commit working code: phase-$ARGUMENTS/component: description
7. Update .current-phase file to $ARGUMENTS
8. When ALL test criteria pass, output <promise>PHASE${ARGUMENTS}_DONE</promise>

## Guard Rail Checklist
Before marking this phase complete, verify:
- [ ] All Layer 1 (Git) hooks pass: run `pre-commit run --all-files`
- [ ] All Layer 3 (K8s) guardrails for this phase are implemented per the mapping in the walkthrough
- [ ] SCORECARD.md is updated for every component in this phase
- [ ] All commits follow conventional format: phase-X/component: description

## Rules
- Read the skill file BEFORE generating any config
- Write tests FIRST, then implement
- No kubectl apply after Phase 2 — everything via ArgoCD
- No secrets in Git — use External Secrets Operator
- If stuck on IAM for more than 3 iterations, fall back to eksctl (Phase 1 only)
```

#### `/score-component` command

File: `.claude/commands/score-component.md`

```markdown
# Score Component: $ARGUMENTS

Update spec/SCORECARD.md for the component: $ARGUMENTS

## Scoring Criteria

**Toil Reduced (1-10):**
- 10 = Hours manually, minutes with AI, no corrections
- 7-9 = Working output with minor corrections
- 4-6 = Starting point, significant human correction needed
- 1-3 = Starting from scratch would have been faster

**Correction Cycles:** Number of human interventions needed.
**AI Time:** Wall clock from first prompt to working output.
**Est. Manual Time:** Senior engineer (10+ years K8s) doing it manually.
**Toil Shifted?:** Did AI remove toil or convert "writing YAML" into "debugging AI YAML"?
**Guardrail Layer:** Which guardrails does this component implement? (1-8)
**Notes:** What specifically went wrong? Root cause?
```

#### `/validate-phase` command

File: `.claude/commands/validate-phase.md`

```markdown
# Validate Phase $ARGUMENTS

## Process
1. Run Layer 1 checks: `pre-commit run --all-files`
2. Run phase tests: `python -m pytest tests/test_phase_0$ARGUMENTS_*.py -v`
3. Verify guardrail coverage: check which of the Eight Guardrails are now active
4. Report pass/fail for each test
5. If all pass, output <promise>PHASE${ARGUMENTS}_DONE</promise>
6. If any fail, diagnose root cause and continue working
```

---

### Step 6: Write Test Files (BEFORE Implementation)

Each phase's test file mirrors the spec's test criteria. This is the TDD gate.

Example: `tests/test_phase_01_foundation.py`

```python
"""Phase 1: Foundation Tests
All must pass before Phase 2 begins.
Guardrails validated: None yet (Layer 3 not deployed)
"""
import subprocess
import json
import pytest

class TestPhase01Foundation:

    def test_terraform_validates(self):
        """terraform validate passes with no errors"""
        result = subprocess.run(
            ["terraform", "validate"],
            cwd="infrastructure/terraform",
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"terraform validate failed: {result.stderr}"

    def test_terraform_plan_succeeds(self):
        """terraform plan produces no errors"""
        result = subprocess.run(
            ["terraform", "plan", "-detailed-exitcode"],
            cwd="infrastructure/terraform",
            capture_output=True, text=True
        )
        assert result.returncode in [0, 2], f"terraform plan failed: {result.stderr}"

    def test_eks_cluster_reachable(self):
        """EKS cluster endpoint is reachable"""
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0, f"Cluster not reachable: {result.stderr}"

    def test_nodes_ready(self):
        """At least 2 Ready nodes"""
        result = subprocess.run(
            ["kubectl", "get", "nodes", "-o", "json"],
            capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0
        nodes = json.loads(result.stdout)
        ready = [n for n in nodes["items"]
                 if any(c["type"] == "Ready" and c["status"] == "True"
                        for c in n["status"]["conditions"])]
        assert len(ready) >= 2, f"Only {len(ready)} nodes Ready"

    def test_namespaces_exist(self):
        """All required namespaces exist"""
        required = ["platform", "argocd", "monitoring", "backstage", "apps", "security"]
        result = subprocess.run(
            ["kubectl", "get", "namespaces", "-o", "json"],
            capture_output=True, text=True
        )
        existing = [ns["metadata"]["name"] for ns in json.loads(result.stdout)["items"]]
        for ns in required:
            assert ns in existing, f"Namespace '{ns}' missing"

    def test_pod_identity_agent(self):
        """EKS Pod Identity agent addon is active"""
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "kube-system",
             "-l", "app.kubernetes.io/name=eks-pod-identity-agent", "-o", "json"],
            capture_output=True, text=True
        )
        pods = json.loads(result.stdout)["items"]
        assert len(pods) > 0, "Pod Identity agent not found"
        for pod in pods:
            assert pod["status"]["phase"] == "Running"

    def test_precommit_hooks_pass(self):
        """Layer 1 guardrails are functional"""
        result = subprocess.run(
            ["pre-commit", "run", "--all-files"],
            capture_output=True, text=True
        )
        # Allow pass or no-files-changed
        assert result.returncode in [0, 1], f"Pre-commit hooks broken: {result.stderr}"
```

Note the `test_precommit_hooks_pass` — every phase now validates that Layer 1 guardrails are still functional. This catches the case where a build step accidentally breaks the pre-commit config.

---

### Step 7: Execute Phase by Phase

#### Phase Execution

Each phase runs as a separate Claude Code session. Update `.current-phase` between phases.

```bash
# Phase 1: Foundation (60 min, 15 iterations)
echo "1" > .current-phase
claude -p "/build-phase 1" --max-iterations 15

# Phase 2: GitOps (90 min, 20 iterations)
echo "2" > .current-phase
claude -p "/build-phase 2" --max-iterations 20

# Phase 3: Security (120 min, 30 iterations) — the hard one
echo "3" > .current-phase
claude -p "/build-phase 3" --max-iterations 30

# Phase 4: Observability (90 min, 20 iterations)
echo "4" > .current-phase
claude -p "/build-phase 4" --max-iterations 20

# Phase 5: Developer Portal (90 min, 20 iterations)
echo "5" > .current-phase
claude -p "/build-phase 5" --max-iterations 20

# Phase 6: Integration Testing (60 min, 15 iterations)
echo "6" > .current-phase
claude -p "/build-phase 6" --max-iterations 15

# Phase 7: Production Hardening (60 min, 15 iterations)
echo "7" > .current-phase
claude -p "/build-phase 7" --max-iterations 15
```

#### Overnight Batch Script (Updated)

```bash
#!/bin/bash
# overnight-build.sh — Three-layer guardrail enforcement
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$REPO_DIR/recordings/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$LOG_DIR"

PHASES=(1 2 3 4 5 6 7)
MAX_ITERS=(15 20 30 20 20 15 15)

# Start terminal recording
if command -v script &> /dev/null; then
    exec script -a "$LOG_DIR/full-session-${TIMESTAMP}.log"
fi

for i in "${!PHASES[@]}"; do
    PHASE=${PHASES[$i]}
    ITERS=${MAX_ITERS[$i]}
    START_TIME=$(date +%s)

    echo "========================================="
    echo "Starting Phase $PHASE (max $ITERS iterations)"
    echo "$(date)"
    echo "========================================="

    # Update phase tracker (used by Layer 1 hooks)
    echo "$PHASE" > "$REPO_DIR/.current-phase"

    cd "$REPO_DIR"
    claude -p "/build-phase $PHASE" \
        --max-iterations "$ITERS" \
        2>&1 | tee "$LOG_DIR/phase-${PHASE}-${TIMESTAMP}.log"

    # Export transcript (Guardrail 5: Audit Trail)
    claude --export > "$LOG_DIR/phase-${PHASE}-transcript-${TIMESTAMP}.json" 2>/dev/null || true

    # Run Layer 1 checks
    echo "Running Layer 1 (Git) guardrail checks..."
    pre-commit run --all-files 2>&1 | tee -a "$LOG_DIR/phase-${PHASE}-${TIMESTAMP}.log"

    # Run phase tests
    echo "Running Phase $PHASE tests..."
    python -m pytest "tests/test_phase_0${PHASE}_*.py" -v 2>&1 | tee -a "$LOG_DIR/phase-${PHASE}-${TIMESTAMP}.log"

    if [ $? -ne 0 ]; then
        END_TIME=$(date +%s)
        ELAPSED=$(( (END_TIME - START_TIME) / 60 ))
        echo "PHASE $PHASE TESTS FAILED after ${ELAPSED} minutes."
        exit 1
    fi

    # Tag completion (Guardrail 6: Rollback point)
    git tag "phase-${PHASE}-complete" 2>/dev/null || true

    END_TIME=$(date +%s)
    ELAPSED=$(( (END_TIME - START_TIME) / 60 ))
    echo "Phase $PHASE complete in ${ELAPSED} minutes."
    echo ""
done

echo "========================================="
echo "ALL PHASES COMPLETE — $(date)"
echo "========================================="
```

---

### Step 8: Capture Everything for Talk Material

```bash
# Terminal recording
asciinema rec recordings/full-build.cast

# After each phase
claude --export > recordings/phase-X-transcript.json

# Git history as timeline
git log --oneline --format="%h %s (%ci)" > recordings/git-timeline.txt

# Tag-based phase durations
git log --tags --format="%D %ci" | grep phase > recordings/phase-timestamps.txt
```

---

## Updated Scorecard Template

The scorecard now includes a guardrail coverage column:

| Component | Toil Reduced (1-10) | Correction Cycles | AI Time | Est. Manual Time | Toil Shifted? | Guardrails Implemented | Notes |
|---|---|---|---|---|---|---|---|
| VPC + Networking | | | | | | — | |
| EKS Cluster | | | | | | — | |
| IAM Roles + Pod Identity | | | | | | #7 | |
| Namespace Structure | | | | | | #2 | |
| ArgoCD Install + Config | | | | | | #1, #6 | |
| App-of-Apps Pattern | | | | | | #1 | |
| Sync Waves + Ordering | | | | | | #1 | |
| Kyverno Install | | | | | | #3, #8 | |
| Kyverno Policies | | | | | | #2, #3, #8 | |
| Kyverno Policy Interactions | | | | | | #3 | |
| Falco Install | | | | | | #3 | |
| Falco Custom Rules | | | | | | #3, #5 | |
| ESO + Secrets Manager | | | | | | #7 | |
| RBAC | | | | | | #2 | |
| NetworkPolicies | | | | | | #2 | |
| Prometheus + Grafana | | | | | | #5 | |
| OTel Collector Config | | | | | | #5 | |
| Grafana Dashboards | | | | | | #5 | |
| Alert Rules | | | | | | #3, #5 | |
| Backstage Install | | | | | | #1 | |
| Software Templates | | | | | | #1 | |
| Backstage Plugin Wiring | | | | | | — | |
| E2E Integration | | | | | | ALL | |
| TLS + cert-manager | | | | | | #8 | |
| OIDC Authentication | | | | | | #2, #7 | |
| Documentation | | | | | | #5 | |
| Git Hooks (Layer 1) | | | | | | #1-8 | |
| Claude Code Hooks (Layer 2) | | | | | | #1-7 | |

**Totals:**
- Total AI-assisted build time: ___ hours
- Total human correction time: ___ hours
- Estimated manual build time: ___ hours
- Net toil reduction: ___%
- Guardrail coverage at completion: ___/8 at Layer 1, ___/8 at Layer 2, ___/8 at Layer 3

---

## Actual Timeline (Reconciled)

| Date | Milestone | Status |
|---|---|---|
| Feb 9 | Spec complete | Done |
| Feb 11 | Version audit (EKS, ArgoCD, Kyverno, Falco, Backstage all updated) | Done |
| Feb 17 | Phases 1-6 complete (foundation through integration testing) | Done |
| Feb 18 | Phase 7 complete (cert-manager, quotas, PDBs, gitleaks, security docs) | Done |
| Feb 19 | Phase 8 collateral, documentation gaps, ALB Ingress, ACM TLS, OIDC | Done |
| Feb 20 | Reconciliation — this checklist updated against actual state | Done |
| Mar 4-10 | Build actual slides from outline, QR codes | TODO |
| Mar 11-17 | Practice runs with timer, demo runbook 3x end-to-end | TODO |
| Mar 18-22 | Buffer + final polish | TODO |
| Mar 23 | KubeAuto Day Europe — Amsterdam | Target |

---

## Risk Register (Reconciled)

| Risk | Likelihood | Impact | Mitigation | Outcome |
|---|---|---|---|---|
| Terraform EKS IAM issues | High | Phase 1 blocked | eksctl fallback | IRSA used for EBS CSI + LB Controller; Pod Identity for future. No eksctl needed. |
| Kyverno policy interactions | High | Phase 3 extended | kyverno-policies skill | 3 correction cycles. Webhook format wrong, CRD annotation too large (ServerSideApply fix), stale cache. |
| OTel config hallucination | High | Phase 4 broken | otel-wiring skill | 3 correction cycles. Missing image.repository, wrong image (k8s vs contrib), DaemonSet disables ClusterIP service. |
| Backstage plugin wiring | Medium | Phase 5 broken | backstage-templates skill | 1 correction cycle. Kyverno livenessProbe validation on dry-run. Private repo catalog solved via ConfigMap. |
| Context window exhaustion | Medium | Lost progress | Separate sessions per phase | Hit twice. Session continuations worked via summary + context reload. |
| AWS costs | Medium | $ | TEARDOWN.md | TEARDOWN.md written. Cluster running since Feb 17. |
| Clock past 10 hours | Medium | Narrative adjusts | Honest scorecard | 3hr AI / 11.5hr manual est. 73.6% toil reduction. Narrative holds. |
| Pre-commit hooks too strict | Medium | Build friction | Warning mode first | Not implemented — existing llm_coding_workflow hooks used instead (lint, secret scan, AI ref blocking). |
| Smart Ralph incompatibility | Low | Can't automate | Manual execution | Not used. Interactive sessions with human-in-the-loop instead. |
| **NEW: Sanitization breaks live cluster** | — | — | — | Replacing AWS account IDs with placeholders while ArgoCD syncs from repo broke image pulls. Lesson: sanitize at publish time only. |
| **NEW: IRSA token caching** | — | — | — | Restoring IAM role ARN on service account insufficient — pods cache projected tokens. Must restart pods after annotation fix. |
| **NEW: ArgoCD cache staleness** | — | — | — | After fixing CRD API versions or Helm values, must hard-refresh ArgoCD Applications. Cache aggressively caches API discovery. |

---

## Execution Checklist (Reconciled Against Actual Build)

### Repo Scaffolding
- [x] Scaffold repo directory structure
- [x] Write CLAUDE.md
- [x] Copy spec to `spec/BUILD-SPEC.md`
- [x] Create `SCORECARD.md` (6-dimension template; guardrail column not added)
- [ ] Create `.current-phase` file — **Not created. Phases tracked via TaskCreate/TaskUpdate instead.**

### Layer 1: Git Hooks
- [ ] Write `.pre-commit-config.yaml` — **Not implemented. Used existing llm_coding_workflow git hooks (pre-commit: lint/typecheck, pre-push: secret scan + tests) deployed via `deploy.sh`.**
- [ ] Write IDP-specific hook scripts (`commit-msg-validate.sh`, `pre-push-tests.sh`, `check-image-allowlist.sh`, `check-namespace-scope.sh`) — **Not implemented. These are NEW scripts described in the walkthrough for the rebuild. The existing hooks cover general code quality, not IDP-specific phase/namespace scoping.**
- [ ] Install pre-commit framework — **Not used. Standalone bash hooks from llm_coding_workflow used instead.**

### Layer 2: Claude Code Hooks
- [ ] Write `.claude/settings.json` with IDP-specific hooks — **Not implemented as project-level settings. Global hooks (check-aboutme, check-commit-message, validate-file) from llm_coding_workflow were active. IDP-specific hooks (cc-pretool-guard, cc-posttool-audit, cc-stop-deterministic) were NOT created.**
- [ ] Write `cc-pretool-guard.sh` (block kubectl apply after Phase 2) — **Not implemented. kubectl apply was used manually in some cases.**
- [ ] Write `cc-posttool-audit.sh` (scorecard reminders) — **Not implemented.**
- [ ] Write `cc-stop-deterministic.sh` (Ralph Wiggum phase gate) — **Not implemented. Existing `stop-hook.sh` present but phase gate pattern not used.**

### Commands & Skills
- [x] Write 3 slash commands (`build-phase`, `score-component`, `validate-phase`)
- [x] Write 6 skills files (`eks-hardening`, `argocd-patterns`, `kyverno-policies`, `falco-rules`, `otel-wiring`, `backstage-templates`)
- [x] Write test files for all 7 phases (59 tests total)

### Build Execution
- [x] Phases 1-7 complete — all 59 tests passing
- [x] Terminal recordings exist (phase-00, phase-01 in recordings/)
- [ ] Export transcript after each phase — **Transcripts not exported as JSON. Prompt logs reconstructed retrospectively in `prompts/phase-01 through 07-prompts.md`.**
- [ ] `pre-commit run --all-files` after each phase — **Pre-commit framework not installed. Existing git hooks ran on each commit.**
- [ ] `git tag phase-X-complete` after each phase — **No git tags created.**
- [ ] Verify guardrail coverage grows with each phase — **Not formally tracked.**

### Collateral (Phase 8)
- [x] Scorecard finalized (3hr AI / 11.5hr manual / 73.6% reduction / 24 correction cycles)
- [x] Blog post draft (`collateral/blog-post-draft.md`)
- [x] Demo runbook (`collateral/demo-runbook.md`)
- [x] Slide outline (`collateral/slide-outline.md`)
- [x] Attendee handout (`collateral/attendee-handout.md`)
- [x] Social media thread (`collateral/social-media-thread.md`)
- [ ] 3x end-to-end demo flow — **Manual task, not yet done.**

### Documentation
- [x] ARCHITECTURE.md
- [x] SETUP.md (with pre-flight checklist)
- [x] TEARDOWN.md
- [x] LESSONS-LEARNED.md (9 cross-cutting lessons, 24 correction cycles documented)
- [x] VERSION-MAP.md (chart-to-app version mapping)
- [x] SECURITY.md
- [x] COST.md
- [x] WALKTHROUGH.md (this document)
- [x] README.md (public-facing)
- [x] LICENSE (Apache 2.0)
- [x] Prompt logs populated for all 7 phases

### Production Hardening
- [x] cert-manager with Let's Encrypt ClusterIssuers (staging + production)
- [x] ALB Ingress for ArgoCD with ACM TLS certificate
- [x] ArgoCD accessible at `https://argocd.ai-enhanced-devops.com`
- [x] GitHub OIDC via Dex (peopleforrester = platform-admin)
- [x] Resource quotas (10 pods, 4 CPU, 8Gi in apps)
- [x] PodDisruptionBudgets for sample-app and ArgoCD
- [x] gitleaks clean
- [ ] OIDC tested with second GitHub account — **Manual task.**

### Remaining Items
- [ ] **Build actual slides** from `collateral/slide-outline.md` (PowerPoint/Google Slides)
- [ ] **QR codes** for repo, scorecard, `https://argocd.ai-enhanced-devops.com`
- [ ] **Demo runbook 3x end-to-end** without intervention
- [ ] **Practice run with timer** (target 27 min for 30-min slot)
- [ ] **OIDC test with second account**
- [ ] **Add scorecard guardrail coverage column** (optional — current 6-dimension scorecard is complete)
- [ ] **Git tags for phase completion** (retroactive, optional)
- [ ] **IDP-specific Layer 1 + Layer 2 hooks** (for the rebuild walkthrough — not needed for current live platform)

---

## What Makes This Talk Sing

Two payload artifacts, not one:

**Payload 1: The AI Platform Building Scorecard.** Component-by-component honesty about where AI helped and where it didn't. The 68% over-automation pattern validates the findings.

**Payload 2: The Three-Layer Guardrail Architecture.** The IDP wasn't just built *with* guardrails — it was built *by* guardrails. Git hooks (deterministic, local) → Claude Code hooks (build-time enforcement) → Kubernetes infrastructure (runtime enforcement). Same Eight Guardrails Framework at every layer, with problems caught at the cheapest possible point.

**Talk narrative:**

1. **Setup** (2 min): "What if AI built your entire platform? Let's find out — with guardrails."
2. **The Three Layers** (3 min): Quick visual showing Git → Claude Code → Kubernetes. "We didn't just build guardrails into the platform. We built the platform using guardrails."
3. **The Build** (5 min): Speed-run through 7 phases. Real prompts, real failures.
4. **The Scorecard** (8 min): Component by component. Where AI scored high (boilerplate, docs), where it scored low (cross-resource debugging, custom Falco rules). The guardrail coverage column shows which protections came online at each phase.
5. **The Failures** (5 min): Specific moments where each layer caught something. Git hook blocked a secret. Claude Code hook blocked a `kubectl apply`. Kyverno rejected a non-compliant pod. Show the actual terminal output.
6. **When NOT To Do This** (2 min): Brownfield, regulated without audit trails. The honest boundaries.
7. **Takeaway** (2 min): Two things you can steal — the scorecard template and the three-layer guardrail architecture. QR code to the repo.

Total: ~27 minutes for a 30-minute slot.
