variable "project_name" {
  description = "Nome exato do projeto na conta Aiven da equipe."
  type        = string
  validation {
    condition     = length(trimspace(var.project_name)) > 0
    error_message = "Informe o projeto Aiven existente."
  }
}

variable "service_name" {
  description = "Nome do novo servico PostgreSQL."
  type        = string
  default     = "caged-postgres"
}

variable "plan" {
  description = "Plano gratuito. Confirme a disponibilidade na conta antes do apply."
  type        = string
  default     = "free-1-1gb"
  validation {
    condition     = startswith(var.plan, "free-")
    error_message = "Esta entrega aceita somente plano free. Uma mudanca para plano pago exige revisao explicita."
  }
}

variable "cloud_name" {
  description = "Nulo permite a escolha automatica da regiao do plano gratuito."
  type        = string
  default     = null
}

variable "allowed_cidrs" {
  description = "IPs publicos autorizados, em CIDR. Ex.: IP atual da equipe seguido de /32."
  type        = set(string)
  validation {
    condition = length(var.allowed_cidrs) > 0 && alltrue([
      for cidr in var.allowed_cidrs :
      can(cidrhost(cidr, 0)) && !endswith(cidr, "/0")
    ])
    error_message = "Informe ao menos um CIDR valido e restrito. Abertura global /0 nao e aceita."
  }
}
