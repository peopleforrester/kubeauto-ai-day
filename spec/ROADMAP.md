# Phases 8–16 Roadmap: AI-Native, Identity-First, Self-Service IDP

<!-- ABOUTME: Forward-looking roadmap for phases 8–16 — AI/Agent Gateway, workload identity,
     ABOUTME: human SSO, secrets vault, supply chain, progressive delivery, service mesh. -->

**Status:** Active roadmap. Supersedes any earlier informal Phase 8+ notes.
**Scope:** Phases 8–16 only. Phases 0–7 are complete (see [BUILD-SPEC.md](BUILD-SPEC.md)
and [SCORECARD.md](SCORECARD.md)).
**Locks in:** confirmed additions (Phases 8, 13, 14, 15, 16).
**Drops:** multi-cluster federation. Out of scope.

---

## Updated final ranking (supersedes any earlier TL;DR)

Build phases in this order. Bold = confirmed.

1. **Phase 8 — AI/Agent Gateway + Agent Runtime** (kgateway + agentgateway + kagent). *Confirmed.* Single biggest 2026 differentiator.
2. **Phase 13 — Workload Identity** (SPIFFE/SPIRE + cert-manager-csi-driver-spiffe). *Confirmed.* The trust foundation that makes Phase 8 actually safe.
3. **Phase 14 — Human Identity & Self-Service Access** (Dex + kubelogin + Backstage JIT scaffolder). *Confirmed.* Federated SSO without commercial vendors.
4. **Phase 15 — Secrets Vault** (OpenBao + ESO integration). *Confirmed.* SPIFFE-authenticated dynamic secrets; cluster-portable secrets-of-record.
5. **Phase 9 — LLM Inference Stack** (KServe + llm-d + vLLM). Required if claiming "AI-native."
6. **Phase 10 — Platform Self-Service Layer** (Crossplane + Score + KEDA + Argo Workflows/Events).
7. **Phase 11 — Supply-Chain + Runtime Hardening** (Sigstore/cosign + Kyverno verify-images + Trivy + Tetragon).
8. **Phase 16 — Service Mesh** (Cilium Service Mesh recommended, Istio Ambient as alternative). *Confirmed addition.*
9. **Phase 12 — Progressive Delivery, FinOps, Stateful Workloads** (Argo Rollouts + OpenFeature/Flipt + OpenCost + CloudNativePG).

**Dropped from the roadmap:** multi-cluster federation (Karmada, Open Cluster Management, Cilium Cluster Mesh).

---

## Phase 8 — AI/Agent Gateway + Agent Runtime

Single biggest 2026 differentiator. See `spec/phases/phase-08-*.md` when authored.

Stack: kgateway (north-south gateway), agentgateway (agent-aware proxy with MCP awareness), kagent (CRD-driven agent runtime).

---

## Phase 13 — Workload Identity (SPIFFE/SPIRE)

**Verdict:** Confirmed. The single most important security addition once Phase 8 lands.

### Why this phase exists

Phase 8 (Agent Gateway) introduces agents and MCP servers as first-class workloads. Without verifiable workload identity, every agent → MCP, agent → agent, and agent → LLM-provider call relies on bearer tokens — which are forgeable, long-lived, and prone to leakage. This is exactly the "Shadow MCP" pattern OWASP MCP Top 10 flagged at KubeCon EU 2026.

Kubernetes ServiceAccount tokens solve cluster-internal RBAC. They do not federate, they do not attest workload identity at the kernel level, and they do not give downstream systems a verifiable identity document.

SPIFFE solves this with short-lived X.509 SVIDs (Secure Verifiable Identity Documents) and JWT-SVIDs, both backed by workload attestation tied to the runtime (Kubernetes labels, container image hashes, kernel-verified PID lineage). Federation across trust domains is built into the spec.

### Recommended stack

