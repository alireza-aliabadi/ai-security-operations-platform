variable "name_prefix" {
  type    = string
  default = "aisoc"
}

variable "enable_rds" {
  description = "When true, create aws_db_instance (requires AWS provider)"
  type        = bool
  default     = false
}

variable "create_random_password" {
  description = "Generate a random DB password (even when RDS is disabled)"
  type        = bool
  default     = false
}

variable "db_password" {
  description = "Static password used when create_random_password=false"
  type        = string
  default     = "aisoc_secret"
  sensitive   = true
}

variable "db_name" {
  type    = string
  default = "aisoc"
}

variable "db_username" {
  type    = string
  default = "aisoc"
}

variable "engine_version" {
  type    = string
  default = "16.4"
}

variable "instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "allocated_storage" {
  type    = number
  default = 20
}

variable "vpc_security_group_ids" {
  type    = list(string)
  default = []
}

variable "db_subnet_group_name" {
  type    = string
  default = null
}

variable "tags" {
  type    = map(string)
  default = {}
}
