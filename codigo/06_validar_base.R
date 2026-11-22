# Valida a base publicada OU a saida de um novo tratamento, sem acessar a nuvem.
csv_base <- "resultados/base_tratada.csv"
if (!file.exists(csv_base)) {
  if (!file.exists("resultados/base_tratada.zip")) stop("Base tratada nao encontrada.")
  itens <- unzip("resultados/base_tratada.zip", list=TRUE)$Name
  if (!identical(itens, "base_tratada.csv")) stop("Conteudo inesperado no ZIP.")
  unzip("resultados/base_tratada.zip", files="base_tratada.csv", exdir="resultados")
}
hash_base <- digest::digest(file=csv_base, algo="sha256")
esperado <- jsonlite::read_json("resultados/resumo_processamento.json", simplifyVector=TRUE)
if (!identical(hash_base, esperado$sha256_csv)) stop("Hash da base difere do resumo. Carga bloqueada.")

auditorias <- file.path("resultados", paste0("revisao_salarios_", meses, ".csv"))
if (all(file.exists(auditorias)) && file.exists("resultados/arquivos_origem.csv")) {
  caminho_arquivos <- "resultados/arquivos_origem.csv"
  auditoria <- do.call(rbind, lapply(auditorias, function(x)
    read.csv2(x, colClasses="character", fileEncoding="UTF-8")))
  origem_auditoria <- "Arquivos de revisao gerados pelo tratamento local dos 12 meses"
} else {
  # Anexos historicos so podem ser usados com o pacote publicado correspondente.
  pacote <- jsonlite::read_json("dados/pacote_publicado.json", simplifyVector=TRUE)
  if (!identical(hash_base, pacote$sha256_csv)) stop("Refaca o tratamento para gerar a auditoria desta base.")
  for (arquivo in names(pacote$arquivos)) {
    if (!file.exists(arquivo) || digest::digest(file=arquivo, algo="sha256") != pacote$arquivos[[arquivo]])
      stop("Arquivo do pacote publicado alterado: ", arquivo)
  }
  caminho_arquivos <- "dados/arquivos_origem.csv"
  auditoria <- read.csv2("dados/auditoria_salarios.csv", colClasses="character", fileEncoding="UTF-8")
  if (nrow(auditoria) != pacote$ocorrencias_salariais) stop("Auditoria historica incompleta.")
  origem_auditoria <- "Anomalias salariais versionadas do pacote publicado; nao houve nova leitura dos TXT"
}
arquivos <- read.csv2(caminho_arquivos, colClasses="character", fileEncoding="UTF-8")
if (nrow(arquivos) != 12 || !setequal(arquivos$competencia, meses) ||
    anyDuplicated(arquivos$id) || anyDuplicated(arquivos$competencia)) stop("Metadados de origem invalidos.")
if (any(!auditoria$arquivo_id %in% arquivos$id) ||
    anyDuplicated(paste(auditoria$arquivo_id, auditoria$linha_origem))) stop("Auditoria inconsistente.")

dbExecute(con, "CREATE OR REPLACE TEMP TABLE base_validada AS SELECT * FROM read_csv(
 'resultados/base_tratada.csv', delim=';', header=true, strict_mode=true,
 types={'id':'BIGINT','competencia':'DATE','regiao_codigo':'VARCHAR','uf_codigo':'VARCHAR',
 'setor_cnae':'VARCHAR','sexo_codigo':'VARCHAR','racacor_codigo':'VARCHAR',
 'faixa_etaria':'VARCHAR','tipo_movimentacao_codigo':'VARCHAR','tipo_fluxo':'VARCHAR',
 'total_registros':'BIGINT','admissoes':'BIGINT','desligamentos':'BIGINT','saldo':'BIGINT',
 'saldo_invalido':'BIGINT','soma_salarios_validos':'DECIMAL(38,6)',
 'quantidade_salarios_validos':'BIGINT','remuneracao_media':'DOUBLE'})")
resumo <- dbGetQuery(con, "SELECT COUNT(*) AS linhas, COUNT(DISTINCT competencia) AS meses,
 SUM(total_registros) AS movimentacoes, SUM(admissoes) AS admissoes,
 SUM(desligamentos) AS desligamentos, SUM(saldo) AS saldo FROM base_validada")
for (nome in names(resumo)) {
  if (as.numeric(resumo[[nome]]) != as.numeric(esperado$resumo[[nome]])) stop("Total divergente: ", nome)
}
if (as.numeric(resumo$movimentacoes) != sum(as.numeric(arquivos$linhas))) stop("Total diverge da origem.")
competencias <- dbGetQuery(con, "SELECT DISTINCT strftime(competencia,'%Y%m') AS mes FROM base_validada")$mes
if (!setequal(competencias, meses)) stop("Recorte da base incorreto.")
erros <- dbGetQuery(con, "SELECT COUNT(*) AS n FROM base_validada WHERE
 id IS NULL OR id<1 OR competencia IS NULL OR competencia<>date_trunc('month',competencia)
 OR regiao_codigo IS NULL OR uf_codigo IS NULL OR setor_cnae IS NULL OR sexo_codigo IS NULL
 OR racacor_codigo IS NULL OR faixa_etaria IS NULL OR tipo_movimentacao_codigo IS NULL OR tipo_fluxo IS NULL
 OR total_registros IS NULL OR admissoes IS NULL OR desligamentos IS NULL OR saldo IS NULL
 OR saldo_invalido IS NULL OR quantidade_salarios_validos IS NULL OR soma_salarios_validos IS NULL
 OR total_registros<1 OR admissoes<0 OR desligamentos<0 OR saldo_invalido<0
 OR total_registros<>admissoes+desligamentos+saldo_invalido OR saldo<>admissoes-desligamentos
 OR quantidade_salarios_validos<0 OR quantidade_salarios_validos>total_registros OR soma_salarios_validos<0
 OR (quantidade_salarios_validos=0 AND (remuneracao_media IS NOT NULL OR soma_salarios_validos<>0))
 OR (quantidade_salarios_validos>0 AND (remuneracao_media IS NULL OR NOT isfinite(remuneracao_media)
 OR abs(remuneracao_media-soma_salarios_validos/quantidade_salarios_validos)>0.000001))")$n
ids <- dbGetQuery(con, "SELECT COUNT(*)-COUNT(DISTINCT id) AS n FROM base_validada")$n
grupos <- dbGetQuery(con, "SELECT COUNT(*) AS n FROM (SELECT competencia,regiao_codigo,uf_codigo,
 setor_cnae,sexo_codigo,racacor_codigo,faixa_etaria,tipo_movimentacao_codigo,tipo_fluxo
 FROM base_validada GROUP BY ALL HAVING COUNT(*)>1)")$n
if (any(c(erros, ids, grupos) != 0)) stop("Base inconsistente ou com grupos/IDs duplicados.")

dir.create("verificacoes", showWarnings=FALSE)
jsonlite::write_json(list(status="validado_localmente", sha256_csv=hash_base, resumo=resumo,
  ocorrencias_auditoria=nrow(auditoria), origem_auditoria=origem_auditoria,
  verificado_em_utc=format(Sys.time(), tz="UTC", usetz=TRUE),
  nuvem="Nao verificada por este comando"),
  "verificacoes/validacao_base_atual.json", pretty=TRUE, auto_unbox=TRUE)
print(resumo)
cat("Base, hash, metadados e auditoria validados localmente.\n")