| Component | CNCF status (May 2026) | Role |
|---|---|---|
| **SPIRE Server** | **CNCF Graduated** (SPIFFE/SPIRE graduated 2022) | Issues SVIDs. One per trust domain (typically one per cluster, or one per logical environment). |
| **SPIRE Agent** | CNCF Graduated | DaemonSet on every node. Attests workloads via Kubernetes Workload Attestor and Unix Workload Attestor. Caches SVIDs and serves them to workloads via Unix domain socket. |
| **cert-manager-csi-driver-spiffe** | jetstack/spiffe (community) | CSI driver that injects X.509 SVIDs into pods as TLS certificates. Bridges SPIFFE to cert-manager-native consumers. |
| **SPIRE OIDC Discovery Provider** | Part of SPIRE | Exposes JWT-SVIDs as OIDC tokens for AWS/GCP/Azure IAM trust relationships. Replaces IRSA with a cluster-portable pattern. |

### What it integrates with

**Phase 8 (Agent Gateway):**
- `kgateway` TLSPolicy can require client SVIDs for upstream backends.
- `agentgateway` validates inbound SVIDs as alternative to JWT bearer tokens.
- Every MCP call carries a non-forgeable identity in mTLS — audit logs gain per-workload attribution.

**Phase 9 (LLM Inference):**
- KServe `InferenceService` pods get SVIDs at startup.
- vLLM-backed `LLMInferenceService` authenticates to OpenBao (Phase 15) via JWT-SVID to fetch model weights without static credentials.

**Phase 11 (Supply Chain + Runtime):**
- Tetragon `TracingPolicy` can match on SPIFFE identity for kernel-level enforcement: "kill any process in workload `spiffe://acme.org/ns/agents/sa/research-agent` that exec()s a shell".
- Sigstore signing identities can be SPIFFE-rooted (keyless signing tied to workload identity, not just CI OIDC).

**Phase 4 (Observability):**
- Every audit log entry includes SPIFFE ID.
- Per-agent attribution becomes trivial: Loki query `{spiffe_id=~"spiffe://acme.org/ns/agents/.*"} |= "tool_call"`.

**Phase 16 (Service Mesh):**
- Cilium and Istio Ambient both natively consume SPIFFE SVIDs for mTLS identity.
- AuthorizationPolicy / CiliumNetworkPolicy can match on `principal: "spiffe://..."` instead of namespace selectors.

### EKS + kubeadm federation pattern

Each cluster runs its own SPIRE Server in its own trust domain (`spiffe://eks.acme.org`, `spiffe://kubeadm.acme.org`). Cross-cluster authentication uses **SPIFFE Trust Domain Federation**: each SPIRE Server publishes its trust bundle via a federation endpoint, peers consume it, and workloads in either cluster can authenticate to services in the other without shared secrets.

Operational, not theoretical — Bloomberg, Square, Pinterest, ByteDance, Uber, and Netflix run this at scale.

### Adoption signal

Production-proven at: Bloomberg, Square, Pinterest, ByteDance, Uber, Netflix. GitHub Actions OIDC issuer is essentially a SPIFFE-shaped pattern. Cosign keyless signing uses Fulcio which is SPIFFE-aligned. Istio's identity model is SPIFFE-compatible. Cilium's identity model is SPIFFE-compatible.

### Multi-cluster complexity

Medium. Bootstrapping SPIRE Servers requires care (trust bundle distribution, attestation policy authoring), but the patterns are mature and well-documented. The SPIRE Helm charts are good. Plan ~1 week for first integration, days for subsequent clusters.

### Workshop components

- `phase-13-workload-identity/spire-server/` — SPIRE Server StatefulSet + ConfigMap with attestation policy
- `phase-13-workload-identity/spire-agent/` — DaemonSet with K8s Workload Attestor
- `phase-13-workload-identity/csi-driver-spiffe/` — CSI driver + sample workload mounting an SVID
- `phase-13-workload-identity/oidc-discovery/` — SPIRE OIDC Discovery Provider + IAM trust policy example
- `phase-13-workload-identity/federation/` — Trust Domain Federation demo between EKS and kubeadm clusters
- `phase-13-workload-identity/kyverno-policies/` — Kyverno policy requiring every pod in `agents` namespace to have a SPIRE registration entry

