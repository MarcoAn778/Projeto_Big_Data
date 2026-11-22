if (!exists("hash_base") || !exists("auditoria") || !exists("arquivos"))
  stop("Execute 06_validar_base.R antes da carga, ou use codigo/executar.R carga.")
if (digest::digest(file="resultados/base_tratada.csv", algo="sha256") != hash_base)
  stop("A base mudou apos a validacao.")
schema <- "caged"
estrutura <- gsub("caged", schema, ler_sql("sql/estrutura.sql"), fixed=TRUE)
comandos <- strsplit(estrutura, ";", fixed=TRUE)[[1]]

DBI::dbWithTransaction(con_aiven, {
  for (sql in comandos) if (nzchar(trimws(sql))) dbExecute(con_aiven, sql)
  dbExecute(con_aiven, "LOCK TABLE caged.indicadores_emprego, caged.arquivos,
    caged.revisao_salarios, caged.cargas, caged.dicionarios IN ACCESS EXCLUSIVE MODE")
  tabela <- Id(schema=schema, table="indicadores_emprego")
  n <- dbGetQuery(con_aiven, paste0("SELECT COUNT(*) AS n FROM ", schema, ".indicadores_emprego"))$n
  if (n != 0) stop("O schema ja tem dados. A carga foi interrompida para nao duplicar.")
  for (nome in c("arquivos", "revisao_salarios", "cargas", "dicionarios")) {
    if (as.numeric(dbGetQuery(con_aiven, paste0("SELECT COUNT(*) AS n FROM caged.", nome))$n) != 0)
      stop("Tabela auxiliar ja contem dados. Carga interrompida: ", nome)
  }

  leitura <- dbSendQuery(con, "SELECT * FROM read_csv('resultados/base_tratada.csv',
    delim=';', header=true, all_varchar=true, nullstr='')")
  tryCatch({
    repeat {
      bloco <- dbFetch(leitura, n=20000)
      if (nrow(bloco) == 0) break
      dbAppendTable(con_aiven, tabela, bloco, copy=TRUE)
    }
  }, finally=dbClearResult(leitura))

  dbAppendTable(con_aiven, Id(schema=schema, table="arquivos"), arquivos, copy=TRUE)
  if (nrow(auditoria)) dbAppendTable(con_aiven, Id(schema=schema, table="revisao_salarios"), auditoria, copy=TRUE)
  hash <- digest::digest(file="resultados/base_tratada.csv", algo="sha256")
  dbExecute(con_aiven, paste0("INSERT INTO ", schema, ".cargas
    (sha256_csv,versao_script,periodo_inicio,periodo_fim,linhas_agregadas,eventos_representados)
    VALUES ($1,'marco2-terraform','202508','202607',$2,$3)"),
    params=list(hash,as.numeric(resumo$linhas),as.numeric(resumo$movimentacoes)))
  dicionario <- read.csv2("referencias/dicionarios.csv", colClasses="character", fileEncoding="UTF-8")
  dbAppendTable(con_aiven, Id(schema=schema, table="dicionarios"), dicionario, copy=TRUE)
  vista <- gsub("caged", schema, ler_sql("sql/view_rotulos.sql"), fixed=TRUE)
  for (sql in strsplit(vista,";",fixed=TRUE)[[1]]) {
    if (nzchar(trimws(sql))) dbExecute(con_aiven, sql)
  }
  contagem <- dbGetQuery(con_aiven, paste0("SELECT COUNT(*) AS linhas,
    SUM(total_registros) AS eventos FROM ", schema, ".v_indicadores_emprego"))
  stopifnot(as.numeric(contagem$linhas)==as.numeric(resumo$linhas),
    as.numeric(contagem$eventos)==as.numeric(resumo$movimentacoes))
  source("codigo/validar_banco.R", local=TRUE)
})

print(contagem)
cat("Carga concluida no schema caged.\n")
