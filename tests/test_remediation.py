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
