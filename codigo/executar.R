# Execute da raiz: Rscript codigo/executar.R validar|tratamento|carga|verificar-nuvem
executar <- function() {
  args <- commandArgs(trailingOnly=TRUE)
  modo <- if (length(args)) args[[1]] else "validar"
  if (!modo %in% c("validar", "tratamento", "carga", "verificar-nuvem")) stop("Modo invalido.")
  if (!file.exists("sql/estrutura.sql")) stop("Execute este comando na raiz do repositorio.")
  source("codigo/00_configuracao.R", local=TRUE)
  on.exit(source("codigo/05_encerrar.R", local=TRUE), add=TRUE)
  if (modo == "tratamento") {
    source("codigo/01_tratar.R", local=TRUE)
    source("codigo/02_finalizar.R", local=TRUE)
  } else if (modo == "validar") {
    source("codigo/06_validar_base.R", local=TRUE)
  } else {
    source("codigo/06_validar_base.R", local=TRUE)
    source("codigo/03_conectar.R", local=TRUE)
    if (modo == "carga") source("codigo/04_carregar.R", local=TRUE)
    source("codigo/07_verificar_nuvem.R", local=TRUE)
  }
}
executar()
