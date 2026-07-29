terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# Local environment: no cloud resources by default (enable_cloud=false).
provider "aws" {
  region                      = var.aws_region
  skip_credentials_validation = !var.enable_cloud
  skip_requesting_account_id  = !var.enable_cloud
  skip_metadata_api_check     = !var.enable_cloud

  # Dummy keys keep terraform validate working offline when enable_cloud=false.
  access_key = var.enable_cloud ? null : "local"
  secret_key = var.enable_cloud ? null : "local"
}

module "network" {
  source = "../../modules/network"

  name_prefix    = var.name_prefix
  cidr_block     = var.cidr_block
  enable_aws_vpc = var.enable_cloud
  tags           = var.tags
}

module "database" {
  source = "../../modules/database"

  name_prefix             = var.name_prefix
  enable_rds              = var.enable_cloud
  create_random_password  = var.enable_cloud
  db_name                 = var.db_name
  db_username             = var.db_username
  tags                    = var.tags
}

output "enable_cloud" {
  value = var.enable_cloud
}

output "network" {
  value = module.network.network_summary
}

output "database_connection_hint" {
  value = module.database.connection_hint
}

output "local_stack_hints" {
  description = "How to reach AISOC services via docker-compose locally"
  value = {
    api       = "http://localhost:8000"
    frontend  = "http://localhost:3000"
    mcp       = "http://localhost:8100"
    postgres  = "postgresql://aisoc:aisoc_secret@localhost:5432/aisoc"
    redis     = "redis://localhost:6379/0"
    qdrant    = "http://localhost:6333"
    grafana   = "http://localhost:3002"
    prometheus = "http://localhost:9090"
  }
}
