-- Execute no PostgreSQL apos a carga. Nao altera os dados.
SELECT COUNT(*) AS linhas_agregadas, COUNT(DISTINCT competencia) AS meses,
       SUM(total_registros) AS movimentacoes, SUM(admissoes) AS admissoes,
       SUM(desligamentos) AS desligamentos, SUM(saldo) AS saldo
FROM caged.indicadores_emprego;

SELECT competencia, SUM(admissoes) AS admissoes, SUM(desligamentos) AS desligamentos,
       SUM(saldo) AS saldo
FROM caged.indicadores_emprego GROUP BY competencia ORDER BY competencia;

-- Media recomposta: nao usar AVG(remuneracao_media).
SELECT setor_economico, SUM(soma_salarios_validos) /
       NULLIF(SUM(quantidade_salarios_validos), 0) AS remuneracao_media_ponderada
FROM caged.v_indicadores_emprego GROUP BY setor_economico ORDER BY setor_economico;

SELECT COUNT(*) AS ocorrencias_para_revisao FROM caged.revisao_salarios;
SELECT sha256_csv, linhas_agregadas, eventos_representados, carregado_em FROM caged.cargas;
SELECT ssl, version AS versao_tls FROM pg_stat_ssl WHERE pid = pg_backend_pid();
