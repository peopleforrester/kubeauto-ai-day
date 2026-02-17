# ABOUTME: AWS Secrets Manager secrets for ESO (External Secrets Operator) testing.
# ABOUTME: Creates test secret used in Phase 3 to validate ESO sync from AWS SM to K8s.

resource "aws_secretsmanager_secret" "test_secret" {
  name                    = "kubeauto/test-secret"
  description             = "Test secret for ESO validation in Phase 3"
  recovery_window_in_days = 0 # Demo: allow immediate deletion

  tags = {
    Component = "external-secrets"
    Phase     = "3"
  }
}

resource "aws_secretsmanager_secret_version" "test_secret" {
  secret_id = aws_secretsmanager_secret.test_secret.id
  secret_string = jsonencode({
    username = "admin"
    password = "testpass123"
  })
}
