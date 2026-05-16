# ADR-000: Domain Name for Platform Ingresses

## Status

Accepted

## Context

The IDP platform needs a domain name for TLS-secured ingresses (ArgoCD, Backstage,
Grafana, sample app). The domain must have a Route53 hosted zone for cert-manager
DNS-01 validation with Let's Encrypt.

The platform is being built for a KubeAuto Day Europe 2026 talk. Ideally the
final domain would be under kodekloud.com, but we need a working domain during
the build phase.

## Decision

Use `kubeauto.<personal-domain>` as the build-time domain — a domain the build
operator already controls and has a Route53 hosted zone for. The original build
used the author's personal domain; forks should substitute their own.

Platform ingress subdomains:
- `argocd.kubeauto.<personal-domain>`
- `backstage.kubeauto.<personal-domain>`
- `grafana.kubeauto.<personal-domain>`
- `app.kubeauto.<personal-domain>`

If KodeKloud provides a subdomain (e.g., `kubeauto.kodekloud.com`), update the
ingress annotations and cert-manager config at that time. This is a
configuration-only change — no architectural impact.

## Consequences

- Build can proceed immediately without waiting for KodeKloud team
- Domain switch later requires updating: ingress hosts, cert-manager Certificates,
  OAuth callback URLs, Backstage app-config baseUrl
- All domain references should be parameterized in Terraform/Helm values to make
  the switch straightforward

## Alternatives Considered

- **Wait for KodeKloud subdomain:** Blocks Phase 7 until external team responds.
  Rejected because build timeline is tight.
- **Use nip.io or sslip.io:** Free wildcard DNS for IP-based domains. Rejected
  because Let's Encrypt rate-limits these domains and they look unprofessional.
- **Use a new domain:** Unnecessary cost and setup when an existing domain works.
