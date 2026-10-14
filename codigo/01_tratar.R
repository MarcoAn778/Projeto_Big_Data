unlink("resultados/VALIDADO.txt")
metadados <- list()

for (mes in meses) {
  arquivo <- file.path(pasta_originais, paste0("CAGEDMOV", mes, ".txt"))
  if (!file.exists(arquivo)) stop("Falta o arquivo: ", arquivo)

  hash_original <- digest::digest(file=arquivo, algo="sha256")
  cat("Tratando", mes, "\n")

  caminho <- aspas(normalizePath(arquivo, winslash="/"))
  dbExecute(con, paste0("CREATE OR REPLACE TEMP TABLE bruto AS SELECT * FROM read_csv(",
    caminho, ", delim=';', header=true, all_varchar=true, normalize_names=false,",
    " parallel=false, strict_mode=true, ignore_errors=false, null_padding=false)"))

  cabecalho <- dbListFields(con, "bruto")
  nomes <- c("competenciamov", "regiao", "uf", "municipio", "secao", "subclasse",
    "saldomovimentacao", "cbo2002ocupacao", "categoria", "graudeinstrucao", "idade",
    "horascontratuais", "racacor", "sexo", "tipoempregador", "tipoestabelecimento",
    "tipomovimentacao", "tipodedeficiencia", "indtrabintermitente", "indtrabparcial",
    "salario", "tamestabjan", "indicadoraprendiz", "origemdainformacao", "competenciadec",
    "indicadordeforadoprazo", "unidadesalariocodigo", "valorsalariofixo")
  esperado_cabecalho <- c("compet\u00eanciamov", "regi\u00e3o", "uf", "munic\u00edpio", "se\u00e7\u00e3o", "subclasse",
    "saldomovimenta\u00e7\u00e3o", "cbo2002ocupa\u00e7\u00e3o", "categoria", "graudeinstru\u00e7\u00e3o", "idade",
    "horascontratuais", "ra\u00e7acor", "sexo", "tipoempregador", "tipoestabelecimento",
    "tipomovimenta\u00e7\u00e3o", "tipodedefici\u00eancia", "indtrabintermitente", "indtrabparcial",
    "sal\u00e1rio", "tamestabjan", "indicadoraprendiz", "origemdainforma\u00e7\u00e3o", "compet\u00eanciadec",
    "indicadordeforadoprazo", "unidadesal\u00e1rioc\u00f3digo", "valorsal\u00e1riofixo")

  if (!identical(enc2utf8(cabecalho), enc2utf8(esperado_cabecalho))) stop("Cabecalho inesperado.")
  for (i in seq_along(nomes)) {
    if (cabecalho[i] != nomes[i]) dbExecute(con, paste("ALTER TABLE bruto RENAME COLUMN",
      dbQuoteIdentifier(con, cabecalho[i]), "TO", dbQuoteIdentifier(con, nomes[i])))
  }

  divergentes <- dbGetQuery(con, paste0("SELECT COUNT(*) AS n FROM bruto WHERE ",
    "NULLIF(trim(competenciamov),'') IS NOT NULL AND trim(competenciamov) <> '", mes, "'"))$n
  if (divergentes != 0) stop("Competencia diferente do nome do arquivo.")
  dbExecute(con, ler_sql("sql/limpar.sql"))
  auditoria <- paste0("SELECT ", match(mes, meses), " AS arquivo_id, linha_origem,
    salario AS salario_original, TRY_CAST(salario_normalizado AS DECIMAL(38,6)) AS salario_numerico,
    'Formato nao aceito na media; revisar valor na fonte' AS classificacao,
    'Movimentacao mantida; salario fora da media' AS decisao
    FROM (SELECT row_number() OVER () + 1 AS linha_origem, salario, salario_normalizado
          FROM normalizado)
    WHERE salario_normalizado IS NOT NULL AND
      (NOT regexp_full_match(salario_normalizado, '[+-]?[0-9]+([.][0-9]{1,6})?')
       OR TRY_CAST(salario_normalizado AS DECIMAL(24,6)) IS NULL)")

  dbExecute(con, paste0("COPY (", auditoria, ") TO ",
    aspas(file.path("resultados", paste0("revisao_salarios_", mes, ".csv"))),
    " (FORMAT CSV, HEADER true, DELIMITER ';', NULLSTR '')"))
  dbExecute(con, paste0("UPDATE tratado SET competenciamov='", mes,
    "' WHERE competenciamov IS NULL"))
  dbExecute(con, ler_sql("sql/categorias.sql"))
  dbExecute(con, ler_sql("sql/agregar.sql"))
  n_original <- dbGetQuery(con, "SELECT COUNT(*) AS n FROM bruto")$n
  n_agregado <- dbGetQuery(con, "SELECT SUM(total_registros) AS n FROM agregado_mes")$n
  stopifnot(n_original == n_agregado)

  saida <- aspas(file.path("resultados", paste0("agregado_", mes, ".csv")))
  dbExecute(con, paste0("COPY agregado_mes TO ", saida,
    " (FORMAT CSV, HEADER true, DELIMITER ';', NULLSTR '')"))
  metadados[[mes]] <- data.frame(id=match(mes, meses), arquivo=basename(arquivo),
    competencia=mes, sha256_original=hash_original, bytes_original=file.info(arquivo)$size,
    linhas=as.numeric(n_original), csv_tratado=paste0("agregado_", mes, ".csv"),
    sha256_tratado=digest::digest(file=file.path("resultados",paste0("agregado_",mes,".csv")),algo="sha256"))
}

write.table(do.call(rbind, metadados), "resultados/arquivos_origem.csv",
  sep=";", row.names=FALSE, quote=TRUE)
cat("Tratamento mensal concluido. Execute 02_finalizar.R.\n")