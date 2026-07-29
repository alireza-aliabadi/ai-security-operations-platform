# AISOC Terraform

Placeholder infrastructure modules for local development and future AWS environments.

## Layout

- `modules/network` — VPC-shaped locals; optional `aws_vpc` (`enable_aws_vpc`, default off)
- `modules/database` — optional RDS Postgres (`enable_rds`, default off) + optional `random_password`
- `environments/local` — wires modules with `enable_cloud=false` and prints docker-compose connection hints

## Local usage

```bash
cd infra/terraform/environments/local
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
```

With `enable_cloud=false` (default), no AWS resources are created. Outputs still describe:

- Planned subnet CIDRs
- Local Postgres / Redis / Qdrant / API URLs matching `docker-compose.yml`

## Cloud (stub)

Set `enable_cloud = true` in `terraform.tfvars` and configure real AWS credentials to materialize VPC + RDS placeholders. Review security groups, subnet groups, and secrets before applying.
