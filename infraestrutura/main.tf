# O projeto Aiven pertence a conta da equipe e deve existir antes do apply.
# O servico PostgreSQL e criado pelo Terraform; tabelas e carga ficam em R/SQL.
resource "aiven_pg" "caged" {
  project                = var.project_name
  service_name           = var.service_name
  plan                   = var.plan
  cloud_name             = var.cloud_name
  termination_protection = true

  pg_user_config {
    ip_filter_string = var.allowed_cidrs
  }

  lifecycle {
    prevent_destroy = true
  }
}
