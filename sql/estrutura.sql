CREATE SCHEMA IF NOT EXISTS caged;
REVOKE ALL ON SCHEMA caged FROM PUBLIC;
CREATE TABLE IF NOT EXISTS caged.arquivos (
    id INTEGER PRIMARY KEY, arquivo TEXT, competencia TEXT, sha256_original TEXT,
    bytes_original BIGINT, linhas BIGINT, csv_tratado TEXT, sha256_tratado TEXT
);
CREATE TABLE IF NOT EXISTS caged.cargas (
    sha256_csv TEXT PRIMARY KEY, versao_script TEXT, periodo_inicio TEXT,
    periodo_fim TEXT, linhas_agregadas BIGINT, eventos_representados BIGINT,
    carregado_em TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS caged.indicadores_emprego (
    id BIGINT,
    competencia DATE,
    regiao_codigo TEXT,
    uf_codigo TEXT,
    setor_cnae TEXT,
    sexo_codigo TEXT,
    racacor_codigo TEXT,
    faixa_etaria TEXT,
    tipo_movimentacao_codigo TEXT,
    tipo_fluxo TEXT,
    total_registros BIGINT,
    admissoes BIGINT,
    desligamentos BIGINT,
    saldo BIGINT,
    saldo_invalido BIGINT,
    soma_salarios_validos NUMERIC(38,6),
    quantidade_salarios_validos BIGINT,
    remuneracao_media NUMERIC,
    PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS caged.revisao_salarios (
    arquivo_id INTEGER REFERENCES caged.arquivos(id), linha_origem BIGINT,
    salario_original TEXT, salario_numerico NUMERIC(38,6), classificacao TEXT,
    decisao TEXT, PRIMARY KEY (arquivo_id, linha_origem)
);
CREATE TABLE IF NOT EXISTS caged.dicionarios (
    variavel TEXT NOT NULL, codigo TEXT NOT NULL, descricao TEXT NOT NULL,
    sha256_layout TEXT NOT NULL, PRIMARY KEY (variavel,codigo)
);
REVOKE ALL ON ALL TABLES IN SCHEMA caged FROM PUBLIC;
