"""Testes locais: python -m unittest discover -s testes -p 'test_*.py' -v."""
import csv
from decimal import Decimal
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "codigo"))
from caged.validacao import (MESES, TIPOS_BASE, COLUNAS_ARQUIVOS, COLUNAS_AUDITORIA,
    COLUNAS_DICIONARIO, ErroValidacao, sha256, validar_base)
from caged.banco import parametros_conexao
from preparar_envio import selecionar_arquivos, gerar_pacote


def csv_escrever(path, colunas, linhas):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter=";", lineterminator="\n")
        writer.writerow(colunas)
        writer.writerows(linhas)


def criar_fixture(raiz):
    for nome in ("resultados", "referencias", "sql"):
        (raiz / nome).mkdir()
    for nome in ("estrutura.sql", "view_rotulos.sql", "indices_python.sql"):
        shutil.copyfile(RAIZ / "sql" / nome, raiz / "sql" / nome)
    linhas = []
    for i, mes in enumerate(MESES, 1):
        valor = "9007199254740992.123456" if i == 1 else "2469.135780"
        quantidade = 1 if i == 1 else 2
        media = valor if i == 1 else "1234.567890"
        linhas.append([i, mes[:4] + "-" + mes[4:] + "-01", "1", "11", "A", "1", "1", "18 a 24",
                       "10", "Admissao", 3, 2, 1, 1, 0, valor, quantidade, media])
        csv_escrever(raiz / f"resultados/revisao_salarios_{mes}.csv", COLUNAS_AUDITORIA, [])
    csv_escrever(raiz / "referencias/dicionarios.csv", COLUNAS_DICIONARIO,
                 [("uf", "11", "Rondônia", "a" * 64)])
    atualizar_fixture(raiz, linhas)
    return linhas


def atualizar_fixture(raiz, linhas):
    base = raiz / "resultados/base_tratada.csv"
    csv_escrever(base, TIPOS_BASE, linhas)
    resumo = {"linhas": len(linhas), "meses": len({r[1] for r in linhas}),
              "movimentacoes": sum(r[10] for r in linhas), "admissoes": sum(r[11] for r in linhas),
              "desligamentos": sum(r[12] for r in linhas), "saldo": sum(r[13] for r in linhas)}
    (raiz / "resultados/resumo_processamento.json").write_text(
        json.dumps({"sha256_csv": sha256(base), "resumo": [resumo]}), encoding="utf-8")
    registros = []
    for i, mes in enumerate(MESES, 1):
        total = sum(r[10] for r in linhas if str(r[1]).replace("-", "")[:6] == mes)
        registros.append([i, f"CAGEDMOV{mes}.txt", mes, "a" * 64, 1, total, f"agregado_{mes}.csv", "b" * 64])
    csv_escrever(raiz / "resultados/arquivos_origem.csv", COLUNAS_ARQUIVOS, registros)


