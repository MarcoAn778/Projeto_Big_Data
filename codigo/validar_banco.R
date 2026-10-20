# Somente SELECT: usado antes do COMMIT e na verificacao independente da nuvem.
resumo_nuvem <- dbGetQuery(con_aiven, "SELECT COUNT(*) AS linhas,
 COUNT(DISTINCT competencia) AS meses, SUM(total_registros) AS movimentacoes,
 SUM(admissoes) AS admissoes, SUM(desligamentos) AS desligamentos, SUM(saldo) AS saldo
 FROM caged.v_indicadores_emprego")
for (nome in names(resumo)) {
  if (as.numeric(resumo_nuvem[[nome]]) != as.numeric(resumo[[nome]])) stop("Total no banco divergente: ", nome)
}
controle <- dbGetQuery(con_aiven,
  "SELECT sha256_csv FROM caged.cargas ORDER BY carregado_em DESC")
if (nrow(controle) != 1 || controle$sha256_csv[[1]] != hash_base) stop("Controle de carga divergente.")
checagem <- dbGetQuery(con_aiven, "SELECT COUNT(*) AS n FROM caged.indicadores_emprego
 WHERE total_registros<>admissoes+desligamentos+saldo_invalido OR saldo<>admissoes-desligamentos
 OR quantidade_salarios_validos<0 OR quantidade_salarios_validos>total_registros
 OR soma_salarios_validos<0")$n
if (as.numeric(checagem) != 0) stop("Indicadores inconsistentes no PostgreSQL.")
for (nome in c("arquivos", "revisao_salarios", "dicionarios")) {
  local_n <- switch(nome, arquivos=nrow(arquivos), revisao_salarios=nrow(auditoria),
    dicionarios=nrow(read.csv2("referencias/dicionarios.csv", colClasses="character")))
  remoto_n <- dbGetQuery(con_aiven, paste0("SELECT COUNT(*) AS n FROM caged.", nome))$n
  if (as.numeric(remoto_n) != local_n) stop("Contagem divergente: ", nome)
}
