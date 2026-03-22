---
name: Bug Report
about: Report a bug in the KubeAuto Day IDP
title: "[Bug] "
labels: bug
assignees: ''
---

## Describe the Bug

A clear and concise description of the issue.

## To Reproduce

1. Which phase/component is affected?
2. What command or action triggered the bug?
3. What did you expect to happen?
4. What actually happened?

## Environment

- **EKS cluster version:** (e.g., 1.34)
- **AWS region:** (e.g., us-west-2)
- **Terraform version:** (e.g., 1.x)
- **Helm version:** (e.g., 3.x)
- **kubectl version:** (e.g., 1.34)

## Relevant Logs

```
Paste relevant logs here (kubectl logs, terraform output, ArgoCD sync errors, etc.)
```

## Additional Context

- Have you followed the setup steps in `docs/SETUP.md`?
- Is the EKS cluster reachable? (`kubectl get nodes`)
- Are all ArgoCD applications synced? (`kubectl get applications -n argocd`)
