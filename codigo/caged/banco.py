"""Conexao TLS e carga atomica com Psycopg 3. Nao apaga tabelas existentes."""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from .validacao import (BaseValidada, ErroValidacao, GRUPO, RESUMO_SQL, TIPOS_BASE,
                         COLUNAS_ARQUIVOS, COLUNAS_AUDITORIA, COLUNAS_DICIONARIO)


def parametros_conexao(ambiente=None) -> dict:
    ambiente = os.environ if ambiente is None else ambiente
    nomes = ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD", "PGSSLROOTCERT")
    faltantes = [n for n in nomes if not ambiente.get(n, "").strip()]
    if faltantes:
        raise ErroValidacao("Configure localmente as variaveis: " + ", ".join(faltantes))
    try:
        porta = int(ambiente["PGPORT"])
        if not 1 <= porta <= 65535:
            raise ValueError
    except ValueError:
        raise ErroValidacao("PGPORT invalida.") from None
    certificado = Path(ambiente["PGSSLROOTCERT"]).expanduser().resolve()
    if not certificado.is_file():
        raise ErroValidacao("Certificado CA de PGSSLROOTCERT nao encontrado.")
    return {"host": ambiente["PGHOST"], "port": porta, "dbname": ambiente["PGDATABASE"],
            "user": ambiente["PGUSER"], "password": ambiente["PGPASSWORD"],
            "sslrootcert": str(certificado), "sslmode": "verify-full", "connect_timeout": 15,
            "application_name": "projeto_big_data_python", "client_encoding": "UTF8",
            "autocommit": True, "row_factory": dict_row}


def conectar():
    certificado_pem = os.environ.get("PGSSLROOTCERT_PEM")
    try:
        if not certificado_pem or os.environ.get("PGSSLROOTCERT"):
            return psycopg.connect(**parametros_conexao())
        with TemporaryDirectory(prefix="caged-ca-") as diretorio:
            certificado = Path(diretorio) / "ca.pem"
            certificado.write_text(certificado_pem, encoding="ascii")
            ambiente = {**os.environ, "PGSSLROOTCERT": str(certificado)}
            return psycopg.connect(**parametros_conexao(ambiente))
    except (OSError, UnicodeError):
        raise ErroValidacao("Não foi possível usar o certificado CA configurado.") from None
    except psycopg.Error:
        raise ErroValidacao("Conexao falhou. Confira IP autorizado, porta, CA e credenciais locais.") from None


def confirmar_tls(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()")
        registro = cur.fetchone()
        if not registro or registro["ssl"] is not True:
            raise ErroValidacao("A sessao PostgreSQL nao confirmou TLS.")


def copiar_csv(cur, tabela: str, colunas, caminho: Path) -> None:
    comando = sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ';', NULL '', ENCODING 'UTF8')").format(
        sql.Identifier("caged", tabela), sql.SQL(",").join(map(sql.Identifier, colunas)))
    # COPY recebe os bytes do CSV, preservando decimais e nulos sem passar por float.
    with caminho.open("rb") as stream, cur.copy(comando) as copia:
        for bloco in iter(lambda: stream.read(1024 * 1024), b""):
            copia.write(bloco)


