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
