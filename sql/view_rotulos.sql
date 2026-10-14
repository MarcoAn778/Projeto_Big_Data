CREATE OR REPLACE VIEW caged.v_indicadores_emprego AS
    SELECT i.*,
      COALESCE(r.descricao, 'Codigo ausente no layout') AS regiao,
      COALESCE(u.descricao, 'Codigo ausente no layout') AS uf,
      COALESCE(s.descricao, 'Codigo ausente no layout') AS setor_economico,
      COALESCE(x.descricao, 'Codigo ausente no layout') AS sexo,
      COALESCE(c.descricao, 'Codigo ausente no layout') AS raca_cor,
      COALESCE(m.descricao, 'Codigo ausente no layout') AS tipo_movimentacao
    FROM caged.indicadores_emprego i
    LEFT JOIN caged.dicionarios r ON r.variavel='regiao' AND r.codigo=i.regiao_codigo
    LEFT JOIN caged.dicionarios u ON u.variavel='uf' AND u.codigo=i.uf_codigo
    LEFT JOIN caged.dicionarios s ON s.variavel='setor_cnae' AND s.codigo=i.setor_cnae
    LEFT JOIN caged.dicionarios x ON x.variavel='sexo' AND x.codigo=i.sexo_codigo
    LEFT JOIN caged.dicionarios c ON c.variavel='racacor' AND c.codigo=i.racacor_codigo
    LEFT JOIN caged.dicionarios m ON m.variavel='tipo_movimentacao' AND m.codigo=i.tipo_movimentacao_codigo;
REVOKE ALL ON caged.v_indicadores_emprego FROM PUBLIC;
