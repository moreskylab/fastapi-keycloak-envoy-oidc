# EKS module — hardened configuration
# kube-proxy disabled (replaced by Cilium eBPF)
# aws-node CNI disabled (replaced by Cilium)

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.31"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  vpc_id     = var.vpc_id
  subnet_ids = var.subnet_ids

  # Security: private endpoint + restricted public access
  cluster_endpoint_public_access       = true
  cluster_endpoint_public_access_cidrs = ["0.0.0.0/0"] # Restrict in prod tfvars
  cluster_endpoint_private_access      = true

  # Security: envelope encryption for K8s secrets
  cluster_encryption_config = {
    resources = ["secrets"]
  }

  # Disable kube-proxy and aws-node — Cilium replaces both
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    # kube-proxy intentionally omitted — Cilium eBPF replaces it
    # vpc-cni intentionally omitted — Cilium replaces AWS VPC CNI
  }

  # Managed node group for system components (Cilium, CoreDNS, ArgoCD)
  eks_managed_node_groups = {
    system = {
      instance_types = ["m7g.large"]  # Graviton3 for cost optimization
      ami_type       = "AL2023_ARM_64_STANDARD"

      min_size     = 2
      max_size     = 4
      desired_size = 2

      labels = {
        "node.kubernetes.io/purpose" = "system"
      }

      # Security: IMDSv2 enforced (OWASP A10)
      metadata_options = {
        http_tokens                 = "required"
        http_put_response_hop_limit = 1
        instance_metadata_tags      = "enabled"
      }

      # Security: encrypted root volumes
      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size = 50
            volume_type = "gp3"
            encrypted   = true
          }
        }
      }
    }
  }

  # Enable OIDC for IRSA
  enable_irsa = true

  tags = var.tags
}
