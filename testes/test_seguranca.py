import sys
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "codigo"))

from caged.seguranca import BUSCA, caminho_privado, verificar_indice


class TesteSeguranca(unittest.TestCase):
    @unittest.skipUnless((RAIZ / ".git").exists(), "Exige checkout Git do projeto")
    def test_nenhum_segredo_versionado(self):
        self.assertEqual(verificar_indice(RAIZ), [])

    def test_detector_reconhece_exemplos_sem_bloquear_modelos(self):
        self.assertTrue(caminho_privado("infraestrutura/terraform.tfstate"))
        self.assertTrue(caminho_privado(".env.local"))
        self.assertFalse(caminho_privado(".env.example"))
        self.assertFalse(caminho_privado(".streamlit/config.toml"))
        self.assertIsNotNone(BUSCA.search("AIVEN_TOKEN" + "=valor-ficticio"))
        self.assertIsNotNone(BUSCA.search("postgresql:" + "//teste:teste@localhost/banco"))
        self.assertIsNone(BUSCA.search("PGPASSWORD=\nPGSSLROOTCERT=\n"))
