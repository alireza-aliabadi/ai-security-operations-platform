variable "name_prefix" {
  description = "Prefix for network resource names"
  type        = string
  default     = "aisoc"
}

variable "cidr_block" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.40.0.0/16"
}

variable "availability_zones" {
  description = "AZs used to derive placeholder subnet CIDRs"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "enable_aws_vpc" {
  description = "When true, create a real aws_vpc (requires AWS provider credentials)"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Extra tags"
  type        = map(string)
  default     = {}
}
