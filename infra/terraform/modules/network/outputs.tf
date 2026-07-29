output "name_prefix" {
  value = local.name_prefix
}

output "cidr_block" {
  value = local.cidr_block
}

output "public_subnet_cidrs" {
  value = local.public_subnet_cidrs
}

output "private_subnet_cidrs" {
  value = local.private_subnet_cidrs
}

output "vpc_id" {
  description = "Real VPC id when enable_aws_vpc=true; otherwise null"
  value       = try(aws_vpc.this[0].id, null)
}

output "network_summary" {
  value = {
    name_prefix          = local.name_prefix
    cidr_block           = local.cidr_block
    public_subnet_cidrs  = local.public_subnet_cidrs
    private_subnet_cidrs = local.private_subnet_cidrs
    aws_vpc_enabled      = var.enable_aws_vpc
  }
}
