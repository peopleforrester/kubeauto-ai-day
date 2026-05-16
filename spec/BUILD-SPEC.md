# KubeAuto Day IDP Build Spec
# "The 10-Hour IDP: Can Claude Code Actually Reduce Platform Engineering Toil?"

## Project Overview

This spec defines a complete Internal Developer Platform built from scratch on EKS using Claude Code. The build is recorded end-to-end for a KubeAuto Day Europe 2026 presentation. Every prompt, failure, correction, and iteration is captured as talk material.

The repo serves three purposes:
1. The live demo platform for the KubeAuto Day talk
2. An open-source reference IDP (Apache 2.0)
3. Evidence for the AI Platform Building Scorecard

This document covers Phases 0–7 (the KubeAuto talk scope, complete as of
March 2026). Forward-looking phases 8–16 (Agent Gateway, workload identity,
human SSO, secrets vault, supply chain, service mesh, progressive delivery)
are tracked in [`ROADMAP.md`](ROADMAP.md).

## Repository Structure

```
kubeauto-idp/
├── CLAUDE.md                          # Claude Code project instructions
├── .claude/
│   ├── commands/
│   │   ├── build-phase.md             # /build-phase slash command
│   │   ├── score-component.md         # /score-component slash command
│   │   └── validate-phase.md          # /validate-phase slash command
│   ├── hooks/
│   │   └── stop-hook.sh               # Ralph Wiggum stop hook
│   └── skills/
│       ├── eks-hardening.md           # EKS security patterns
│       ├── argocd-patterns.md         # GitOps app-of-apps patterns
│       ├── kyverno-policies.md        # Policy authoring patterns
│       ├── falco-rules.md             # Runtime security rule patterns
│       ├── backstage-templates.md     # Software template patterns
│       └── otel-wiring.md            # Observability stack patterns
├── spec/
│   ├── BUILD-SPEC.md                  # This file (copied into repo)
│   ├── SCORECARD.md                   # AI Platform Building Scorecard (updated during build)
│   └── phases/
│       ├── phase-01-foundation.md
│       ├── phase-02-gitops.md
│       ├── phase-03-security.md
│       ├── phase-04-observability.md
│       ├── phase-05-portal.md
│       ├── phase-06-integration.md
│       └── phase-07-hardening.md
├── infrastructure/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── eks.tf
│   │   ├── vpc.tf
│   │   ├── iam.tf
│   │   └── secrets-manager.tf
│   └── eksctl/                        # Fallback if Terraform EKS module fights back
│       └── cluster-config.yaml
├── gitops/
│   ├── bootstrap/
│   │   └── app-of-apps.yaml
│   ├── argocd/
│   │   ├── install.yaml
│   │   ├── argocd-cm.yaml
│   │   ├── argocd-rbac-cm.yaml
│   │   └── applicationsets/
│   ├── namespaces/
│   │   └── namespaces.yaml
│   └── apps/
│       ├── kyverno/
│       ├── falco/
│       ├── falcosidekick/
│       ├── external-secrets/
│       ├── cert-manager/
│       ├── prometheus/
│       ├── grafana/
│       ├── otel-collector/
│       ├── backstage/
│       └── sample-app/
├── policies/
│   ├── kyverno/
│   │   ├── require-labels.yaml
│   │   ├── restrict-registries.yaml
│   │   ├── require-resource-limits.yaml
│   │   ├── disallow-privileged.yaml
│   │   ├── require-probes.yaml
│   │   └── require-network-policies.yaml
│   └── network-policies/
│       ├── default-deny.yaml
│       └── per-namespace/
├── security/
│   ├── falco/
│   │   ├── custom-rules.yaml
│   │   └── eks-aware-rules.yaml
│   ├── falcosidekick/
│   │   └── values.yaml
│   └── rbac/
│       ├── cluster-roles.yaml
│       └── role-bindings.yaml
├── observability/
│   ├── otel-collector/
│   │   └── config.yaml
│   ├── prometheus/
│   │   ├── values.yaml
│   │   └── rules/
│   ├── grafana/
│   │   ├── values.yaml
│   │   └── dashboards/
│   │       ├── platform-overview.json
│   │       ├── argocd-sync.json
│   │       ├── kyverno-policy.json
│   │       └── falco-alerts.json
│   └── alerting/
│       └── alert-rules.yaml
├── backstage/
│   ├── app-config.yaml
│   ├── catalog/
│   │   ├── catalog-info.yaml
│   │   └── systems/
│   └── templates/
│       ├── deploy-service/
│       │   ├── template.yaml
│       │   └── skeleton/
│       └── create-namespace/
│           ├── template.yaml
│           └── skeleton/
├── sample-app/
│   ├── Dockerfile
│   ├── src/
│   ├── k8s/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── ingress.yaml
│   │   └── network-policy.yaml
│   └── catalog-info.yaml
├── tests/
│   ├── conftest.py
│   ├── test_phase_01_foundation.py
│   ├── test_phase_02_gitops.py
│   ├── test_phase_03_security.py
│   ├── test_phase_04_observability.py
│   ├── test_phase_05_portal.py
│   ├── test_phase_06_integration.py
│   ├── test_phase_07_hardening.py
│   └── helpers/
│       ├── kubectl_helpers.py
│       └── wait_helpers.py
├── prompts/
│   ├── README.md                      # Prompt strategy and methodology
│   ├── phase-01-prompts.md
│   ├── phase-02-prompts.md
│   ├── phase-03-prompts.md
│   ├── phase-04-prompts.md
│   ├── phase-05-prompts.md
│   ├── phase-06-prompts.md
│   └── phase-07-prompts.md
├── scorecard/
│   ├── SCORECARD-TEMPLATE.md          # Reusable framework for other teams
│   ├── raw-scores.json                # Machine-readable scores per component
│   └── methodology.md                 # How we scored, what counts as "toil reduced"
├── collateral/
│   ├── blog-post-draft.md             # Post-talk writeup
│   ├── slide-outline.md               # Presentation structure
│   ├── demo-runbook.md                # Step-by-step live demo script
│   ├── attendee-handout.md            # What attendees get access to
│   └── social-media-thread.md         # Promotion thread for post-acceptance
├── docs/
│   ├── SETUP.md                       # Full cluster setup instructions
│   ├── ARCHITECTURE.md                # Architecture decisions and rationale
│   ├── SECURITY.md                    # Security posture documentation
│   ├── COST.md                        # What this costs to run
│   └── TEARDOWN.md                    # How to destroy everything cleanly
└── recordings/
    └── README.md                      # Links to screen recordings per phase
```

