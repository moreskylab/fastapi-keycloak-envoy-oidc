output "cluster_name" { value = module.eks.cluster_name }
output "cluster_endpoint" { value = module.eks.cluster_endpoint }
output "oidc_provider_arn" { value = module.eks.oidc_provider_arn }
output "oidc_provider_url" { value = module.eks.cluster_oidc_issuer_url }
output "node_iam_role_arn" { value = module.eks.eks_managed_node_groups["system"].iam_role_arn }
output "node_security_group_id" { value = module.eks.node_security_group_id }
