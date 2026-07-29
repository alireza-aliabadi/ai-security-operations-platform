variable "enable_cloud" {
  description = "Create real AWS resources when true"
  type        = bool
  default     = false
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "name_prefix" {
  type    = string
  default = "aisoc-local"
}

variable "cidr_block" {
  type    = string
  default = "10.40.0.0/16"
}

variable "db_name" {
  type    = string
  default = "aisoc"
}

variable "db_username" {
  type    = string
  default = "aisoc"
}

variable "tags" {
  type = map(string)
  default = {
    Environment = "local"
  }
}
