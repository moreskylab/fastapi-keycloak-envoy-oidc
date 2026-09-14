# Cilium CNI — Helm release with production-hardened configuration
resource "helm_release" "cilium" {
  name       = "cilium"
  repository = "https://helm.cilium.io/"
  chart      = "cilium"
  version    = "1.17.0"
  namespace  = "kube-system"

  values = [yamlencode({
    kubeProxyReplacement = true
    k8sServiceHost       = var.eks_endpoint
    k8sServicePort       = 443

    encryption = {
      enabled        = true
      type           = "wireguard"
      nodeEncryption = true
    }

    authentication = {
      mutual = {
        spiffe = {
          enabled     = true
          installCRDs = true
        }
      }
    }

    policyEnforcementMode = "always"
    hostFirewall = {
      enabled = true
    }

    hubble = {
      enabled = true
      relay   = { enabled = true }
      ui      = { enabled = true }
      metrics = {
        enabled = [
          "dns", "drop", "tcp", "flow", "icmp",
          "httpV2:exemplars=true;labelsContext=source_ip,source_namespace,destination_ip,destination_namespace"
        ]
        dashboards = {
          enabled   = true
          namespace = "observability"
        }
      }
    }

    resources = {
      requests = { cpu = "100m", memory = "128Mi" }
      limits   = { cpu = "500m", memory = "512Mi" }
    }

    eni   = { enabled = true }
    ipam  = { mode = "eni" }
    bandwidthManager = { enabled = true }
  })]
}
