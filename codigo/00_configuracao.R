if (dir.exists(".biblioteca")) .libPaths(c(".biblioteca", .libPaths()))
if (dir.exists("testes/biblioteca")) .libPaths(c("testes/biblioteca", .libPaths()))
necessarios <- c("DBI", "duckdb", "digest", "jsonlite")
faltantes <- necessarios[!vapply(necessarios, requireNamespace, logical(1), quietly=TRUE)]
if (length(faltantes)) stop("Instale os pacotes: ", paste(faltantes, collapse=", "))
library(DBI)
library(duckdb)

pasta_originais <- "dados_originais"
meses <- format(seq(as.Date("2025-08-01"), as.Date("2026-07-01"), by="month"), "%Y%m")
dir.create("resultados", showWarnings=FALSE)
con <- dbConnect(duckdb(), dbdir=":memory:")
dbExecute(con, "SET memory_limit = '4GB'")
dbExecute(con, "SET threads = 2")
dbExecute(con, "SET preserve_insertion_order = true")

aspas <- function(x) as.character(dbQuoteString(con, x))
ler_sql <- function(arquivo) paste(readLines(arquivo, encoding="UTF-8"), collapse="\n")
