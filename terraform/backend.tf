# S3 backend for Terraform state with DynamoDB locking
terraform {
  backend "s3" {
    bucket         = "REPLACE-terraform-state"
    key            = "fastapi-oidc/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
