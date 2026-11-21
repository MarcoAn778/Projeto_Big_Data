"""Consultas parametrizadas da camada de visualização."""

from dataclasses import asdict, dataclass
from datetime import date

import psycopg

from caged.banco import conectar
from caged.validacao import ErroValidacao


@dataclass(frozen=True)
class Filtros:
    inicio: date
    fim: date
    regioes: tuple[str, ...] = ()
    ufs: tuple[str, ...] = ()
    setores: tuple[str, ...] = ()
    sexos: tuple[str, ...] = ()
    racas: tuple[str, ...] = ()
    idades: tuple[str, ...] = ()

    def parametros(self):
        return {
            nome: (list(valor) or None) if isinstance(valor, tuple) else valor
            for nome, valor in asdict(self).items()
        }


ROTULOS = """
    SELECT competencia, regiao_codigo, uf_codigo, setor_cnae, sexo_codigo,
           racacor_codigo, faixa_etaria, tipo_fluxo, admissoes, desligamentos,
           soma_salarios_validos, quantidade_salarios_validos,
           CASE WHEN regiao = 'Codigo ausente no layout'
                THEN 'Região sem rótulo (' || regiao_codigo || ')' ELSE regiao END AS regiao,
           CASE WHEN uf = 'Codigo ausente no layout'
                THEN 'UF sem rótulo (' || uf_codigo || ')' ELSE uf END AS uf,
           CASE WHEN setor_economico = 'Codigo ausente no layout'
                THEN 'Setor sem rótulo (' || setor_cnae || ')' ELSE setor_economico END AS setor,
           CASE WHEN sexo = 'Codigo ausente no layout'
                THEN 'Sexo sem rótulo (' || sexo_codigo || ')' ELSE sexo END AS sexo,
           CASE racacor_codigo
                WHEN '9' THEN 'Não identificado'
                WHEN '6' THEN 'Não informada'
                WHEN 'Nao informado' THEN 'Sem código'
                ELSE CASE WHEN raca_cor = 'Codigo ausente no layout'
                     THEN 'Raça/cor sem rótulo (' || racacor_codigo || ')' ELSE raca_cor END
           END AS raca
    FROM caged.v_indicadores_emprego
"""

CATALOGO = f"""
WITH dados AS ({ROTULOS})
SELECT CASE
           WHEN GROUPING(competencia) = 0 THEN 'competencias'
           WHEN GROUPING(uf_codigo) = 0 THEN 'ufs'
           WHEN GROUPING(regiao) = 0 THEN 'regioes'
           WHEN GROUPING(setor_cnae) = 0 THEN 'setores'
           WHEN GROUPING(sexo_codigo) = 0 THEN 'sexos'
           WHEN GROUPING(racacor_codigo) = 0 THEN 'racas'
           ELSE 'idades'
       END AS filtro,
       COALESCE(competencia::text, uf_codigo, regiao_codigo, setor_cnae,
                sexo_codigo, racacor_codigo, faixa_etaria) AS codigo,
       COALESCE(to_char(competencia, 'MM/YYYY'), uf, regiao, setor, sexo, raca,
                NULLIF(faixa_etaria, 'Nao informado ou invalido'),
                'Não informado ou inválido') AS rotulo,
       CASE WHEN GROUPING(uf_codigo) = 0 THEN regiao_codigo END AS regiao_uf
FROM dados
GROUP BY GROUPING SETS ((competencia), (uf_codigo, uf, regiao_codigo),
                       (regiao_codigo, regiao), (setor_cnae, setor),
                       (sexo_codigo, sexo), (racacor_codigo, raca), (faixa_etaria))
ORDER BY filtro, codigo, rotulo, regiao_uf
"""

RECORTE = f"""
WITH base AS (
    {ROTULOS}
    WHERE competencia BETWEEN %(inicio)s AND %(fim)s
      AND (%(regioes)s::text[] IS NULL OR regiao_codigo = ANY(%(regioes)s))
      AND (%(ufs)s::text[] IS NULL OR uf_codigo = ANY(%(ufs)s))
      AND (%(setores)s::text[] IS NULL OR setor_cnae = ANY(%(setores)s))
      AND (%(idades)s::text[] IS NULL OR faixa_etaria = ANY(%(idades)s))
)
"""

