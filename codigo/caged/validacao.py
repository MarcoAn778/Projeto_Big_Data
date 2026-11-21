"""Preflight local. Nenhuma conexao com o PostgreSQL e aberta neste modulo."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import zipfile

import duckdb

MESES = tuple(f"{ano}{mes:02d}" for ano, meses in ((2025, range(8, 13)), (2026, range(1, 8))) for mes in meses)
TIPOS_BASE = dict(zip(
    ("id", "competencia", "regiao_codigo", "uf_codigo", "setor_cnae", "sexo_codigo",
     "racacor_codigo", "faixa_etaria", "tipo_movimentacao_codigo", "tipo_fluxo",
     "total_registros", "admissoes", "desligamentos", "saldo", "saldo_invalido",
     "soma_salarios_validos", "quantidade_salarios_validos", "remuneracao_media"),
    ("BIGINT", "DATE", *(["VARCHAR"] * 8), *(["BIGINT"] * 5), "DECIMAL(38,6)", "BIGINT", "DOUBLE"),
))
GRUPO = tuple(list(TIPOS_BASE)[1:10])
COLUNAS_ARQUIVOS = ("id", "arquivo", "competencia", "sha256_original", "bytes_original", "linhas", "csv_tratado", "sha256_tratado")
COLUNAS_AUDITORIA = ("arquivo_id", "linha_origem", "salario_original", "salario_numerico", "classificacao", "decisao")
COLUNAS_DICIONARIO = ("variavel", "codigo", "descricao", "sha256_layout")
RESUMO_SQL = """SELECT COUNT(*) AS linhas, COUNT(DISTINCT competencia) AS meses,
 SUM(total_registros) AS movimentacoes, SUM(admissoes) AS admissoes,
 SUM(desligamentos) AS desligamentos, SUM(saldo) AS saldo FROM {tabela}"""


class ErroValidacao(ValueError):
    """Erro apresentavel ao usuario, sem valores de credenciais."""


def sha256(arquivo: Path) -> str:
    digest = hashlib.sha256()
    with arquivo.open("rb") as stream:
        for bloco in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def ler_json(arquivo: Path):
    return json.loads(arquivo.read_text(encoding="utf-8-sig"))


def ler_csv(arquivo: Path, colunas: tuple[str, ...]) -> list[dict[str, str]]:
    with arquivo.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";", strict=True)
        if tuple(reader.fieldnames or ()) != colunas:
            raise ErroValidacao(f"Cabecalho inesperado: {arquivo.name}")
        linhas = list(reader)
    if any(None in linha or any(v is None for v in linha.values()) for linha in linhas):
        raise ErroValidacao(f"Quantidade de campos incorreta: {arquivo.name}")
    return linhas


def escrever_json(arquivo: Path, dados: dict) -> None:
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=arquivo.parent,
                                     prefix=".evidencia-", suffix=".tmp", delete=False) as stream:
        temporario = Path(stream.name)
        json.dump(dados, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    try:
        temporario.replace(arquivo)
    finally:
        temporario.unlink(missing_ok=True)


def extrair_base(raiz: Path) -> Path:
    destino = raiz / "resultados/base_tratada.csv"
    if not destino.exists():
        with zipfile.ZipFile(raiz / "resultados/base_tratada.zip") as pacote:
            if pacote.namelist() != ["base_tratada.csv"]:
                raise ErroValidacao("Conteudo inesperado no ZIP; extracao bloqueada.")
            # Copia para destino fixo; nomes do ZIP nunca definem o caminho de escrita.
            with pacote.open("base_tratada.csv") as origem, destino.open("wb") as saida:
                shutil.copyfileobj(origem, saida)
    return destino


@dataclass(frozen=True)
class BaseValidada:
    raiz: Path
    csv: Path
    hash_base: str
    resumo: dict[str, int]
    mensal: dict[str, int]
    soma_salarios: Decimal
    quantidade_salarios: int
    arquivos: Path
    auditorias: tuple[Path, ...]
    dicionario: Path
    contagens: dict[str, int]
    origem_auditoria: str
    hashes: dict[Path, str]

    def conferir_arquivos(self) -> None:
        for caminho, esperado in self.hashes.items():
            if not caminho.is_file() or sha256(caminho) != esperado:
                raise ErroValidacao(f"Arquivo alterado apos a validacao: {caminho.name}")

    def evidencia(self, status: str = "validado_localmente") -> dict:
        return {"status": status, "linguagem": "Python", "sha256_csv": self.hash_base,
                "resumo": [self.resumo], "ocorrencias_auditoria": self.contagens["revisao_salarios"],
                "origem_auditoria": self.origem_auditoria,
                "verificado_em_utc": datetime.now(timezone.utc).isoformat(),
                "nuvem": "Nao verificada por este comando"}


def validar_base(raiz: Path) -> BaseValidada:
    raiz = raiz.resolve()
    csv_base = extrair_base(raiz)
    resumo_path = raiz / "resultados/resumo_processamento.json"
    esperado = ler_json(resumo_path)
    hash_base = sha256(csv_base)
    if hash_base != esperado["sha256_csv"]:
        raise ErroValidacao("Hash da base difere do resumo. Carga bloqueada.")
    auditorias = tuple(raiz / f"resultados/revisao_salarios_{mes}.csv" for mes in MESES)
    arquivos = raiz / "resultados/arquivos_origem.csv"
    dicionario = raiz / "referencias/dicionarios.csv"
    anexos = [csv_base, resumo_path, dicionario]
    if arquivos.exists() or any(p.exists() for p in auditorias):
        if not arquivos.exists() or not all(p.exists() for p in auditorias):
            raise ErroValidacao("Saida de tratamento incompleta: faltam metadados ou auditorias mensais.")
        origem = "Auditorias geradas pelo tratamento local em R dos 12 meses"
    else:
        manifesto = raiz / "dados/pacote_publicado.json"
        pacote = ler_json(manifesto)
        if hash_base != pacote["sha256_csv"]:
            raise ErroValidacao("Esta base precisa da auditoria do seu proprio tratamento.")
        caminhos = {"dados/arquivos_origem.csv", "dados/auditoria_salarios.csv", "referencias/dicionarios.csv"}
        if set(pacote["arquivos"]) != caminhos:
            raise ErroValidacao("Manifesto de anexos inesperado.")
        for nome, digest in pacote["arquivos"].items():
            if sha256(raiz / nome) != digest:
                raise ErroValidacao(f"Anexo do pacote publicado alterado: {nome}")
        arquivos = raiz / "dados/arquivos_origem.csv"
        auditorias = (raiz / "dados/auditoria_salarios.csv",)
        anexos.append(manifesto)
        origem = "Auditoria historica do pacote publicado; sem nova leitura dos TXT"

    anexos.extend([arquivos, *auditorias])
    hashes_entrada = {p: sha256(p) for p in anexos}
    if hashes_entrada[csv_base] != hash_base:
        raise ErroValidacao("Base alterada durante a validacao.")
    metadados = ler_csv(arquivos, COLUNAS_ARQUIVOS)
    if len(metadados) != 12 or {r["competencia"] for r in metadados} != set(MESES):
        raise ErroValidacao("Metadados devem conter exatamente as 12 competencias do recorte.")
    if len({r["id"] for r in metadados}) != 12:
        raise ErroValidacao("IDs dos arquivos de origem duplicados.")
    for r in metadados:
        if int(r["id"]) < 1 or int(r["linhas"]) < 1 or int(r["bytes_original"]) < 1:
            raise ErroValidacao("Contagens de origem invalidas.")
        if any(not re.fullmatch("[0-9a-f]{64}", r[k]) for k in ("sha256_original", "sha256_tratado")):
            raise ErroValidacao("Hash de origem invalido.")
    revisoes = [r for p in auditorias for r in ler_csv(p, COLUNAS_AUDITORIA)]
    chaves = set()
    for r in revisoes:
        chave = (int(r["arquivo_id"]), int(r["linha_origem"]))
        if chave[0] not in {int(m["id"]) for m in metadados} or chave[1] < 2 or chave in chaves:
            raise ErroValidacao("Chave de auditoria invalida ou duplicada.")
        chaves.add(chave)
        if r["salario_numerico"]:
            try:
                valor = Decimal(r["salario_numerico"])
                if not valor.is_finite() or abs(valor) >= Decimal("1e32"):
                    raise InvalidOperation
            except InvalidOperation:
                raise ErroValidacao("Valor da auditoria nao cabe em NUMERIC(38,6).") from None
    if len(auditorias) == 1 and len(revisoes) != pacote["ocorrencias_salariais"]:
        raise ErroValidacao("Quantidade de ocorrencias da auditoria historica divergente.")
    rotulos = ler_csv(dicionario, COLUNAS_DICIONARIO)
    if not rotulos or any(not all(r.values()) for r in rotulos) or len({(r["variavel"], r["codigo"]) for r in rotulos}) != len(rotulos):
        raise ErroValidacao("Dicionario vazio, incompleto ou com chaves duplicadas.")
    with csv_base.open(encoding="utf-8", newline="") as stream:
        if next(csv.reader(stream, delimiter=";")) != list(TIPOS_BASE):
            raise ErroValidacao("Cabecalho da base tratada inesperado.")
    with duckdb.connect() as con:
        con.execute("SET memory_limit='2GB'")
        con.execute("SET threads=2")
        con.execute("""CREATE TABLE base_validada AS SELECT * FROM read_csv(
            ?, delim=';', header=true, columns=?, nullstr='', strict_mode=true)""",
            [str(csv_base), TIPOS_BASE])
        cursor = con.execute(RESUMO_SQL.format(tabela="base_validada"))
        resumo = dict(zip((d[0] for d in cursor.description), map(int, cursor.fetchone())))
        if resumo != esperado["resumo"][0]:
            raise ErroValidacao("Totais da base diferentes do resumo de processamento.")
        mensal = dict(con.execute("SELECT strftime(competencia,'%Y%m'), CAST(SUM(total_registros) AS BIGINT) FROM base_validada GROUP BY 1").fetchall())
        if mensal != {r["competencia"]: int(r["linhas"]) for r in metadados}:
            raise ErroValidacao("Contagens mensais divergentes da origem.")
        nulos = " OR ".join(f"{c} IS NULL" for c in list(TIPOS_BASE)[:-1])
        erros = con.execute(f"""SELECT COUNT(*) FROM base_validada WHERE {nulos}
          OR id<1 OR competencia<>date_trunc('month',competencia) OR total_registros<1
          OR admissoes<0 OR desligamentos<0 OR saldo_invalido<0
          OR total_registros<>admissoes+desligamentos+saldo_invalido OR saldo<>admissoes-desligamentos
          OR quantidade_salarios_validos<0 OR quantidade_salarios_validos>total_registros
          OR soma_salarios_validos<0
          OR (quantidade_salarios_validos=0 AND (soma_salarios_validos<>0 OR remuneracao_media IS NOT NULL))
          OR (quantidade_salarios_validos>0 AND (remuneracao_media IS NULL OR NOT isfinite(remuneracao_media)
              OR abs(remuneracao_media-soma_salarios_validos/quantidade_salarios_validos)>0.000001))""").fetchone()[0]
        grupos = ",".join(GRUPO)
        duplicados = con.execute(f"SELECT COUNT(*) FROM (SELECT {grupos} FROM base_validada GROUP BY ALL HAVING COUNT(*)>1)").fetchone()[0]
        ids = con.execute("SELECT COUNT(*)-COUNT(DISTINCT id) FROM base_validada").fetchone()[0]
        if erros or duplicados or ids:
            raise ErroValidacao("Indicadores inconsistentes ou IDs/grupos duplicados.")
        soma, quantidade = con.execute("SELECT SUM(soma_salarios_validos), SUM(quantidade_salarios_validos) FROM base_validada").fetchone()
    base = BaseValidada(raiz, csv_base, hash_base, resumo, mensal, soma, int(quantidade),
                         arquivos, auditorias, dicionario,
                         {"arquivos": len(metadados), "revisao_salarios": len(revisoes), "dicionarios": len(rotulos)},
                         origem, hashes_entrada)
    base.conferir_arquivos()
    return base
