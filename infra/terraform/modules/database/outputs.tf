output "rds_endpoint" {
  value = try(aws_db_instance.postgres[0].address, null)
}

output "rds_port" {
  value = try(aws_db_instance.postgres[0].port, null)
}

output "db_name" {
  value = var.db_name
}

output "db_username" {
  value = var.db_username
}

output "connection_hint" {
  description = "Local docker-compose Postgres hint when RDS is disabled"
  value = var.enable_rds ? {
    host = try(aws_db_instance.postgres[0].address, null)
    port = try(aws_db_instance.postgres[0].port, 5432)
    db   = var.db_name
    user = var.db_username
    } : {
    host = "localhost"
    port = 5432
    db   = var.db_name
    user = var.db_username
    note = "Use docker compose postgres; set enable_rds=true for AWS RDS"
  }
}
