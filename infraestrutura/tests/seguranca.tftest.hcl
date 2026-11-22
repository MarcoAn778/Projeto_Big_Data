# Simulacao sem conta, token ou criacao de recursos na nuvem.
mock_provider "aiven" {}

variables {
  project_name  = "projeto-teste"
  allowed_cidrs = ["203.0.113.10/32"]
}

run "protecao_do_servico" {
  command = plan
  assert {
    condition     = aiven_pg.caged.termination_protection && aiven_pg.caged.plan == "free-1-1gb"
    error_message = "O servico precisa ter protecao contra exclusao e usar plano gratuito."
  }
}

run "bloqueia_plano_pago" {
  command = plan
  variables {
    plan = "startup-4"
  }
  expect_failures = [var.plan]
}

run "bloqueia_acesso_global" {
  command = plan
  variables {
    allowed_cidrs = ["0.0.0.0/0"]
  }
  expect_failures = [var.allowed_cidrs]
}

run "bloqueia_cidr_invalido" {
  command = plan
  variables {
    allowed_cidrs = ["IP-INVALIDO"]
  }
  expect_failures = [var.allowed_cidrs]
}
