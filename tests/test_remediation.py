# ABOUTME: Static-file remediation tests driven by the senior-review plan.
# ABOUTME: Runs without a live cluster; covers PII, hygiene, versions, and security docs.

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Phase 1 — test infrastructure smoke tests
# ---------------------------------------------------------------------------


def test_remediation_plan_exists() -> None:
    """The plan committed in docs/ is the source of truth for this work."""
    plan = REPO_ROOT / "docs" / "REMEDIATION-PLAN.md"
    assert plan.is_file(), f"missing remediation plan: {plan}"


def test_static_test_runs_without_cluster() -> None:
    """Sanity check: a static test in this module must run without kubeconfig.

    If this test executes, it proves the autouse cluster fixture has been
    converted to opt-in. Without that change, pytest fails at collection or
    setup with a kubeconfig error before this body ever runs.
    """
    assert True


def test_requires_cluster_marker_registered() -> None:
    """The 'requires_cluster' marker must be registered in pyproject.toml."""
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    assert "requires_cluster" in pyproject, (
        "pyproject.toml must register the 'requires_cluster' marker under "
        "[tool.pytest.ini_options].markers"
    )


@pytest.mark.requires_cluster
def test_marker_does_not_blow_up() -> None:
    """A marked test must be valid — pytest --strict-markers should not warn."""
    # When --strict-markers is on, an unregistered marker raises at collection.
    # If this test even runs (under -m requires_cluster), the marker is fine.
    assert True


# ---------------------------------------------------------------------------
# Phase 2 — critical hygiene
# ---------------------------------------------------------------------------


def test_falco_custom_rules_zombie_file_absent() -> None:
    """The duplicate Falco rules file must not exist on disk.

    Authoritative source for custom Falco rules is gitops/apps/falco.yaml's
    customRules block (commit 27e5876 deleted the standalone file). A copy
    in security/falco/custom-rules.yaml drifts from truth — fail if present.
    """
    zombie = REPO_ROOT / "security" / "falco" / "custom-rules.yaml"
    assert not zombie.exists(), (
        f"{zombie} reappeared on disk. Delete it; rules live in "
        "gitops/apps/falco.yaml."
    )


def test_kyverno_image_registries_no_duplicate() -> None:
    """The restrict-image-registries pattern must not duplicate docker.io/library."""
    policy = (
        REPO_ROOT / "policies" / "kyverno" / "restrict-image-registries.yaml"
    ).read_text()
    pattern_line = next(
        (line for line in policy.splitlines() if "image:" in line and "ghcr.io" in line),
        None,
    )
    assert pattern_line is not None, "expected image: pattern line not found"
    assert pattern_line.count("docker.io/library/*") == 1, (
        f"duplicated docker.io/library/* in pattern: {pattern_line.strip()}"
    )


def test_teardown_script_success_banner_renders_dollar_zero_correctly() -> None:
    """teardown.sh banner must render '$0' as a literal, not the script path."""
    script = (REPO_ROOT / "scripts" / "teardown.sh").read_text()
    bad = "TEARDOWN COMPLETE — $0 recurring charges"
    assert bad not in script, (
        "teardown.sh contains an unescaped $0 in the success banner; the "
        "rendered output reads as the script path, not '$0/hr'."
    )


# ---------------------------------------------------------------------------
# Phase 3 — PII removal for public readiness
# ---------------------------------------------------------------------------


# Tracked files that historically held personal email addresses.
PII_PATHS = [
    "security/cert-manager/cluster-issuers.yaml",
    "gitops/argocd/values.yaml",
]

PII_LITERALS = [
    "michael@kubeauto.dev",
    "michaelrishiforrester@gmail.com",
]


@pytest.mark.parametrize("relpath", PII_PATHS)
def test_no_personal_email_in_committed_manifests(relpath: str) -> None:
    """Personal emails must not appear in committed cluster-config manifests."""
    text = (REPO_ROOT / relpath).read_text()
    for needle in PII_LITERALS:
        assert needle not in text, (
            f"{relpath} still contains personal email literal {needle!r}; "
            "use a placeholder and document substitution in docs/SETUP.md."
        )


def test_setup_doc_lists_substitutions() -> None:
    """SETUP.md must include a substitutions section listing forker placeholders."""
    setup = (REPO_ROOT / "docs" / "SETUP.md").read_text()
    assert "Substitutions" in setup or "substitutions" in setup, (
        "docs/SETUP.md is missing a 'Substitutions' section that lists every "
        "placeholder a forker must replace before applying manifests."
    )
    # Spot-check that the well-known placeholders are mentioned.
    for placeholder in ("<YOUR_EMAIL>", "<YOUR_AWS_ACCOUNT_ID>"):
        assert placeholder in setup, (
            f"docs/SETUP.md substitutions section must reference {placeholder}."
        )


# ---------------------------------------------------------------------------
# Phase 4 — security hardening (static)
# ---------------------------------------------------------------------------


def test_grafana_password_not_plaintext() -> None:
    """Prometheus/Grafana values must not embed a plaintext admin password.

    The repo's stated narrative is 'all secrets via External Secrets Operator';
    leaving adminPassword: "admin" undermines that. The ExternalSecret should
    be the source of the credential.
    """
    text = (REPO_ROOT / "gitops" / "apps" / "prometheus.yaml").read_text()
    assert 'adminPassword: "admin"' not in text, (
        "gitops/apps/prometheus.yaml still contains a plaintext "
        '`adminPassword: "admin"`; wire Grafana credentials through ESO.'
    )
    assert "existingSecret" in text, (
        "gitops/apps/prometheus.yaml must use admin.existingSecret to pull "
        "Grafana credentials from a Secret synced by ESO."
    )


def test_grafana_admin_external_secret_exists() -> None:
    """An ExternalSecret manifest must exist that materialises the Grafana Secret."""
    eso = (
        REPO_ROOT / "security" / "eso" / "grafana-admin-external-secret.yaml"
    )
    assert eso.is_file(), (
        f"missing {eso}: expected an ExternalSecret that creates "
        "`grafana-admin-credentials` in monitoring namespace."
    )
    text = eso.read_text()
    assert "kind: ExternalSecret" in text
    assert "grafana-admin-credentials" in text
    assert "namespace: monitoring" in text


def test_cluster_role_renamed_to_demo_cluster_admin() -> None:
    """ClusterRole that grants *:* on *:* must be named demo-cluster-admin.

    'platform-admin' is a misleading name for a role that is identical to
    cluster-admin — readers cribbing the manifest could inherit the wrong
    mental model.
    """
    text = (REPO_ROOT / "security" / "rbac" / "cluster-roles.yaml").read_text()
    assert "name: demo-cluster-admin" in text, (
        "expected ClusterRole renamed to `demo-cluster-admin`"
    )
    assert "name: platform-admin" not in text, (
        "stale `platform-admin` ClusterRole name still present"
    )


def test_security_doc_documents_argocd_tls_tradeoff() -> None:
    """SECURITY.md must explain the ArgoCD --insecure trade-off explicitly."""
    text = (REPO_ROOT / "docs" / "SECURITY.md").read_text()
    assert "ArgoCD TLS" in text or "argocd" in text.lower(), (
        "docs/SECURITY.md should mention ArgoCD"
    )
    # The explicit trade-off discussion must be present.
    needles = ("server.insecure", "ALB")
    for needle in needles:
        assert needle in text, (
            f"docs/SECURITY.md is missing '{needle}' — readers need to "
            "understand why server.insecure is set and what the trade-off is."
        )
