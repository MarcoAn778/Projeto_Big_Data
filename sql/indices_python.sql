-- Indices novos desta etapa. O DDL da etapa anterior permanece intacto.
CREATE INDEX IF NOT EXISTS indicadores_competencia_idx ON caged.indicadores_emprego (competencia);
CREATE INDEX IF NOT EXISTS indicadores_uf_competencia_idx ON caged.indicadores_emprego (uf_codigo, competencia);
