-- Consultas de reprodução dos resultados descritos no README.
SELECT SUM(admissoes) AS admissoes,
       SUM(desligamentos) AS desligamentos,
       SUM(admissoes) FILTER (WHERE sexo_codigo = '3') AS mulheres_admissoes,
       SUM(desligamentos) FILTER (WHERE sexo_codigo = '3') AS mulheres_desligamentos,
       SUM(admissoes) FILTER (WHERE racacor_codigo IN ('2', '3')) AS negras_admissoes,
       SUM(desligamentos) FILTER (WHERE racacor_codigo IN ('2', '3')) AS negras_desligamentos,
       SUM(admissoes) FILTER (WHERE sexo_codigo = '3' AND racacor_codigo IN ('2', '3')) AS mulheres_negras_admissoes,
       SUM(desligamentos) FILTER (WHERE sexo_codigo = '3' AND racacor_codigo IN ('2', '3')) AS mulheres_negras_desligamentos,
       SUM(total_registros) FILTER (WHERE racacor_codigo = '6') AS raca_nao_informada,
       SUM(total_registros) FILTER (WHERE racacor_codigo = '9') AS raca_nao_identificada
FROM caged.v_indicadores_emprego;

SELECT sexo, raca_cor, SUM(admissoes) AS admissoes, SUM(desligamentos) AS desligamentos,
       SUM(saldo) AS saldo,
       ROUND(SUM(soma_salarios_validos) FILTER (WHERE tipo_fluxo = 'Admissao')
           / NULLIF(SUM(quantidade_salarios_validos) FILTER (WHERE tipo_fluxo = 'Admissao'), 0), 2) AS salario_medio_admissao
FROM caged.v_indicadores_emprego
GROUP BY sexo, raca_cor
ORDER BY salario_medio_admissao DESC NULLS LAST, sexo, raca_cor;

SELECT setor_economico,
       ROUND(100 * SUM(admissoes) FILTER (WHERE sexo_codigo = '3')
           / NULLIF(SUM(admissoes), 0), 2) AS pct_mulheres_admissoes,
       ROUND(100 * SUM(desligamentos) FILTER (WHERE sexo_codigo = '3')
           / NULLIF(SUM(desligamentos), 0), 2) AS pct_mulheres_desligamentos,
       ROUND(100 * SUM(admissoes) FILTER (WHERE racacor_codigo IN ('2', '3'))
           / NULLIF(SUM(admissoes), 0), 2) AS pct_negras_admissoes,
       ROUND(100 * SUM(desligamentos) FILTER (WHERE racacor_codigo IN ('2', '3'))
           / NULLIF(SUM(desligamentos), 0), 2) AS pct_negras_desligamentos
FROM caged.v_indicadores_emprego
WHERE setor_cnae IN ('C', 'F', 'G', 'Q')
GROUP BY setor_economico
ORDER BY setor_economico;
