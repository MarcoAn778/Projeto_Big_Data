CREATE OR REPLACE TEMP TABLE normalizado AS
SELECT *,
  CASE WHEN regexp_full_match(NULLIF(trim(salario), ''), '[+-]?[0-9]{1,3}([.][0-9]{3})+,[0-9]+')
    THEN replace(replace(NULLIF(trim(salario), ''), '.', ''), ',', '.')
    ELSE replace(NULLIF(trim(salario), ''), ',', '.') END AS salario_normalizado,
  CASE WHEN regexp_full_match(NULLIF(trim(horascontratuais), ''), '[+-]?[0-9]{1,3}([.][0-9]{3})+,[0-9]+')
    THEN replace(replace(NULLIF(trim(horascontratuais), ''), '.', ''), ',', '.')
    ELSE replace(NULLIF(trim(horascontratuais), ''), ',', '.') END AS horascontratuais_normalizado
FROM bruto;

CREATE OR REPLACE TEMP TABLE tratado AS
SELECT
  NULLIF(trim(competenciamov), '') AS competenciamov,
  NULLIF(trim(regiao), '') AS regiao,
  NULLIF(trim(uf), '') AS uf,
  NULLIF(trim(municipio), '') AS municipio,
  NULLIF(trim(secao), '') AS secao,
  NULLIF(trim(subclasse), '') AS subclasse,
  CASE WHEN regexp_full_match(NULLIF(trim(saldomovimentacao), ''), '[+-]?[0-9]+') THEN TRY_CAST(NULLIF(trim(saldomovimentacao), '') AS INTEGER) END AS saldomovimentacao,
  NULLIF(trim(tipomovimentacao), '') AS tipomovimentacao,
  NULLIF(trim(sexo), '') AS sexo,
  NULLIF(trim(racacor), '') AS racacor,
  CASE WHEN regexp_full_match(NULLIF(trim(idade), ''), '[+-]?[0-9]+') THEN TRY_CAST(NULLIF(trim(idade), '') AS INTEGER) END AS idade,
  NULLIF(trim(graudeinstrucao), '') AS graudeinstrucao,
  CASE WHEN regexp_full_match(horascontratuais_normalizado, '[+-]?[0-9]+([.][0-9]{1,6})?') THEN TRY_CAST(horascontratuais_normalizado AS DECIMAL(24,6)) END AS horascontratuais,
  CASE WHEN regexp_full_match(salario_normalizado, '[+-]?[0-9]+([.][0-9]{1,6})?') THEN TRY_CAST(salario_normalizado AS DECIMAL(24,6)) END AS salario,
  NULLIF(trim(tamestabjan), '') AS tamestabjan,
  NULLIF(trim(indtrabintermitente), '') AS indtrabintermitente,
  NULLIF(trim(indtrabparcial), '') AS indtrabparcial
FROM normalizado;
