"""Python apos o tratamento: validar, carga ou verificar-nuvem."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validacao e carga da base Novo CAGED tratada em R.")
    parser.add_argument("modo", choices=("validar", "carga", "verificar-nuvem"))
    parser.add_argument("--raiz", type=Path, default=Path(__file__).resolve().parents[1],
                        help="Pasta raiz do projeto (padrao: descoberta automaticamente).")
    args = parser.parse_args(argv)
    try:
        from caged.validacao import validar_base, escrever_json
        from caged.banco import conectar, carregar, verificar_banco
    except ImportError:
        print("Dependencias ausentes. Execute: python -m pip install -r requirements.txt", file=sys.stderr)
        return 1
    try:
        base = validar_base(args.raiz)
        escrever_json(base.raiz / "verificacoes/validacao_base_atual.json", base.evidencia())
        print(f"Base validada: {base.resumo['linhas']:,} linhas, {base.resumo['movimentacoes']:,} movimentacoes, {base.resumo['meses']} meses.")
        if args.modo == "validar":
            return 0
        with conectar() as conn:
            if args.modo == "carga":
                carregar(conn, base)
            evidencia = verificar_banco(conn, base)
        escrever_json(base.raiz / "verificacoes/carga_nuvem.json", evidencia)
        print("PostgreSQL conferido com TLS. Evidencia: verificacoes/carga_nuvem.json")
        return 0
    except Exception as erro:
        from caged.validacao import ErroValidacao
        if isinstance(erro, ErroValidacao):
            print(f"ERRO: {erro}", file=sys.stderr)
        else:
            # Mensagens do driver podem incluir detalhes privados; nao imprimir conexao ou traceback.
            print(f"ERRO ({type(erro).__name__}): operacao nao concluida. Confira os arquivos, dependencias e a conexao local.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
