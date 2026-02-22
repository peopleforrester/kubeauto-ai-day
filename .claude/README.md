# Claude Code Configuration

AI-assisted development tooling for this IDP build. These files configure
Claude Code's behavior, provide domain knowledge, and enforce guardrails.

## Commands (Slash Commands)

Invoke with `/command-name` in Claude Code.

| Command | Purpose |
|---------|---------|
| `build-phase.md` | Execute a build phase with TDD workflow |
| `validate-phase.md` | Validate all tests for a completed phase |
| `score-component.md` | Score a component on the AI Platform Building Scorecard |

## Skills (Context Injection)

Domain-specific knowledge that Claude Code reads before generating config.

| Skill | Covers |
|-------|--------|
| `argocd-patterns.md` | ArgoCD 3.x, app-of-apps, sync waves, Helm values |
| `backstage-templates.md` | Backstage 1.46+, new backend system, catalog format |
| `eks-hardening.md` | EKS module v21, Pod Identity, managed addons |
| `falco-rules.md` | Falco eBPF, custom rules, EKS-aware detection |
| `kyverno-policies.md` | Kyverno 1.17, CEL direction, namespace exclusions |
| `otel-wiring.md` | OTel Collector contrib, DaemonSet mode, remote write |

Each skill file includes a "Guardrail Integration" section mapping to the
Eight Guardrails framework.

## Hooks (Guardrail Layer 2)

Registered in `settings.json`. Fire during Claude Code sessions.

| Hook | Event | What It Does |
|------|-------|-------------|
| `cc-pretool-guard.sh` | PreToolUse | Blocks dangerous commands (kubectl apply post-Phase 2, terraform destroy, secret dumps) |
| `cc-posttool-audit.sh` | PostToolUse | Scorecard reminders, verify-after-apply, rollback suggestions |
| `cc-stop-deterministic.sh` | Stop | Ralph Wiggum pattern — blocks exit without phase promise |
| `check-image-allowlist.sh` | Pre-commit | Registry allowlist enforcement |
| `check-namespace-scope.sh` | Pre-commit | Phase-scoped namespace validation |
| `commit-msg-validate.sh` | Commit-msg | Conventional commit format enforcement |
| `pre-push-tests.sh` | Pre-push | Block push if phase tests fail |
| `stop-hook.sh` | Legacy | Original stop hook (superseded by cc-stop-deterministic.sh) |

## Settings

`settings.json` registers all hooks with their event matchers and timeouts.
See [docs/EIGHT-GUARDRAILS.md](../docs/EIGHT-GUARDRAILS.md) for the full
Layer 2 guardrail architecture.
