stopifnot(file.exists("resultados/VALIDADO.txt"))
auditorias <- list.files("resultados",pattern="^revisao_salarios_[0-9]{6}[.]csv$")

if (length(auditorias)!=length(meses)) stop("Execute o tratamento dos 12 meses antes da carga.")
schema <- "caged"
estrutura <- gsub("caged", schema, ler_sql("sql/estrutura.sql"), fixed=TRUE)
comandos <- strsplit(estrutura, ";", fixed=TRUE)[[1]]

DBI::dbWithTransaction(con_aiven, {
  for (sql in comandos) if (nzchar(trimws(sql))) dbExecute(con_aiven, sql)
  tabela <- Id(schema=schema, table="indicadores_emprego")
  n <- dbGetQuery(con_aiven, paste0("SELECT COUNT(*) AS n FROM ", schema, ".indicadores_emprego"))$n
  if (n != 0) stop("O schema ja tem dados. A carga foi interrompida para nao duplicar.")

  leitura <- dbSendQuery(con, "SELECT * FROM read_csv('resultados/base_tratada.csv',
    delim=';', header=true, all_varchar=true, nullstr='')")
  tryCatch({
    repeat {
      bloco <- dbFetch(leitura, n=20000)
      if (nrow(bloco) == 0) break
      dbAppendTable(con_aiven, tabela, bloco, copy=TRUE)
    }
  }, finally=dbClearResult(leitura))

  arquivos <- read.csv2("resultados/arquivos_origem.csv", colClasses="character")
  dbAppendTable(con_aiven, Id(schema=schema, table="arquivos"), arquivos, copy=TRUE)
  revisao <- dbGetQuery(con, "SELECT * FROM read_csv('resultados/revisao_salarios_*.csv',
    delim=';', header=true, all_varchar=true, nullstr='')")
  dbAppendTable(con_aiven, Id(schema=schema, table="revisao_salarios"), revisao, copy=TRUE)
  hash <- digest::digest(file="resultados/base_tratada.csv", algo="sha256")
  dbExecute(con_aiven, paste0("INSERT INTO ", schema, ".cargas
    (sha256_csv,versao_script,periodo_inicio,periodo_fim,linhas_agregadas,eventos_representados)
    VALUES ($1,'autonomo','202508','202607',$2,$3)"),
    params=list(hash,as.numeric(resumo$linhas),as.numeric(resumo$movimentacoes)))
  dicionario <- read.csv2("referencias/dicionarios.csv", colClasses="character")
  dbAppendTable(con_aiven, Id(schema=schema, table="dicionarios"), dicionario, copy=TRUE)
  vista <- gsub("caged", schema, ler_sql("sql/view_rotulos.sql"), fixed=TRUE)
  for (sql in strsplit(vista,";",fixed=TRUE)[[1]]) {
    if (nzchar(trimws(sql))) dbExecute(con_aiven, sql)
  }
  contagem <- dbGetQuery(con_aiven, paste0("SELECT COUNT(*) AS linhas,
    SUM(total_registros) AS eventos FROM ", schema, ".v_indicadores_emprego"))
  stopifnot(as.numeric(contagem$linhas)==as.numeric(resumo$linhas),
    as.numeric(contagem$eventos)==as.numeric(resumo$movimentacoes))
})

print(contagem)
cat("Carga concluida no schema caged.\n")