# Confere que uma base adulterada e bloqueada antes de qualquer acesso ao banco.
testar_integridade <- function() {
  raiz <- normalizePath(".", winslash="/")
  teste <- tempfile("caged_integridade_")
  dir.create(teste)
  dir.create(file.path(teste, "resultados"))
  file.copy("resultados/resumo_processamento.json", file.path(teste, "resultados"))
  writeLines("conteudo adulterado", file.path(teste, "resultados/base_tratada.csv"))
  on.exit(setwd(raiz), add=TRUE)
  setwd(teste)
  mensagem <- tryCatch({source(file.path(raiz,"codigo/06_validar_base.R"), local=TRUE); "SEM ERRO"},
    error=function(e) conditionMessage(e))
  if (!grepl("Hash da base difere", mensagem, fixed=TRUE)) stop("Bloqueio de integridade falhou: ", mensagem)
  cat("Base adulterada bloqueada antes da conexao: OK.\n")
}
testar_integridade()