SEXO = "(%(sexos)s::text[] IS NULL OR sexo_codigo = ANY(%(sexos)s))"
RACA = "(%(racas)s::text[] IS NULL OR racacor_codigo = ANY(%(racas)s))"

INDICADORES = {
    "saldo": RECORTE + f"""
        SELECT competencia, sexo, raca,
               SUM(admissoes)::bigint AS admissoes, SUM(desligamentos)::bigint AS desligamentos,
               (SUM(admissoes) - SUM(desligamentos))::bigint AS saldo
        FROM base WHERE {SEXO} AND {RACA}
        GROUP BY competencia, sexo, raca
        ORDER BY competencia, sexo, raca
    """,
    "turnover": RECORTE + f"""
        SELECT competencia, setor, sexo, raca,
               SUM(admissoes)::bigint AS admissoes, SUM(desligamentos)::bigint AS desligamentos,
               SUM(desligamentos) / NULLIF(SUM(admissoes), 0) AS razao
        FROM base WHERE {SEXO} AND {RACA}
        GROUP BY competencia, setor, sexo, raca
        ORDER BY competencia, setor, sexo, raca
    """,
    "salario": RECORTE + f"""
        , medias AS (
            SELECT sexo, raca, SUM(quantidade_salarios_validos)::bigint AS salarios_validos,
                   SUM(soma_salarios_validos) / NULLIF(SUM(quantidade_salarios_validos), 0) AS media
            FROM base WHERE tipo_fluxo = 'Admissao' AND {SEXO} AND {RACA}
            GROUP BY sexo, raca
        )
        SELECT *, media / NULLIF(MAX(media) OVER (), 0) AS razao
        FROM medias ORDER BY media DESC NULLS LAST, sexo, raca
    """,
    "participacao": RECORTE + f"""
        , por_setor AS (
            SELECT setor,
                   SUM(admissoes) FILTER (WHERE {RACA}) AS total_adm_raca,
                   SUM(desligamentos) FILTER (WHERE {RACA}) AS total_des_raca,
                   SUM(admissoes) FILTER (WHERE {RACA} AND sexo_codigo = '3') AS mulheres_adm,
                   SUM(desligamentos) FILTER (WHERE {RACA} AND sexo_codigo = '3') AS mulheres_des,
                   SUM(admissoes) FILTER (WHERE {SEXO}) AS total_adm_sexo,
                   SUM(desligamentos) FILTER (WHERE {SEXO}) AS total_des_sexo,
                   SUM(admissoes) FILTER (WHERE {SEXO} AND racacor_codigo IN ('2', '3')) AS negras_adm,
                   SUM(desligamentos) FILTER (WHERE {SEXO} AND racacor_codigo IN ('2', '3')) AS negras_des
            FROM base GROUP BY setor
        )
        SELECT setor, grupo, fluxo, quantidade::bigint, total::bigint,
               quantidade / NULLIF(total, 0) AS proporcao
        FROM por_setor
        CROSS JOIN LATERAL (VALUES
            ('Mulheres', 'Admissões', COALESCE(mulheres_adm, 0), COALESCE(total_adm_raca, 0)),
            ('Mulheres', 'Desligamentos', COALESCE(mulheres_des, 0), COALESCE(total_des_raca, 0)),
            ('Pessoas negras', 'Admissões', COALESCE(negras_adm, 0), COALESCE(total_adm_sexo, 0)),
            ('Pessoas negras', 'Desligamentos', COALESCE(negras_des, 0), COALESCE(total_des_sexo, 0))
        ) AS linhas(grupo, fluxo, quantidade, total)
        ORDER BY setor, grupo, fluxo
    """,
}


def consultar(comando, parametros=None):
    """Abre uma conexão TLS curta e limita todas as consultas à leitura."""
    try:
        with conectar() as conn, conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout = '20s'")
            return conn.execute(comando, parametros).fetchall()
    except psycopg.Error:
        raise ErroValidacao("Não foi possível consultar os indicadores no PostgreSQL.") from None


def carregar_indicador(indicador, filtros):
    return consultar(INDICADORES[indicador], filtros.parametros())
