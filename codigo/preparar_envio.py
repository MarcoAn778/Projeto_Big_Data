"""Gera pacote limpo para upload manual; nao publica nada no GitHub."""
from __future__ import annotations

import argparse
import io
from pathlib import Path
import tempfile
import zipfile

from caged.seguranca import verificar_conteudo
from caged.validacao import ErroValidacao, MESES, ler_json, validar_base


def selecionar_arquivos(raiz: Path) -> list[Path]:
    nomes = {"README.md", "LEIA_ME_ETAPA_ATUAL.md", ".gitignore", ".gitattributes",
             ".env.example", ".streamlit/config.toml", "requirements.txt", "requirements-lock.txt"}
    nomes.update(p.name for p in raiz.glob("*.pdf"))
    regras = {"codigo": {".py", ".R", ".ps1"}, "sql": {".sql"},
              "dashboard": {".py"}, "documentacao": {".md", ".png"}, "dados": {".csv", ".json"}}
    for pasta, extensoes in regras.items():
        for p in (raiz / pasta).rglob("*"):
            if p.is_file() and p.suffix in extensoes and not any(s.startswith(".") or s == "__pycache__" for s in p.relative_to(raiz / pasta).parts):
                nomes.add(p.relative_to(raiz).as_posix())
    for p in (raiz / "infraestrutura").rglob("*"):
        relativo = p.relative_to(raiz / "infraestrutura")
        if p.is_file() and ".terraform" not in relativo.parts and (
                p.suffix in {".tf", ".ps1"} or p.name in {".terraform.lock.hcl", "terraform.tfvars.example"}
                or (relativo.parts[0] == "tests" and p.name.endswith(".tftest.hcl"))):
            nomes.add(p.relative_to(raiz).as_posix())
    for p in (raiz / "testes").glob("*"):
        if p.is_file() and (p.suffix in {".py", ".R"} or p.name == "originais_conferidos.json"):
            nomes.add(p.relative_to(raiz).as_posix())
    nomes.update({"referencias/dicionarios.csv", "resultados/resumo_processamento.json",
                  "resultados/arquivos_origem.csv", *[f"resultados/revisao_salarios_{m}.csv" for m in MESES]})
    evidencias = {"resultado_processamento.json", "validacao_base_atual.json", "carga_nuvem.json", "carga_nuvem_historica.json",
                 "carga_python_teste_local.json", "preservacao_etapa_anterior.json", "dicionario_colunas.csv", "qualidade_mensal.csv", "resumo_mensal.csv",
                 *[f"anomalias_{m}.csv" for m in MESES]}
    nomes.update("verificacoes/" + n for n in evidencias)
    return [raiz / n for n in sorted(nomes) if (raiz / n).is_file()]


def gerar_pacote(raiz: Path, saida: Path, rascunho: bool = False) -> None:
    raiz, saida = raiz.resolve(), saida.resolve()
    base = validar_base(raiz)
    if not rascunho:
        evidencia = raiz / "verificacoes/carga_nuvem.json"
        if not evidencia.exists():
            raise ErroValidacao("Falta a evidencia real de nuvem. Execute a carga e verificar-nuvem antes de preparar o envio final.")
        registro = ler_json(evidencia)
        if registro.get("status") != "carga_nuvem_validada" or registro.get("sha256_csv") != base.hash_base or registro.get("resumo") != [base.resumo] or registro.get("tls_verificado") is not True:
            raise ErroValidacao("A evidencia de nuvem nao corresponde a base validada.")
    selecionados = selecionar_arquivos(raiz)
    problemas = verificar_conteudo(raiz, selecionados)
    if problemas:
        raise ErroValidacao("Revise arquivos que parecem conter segredos: " + ", ".join(problemas))
    # Atualiza a base compactada a partir do CSV efetivamente validado, inclusive apos novo tratamento.
    anterior = raiz / "resultados/base_tratada.zip"
    dados_base = None
    if anterior.exists():
        from hashlib import sha256
        with zipfile.ZipFile(anterior) as interna:
            if interna.namelist() == ["base_tratada.csv"] and sha256(interna.read("base_tratada.csv")).hexdigest() == base.hash_base:
                dados_base = anterior.read_bytes()
    if dados_base is None:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as interna:
            interna.write(base.csv, "base_tratada.csv")
        dados_base = buffer.getvalue()
    saida.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=saida.parent, prefix=".pacote-", suffix=".tmp", delete=False) as stream:
        temporario = Path(stream.name)
    try:
        with zipfile.ZipFile(temporario, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as pacote:
            for arquivo in selecionados:
                pacote.write(arquivo, "Projeto_Big_Data/" + arquivo.relative_to(raiz).as_posix())
            pacote.writestr("Projeto_Big_Data/resultados/base_tratada.zip", dados_base)
        base.conferir_arquivos()
        temporario.replace(saida)
    finally:
        temporario.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rascunho", action="store_true", help="Permite pacote local antes da carga na nuvem.")
    parser.add_argument("--saida", type=Path)
    args = parser.parse_args()
    raiz = Path(__file__).resolve().parents[1]
    saida = args.saida or raiz / "output/envio" / ("PROJETO_BIG_DATA_RASCUNHO.zip" if args.rascunho else "PROJETO_BIG_DATA_ENVIO.zip")
    try:
        gerar_pacote(raiz, saida, args.rascunho)
    except ErroValidacao as erro:
        print(f"ERRO: {erro}")
        return 1
    print("Pacote local criado:", saida.resolve())
    print("Rascunho: implantacao na nuvem ainda precisa ser concluida." if args.rascunho else "Pacote para revisao e upload manual. Confira tambem o status no README.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
