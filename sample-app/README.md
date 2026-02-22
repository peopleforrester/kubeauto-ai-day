# Sample App

A minimal Python Flask application used as the IDP's reference workload.

## What It Does

Three HTTP endpoints:
- `GET /` — Returns platform info JSON
- `GET /health` — Liveness probe endpoint
- `GET /ready` — Readiness probe endpoint

## OpenTelemetry Instrumentation

The app is auto-instrumented via the `opentelemetry-instrument` wrapper.
No code changes are needed — the OTel SDK injects tracing and metrics
automatically at startup via the Kubernetes `Instrumentation` CRD.

Traces flow: App → OTel Collector → Tempo → Grafana.

## Directory Structure

```
src/
  app.py               # Flask application (3 endpoints)
  requirements.txt     # Flask + gunicorn
Dockerfile             # Container image build
catalog-info.yaml      # Backstage catalog entity
k8s/
  deployment.yaml      # Kubernetes Deployment (Kyverno-compliant)
  service.yaml         # ClusterIP Service
```

## Kyverno Compliance

The Deployment includes all fields required by the platform's Kyverno policies:
- `app.kubernetes.io/name` and `app.kubernetes.io/version` labels
- CPU and memory resource limits
- Liveness and readiness probes
- Non-privileged container

## Building

```bash
docker build -t sample-app:latest .
```

The image is deployed to the `apps` namespace via ArgoCD (`gitops/apps/sample-app.yaml`).

## Extending

To add your own app to the platform:
1. Use the Backstage "Deploy Service" template, or
2. Copy this directory, update the image/port, and add an ArgoCD Application manifest
