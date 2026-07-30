# Placeholder network module — VPC-shaped locals for local/dev.
# Real aws_vpc is optional (count=0 by default) so terraform plan works offline.

locals {
  name_prefix = var.name_prefix
  cidr_block  = var.cidr_block
  azs         = var.availability_zones

  public_subnet_cidrs = [
    for i, az in local.azs : cidrsubnet(local.cidr_block, 4, i)
  ]
  private_subnet_cidrs = [
    for i, az in local.azs : cidrsubnet(local.cidr_block, 4, i + 8)
  ]

  tags = merge(
    {
      Project   = "aisoc"
      ManagedBy = "terraform"
      Module    = "network"
    },
    var.tags,
  )
}

resource "aws_vpc" "this" {
  count = var.enable_aws_vpc ? 1 : 0

  cidr_block           = local.cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.tags, { Name = "${local.name_prefix}-vpc" })
}
