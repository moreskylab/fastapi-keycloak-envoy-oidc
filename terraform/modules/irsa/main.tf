# IRSA — IAM Roles for Service Accounts
# Follows least-privilege: each workload gets only the permissions it needs.

# External Secrets Operator — read secrets from Vault
resource "aws_iam_role" "eso" {
  name = "${var.cluster_name}-eso"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = var.oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${var.oidc_provider_url}:sub" = "system:serviceaccount:external-secrets:external-secrets"
        }
      }
    }]
  })

  tags = var.tags
}

# Velero — backup and disaster recovery
resource "aws_iam_role" "velero" {
  name = "${var.cluster_name}-velero"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = var.oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${var.oidc_provider_url}:sub" = "system:serviceaccount:velero:velero"
        }
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "velero_s3" {
  name = "velero-s3"
  role = aws_iam_role.velero.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.cluster_name}-velero-backups",
          "arn:aws:s3:::${var.cluster_name}-velero-backups/*"
        ]
      }
    ]
  })
}
