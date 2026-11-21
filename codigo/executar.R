# R fica responsavel somente pelo tratamento. Depois use codigo/executar.py.
executar <- function() {
  args <- commandArgs(trailingOnly=TRUE)
  modo <- if (length(args)) args[[1]] else "tratamento"
  if (modo != "tratamento") stop("Apos o tratamento, use Python: codigo/executar.py validar|carga|verificar-nuvem")
  if (!file.exists("sql/estrutura.sql")) stop("Execute este comando na raiz do repositorio.")
  source("codigo/00_configuracao.R", local=TRUE)
  on.exit(if (DBI::dbIsValid(con)) DBI::dbDisconnect(con, shutdown=TRUE), add=TRUE)
  source("codigo/01_tratar.R", local=TRUE)
  source("codigo/02_finalizar.R", local=TRUE)
}
executar()
