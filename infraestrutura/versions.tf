terraform {
  required_version = ">= 1.7.0, < 2.0.0"
  backend "local" {}
  required_providers {
    aiven = {
      source  = "aiven/aiven"
      version = "~> 4.0"
    }
  }
}

# A autenticacao vem de AIVEN_TOKEN, definido somente na sessao local.
provider "aiven" {}
