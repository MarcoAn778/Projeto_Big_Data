"""Testes somente leitura no PostgreSQL carregado, habilitados explicitamente."""

from decimal import Decimal
import os
from pathlib import Path
import sys
import unittest


RAIZ = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(RAIZ), str(RAIZ / "codigo")]

from caged.banco import confirmar_tls, conectar
from dashboard.consultas import CATALOGO, Filtros, carregar_indicador, consultar


@unittest.skipUnless(os.getenv("CAGED_TESTE_DASHBOARD") == "1", "Requer PostgreSQL carregado e PG* configurado")
class TesteIndicadores(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datas = consultar("""
            SELECT MIN(competencia) AS inicio, MAX(competencia) AS fim
            FROM caged.v_indicadores_emprego
        """)[0]
        cls.recorte = Filtros(**cls.datas)

    def test_conexao_tls_e_dimensoes(self):
        with conectar() as conn:
            confirmar_tls(conn)
        self.assertIsNotNone(self.datas["inicio"])
        opcoes = consultar(CATALOGO)
        self.assertEqual({r["filtro"] for r in opcoes},
                         {"competencias", "regioes", "ufs", "setores", "sexos", "racas", "idades"})
        racas = {r["codigo"]: r["rotulo"] for r in opcoes if r["filtro"] == "racas"}
        self.assertEqual(racas["9"], "Não identificado")
        self.assertEqual(racas["6"], "Não informada")

    def test_saldo_mensal_e_filtros_cruzados(self):
        referencia = consultar("""
            SELECT competencia, SUM(admissoes) AS admissoes,
                   SUM(desligamentos) AS desligamentos, SUM(saldo) AS saldo
            FROM caged.v_indicadores_emprego
            WHERE regiao_codigo = '2' AND uf_codigo = '29' AND setor_cnae = 'G'
              AND sexo_codigo = '3' AND racacor_codigo = '2' AND faixa_etaria = '25 a 29'
            GROUP BY competencia ORDER BY competencia
        """)
        self.assertTrue(referencia)
        recorte = Filtros(**self.datas, regioes=("2",), ufs=("29",), setores=("G",),
                          sexos=("3",), racas=("2",), idades=("25 a 29",))
        resultado = carregar_indicador("saldo", recorte)
        campos = ("competencia", "admissoes", "desligamentos", "saldo")
        self.assertEqual([{c: r[c] for c in campos} for r in resultado], referencia)
        self.assertTrue(all(r["sexo"] == "Mulher" and r["raca"] == "Preta" for r in resultado))

    def test_turnover_setorial_mensal(self):
        referencia = consultar("""
            SELECT setor_economico AS setor, SUM(admissoes) AS admissoes,
                   SUM(desligamentos) AS desligamentos
            FROM caged.v_indicadores_emprego
            WHERE competencia = %s AND sexo_codigo = '3' AND racacor_codigo = '3'
            GROUP BY setor_economico ORDER BY setor_economico
        """, (self.datas["fim"],))
        self.assertTrue(referencia)
        recorte = Filtros(self.datas["fim"], self.datas["fim"], sexos=("3",), racas=("3",))
        resultado = carregar_indicador("turnover", recorte)
        self.assertEqual([{c: r[c] for c in ("setor", "admissoes", "desligamentos")} for r in resultado],
                         referencia)
        for r in resultado:
            if r["admissoes"]:
                self.assertAlmostEqual(r["razao"], Decimal(r["desligamentos"]) / r["admissoes"], places=12)
            else:
                self.assertIsNone(r["razao"])

    def test_salario_so_admissoes_e_referencia_do_recorte(self):
        referencia = consultar("""
            SELECT sexo, raca_cor AS raca, SUM(soma_salarios_validos) AS massa,
                   SUM(quantidade_salarios_validos) AS salarios_validos
            FROM caged.v_indicadores_emprego
            WHERE admissoes > 0 AND racacor_codigo IN ('1', '2', '3')
            GROUP BY sexo, raca_cor
        """)
        por_grupo = {(r["sexo"], r["raca"]): r for r in referencia}
        resultado = carregar_indicador("salario", Filtros(**self.datas, racas=("1", "2", "3")))
        self.assertTrue(resultado)
        self.assertEqual(len(resultado), len(referencia))
        maior = max(r["media"] for r in resultado)
        for r in resultado:
            esperado = por_grupo[r["sexo"], r["raca"]]
            self.assertEqual(r["salarios_validos"], esperado["salarios_validos"])
            self.assertAlmostEqual(r["media"], esperado["massa"] / r["salarios_validos"], places=10)
            self.assertAlmostEqual(r["razao"], r["media"] / maior, places=12)

    def test_participacao_usa_denominador_do_fluxo_e_do_filtro(self):
        referencia = consultar("""
            SELECT SUM(admissoes) FILTER (WHERE racacor_codigo = '9') AS total_mulheres,
                   SUM(admissoes) FILTER (WHERE racacor_codigo = '9' AND sexo_codigo = '3') AS mulheres,
                   SUM(desligamentos) FILTER (WHERE sexo_codigo = '1') AS total_negras,
                   SUM(desligamentos) FILTER (WHERE sexo_codigo = '1' AND racacor_codigo IN ('2', '3')) AS negras
            FROM caged.v_indicadores_emprego WHERE setor_cnae = 'G'
        """)[0]
        recorte = Filtros(**self.datas, setores=("G",), sexos=("1",), racas=("9",))
        resultado = carregar_indicador("participacao", recorte)
        self.assertEqual(len(resultado), 4)
        grupos = {(r["grupo"], r["fluxo"]): r for r in resultado}
        for chave, base in ((("Mulheres", "Admissões"), "mulheres"),
                            (("Pessoas negras", "Desligamentos"), "negras")):
            r = grupos[chave]
            self.assertEqual(r["quantidade"], referencia[base] or 0)
            self.assertEqual(r["total"], referencia[f"total_{base}"])
            if r["total"]:
                self.assertAlmostEqual(r["proporcao"], Decimal(r["quantidade"]) / r["total"], places=12)
            else:
                self.assertIsNone(r["proporcao"])
