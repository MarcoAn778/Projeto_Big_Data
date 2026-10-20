# Sem URI, token ou senha nos outputs. O provider ainda grava dados sensiveis no state.
output "host" {
  description = "Host para PGHOST."
  value       = aiven_pg.caged.service_host
}

output "port" {
  description = "Porta para PGPORT."
  value       = aiven_pg.caged.service_port
}

output "service_name" {
  value = aiven_pg.caged.service_name
}