---

## Phase 14 — Human Identity & Self-Service Access (Dex)

**Verdict:** Confirmed. Federated SSO is the minimum viable enterprise-realistic story.

### Why this phase exists

Today there is no human-identity story beyond cloud IAM. Developers access ArgoCD via what? kubectl via long-lived service account tokens? Backstage with no auth? This is the most common gap in DIY platforms.

The CNCF-native answer is OIDC federation. Bridge from a corporate IdP (GitHub, Okta, Azure AD, Google Workspace) into every platform component, give developers short-lived tokens, and use group membership for authorization.

### Dex vs. Keycloak — pick one

| | **Dex** | **Keycloak** |
|---|---|---|
| CNCF status | Sandbox | Incubating (joined late 2023) |
| Footprint | ~50MB binary, no DB required | JVM, requires PostgreSQL |
| Philosophy | Federation broker | Full IdP with own user store |
| MFA | Via upstream IdP | Built-in TOTP, WebAuthn, etc. |
| SAML | OIDC-first; SAML 2.0 supported | Native SAML, OIDC, more |
| User store | None (federation-only) | Built-in + LDAP federation |
| When to pick | Users live in GitHub/Okta/Azure AD already | Need own user store; legacy SAML apps |

**Recommendation for the workshop: Dex.** Lighter footprint, no PostgreSQL operational burden, pairs cleanly with GitHub as upstream IdP for an open-source workshop. Document Keycloak as the "if you need a full IdP" alternative.

### Recommended stack

- **Dex** as the OIDC broker, federating GitHub (workshop) or Okta/Azure AD (enterprise) as upstream
- **`kubelogin`** (sigs.k8s.io/kubelogin or `kubectl-oidc-login`) for short-lived OIDC tokens against the Kubernetes API
- **OAuth2 Proxy** as the per-app authenticator for components that do not speak OIDC natively
- **Kyverno** policies enforcing group-based RBAC

### Federation targets (everything consumes Dex)

- **Kubernetes API server**: `--oidc-issuer-url=https://dex.acme.org`, group claim → ClusterRoleBinding
- **ArgoCD**: OIDC config block in `argocd-cm`, group → AppProject roles
- **Backstage**: GitHub provider can pass-through to Dex, or direct OIDC integration
- **Grafana**: built-in OIDC support
- **Loki + Mimir + Tempo**: via Grafana proxy or OAuth2 Proxy
- **kgateway (Phase 8)**: kgateway's OIDC policy validates Dex JWTs at the ingress

### JIT elevation pattern (the self-service piece)

The real self-service value is not "log in via SSO" — it is **time-bounded privilege escalation through a Backstage form**:

1. Developer fills Backstage scaffolder form: *"I need `edit` in namespace `team-a-prod` for 2 hours to debug an incident"*
2. Scaffolder validates against Kyverno policy (right group? right namespace? within max-duration?)
3. Generates a `RoleBinding` with annotation `ttl.acme.org/expires-at: 2026-05-16T14:30:00Z`
4. A small TTL controller (custom or a CronJob with `kubectl`) reaps expired bindings
5. Audit log entry in Loki: `{spiffe_id=..., dex_user=..., dex_groups=...} requested elevated_access for namespace=team-a-prod`

No commercial vendor required. The components are: Backstage (Phase 5), Kyverno (Phase 3), Dex (Phase 14), Loki (Phase 4).

### What it integrates with

**Phase 5 (Backstage):** Backstage SSO via Dex; scaffolder templates that emit Dex OIDC client manifests for new apps.
**Phase 10 (Self-Service Platform):** Crossplane Composition that bundles "new app" = Dex OIDC client + Kyverno policy + Backstage entity + RoleBinding template.
**Phase 13 (SPIFFE):** Humans get OIDC tokens; workloads get SVIDs. Cross-references in audit logs.
**Phase 15 (OpenBao):** OpenBao auth via Dex OIDC for humans; OpenBao auth via SPIFFE JWT for workloads.
**Phase 16 (Service Mesh):** Service-to-service authz can reference Dex group claims forwarded via headers.