def verificar_banco(conn, base: BaseValidada) -> dict:
    confirmar_tls(conn)
    with conn.cursor() as cur:
        cur.execute(RESUMO_SQL.format(tabela="caged.v_indicadores_emprego"))
        resumo = {k: int(v) for k, v in cur.fetchone().items()}
        if resumo != base.resumo:
            raise ErroValidacao("Totais no PostgreSQL divergentes da base local.")
        cur.execute("SELECT to_char(competencia,'YYYYMM') AS mes, SUM(total_registros) AS n FROM caged.indicadores_emprego GROUP BY 1")
        if {r["mes"]: int(r["n"]) for r in cur.fetchall()} != base.mensal:
            raise ErroValidacao("Contagens mensais no PostgreSQL divergentes.")
        cur.execute("SELECT SUM(soma_salarios_validos) AS soma, SUM(quantidade_salarios_validos) AS quantidade FROM caged.indicadores_emprego")
        salarios = cur.fetchone()
        if salarios["soma"] != base.soma_salarios or int(salarios["quantidade"]) != base.quantidade_salarios:
            raise ErroValidacao("Medidas salariais divergentes no PostgreSQL.")
        cur.execute("SELECT sha256_csv,linhas_agregadas,eventos_representados FROM caged.cargas")
        cargas = cur.fetchall()
        if len(cargas) != 1 or cargas[0]["sha256_csv"] != base.hash_base or int(cargas[0]["linhas_agregadas"]) != base.resumo["linhas"] or int(cargas[0]["eventos_representados"]) != base.resumo["movimentacoes"]:
            raise ErroValidacao("Controle da carga divergente.")
        for nome, n in base.contagens.items():
            cur.execute(sql.SQL("SELECT COUNT(*) AS n FROM {}").format(sql.Identifier("caged", nome)))
            if cur.fetchone()["n"] != n:
                raise ErroValidacao(f"Contagem divergente na tabela {nome}.")
        nulos = " OR ".join(f"{c} IS NULL" for c in list(TIPOS_BASE)[:-1])
        cur.execute(f"""SELECT COUNT(*) AS n FROM caged.indicadores_emprego WHERE {nulos}
          OR id<1 OR total_registros<1 OR admissoes<0 OR desligamentos<0 OR saldo_invalido<0
          OR total_registros<>admissoes+desligamentos+saldo_invalido OR saldo<>admissoes-desligamentos
          OR quantidade_salarios_validos<0 OR quantidade_salarios_validos>total_registros OR soma_salarios_validos<0""")
        if cur.fetchone()["n"]:
            raise ErroValidacao("Indicadores inconsistentes no PostgreSQL.")
        grupo = sql.SQL(",").join(map(sql.Identifier, GRUPO))
        cur.execute(sql.SQL("SELECT COUNT(*) AS n FROM (SELECT {} FROM caged.indicadores_emprego GROUP BY {} HAVING COUNT(*)>1) AS duplicados").format(grupo, grupo))
        if cur.fetchone()["n"]:
            raise ErroValidacao("Grupos duplicados no PostgreSQL.")
        cur.execute("SELECT pg_database_size(current_database()) AS bytes")
        tamanho = int(cur.fetchone()["bytes"])
    return {"status": "carga_nuvem_validada", "linguagem": "Python", "sha256_csv": base.hash_base,
            "resumo": [resumo], "ocorrencias_auditoria": base.contagens["revisao_salarios"],
            "tls_verificado": True, "somas_salariais_conferidas": True, "tamanho_banco_bytes": tamanho,
            "verificado_em_utc": datetime.now(timezone.utc).isoformat()}


def carregar(conn, base: BaseValidada) -> None:
    if not conn.autocommit:
        raise ErroValidacao("A carga exige conexao autocommit com transacao explicita.")
    base.conferir_arquivos()
    confirmar_tls(conn)
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("SET LOCAL lock_timeout='30s'")
            cur.execute((base.raiz / "sql/estrutura.sql").read_text(encoding="utf-8-sig"))
            cur.execute((base.raiz / "sql/indices_python.sql").read_text(encoding="utf-8-sig"))
            cur.execute("LOCK TABLE caged.indicadores_emprego,caged.arquivos,caged.revisao_salarios,caged.cargas,caged.dicionarios IN ACCESS EXCLUSIVE MODE")
            for tabela in ("indicadores_emprego", "arquivos", "revisao_salarios", "cargas", "dicionarios"):
                cur.execute(sql.SQL("SELECT EXISTS (SELECT 1 FROM {}) AS ocupado").format(sql.Identifier("caged", tabela)))
                if cur.fetchone()["ocupado"]:
                    raise ErroValidacao("O schema ja tem dados. Use verificar-nuvem para conferir; nenhuma tabela foi apagada.")
            copiar_csv(cur, "indicadores_emprego", TIPOS_BASE, base.csv)
            copiar_csv(cur, "arquivos", COLUNAS_ARQUIVOS, base.arquivos)
            for auditoria in base.auditorias:
                copiar_csv(cur, "revisao_salarios", COLUNAS_AUDITORIA, auditoria)
            copiar_csv(cur, "dicionarios", COLUNAS_DICIONARIO, base.dicionario)
            cur.execute("""INSERT INTO caged.cargas
                (sha256_csv,versao_script,periodo_inicio,periodo_fim,linhas_agregadas,eventos_representados)
                VALUES (%s,%s,%s,%s,%s,%s)""", (base.hash_base, "marco2-python", "202508", "202607",
                    base.resumo["linhas"], base.resumo["movimentacoes"]))
            cur.execute((base.raiz / "sql/view_rotulos.sql").read_text(encoding="utf-8-sig"))
        base.conferir_arquivos()
        verificar_banco(conn, base)  # Se falhar, o bloco inteiro sofre rollback.
    # COMMIT ja aconteceu aqui. O chamador consulta novamente antes de gravar evidencia.
