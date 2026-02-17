# ADR-003b: Runtime Security Tool

## Status

Accepted

## Context

The IDP needs runtime threat detection to observe syscall-level activity
inside containers. This complements Kyverno (admission-time blocking) and
NetworkPolicies (network-level blocking) with after-the-fact detection of
malicious behavior like shell spawning, credential file reads, and
unexpected network connections.

## Decision

Use **Falco** (CNCF Graduated, February 2024) with the **modern_ebpf**
driver for runtime threat detection on EKS.

Deploy as a DaemonSet (one pod per node) to observe all syscalls across the
cluster. Forward alerts to Prometheus via Falcosidekick for Grafana
dashboards.

## Alternatives Considered

| Tool | Reason for Rejection |
|------|---------------------|
| Tetragon | eBPF-native but smaller ecosystem, fewer pre-built rules |
| Sysdig Secure | Commercial product, not OSS |
| KubeArmor | LSM-based, less mature on EKS |

## Consequences

- Falco DaemonSet consumes resources on every node (~100m CPU, 256Mi per pod)
- modern_ebpf driver uses CO-RE, no kernel headers needed on EKS
- Custom rules scoped to apps namespace to reduce false positives
- Falcosidekick deployed separately to forward events to Prometheus
- Detection only — Falco does not block actions, it alerts on them
