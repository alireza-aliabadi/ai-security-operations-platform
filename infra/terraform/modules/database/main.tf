# Placeholder database module — optional RDS Postgres (count=0 by default).

resource "random_password" "db" {
  count = var.create_random_password ? 1 : 0

  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

locals {
  db_password = var.create_random_password ? random_password.db[0].result : var.db_password
  tags = merge(
    {
      Project   = "aisoc"
      ManagedBy = "terraform"
      Module    = "database"
    },
    var.tags,
  )
}

resource "aws_db_instance" "postgres" {
  count = var.enable_rds ? 1 : 0

  identifier             = "${var.name_prefix}-postgres"
  engine                 = "postgres"
  engine_version         = var.engine_version
  instance_class         = var.instance_class
  allocated_storage      = var.allocated_storage
  db_name                = var.db_name
  username               = var.db_username
  password               = local.db_password
  skip_final_snapshot    = true
  publicly_accessible    = false
  vpc_security_group_ids = var.vpc_security_group_ids
  db_subnet_group_name   = var.db_subnet_group_name

  tags = local.tags
}
