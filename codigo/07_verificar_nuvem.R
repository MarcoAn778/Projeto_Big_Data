source("codigo/validar_banco.R", local=TRUE)
tls <- dbGetQuery(con_aiven, "SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()")
if (nrow(tls) != 1 || !isTRUE(tls$ssl[[1]])) stop("TLS nao confirmado.")
jsonlite::write_json(list(status="carga_nuvem_validada", sha256_csv=hash_base,
  resumo=resumo_nuvem, ocorrencias_auditoria=nrow(auditoria), tls_verificado=TRUE,
  verificado_em_utc=format(Sys.time(), tz="UTC", usetz=TRUE)),
  "verificacoes/carga_nuvem.json", pretty=TRUE, auto_unbox=TRUE)
cat("Carga na nuvem conferida. Evidencia sem credenciais: verificacoes/carga_nuvem.json\n")
