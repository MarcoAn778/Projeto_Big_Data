unlink("resultados/VALIDADO.txt")
metadados <- read.csv2("resultados/arquivos_origem.csv", colClasses="character")
if (!setequal(metadados$competencia, meses) || nrow(metadados)!=12) stop("Faltam meses.")
for (mes in meses) {
  arquivo <- file.path("resultados",paste0("agregado_",mes,".csv"))
  esperado <- metadados$sha256_tratado[metadados$competencia==mes]
  if (digest::digest(file=arquivo,algo="sha256")!=esperado) stop("Agregado alterado: ",mes)
}

dbExecute(con, "CREATE OR REPLACE TEMP TABLE unificado AS SELECT * FROM read_csv(
 'resultados/agregado_*.csv', delim=';', header=true,
 types={'competencia':'DATE','regiao_codigo':'VARCHAR','uf_codigo':'VARCHAR',
 'setor_cnae':'VARCHAR','sexo_codigo':'VARCHAR','racacor_codigo':'VARCHAR',
 'faixa_etaria':'VARCHAR','tipo_movimentacao_codigo':'VARCHAR','tipo_fluxo':'VARCHAR',
 'total_registros':'BIGINT','admissoes':'BIGINT','desligamentos':'BIGINT','saldo':'BIGINT',
 'saldo_invalido':'BIGINT','soma_salarios_validos':'DECIMAL(38,6)',
 'quantidade_salarios_validos':'BIGINT'})")

dbExecute(con, "CREATE OR REPLACE TEMP TABLE final AS SELECT
 row_number() OVER (ORDER BY competencia,regiao_codigo,uf_codigo,setor_cnae,
 sexo_codigo,racacor_codigo,faixa_etaria,tipo_movimentacao_codigo,tipo_fluxo) AS id, *,
 CASE WHEN quantidade_salarios_validos>0 THEN
 soma_salarios_validos/quantidade_salarios_validos END AS remuneracao_media
 FROM unificado")

resumo <- dbGetQuery(con, "SELECT COUNT(*) AS linhas, COUNT(DISTINCT competencia) AS meses,
 SUM(total_registros) AS movimentacoes, SUM(admissoes) AS admissoes,
 SUM(desligamentos) AS desligamentos, SUM(saldo) AS saldo FROM final")

stopifnot(as.numeric(resumo$movimentacoes)==sum(as.numeric(metadados$linhas)),
 as.numeric(resumo$meses)==12)
erros <- dbGetQuery(con, "SELECT COUNT(*) AS n FROM final WHERE
 total_registros<>admissoes+desligamentos+saldo_invalido OR saldo<>admissoes-desligamentos
 OR quantidade_salarios_validos<0 OR quantidade_salarios_validos>total_registros")$n

stopifnot(erros==0)
duplicados <- dbGetQuery(con, "SELECT COUNT(*) AS n FROM (SELECT competencia,
 regiao_codigo,uf_codigo,setor_cnae,sexo_codigo,racacor_codigo,faixa_etaria,
 tipo_movimentacao_codigo,tipo_fluxo FROM final GROUP BY ALL HAVING COUNT(*)>1)")$n

stopifnot(duplicados==0)
dbExecute(con, "COPY (SELECT * FROM final ORDER BY id) TO 'resultados/base_tratada.csv'
 (FORMAT CSV, HEADER true, DELIMITER ';', NULLSTR '')")

jsonlite::write_json(list(status="processamento_validado",resumo=resumo,
 verificado_em_utc=format(Sys.time(),tz="UTC",usetz=TRUE),
 sha256_csv=digest::digest(file="resultados/base_tratada.csv",algo="sha256")),
 "resultados/resumo_processamento.json",pretty=TRUE,auto_unbox=TRUE)
writeLines("Tratamento e validacoes internas concluidos.","resultados/VALIDADO.txt")
print(resumo)