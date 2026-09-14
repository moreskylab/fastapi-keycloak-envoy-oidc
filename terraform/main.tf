# =============================================================================
# Root Terraform Module — Zero Trust OIDC Platform on EKS
# =============================================================================

provider "aws" {
  region = var.region

  default_tags {
    tags = merge(var.tags, {
      Environment = var.environment
    })
  }
}

data "aws_availability_zones" "available" {
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

locals {
  cluster_name = "${var.cluster_name}-${var.environment}"
  azs          = slice(data.aws_availability_zones.available.names, 0, 3)
}

# ── VPC ──
module "vpc" {
  source = "./modules/vpc"

  name        = local.cluster_name
  cidr        = var.vpc_cidr
  azs         = local.azs
  environment = var.environment
  tags        = var.tags
}

# ── EKS ──
module "eks" {
  source = "./modules/eks"

  cluster_name    = local.cluster_name
  cluster_version = var.cluster_version
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids
  environment     = var.environment
  tags            = var.tags
}

# ── Karpenter ──
module "karpenter" {
  source = "./modules/karpenter"

  cluster_name       = module.eks.cluster_name
  cluster_endpoint   = module.eks.cluster_endpoint
  node_iam_role_arn  = module.eks.node_iam_role_arn
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [module.eks.node_security_group_id]
  tags               = var.tags
}

# ── Cilium CNI ──
module "cilium" {
  source = "./modules/cilium"

  eks_endpoint     = module.eks.cluster_endpoint
  cluster_name     = module.eks.cluster_name
  tags             = var.tags
}

# ── IRSA Roles ──
module "irsa" {
  source = "./modules/irsa"

  cluster_name      = module.eks.cluster_name
  oidc_provider_arn = module.eks.oidc_provider_arn
  oidc_provider_url = module.eks.oidc_provider_url
  tags              = var.tags
}