## Technology Stack

### CNCF Graduated
- Kubernetes (EKS 1.34+)
- ArgoCD (3.2+)
- Prometheus (kube-prometheus-stack)
- Falco + Falcosidekick
- Crossplane (2.1+, if time allows)

### CNCF Incubating
- Backstage (1.46+)
- Kyverno (1.17+)
- OpenTelemetry (Collector 0.140+)

### CNCF Sandbox
- External Secrets Operator

### Ecosystem
- Grafana (12.x)
- cert-manager (1.19+)
- AWS Load Balancer Controller

### AWS Services
- EKS, VPC, IAM (Pod Identity/IRSA), Secrets Manager, ACM, Route53, ECR

### AI Tooling
- Claude Code with custom skills, commands, and hooks
- Smart Ralph or ralph-loop plugin for continuous execution


## Build Phases

Each phase has: defined inputs, expected outputs, test criteria (the completion gate), and a time budget. Tests are written FIRST, then the implementation runs until tests pass.

---

### Phase 1: Foundation (Budget: 60 min)

**Goal:** EKS cluster running with VPC, IAM baseline, and kubeconfig working.

**Inputs:** Empty AWS account with admin credentials configured.

**Outputs:**
- Terraform config for VPC (3 AZ, public/private subnets, NAT gateway)
- Terraform config for EKS cluster (private API endpoint, managed node group)
- IAM roles for cluster, node group, and Pod Identity agent
- Working kubeconfig
- Namespace structure: platform, argocd, monitoring, backstage, apps, security

**Test Criteria (tests/test_phase_01_foundation.py):**
```
- terraform validate passes with no errors
- terraform plan produces no errors
- EKS cluster endpoint is reachable via kubeconfig
- kubectl get nodes returns at least 2 Ready nodes
- All defined namespaces exist
- EKS Pod Identity agent addon is active
- VPC CNI is running with NetworkPolicy support enabled
- Private API endpoint is enabled, public is disabled (or restricted to specific CIDR)
- Node security group restricts inbound to cluster SG only
```

**Completion Promise:** `<promise>PHASE1_DONE</promise>`