class TesteFluxoPython(unittest.TestCase):
    def setUp(self):
        self.pasta_temporaria = (RAIZ / "tmp/testes_python").resolve()
        self.pasta_temporaria.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.pasta_temporaria)
        self.raiz = Path(self.temp.name)
        self.linhas = criar_fixture(self.raiz)

    def tearDown(self):
        assert Path(self.temp.name).resolve().is_relative_to(self.pasta_temporaria)
        self.temp.cleanup()

    def test_base_valida_e_decimal_acima_da_precisao_de_float(self):
        base = validar_base(self.raiz)
        self.assertEqual(base.resumo["movimentacoes"], 36)
        self.assertEqual(base.soma_salarios, Decimal("9007199254768152.617036"))
        self.assertEqual(base.contagens["revisao_salarios"], 0)

    def test_hash_adulterado_bloqueado(self):
        with (self.raiz / "resultados/base_tratada.csv").open("a") as stream:
            stream.write("alteracao")
        with self.assertRaisesRegex(ErroValidacao, "Hash da base difere"):
            validar_base(self.raiz)

    def test_grupo_duplicado_mesmo_com_id_novo_bloqueado(self):
        repetida = list(self.linhas[0])
        repetida[0] = 13
        self.linhas.append(repetida)
        atualizar_fixture(self.raiz, self.linhas)
        with self.assertRaisesRegex(ErroValidacao, "IDs/grupos duplicados"):
            validar_base(self.raiz)

    def test_saldo_inconsistente_bloqueado(self):
        self.linhas[0][13] = 9
        atualizar_fixture(self.raiz, self.linhas)
        with self.assertRaisesRegex(ErroValidacao, "Indicadores inconsistentes"):
            validar_base(self.raiz)

    def test_auditoria_mensal_incompleta_bloqueada(self):
        (self.raiz / f"resultados/revisao_salarios_{MESES[0]}.csv").unlink()
        with self.assertRaisesRegex(ErroValidacao, "Saida de tratamento incompleta"):
            validar_base(self.raiz)

    def test_mudanca_apos_validacao_bloqueada(self):
        base = validar_base(self.raiz)
        with base.dicionario.open("a", encoding="utf-8") as stream:
            stream.write("alteracao")
        with self.assertRaisesRegex(ErroValidacao, "Arquivo alterado apos"):
            base.conferir_arquivos()

    def test_zip_com_caminho_externo_bloqueado(self):
        import zipfile
        (self.raiz / "resultados/base_tratada.csv").unlink()
        with zipfile.ZipFile(self.raiz / "resultados/base_tratada.zip", "w") as pacote:
            pacote.writestr("../indevido.csv", "dados")
        with self.assertRaisesRegex(ErroValidacao, "Conteudo inesperado no ZIP"):
            validar_base(self.raiz)
        self.assertFalse((self.raiz / "indevido.csv").exists())

    def test_conexao_exige_certificado_e_nao_mostra_senha(self):
        ambiente = dict(PGHOST="localhost", PGPORT="55439", PGDATABASE="teste",
                        PGUSER="teste", PGPASSWORD="senha-ficticia-do-teste", PGSSLROOTCERT="nao-existe.pem")
        with self.assertRaisesRegex(ErroValidacao, "Certificado CA") as erro:
            parametros_conexao(ambiente)
        self.assertNotIn(ambiente["PGPASSWORD"], str(erro.exception))
        ambiente["PGSSLROOTCERT"] = str(self.raiz / "referencias/dicionarios.csv")
        parametros = parametros_conexao(ambiente)
        self.assertEqual(parametros["sslmode"], "verify-full")

    def test_pacote_nao_inclui_segredos_state_venv_ou_csv_expandido(self):
        for nome in (".env", "infraestrutura/terraform.tfvars", "infraestrutura/terraform.tfstate",
                     "infraestrutura/.terraform/arquivo.tf", ".venv/segredo.py", "segredos/senha.py"):
            path = self.raiz / nome
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("nao publicar", encoding="utf-8")
        selecionados = {p.relative_to(self.raiz).as_posix() for p in selecionar_arquivos(self.raiz)}
        self.assertNotIn("resultados/base_tratada.csv", selecionados)
        self.assertNotIn("infraestrutura/terraform.tfvars", selecionados)
        self.assertNotIn("infraestrutura/terraform.tfstate", selecionados)
        self.assertFalse(any(".venv" in n or "segredos" in n or ".terraform/" in n for n in selecionados))
        self.assertNotIn(".env", selecionados)

    def test_envio_final_bloqueado_sem_evidencia_real(self):
        with self.assertRaisesRegex(ErroValidacao, "Falta a evidencia real de nuvem"):
            gerar_pacote(self.raiz, self.raiz / "envio.zip")
        self.assertFalse((self.raiz / "envio.zip").exists())


if __name__ == "__main__":
    unittest.main()
