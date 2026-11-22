if (!requireNamespace("RPostgres", quietly=TRUE)) stop("Instale RPostgres antes da carga.")
obrigatorias <- c("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD", "PGSSLROOTCERT")
ausentes <- obrigatorias[!nzchar(Sys.getenv(obrigatorias))]
if (length(ausentes)) stop("Configure localmente: ", paste(ausentes, collapse=", "))
certificado <- Sys.getenv("PGSSLROOTCERT")
if (!file.exists(certificado)) stop("O certificado CA indicado em PGSSLROOTCERT nao existe.")
porta <- suppressWarnings(as.integer(Sys.getenv("PGPORT")))
if (is.na(porta) || porta < 1 || porta > 65535) stop("PGPORT invalida.")

con_aiven <- tryCatch(DBI::dbConnect(RPostgres::Postgres(),
  host=Sys.getenv("PGHOST"), port=porta, dbname=Sys.getenv("PGDATABASE"),
  user=Sys.getenv("PGUSER"), password=Sys.getenv("PGPASSWORD"),
  sslmode="verify-full", sslrootcert=certificado, connect_timeout=15,
  application_name="projeto_big_data_caged"),
  error=function(e) stop("Conexao falhou. Confira rede, IP autorizado, CA e credenciais locais.", call.=FALSE))

tls <- DBI::dbGetQuery(con_aiven,
  "SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()")
if (nrow(tls) != 1 || !isTRUE(tls$ssl[[1]])) {
  DBI::dbDisconnect(con_aiven)
  stop("A conexao nao confirmou TLS.")
}
cat("Conexao PostgreSQL com TLS e validacao do certificado confirmada.\n")