### Adoption signal

Dex in production at: Mojang/Minecraft (Microsoft), Pusher, LightStep, eBay, RedHat OpenShift's identity broker. Pinterest published a detailed account of their Dex-based JIT access platform in 2024. Keycloak is the more enterprise-common choice — used at every large company that runs its own IdP.

### Multi-cluster complexity

Low. Dex is single-instance, multi-cluster-friendly (one Dex serves N clusters). Each cluster's API server points at the same Dex issuer. Token introspection is stateless.

### Workshop components

- `phase-14-human-identity/dex/` — Dex Helm chart + GitHub upstream config
- `phase-14-human-identity/kubelogin/` — kubectl plugin install instructions + sample kubeconfig
- `phase-14-human-identity/argocd-oidc/` — ArgoCD ConfigMap with Dex integration
- `phase-14-human-identity/backstage-auth/` — Backstage app-config.yaml Dex provider block
- `phase-14-human-identity/grafana-oidc/` — Grafana values.yaml OIDC config
- `phase-14-human-identity/jit-scaffolder/` — Backstage scaffolder template that emits TTL'd RoleBindings
- `phase-14-human-identity/ttl-controller/` — minimal Go controller (or Kyverno CleanupPolicy) that reaps expired bindings

---

## Phase 15 — Secrets Vault (OpenBao)

**Verdict:** Confirmed. The SPIFFE + OpenBao pairing is the standout pattern for 2026.

### Why this phase exists

External Secrets Operator (Phase 3) is excellent — but ESO is a sync mechanism, not a secrets store. Today it pulls from AWS Secrets Manager. The gaps:

- **Cluster-portability:** AWS Secrets Manager does not exist on kubeadm. The platform is non-portable.
- **Dynamic secrets:** AWS Secrets Manager stores static credentials. Modern platforms mint short-lived per-request credentials (database creds valid for 1 hour, signed JWTs, ephemeral S3 access).
- **PKI engine:** cert-manager needs a CA. Currently self-signed or Let's Encrypt. A real platform has its own internal CA.
- **Encryption-as-a-service:** Apps that need to encrypt PII should not manage keys themselves.

**Vault would solve all this — but Vault went BUSL in 2023.** No longer open-source. OpenBao is the Linux Foundation fork from before the license change, Apache 2.0, with a real community.

### Recommended stack

- **OpenBao** as secrets-of-record outside Kubernetes
- **ESO with OpenBao backend** — already-installed ESO syncs from OpenBao into K8s Secrets
- **OpenBao PKI engine** as a cert-manager ClusterIssuer (replaces self-signed CA for internal mTLS)
- **OpenBao auth methods:** `jwt` for workload auth via SPIFFE JWT-SVIDs, `oidc` for human auth via Dex
- **OpenBao Transit engine** for app-level encrypt-as-a-service
- **OpenBao database secrets engine** for dynamic Postgres/MySQL credentials

### The killer pattern: SPIFFE + OpenBao

Genuinely novel for 2026 and worth highlighting:

1. Agent pod starts (Phase 8).
2. SPIRE Agent attests it, issues a JWT-SVID with audience `openbao.acme.org` (Phase 13).
3. Agent presents the JWT-SVID to OpenBao's `jwt` auth method.
4. OpenBao validates the signature against SPIRE's OIDC discovery, maps `spiffe://acme.org/ns/agents/sa/research-agent` to a policy.
5. OpenBao mints a dynamic Postgres credential valid for 1 hour.
6. Agent uses it, credential auto-expires, OpenBao revokes it.
7. Zero static secrets anywhere in the path.

Compare to the current bearer-token-everywhere AI architecture. This is what "AI-native identity-first platform" actually means.

### What it integrates with

