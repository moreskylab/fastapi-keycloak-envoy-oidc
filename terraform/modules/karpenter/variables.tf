variable "cluster_name" { type = string }
variable "cluster_endpoint" { type = string }
variable "node_iam_role_arn" { type = string }
variable "subnet_ids" { type = list(string) }
variable "security_group_ids" { type = list(string) }
variable "tags" { type = map(string) }
