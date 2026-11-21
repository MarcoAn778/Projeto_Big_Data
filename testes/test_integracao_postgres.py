"""Integracao opt-in, somente em PostgreSQL descartavel na interface local."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_fluxo_python import criar_fixture, RAIZ
from caged import banco
from caged.validacao import ErroValidacao, validar_base


@unittest.skipUnless(os.getenv("CAGED_TESTE_POSTGRES_LOCAL") == "1", "Exige PostgreSQL local descartavel com TLS")
class TestePostgreSQL(unittest.TestCase):
    def setUp(self):
        # Nunca executar limpeza de schema em um endpoint remoto.
        if os.getenv("PGHOST") not in ("localhost", "127.0.0.1"):
            self.fail("Teste de integracao restrito a loopback.")
        self.conn = banco.conectar()
        self.addCleanup(self.conn.close)
        self.conn.execute("DROP SCHEMA IF EXISTS caged CASCADE")
        self.pasta_temporaria = (RAIZ / "tmp/testes_python").resolve()
        self.pasta_temporaria.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.pasta_temporaria)
        assert Path(self.temp.name).resolve().is_relative_to(self.pasta_temporaria)
        self.addCleanup(self.temp.cleanup)
        raiz = Path(self.temp.name)
        criar_fixture(raiz)
        self.base = validar_base(raiz)

    def test_copy_decimal_unicode_tls_e_bloqueio_de_segunda_carga(self):
        from decimal import Decimal
        banco.carregar(self.conn, self.base)
        evidencia = banco.verificar_banco(self.conn, self.base)
        self.assertTrue(evidencia["tls_verificado"])
        valor = self.conn.execute("SELECT soma_salarios_validos FROM caged.indicadores_emprego WHERE id=1").fetchone()
        self.assertEqual(valor["soma_salarios_validos"], Decimal("9007199254740992.123456"))
        rotulo = self.conn.execute("SELECT uf FROM caged.v_indicadores_emprego LIMIT 1").fetchone()
        self.assertEqual(rotulo["uf"], "Rondônia")
        with self.assertRaisesRegex(ErroValidacao, "schema ja tem dados"):
            banco.carregar(self.conn, self.base)
        self.assertEqual(banco.verificar_banco(self.conn, self.base)["resumo"][0]["linhas"], 12)

    def test_erro_antes_do_commit_reverte_estrutura_e_carga(self):
        with patch.object(banco, "verificar_banco", side_effect=ErroValidacao("Falha simulada antes do commit")):
            with self.assertRaisesRegex(ErroValidacao, "Falha simulada"):
                banco.carregar(self.conn, self.base)
        schema = self.conn.execute("SELECT to_regnamespace('caged') AS nome").fetchone()
        self.assertIsNone(schema["nome"])
        banco.carregar(self.conn, self.base)
        self.assertEqual(banco.verificar_banco(self.conn, self.base)["resumo"][0]["linhas"], 12)
