# Phase 6: Integration Testing (Budget: 60 min)

**Goal:** End-to-end flow works. Deploy via Backstage, see it in ArgoCD, validated by Kyverno, observed in Grafana, protected by Falco.

**Inputs:** Complete platform from Phases 1-5.

**Outputs:**
- End-to-end deployment flow tested
- Demo runbook with exact steps for live presentation
- ArgoCD sync interval set to 30s for demo
- Known issues documented with workarounds

**Test Criteria (tests/test_phase_06_integration.py):**
- Deploy via Backstage → ArgoCD sync → pod Running: under 3 minutes
- Non-compliant service blocked by Kyverno
- Exec into pod → Falco alert within 10 seconds
- Falco alert in Grafana within 60 seconds
- OTel traces in Grafana within 30 seconds
- kubectl edit detected by ArgoCD within sync interval
- Full demo runbook executes without errors

**Completion Promise:** `<promise>PHASE6_DONE</promise>`

**Commits:** 2 (Integration fixes; Demo runbook)
