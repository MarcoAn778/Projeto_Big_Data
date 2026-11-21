# Reutilize o projeto da equipe e importe o servico existente se faltar no state.
# Terraform gerencia o servico; tabelas e carga ficam em Python/SQL.
resource "aiven_pg" "caged" {
  project                = var.project_name
  service_name           = var.service_name
  plan                   = var.plan
  cloud_name             = var.cloud_name
  termination_protection = var.termination_protection

  pg_user_config {
    ip_filter_string = var.allowed_cidrs
  }

  lifecycle {
    prevent_destroy = true
  }
}
