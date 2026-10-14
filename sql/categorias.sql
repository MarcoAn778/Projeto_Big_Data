CREATE OR REPLACE TEMP TABLE categorias AS SELECT *,
      CAST(strptime(competenciamov, '%Y%m') AS DATE) AS competencia,
      CASE WHEN idade IS NULL OR idade < 14 OR idade > 100 THEN 'Nao informado ou invalido'
        WHEN idade <= 17 THEN '14 a 17' WHEN idade <= 24 THEN '18 a 24'
        WHEN idade <= 29 THEN '25 a 29' WHEN idade <= 39 THEN '30 a 39'
        WHEN idade <= 49 THEN '40 a 49' WHEN idade <= 64 THEN '50 a 64' ELSE '65 a 100' END AS faixa_etaria,
      CASE saldomovimentacao WHEN 1 THEN 'Admissao' WHEN -1 THEN 'Desligamento' ELSE 'Nao identificado' END AS tipo_fluxo,
      CASE indtrabintermitente WHEN '1' THEN true WHEN '0' THEN false ELSE NULL END AS intermitente_booleano,
      CASE indtrabparcial WHEN '1' THEN true WHEN '0' THEN false ELSE NULL END AS parcial_booleano
      FROM tratado;
