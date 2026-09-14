variable "name" { type = string }
variable "cidr" { type = string }
variable "azs" { type = list(string) }
variable "environment" { type = string }
variable "tags" { type = map(string) }
