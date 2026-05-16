# Senior-Review Remediation Plan

<!-- ABOUTME: Phase-by-phase plan to remediate senior-review findings.
     ABOUTME: TDD-driven; each phase has tests written first, then implementation. -->

## Goal

Address the actionable findings from the post-talk senior review while keeping
the repo verifiable without a live cluster (cluster has been torn down). All
changes are static-file edits that can be validated by file-content tests.

## TDD Protocol Applied

For every fix in every phase:

1. Write a failing test in `tests/test_remediation.py` (or extend conftest).
2. Run the test, observe the expected failure (not an import error).
3. Make the minimal change to pass the test.
4. Run the test, observe pass.
5. Re-run the full local-only test suite (`uv run pytest -m "not requires_cluster"`).

No phase advances until its tests are green.

## Scope

In scope (this plan):
- Critical and high-priority items from the review that are file-level static fixes.
- Test-infrastructure work needed to enable TDD without a cluster.
- Documentation reconciliation.

Out of scope (deferred, tracked in `REMAINING-ITEMS.md`):
- Manifest deduplication for the `*-party/` apps (M1 — large refactor; not blocking).
- GitHub Actions CI workflow (L-priority).
- Any change requiring a running cluster (cluster is torn down).

## Phase Breakdown

### Phase 1 — Test infrastructure (precondition)

The autouse `_kube_config` fixture aborts collection when no kubeconfig is
reachable, so the suite is currently all-or-nothing. Without a cluster, no
TDD is possible. Phase 1 makes the suite partially runnable.

Changes:
- Register `requires_cluster` marker in `pyproject.toml`.
- Convert `_kube_config` from `autouse=True` to opt-in via the marker (apply
  only when a test is marked `requires_cluster`).
- Annotate every existing test that touches the cluster with
  `@pytest.mark.requires_cluster` (all phase-NN tests do).
- Add `tests/test_remediation.py` skeleton with a smoke test that runs
  without a cluster, proving the new mode works.

Exit condition:
- `uv run pytest -m "not requires_cluster" -q` runs and passes.
- `uv run pytest --collect-only` collects without error.

### Phase 2 — Critical hygiene

Three small, low-risk file fixes.

Changes:
- **Falco zombie file**: delete `security/falco/custom-rules.yaml` from the
  working tree; add a test asserting it does not exist (rules are inlined in
  `gitops/apps/falco.yaml`, which is the single source of truth).
- **Kyverno duplicate pattern**: remove the duplicated `docker.io/library/*:*`
  entry in `policies/kyverno/restrict-image-registries.yaml`.
- **teardown.sh shell escape**: replace `$0` with literal `$0/hr` in the success
  banner so the rendered output reads correctly.

Exit condition:
- All Phase 2 tests pass.
- `bash -n scripts/teardown.sh` parses cleanly.

### Phase 3 — PII removal for public readiness

The repo is public; personal email addresses are surface area for spam
harvesting and confuse forkers (Let's Encrypt rate limits attach to the
configured email).

Changes:
- `security/cert-manager/cluster-issuers.yaml`: replace the hardcoded
  cert-manager contact email with a `<YOUR_EMAIL>` placeholder.
- `gitops/argocd/values.yaml`: replace the personal Gmail admin subject
  with `<YOUR_GITHUB_EMAIL_OR_USERNAME>`; keep one named org-level handle
  as an example.
- `docs/SETUP.md`: add a "Substitutions before first apply" table listing
  every placeholder a forker must change.

Exit condition:
- No tracked file contains a personal email literal.
- `docs/SETUP.md` documents every placeholder.

### Phase 4 — Security hardening (static)

Three changes that align the repo with its own stated security narrative.

Changes:
- **Grafana password via ESO**: replace plaintext `adminPassword: "admin"` in
  `gitops/apps/prometheus.yaml` with `admin.existingSecret`/`userKey`/`passwordKey`
  pointing at a `grafana-admin-credentials` Secret synced from AWS Secrets
  Manager via an ExternalSecret. Add the matching `ExternalSecret` manifest.
- **ClusterRole rename**: rename `platform-admin` → `demo-cluster-admin` in
  `security/rbac/cluster-roles.yaml` and every reference in `gitops/argocd/values.yaml`,
  `docs/SECURITY.md`, ADR-007. Inline a comment explicitly stating it's
  cluster-admin equivalent and pointing readers at `app-developer` for scoped use.
- **ArgoCD `--insecure` documentation**: add a section to `docs/SECURITY.md`
  explaining why `server.insecure` is set, what the trade-off is (cleartext
  ALB→pod within the VPC), and how a production reader should switch to
  ALB pass-through TLS.

Exit condition:
- `gitops/apps/prometheus.yaml` contains no plaintext password literal.
- `security/rbac/cluster-roles.yaml` defines `demo-cluster-admin`, not
  `platform-admin`.
- `docs/SECURITY.md` has an "ArgoCD TLS termination trade-off" section.

### Phase 5 — Version reconciliation

The README, CLAUDE.md, scripts/rebuild.sh, and the Falco Application all pin
slightly different versions. Forkers will read the README first.

Changes:
- Make `docs/VERSION-MAP.md` the single source of truth for "what's deployed".
- Update `README.md` versions section to match VERSION-MAP.md exactly.
- Update CLAUDE.md "Technology Versions (deployed)" section to match.
- Update `scripts/rebuild.sh` `ARGOCD_CHART_VERSION` to match.
- Add a short `tests/test_remediation.py::test_version_consistency` that
  parses each file and asserts they agree on ArgoCD, Kyverno, Falco, and
  Backstage versions.

Exit condition:
- `test_version_consistency` passes.
- All four files agree.

## Out-of-Plan Items (Tracked, Not Done Here)

| ID | Item | Reason deferred |
|----|------|-----------------|
| C2 | Hardcoded AWS account ID in 14+ files | Documented in REMAINING-ITEMS.md; large parameterization effort |
| H7 | EKS node group config minimal | Cluster torn down — not relevant to a reference repo unless we re-deploy |
| M1 | `*-party/` manifest duplication | Large refactor; not blocking public-readiness |
| M2 | Falco rules duplicated between standalone files and Application | Resolved by Phase 2 (zombie file deleted) |
| M9 | Backstage→ArgoCD apiKey vs OIDC | Working as designed; production readers can swap |
| L1–L6 | Misc polish | Nice-to-have |

## Verification Method

- File-content assertions in `tests/test_remediation.py`.
- Static parsing (YAML load, bash `-n`) where applicable.
- No live-cluster verification (cluster torn down). Anything requiring
  cluster verification must be flagged as such in PROJECT_STATE.md.
