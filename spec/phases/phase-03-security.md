# Phase 3: Security Stack (Budget: 120 min)

**Goal:** Kyverno policies enforcing, Falco detecting runtime threats, ESO pulling secrets from AWS Secrets Manager, RBAC locked down.

**Inputs:** ArgoCD-managed cluster from Phase 2.

**Pre-Checklist:**
- AWS Secrets Manager test secret created manually before starting

**Outputs:**
- Kyverno 1.17+ installed via ArgoCD Application
- Kyverno policies (enforce in `apps` only, all system NS excluded): require-labels, restrict-registries, require-resource-limits, disallow-privileged, require-probes, require-network-policies
- Falco (CNCF Graduated, eBPF driver) installed with custom EKS-aware rules via ArgoCD
- Falcosidekick forwarding to Prometheus
- External Secrets Operator installed via ArgoCD
- ExternalSecret pulling from AWS Secrets Manager via Pod Identity
- RBAC: demo-cluster-admin (cluster-admin equivalent), app-developer (apps NS only), app-viewer (read-only)
- Default-deny NetworkPolicies in apps namespace

**Test Criteria (tests/test_phase_03_security.py):**
- Kyverno pods are Running
- Policy: pod without resource limits is BLOCKED in apps
- Policy: pod from unauthorized registry is BLOCKED in apps
- Policy: privileged pod is BLOCKED in apps
- Falco pods Running on each node (DaemonSet)
- Falco: exec into pod triggers alert
- ESO: ExternalSecret shows SecretSynced
- ESO: K8s Secret matches AWS SM value
- RBAC: SA in apps cannot list secrets in platform
- NetworkPolicy: cross-namespace traffic blocked

**Completion Promise:** `<promise>PHASE3_DONE</promise>`

**Known Risk:** IAM role trust policies for Pod Identity, Kyverno policy interactions, Falco custom rules matching EKS syscall patterns.

**ADRs:** ADR-003 (Policy Engine: Kyverno), ADR-003b (Runtime Security: Falco), ADR-004 (Secret Management: ESO)
**Commits:** 5 (Kyverno; Falco; ESO; RBAC; NetworkPolicies)