**Known Risk:** Terraform EKS module is notoriously finicky with IAM role chaining. If Claude gets stuck for more than 3 iterations on IAM, fall back to eksctl for cluster creation and Terraform for VPC/IAM only.

---

### Phase 2: GitOps Bootstrap (Budget: 90 min)

**Goal:** ArgoCD installed, app-of-apps pattern bootstrapped, all subsequent components deployed via GitOps.

**Inputs:** Working EKS cluster from Phase 1.

**Outputs:**
- ArgoCD installed in argocd namespace via Helm
- ArgoCD configured with SSO disabled (initial), admin password set via Secret
- App-of-apps root Application pointing to gitops/bootstrap/
- ApplicationSets for environment promotion (dev only initially)
- ArgoCD RBAC configured with project-scoped access
- Every subsequent component deployed as an ArgoCD Application (no more kubectl apply)

**Test Criteria (tests/test_phase_02_gitops.py):**
```
- ArgoCD server pod is Running
- ArgoCD UI is accessible (port-forward or ingress)
- Root app-of-apps Application exists and is Synced/Healthy
- At least the namespace Application is Synced
- argocd app list returns valid JSON with no Degraded apps
- ArgoCD can detect drift (manually change a resource, verify OutOfSync)
- Git repo is the single source of truth (no resources created outside Git)
```

**Completion Promise:** `<promise>PHASE2_DONE</promise>`

**Known Risk:** ArgoCD sync waves and resource ordering. Claude tends to get this wrong on multi-dependency apps. The app-of-apps needs sync waves: namespaces first, then CRDs, then apps.

---

### Phase 3: Security Stack (Budget: 120 min)

**Goal:** Kyverno policies enforcing, Falco detecting runtime threats, ESO pulling secrets from AWS Secrets Manager, RBAC locked down.

**Inputs:** ArgoCD-managed cluster from Phase 2.

**Outputs:**
- Kyverno installed via ArgoCD Application
- Kyverno policies: require-labels, restrict-registries, require-resource-limits, disallow-privileged, require-probes, require-network-policies
- Falco installed with custom EKS-aware rules via ArgoCD Application
- Falcosidekick forwarding to Prometheus (and optionally Slack)
- External Secrets Operator installed via ArgoCD Application
- At least one ExternalSecret pulling from AWS Secrets Manager
- Pod Identity or IRSA configured for ESO to access Secrets Manager
- RBAC: cluster-admin only for platform team, namespace-scoped roles for app teams
- Default-deny NetworkPolicies in all app namespaces

**Test Criteria (tests/test_phase_03_security.py):**
```
- Kyverno pods are Running
- Policy: deploying a pod without resource limits is BLOCKED
- Policy: deploying a pod from an unauthorized registry is BLOCKED
- Policy: deploying a privileged pod is BLOCKED
- Falco pods are Running on each node (DaemonSet)
- Falco: exec into a pod triggers a Falco alert (check falco logs)
- ESO: ExternalSecret resource shows SecretSynced condition
- ESO: Kubernetes Secret created matches value in AWS Secrets Manager
- RBAC: ServiceAccount in apps namespace cannot list secrets in platform namespace
- NetworkPolicy: pod in apps namespace cannot reach pod in platform namespace on arbitrary port
```

**Completion Promise:** `<promise>PHASE3_DONE</promise>`