**Phase 3 (Security/ESO):** ESO's OpenBao backend replaces (or runs alongside) the AWS Secrets Manager backend.
**Phase 7 (Hardening/cert-manager):** OpenBao PKI engine as ClusterIssuer; internal mTLS rooted in your own CA.
**Phase 8 (Agent Gateway):** kgateway secrets policies pull from OpenBao.
**Phase 9 (LLM Inference):** KServe model storage credentials minted dynamically by OpenBao.
**Phase 13 (SPIFFE):** Workload auth to OpenBao via JWT-SVID.
**Phase 14 (Dex):** Human auth to OpenBao via Dex OIDC.

### Trade-off: operational complexity

Most operationally complex addition in the roadmap. OpenBao requires:
- Raft cluster (3 or 5 nodes for HA — single-node for workshop demo only)
- Unseal key management (Shamir's Secret Sharing or KMS auto-unseal)
- Backup discipline (Raft snapshots)
- Audit log to a durable sink
- Careful policy authoring (a misconfigured wildcard policy is a real risk)

For a workshop, single-node `dev` mode is fine — clearly mark it as such. For production, the operational complexity is real and the team needs Vault/OpenBao operator experience.

### When NOT to use it

If you are EKS-only and AWS Secrets Manager + IRSA already meets your needs, the marginal value of OpenBao is the dynamic-secrets and PKI capabilities. If workloads are mostly long-running services with rarely-rotating credentials, the operational overhead may exceed the benefit.

This workshop's case: **confirmed worth doing** because it targets multi-cluster (EKS + kubeadm) and demonstrates AI-native patterns where dynamic per-request secrets matter.

### Adoption signal

OpenBao was donated to Linux Foundation Edge in December 2023, became a top-level LF project mid-2024. Contributors from IBM, Hashicorp alumni, GitLab, OctoPerf. GitLab Cloud Connector uses OpenBao. Production adoption is smaller than Vault's but real. The fork has not stalled — releases are roughly monthly, feature parity with Vault 1.13-1.14 with active work on newer features.

### Multi-cluster complexity

Medium. One OpenBao cluster typically serves N Kubernetes clusters. Each cluster's ESO and cert-manager point at the same OpenBao endpoint. Auth methods are stateless.

### Workshop components

- `phase-15-secrets-vault/openbao/` — OpenBao Helm chart in `ha` mode with Raft backend
- `phase-15-secrets-vault/auth-methods/` — JWT auth method config (for SPIFFE), OIDC auth method config (for Dex)
- `phase-15-secrets-vault/secrets-engines/` — KV v2, Database (Postgres dynamic creds), PKI engine
- `phase-15-secrets-vault/eso-integration/` — ExternalSecret resources sourcing from OpenBao
- `phase-15-secrets-vault/cert-manager-issuer/` — Vault Issuer using OpenBao PKI engine
- `phase-15-secrets-vault/policies/` — OpenBao policies mapping SPIFFE IDs to permitted paths
- `phase-15-secrets-vault/demo/` — agent pod that fetches dynamic Postgres creds via SPIFFE JWT, demonstrates auto-rotation

---

## Phase 16 — Service Mesh (Cilium recommended, Istio Ambient as alternative)

**Verdict:** Add it. Cilium Service Mesh is the recommended choice for this stack; Istio Ambient is documented as the alternative for teams that need richer L7 policy.

### Why this phase exists

North-south traffic management is covered by kgateway (Phase 8). East-west is not: service-to-service mTLS, identity-aware authorization between workloads, traffic split for canaries, cross-cluster service discovery. A mesh fills that gap.

**Do not add a mesh just because.** Add it because:
- Agents (Phase 8) talk to MCP servers, inference services (Phase 9), and other agents across namespaces — those calls need mTLS and identity-aware authz.
- Argo Rollouts (Phase 12) needs traffic splitting at the service layer.
- SPIFFE (Phase 13) gives every workload an identity; the mesh is what consumes it for E-W authorization.
- Cross-cluster service-to-service traffic (EKS ↔ kubeadm) without VPN.

If a platform is mostly N-S (agent calls external LLM via kgateway, done), it may not need a mesh at all. But once Phase 8 + Phase 9 + Phase 13 land, the E-W story matters.

### The 2026 mesh landscape

| Mesh | CNCF status | Architecture | Strength | Weakness |
|---|---|---|---|---|
| **Cilium Service Mesh** | Graduated (2023) | eBPF (no sidecars, no ztunnel) | Lowest overhead, identity in CNI, Hubble observability free | L7 policy less rich than Istio |
| **Istio Ambient Mode** | Graduated | ztunnel (L4, per-node) + waypoint (L7, per-namespace) | Richest L7 policy, biggest ecosystem | Heavier control plane, two-layer mental model |
| **Linkerd** | Graduated | Rust microproxy sidecar | Operational simplicity, lowest config surface | Buoyant license-change shadow lingers; smaller ecosystem |
| **Kuma** | Sandbox | Sidecar or sidecarless | Kong-backed, multi-zone-native | Smaller community |

Skip Linkerd (license shadow) and Kuma (smaller community) for this workshop.

### Honest recommendation: Cilium Service Mesh

Reasons specific to this stack:

1. **Tetragon (Phase 11) is already Cilium** — one eBPF story, one operational model, one team (Isovalent/Cisco) behind both. Adding Istio Ambient means running two parallel data planes.
2. **kgateway handles N-S** — Cilium handles E-W with zero overlap. Istio Ambient's gateway component would compete with kgateway, forcing a "which is canonical" decision.
3. **SPIFFE integration is cleaner** — Cilium's identity model lives in the CNI itself, federates naturally with SPIRE trust bundles. Istio Ambient's identity model is also SPIFFE-compatible but layered on top of Envoy.
4. **Hubble observability is free** — gives per-flow visibility (L3/L4/L7) without adding another telemetry stack.
5. **Lower operational complexity** — single control plane (Cilium operator) vs. Istio Ambient's Istiod + ztunnel + waypoint.
6. **eBPF performance** — typical sidecar overhead 5-10ms per hop; eBPF 0.1-0.5ms.

### When to pick Istio Ambient instead

Document this honestly so the workshop teaches the trade-off:

- Need rich L7 request transformation (header manipulation, JWT claim-based routing, complex authz with CEL).
- Team already operating Istio successfully and does not want to switch.
- Need the broader ecosystem of community Envoy filters (e.g., ext_authz to a centralized policy engine, custom rate limiting).
- Need Istio's WasmPlugin extensibility model.
- Building a service mesh-of-record for a large organization (50+ services) where the feature ceiling matters more than operational simplicity.

Istio Ambient is materially better than 2024-era sidecar Istio. The ztunnel-only mode is comparable to Cilium in operational simplicity for L4 mTLS. Waypoints are opt-in per namespace, so the L7 complexity is bounded to where it is actually needed.

### Recommended stack (Cilium path)

- **Cilium CNI** with mesh features enabled (`cilium install --set envoy.enabled=true`)
- **Hubble** for observability (UI + relay + metrics)
- **CiliumNetworkPolicy** with `principal` matching SPIFFE IDs
- **CiliumEnvoyConfig** for L7 policy where needed
- **Gateway API** support for HTTPRoute (parallel to kgateway's, scoped to E-W if going that route — or just let kgateway own all Gateway API resources and Cilium handle pure E-W policy)

### Recommended stack (Istio Ambient alternative)

- **Istio** with `--set profile=ambient`
- **ztunnel** DaemonSet (L4 + mTLS)
- **Waypoint proxies** per namespace where L7 policy is needed
- **AuthorizationPolicy** with SPIFFE principal matching
- **Telemetry API** for OTel integration

### What it integrates with

**Phase 8 (Agent Gateway):** kgateway handles N-S, mesh handles E-W. Clean separation. Istio Ambient would force a decision between kgateway and Istio Gateway for N-S — Cilium has no Gateway competition so the integration is simpler.

**Phase 11 (Tetragon):** Cilium and Tetragon are sister projects; runtime enforcement (Tetragon) and network enforcement (Cilium NetworkPolicy) share the same eBPF data plane and identity model.

**Phase 12 (Progressive Delivery):** Argo Rollouts has native integrations with both Cilium (via CiliumNetworkPolicy traffic-shifting) and Istio (via VirtualService weight adjustments). Argo Rollouts community examples favor Istio historically; Cilium support is more recent but production-ready.

**Phase 13 (SPIFFE):** Both meshes consume SPIFFE SVIDs. Cilium's identity is rooted in the CNI; Istio's identity is rooted in Envoy. Federation patterns are similar.

**Phase 16 (this phase) outputs feed Phase 4 (Observability):** Hubble (Cilium) or Telemetry API (Istio) → OpenTelemetry Collector → Tempo/Loki/Prometheus.

### Adoption signal

**Cilium Service Mesh in production:** Adobe, Bell Canada, Bloomberg, Capital One, Datadog, Deutsche Telekom, GitLab, IKEA, Palantir, Plaid, Sky, Sportradar, Trip.com. The 2026 CNCF survey shows Cilium as the fastest-growing service mesh by share-of-deployments.

**Istio Ambient in production:** Salesforce, Bloomberg (yes, both), HSBC, Allianz, Spotify, eBay. Istio remains the dominant mesh by total install base. Ambient adoption is growing fast — most KubeCon EU 2026 Istio talks were Ambient-focused.

### Multi-cluster complexity

Cilium: **Low to medium.** ClusterMesh-free deployment is straightforward. Cross-cluster service discovery would require ClusterMesh, which is out of scope — so single-cluster mesh in EKS, single-cluster mesh in kubeadm, no cross-cluster E-W. Fine.

Istio Ambient: **Medium.** Single-cluster ambient is operationally simpler than sidecar Istio. Multi-cluster ambient is still maturing as of May 2026 — workable but not as polished as Cilium ClusterMesh, which is out of scope anyway.

### Workshop components (Cilium path — primary)

- `phase-16-service-mesh/cilium-mesh/` — Cilium upgrade values.yaml enabling mesh features (assumes Cilium is the CNI; if on a non-Cilium CNI, this phase requires CNI replacement, which is a separate concern)
- `phase-16-service-mesh/hubble/` — Hubble Relay + UI + ServiceMonitor
- `phase-16-service-mesh/policies/` — sample CiliumNetworkPolicy with SPIFFE principal matching
- `phase-16-service-mesh/canary/` — sample Argo Rollouts manifest using Cilium traffic-splitting
- `phase-16-service-mesh/envoy-config/` — CiliumEnvoyConfig for L7 ratelimit on agent → MCP traffic

### Workshop components (Istio Ambient path — alternative documentation)

- `phase-16-service-mesh/istio-ambient/` — Istio install profile=ambient
- `phase-16-service-mesh/ztunnel/` — ztunnel DaemonSet config
- `phase-16-service-mesh/waypoint/` — sample waypoint deployment for L7 policy
- `phase-16-service-mesh/authpolicy/` — AuthorizationPolicy with SPIFFE principal matching

Pick one path and ship it. Document the other in a `RATIONALE.md`.

---

## Updated Phase 12 (multi-cluster removed, service mesh moved to Phase 16)

Phase 12 is now just progressive delivery + FinOps + optional stateful workloads:

**Tier A (universally useful):**
- Argo Rollouts (CNCF Incubating) — progressive delivery
- OpenFeature (CNCF Incubating) + Flipt — feature flags
- OpenCost (CNCF Incubating) — cost observability, MCP-server-enabled for Phase 8 integration

**Tier B (only if stateful workloads are in scope):**
- CloudNativePG (CNCF Sandbox) — PostgreSQL operator

**Removed from Phase 12:**
- ~~Karmada / Open Cluster Management~~ — multi-cluster federation dropped
- ~~Cilium Cluster Mesh~~ — multi-cluster service mesh dropped
- ~~Service mesh discussion (Tier D)~~ — moved to Phase 16 as standalone

**Tier E (eBPF observability beyond Prometheus/Loki/Tempo):**
- Hubble (free with Phase 16 if Cilium) — keep
- Parca (CNCF Sandbox) — continuous profiling, optional
- Pixie — skip (covered already by OTel + Loki + Tempo at workshop scale)

---

## Updated "What NOT to add" list

Definitive 2026 don't-add list for an AI-native CNCF-first IDP:

- **Multi-cluster federation (Karmada, OCM)** — out of scope.
- **Cilium Cluster Mesh** — out of scope (multi-cluster dropped).
- **HashiCorp Vault** — BUSL. Use OpenBao instead (Phase 15).
- **OPA / Gatekeeper** — Kyverno is CEL-based and graduated. Do not double up.
- **Linkerd** — license-change shadow lingers; smaller ecosystem than Cilium or Istio.
- **Kuma** — smaller community; Cilium or Istio better choices.
- **Kong, Tyk, standalone API gateway products** — kgateway covers it. Not CNCF native.
- **Connaisseur** — Kyverno verify-images covers it.
- **SpiceDB / Authzed, Cerbos, Permify** — excellent but not CNCF. Architecturally heavy for marginal benefit over Kyverno + Dex groups.
- **Teleport, Pomerium, Boundary, StrongDM** — vendor OSS or commercial. JIT via Backstage scaffolder + Kyverno + Dex is the CNCF-native path (Phase 14).
- **LiteLLM** — laptop tool, not platform infrastructure (use agentgateway in Phase 8).
- **Pixie** — heavy install for marginal value over OTel/Loki/Tempo.
- **Vitess** — overkill unless specifically teaching MySQL sharding.
- **KubeEdge** — no edge use case in scope.

---

## Synthesis: the AI-native, identity-first, self-service IDP

The minimum-viable trio for "this is a 2026 platform" is:

- **Phase 8 (Agent Gateway)** — the AI plane
- **Phase 13 (SPIFFE/SPIRE)** — the identity plane
- **Phase 14 (Dex)** — the human-access plane

With those three, the platform can credibly claim AI-native and identity-first. Everything else is enrichment.

The recommended ship order:

1. **Phase 8** alone — first iteration of new workshop, single-purpose addition.
2. **Phase 13 + Phase 14 + Phase 15** together — second iteration, the identity-and-secrets bundle.
3. **Phase 11** — third iteration, supply chain hardening.
4. **Phase 16** — fourth iteration, service mesh (Cilium primary, Istio Ambient documented).
5. **Phase 9 + Phase 10** — fifth+ iterations, infrastructure depth.
6. **Phase 12** — ongoing, progressive enhancements.

Do not ship all of this as one workshop. Each phase is a 2-4 hour deep-dive on its own; bundling them dilutes the teaching value.

### Conceptual end-state

A developer logs into Backstage via corporate SSO (Phase 14, Dex) → submits a scaffolder form requesting "new agent service with Postgres and S3" → Backstage emits a Score file (Phase 10) + Crossplane Claim (Phase 10) + SPIFFE registration (Phase 13) + Dex OIDC client (Phase 14) + OpenBao policy (Phase 15) + Kyverno-validated RoleBinding + kagent Agent resource (Phase 8) + signed Helm chart (Phase 11) → ArgoCD reconciles → SPIRE issues SVID to the new pod → pod authenticates to OpenBao with its SVID → fetches dynamic Postgres credential → calls upstream MCP servers via agentgateway with mTLS rooted in SPIFFE → Cilium (Phase 16) enforces E-W authz on SPIFFE principal → Tetragon (Phase 11) attests kernel-level behavior → all telemetry flows to Loki/Tempo/Prometheus with per-SPIFFE-ID attribution.

That is the platform. The pieces compose because they all speak SPIFFE, OIDC, and Gateway API. None of them are vendor-locked, all are CNCF or Linux Foundation, all deploy via Helm + ArgoCD.

Phases 13-15 matter so much because without SPIFFE, Dex, and OpenBao, the rest of the stack reverts to bearer-token-everywhere — the 2023 architecture this roadmap is moving past.