**Known Risk:** This is the phase where Claude will struggle the most. IAM role trust policies for Pod Identity, Kyverno policy interaction (one policy blocking another's resources), and Falco custom rules that actually match EKS-specific syscall patterns. Budget 120 min because correction cycles here are expensive.

---

### Phase 4: Observability (Budget: 90 min)

**Goal:** Full observability stack: metrics, logs, traces flowing through OTel Collector to Prometheus and Grafana.

**Inputs:** Secured cluster from Phase 3.

**Outputs:**
- Prometheus (kube-prometheus-stack) installed via ArgoCD
- Grafana installed with pre-provisioned dashboards via ArgoCD
- OTel Collector deployed as DaemonSet, configured to receive OTLP and export to Prometheus
- Grafana dashboards: platform overview, ArgoCD sync status, Kyverno policy violations, Falco alerts
- Alert rules: node not ready, pod crash loop, ArgoCD app degraded, Falco critical alert
- Sample app instrumented with OTel SDK (traces and metrics)

**Test Criteria (tests/test_phase_04_observability.py):**
```
- Prometheus pods are Running
- Grafana pods are Running, UI accessible
- OTel Collector pods are Running on each node
- Prometheus has scrape targets for: kubelet, node-exporter, kube-state-metrics, ArgoCD, Kyverno
- Grafana: platform-overview dashboard loads without errors
- Grafana: at least one panel shows non-zero data
- OTel Collector: sending a test OTLP span results in it appearing in Prometheus/traces backend
- Alert rules exist in Prometheus for at minimum: NodeNotReady, PodCrashLoop
```

**Completion Promise:** `<promise>PHASE4_DONE</promise>`

**Known Risk:** OTel Collector config is where Claude generates plausible-looking YAML that doesn't actually work. Exporters pointed at wrong endpoints, receivers configured for protocols nothing sends. Manual review of the collector config is mandatory.

---

### Phase 5: Developer Portal (Budget: 90 min)

**Goal:** Backstage running with service catalog, software templates that deploy through ArgoCD.

**Inputs:** Observable, secured cluster from Phase 4.

**Outputs:**
- Backstage installed via ArgoCD Application (or Helm)
- Backstage app-config.yaml with: catalog provider (GitHub or local), ArgoCD plugin, Kubernetes plugin
- Service catalog with at least the sample app registered
- Software template: "Deploy a new service" that creates namespace, deployment, service, network policy, registers in catalog, and creates ArgoCD Application
- Software template: "Create a new namespace" with default RBAC and NetworkPolicy
- TechDocs configured for at least one component

**Test Criteria (tests/test_phase_05_portal.py):**
```
- Backstage pod is Running
- Backstage UI is accessible
- Service catalog shows at least 1 registered component
- Software template "Deploy a new service" appears in template list
- Executing the template creates the expected ArgoCD Application
- ArgoCD syncs the new Application to Healthy
- New service's pod is Running with correct labels and resource limits
- New service passes all Kyverno policies (no violations)
```

**Completion Promise:** `<promise>PHASE5_DONE</promise>`

**Known Risk:** Backstage plugin wiring is fragile. The ArgoCD plugin needs specific annotations in catalog-info.yaml. The Kubernetes plugin needs cluster config. Claude generates plausible configs that miss one annotation and the whole plugin shows "no data." Budget time for debugging plugin connectivity.

---

### Phase 6: Integration Testing (Budget: 60 min)

**Goal:** End-to-end flow works. Deploy via Backstage, see it in ArgoCD, validated by Kyverno, observed in Grafana, protected by Falco.

**Inputs:** Complete platform from Phases 1-5.

**Outputs:**
- End-to-end deployment flow tested and documented
- Demo runbook written with exact steps for live presentation
- Backup recordings captured for each demo scenario
- Known issues documented with workarounds

**Test Criteria (tests/test_phase_06_integration.py):**
```
- Deploy service via Backstage template, ArgoCD syncs it, pod is Running: under 3 minutes
- Attempt to deploy a non-compliant service (no limits), Kyverno blocks it
- Exec into a running pod, Falco generates alert within 10 seconds
- Falco alert appears in Grafana Falco dashboard within 60 seconds
- OTel traces from sample app appear in Grafana within 30 seconds
- Modify a deployed resource directly (kubectl edit), ArgoCD detects drift within sync interval
- Full demo runbook can be executed start to finish without errors
```

**Completion Promise:** `<promise>PHASE6_DONE</promise>`

---

### Phase 7: Production Hardening (Budget: 60 min)

**Goal:** OIDC authentication for attendee access, TLS everywhere, final security review.

**Inputs:** Integrated platform from Phase 6.

**Outputs:**
- cert-manager installed with Let's Encrypt ClusterIssuer
- TLS on all ingresses (ArgoCD, Backstage, Grafana, sample app)
- OIDC authentication configured (GitHub OAuth or similar) for Backstage and Grafana
- ArgoCD UI: read-only access for attendees via OIDC group mapping
- Resource quotas on apps namespace to prevent attendee abuse
- Pod disruption budgets on critical platform components
- Final security posture documented in docs/SECURITY.md
- Cost estimate documented in docs/COST.md

**Test Criteria (tests/test_phase_07_hardening.py):**
```
- All ingresses respond on HTTPS with valid TLS certificates
- HTTP requests redirect to HTTPS
- Backstage login via OIDC works (test with a second GitHub account)
- Grafana login via OIDC works
- ArgoCD UI: OIDC user can view but NOT sync or delete applications
- Resource quota prevents creating more than N pods in apps namespace
- PDBs exist for: ArgoCD, Prometheus, Grafana, Backstage
- No pods running as root (audit via Kyverno policy report)
- No secrets stored in Git (scan repo with gitleaks or similar)
```

**Completion Promise:** `<promise>PHASE7_DONE</promise>`

---

## AI Platform Building Scorecard

The scorecard is updated after each phase. Each component gets scored on:

**Toil Reduced (1-10):** How much manual work did AI eliminate?
- 10 = Would have taken hours manually, AI did it in minutes with no corrections
- 5 = AI produced a starting point, but required significant human correction
- 1 = AI output was wrong enough that starting from scratch would have been faster

**Correction Cycles:** Number of times the AI output needed human intervention before it worked.

**Time: AI-Assisted vs Estimated Manual:** Wall clock time with AI vs estimated time for a senior engineer doing it by hand.

**Toil Shifted:** Did AI actually remove toil, or did it convert "writing YAML" toil into "reviewing and debugging AI-generated YAML" toil?

### Scorecard Template

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

**Totals:**
- Total AI-assisted build time: ___ hours
- Total human correction time: ___ hours
- Estimated manual build time: ___ hours
- Net toil reduction: ___%
- Components where AI genuinely reduced toil: ___/27
- Components where AI shifted toil without reducing it: ___/27
- Components where starting from scratch would have been faster: ___/27


## Ralph Wiggum / Smart Ralph Configuration

### Stop Hook (`.claude/hooks/stop-hook.sh`)

```bash
#!/bin/bash
# Ralph Wiggum stop hook for spec-driven IDP build
# Reads Claude's output, checks for phase completion promise
# If promise not found, re-feeds the phase prompt

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
echo '{"decision": "block", "reason": "Phase completion promise not found. Continue working on current phase. Check test results and fix any failures."}'
exit 0
```

### Phase Execution Strategy

Each phase runs as a separate Ralph loop. Do not attempt to run all phases in a single loop; context window will fill.

```bash
# Phase 1
claude -p "/build-phase 1" --max-iterations 15

# Phase 2 (only after Phase 1 tests pass)
claude -p "/build-phase 2" --max-iterations 20

# Phase 3 (budget extra iterations, this is the hard one)
claude -p "/build-phase 3" --max-iterations 30

# Phase 4
claude -p "/build-phase 4" --max-iterations 20

# Phase 5
claude -p "/build-phase 5" --max-iterations 20

# Phase 6
claude -p "/build-phase 6" --max-iterations 15

# Phase 7
claude -p "/build-phase 7" --max-iterations 15
```

### Overnight Batch Script

```bash
#!/bin/bash
# overnight-build.sh
# Run all phases sequentially. Each phase must pass tests before the next starts.

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$REPO_DIR/recordings/logs"
mkdir -p "$LOG_DIR"

PHASES=(1 2 3 4 5 6 7)
MAX_ITERS=(15 20 30 20 20 15 15)

for i in "${!PHASES[@]}"; do
    PHASE=${PHASES[$i]}
    ITERS=${MAX_ITERS[$i]}
    echo "========================================="
    echo "Starting Phase $PHASE (max $ITERS iterations)"
    echo "$(date)"
    echo "========================================="

    cd "$REPO_DIR"
    claude -p "/build-phase $PHASE" \
        --max-iterations "$ITERS" \
        2>&1 | tee "$LOG_DIR/phase-${PHASE}.log"

    # Verify phase tests pass before continuing
    echo "Running Phase $PHASE tests..."
    python -m pytest "tests/test_phase_0${PHASE}_*.py" -v 2>&1 | tee -a "$LOG_DIR/phase-${PHASE}.log"

    if [ $? -ne 0 ]; then
        echo "PHASE $PHASE TESTS FAILED. Stopping build."
        exit 1
    fi

    echo "Phase $PHASE complete. Moving to next phase."
    echo ""
done

echo "========================================="
echo "ALL PHASES COMPLETE"
echo "$(date)"
echo "========================================="
```


## CLAUDE.md Instructions

The following goes into the repo's CLAUDE.md file to give Claude Code persistent context:

```markdown
# KubeAuto Day IDP Build

## What This Is
Building a production-grade Internal Developer Platform on EKS from scratch.
Every component is deployed via ArgoCD GitOps. No kubectl apply after Phase 2.

## How To Work
1. Read spec/BUILD-SPEC.md for the full build plan
2. Check which phase you're on by looking at spec/SCORECARD.md
3. Write tests FIRST (tests/test_phase_0X_*.py), then implement until they pass
4. After each component, update the scorecard with honest scores
5. Commit after each working component, not after each file

## Rules
- Everything after Phase 2 must be deployed as an ArgoCD Application
- No secrets in Git. Ever. Use External Secrets Operator.
- No kubectl apply in production namespaces after ArgoCD is running
- Every Helm install needs a values.yaml in the gitops/apps/ directory
- Test before you commit. If tests don't pass, don't commit.
- When you get stuck on IAM, re-read the AWS docs. Don't guess trust policies.
- Update spec/SCORECARD.md honestly after completing each component
- Record what went wrong in the scorecard notes column

## Completion
Output <promise>PHASEX_DONE</promise> (where X is the phase number) ONLY when
ALL test criteria for that phase pass. Do not output the promise if any test fails.

## Skills
See .claude/skills/ for patterns on specific components. Read the relevant
skill file BEFORE generating any config for that component.
```


## Collateral Plan

### Pre-Talk (produce before KubeAuto Day)
1. **GitHub repo** (Apache 2.0) with all code, tests, and documentation
2. **Scorecard** with final scores, methodology, and raw data
3. **Blog post draft** for post-talk publication (KodeKloud blog or dev.to)
4. **Demo runbook** for live presentation
5. **Slide outline** (not full slides yet, just structure and key points)
6. **Screen recordings** of each build phase (can be raw, edited later)

### At the Talk
7. **Live platform** running on EKS with OIDC authentication for attendees
8. **QR code** to repo, scorecard, and platform access

### Post-Talk
9. **Published blog post** with embedded scorecard and key findings
10. **Social media thread** summarizing results
11. **Scorecard template** published as standalone resource for other teams
12. **Recording link** (KubeAuto Day will record, but also self-record as backup)


## Prompt Strategy

### Methodology

Each phase has a dedicated prompts file (prompts/phase-0X-prompts.md) that captures:
- The initial prompt used to kick off the phase
- Every correction prompt (what went wrong and what was said to fix it)
- Time spent on each correction
- Whether the correction was "AI got it wrong" or "spec was ambiguous"

This becomes talk material. The audience sees real prompts, not sanitized ones.

### Prompt Recording Format

```markdown
## Prompt 1 (Phase X, HH:MM timestamp)
**Type:** Initial / Correction / Clarification
**Prompt:**
> [exact prompt text]

**Result:** Success / Partial / Failure
**Correction Needed:** [what was wrong]
**Time to Correct:** [minutes]
**Scorecard Impact:** [which component score this affects]
```

### Prompt Principles
- Start each phase with a broad prompt referencing the spec and tests
- Let Claude read the test file first so it knows what "done" means
- Don't over-specify implementation details in the prompt; let Claude make choices, then score those choices
- When correcting, be specific about what's wrong, not how to fix it
- Record every prompt, including the embarrassing ones


## Timeline

| Date | Milestone |
|---|---|
| Feb 9, 2026 | Spec complete, repo scaffolded |
| Feb 10-14 | Phase 1-3 build (foundation, gitops, security) |
| Feb 15-18 | Phase 4-5 build (observability, portal) |
| Feb 19-21 | Phase 6-7 build (integration, hardening) |
| Feb 22-28 | Scorecard finalization, blog draft, demo runbook |
| Mar 1-7 | Practice runs, slide creation, recording review |
| Mar 8-14 | Final polish, attendee access testing |
| Mar 15-22 | Buffer week |
| Mar 23, 2026 | KubeAuto Day Europe |

**Total build budget:** 10 hours of AI-assisted build time (wall clock, not calendar)
**Total human correction budget:** 6 hours (based on initial estimates, may vary)
**Recording:** Screen record every build session from minute zero


## Success Criteria

The build is "done" when:
1. All Phase 1-7 tests pass
2. Scorecard is complete with honest scores for all 27 components
3. End-to-end demo flow works three times in a row without intervention
4. At least one person other than the builder can access the platform via OIDC
5. Blog post draft exists
6. Demo runbook is tested
7. All prompt transcripts are captured
8. Total build time is documented (ideally near the 10-hour target)
