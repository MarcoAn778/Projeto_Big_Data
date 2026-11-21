"""Identifica arquivos com configuração privada no índice Git."""

from pathlib import Path

from caged.seguranca import verificar_indice


if __name__ == "__main__":
    try:
        problemas = verificar_indice(Path(__file__).resolve().parents[1])
    except (OSError, RuntimeError):
        print("Não foi possível verificar o índice Git.")
        raise SystemExit(2) from None
    if problemas:
        for caminho in problemas:
            print(f"Revise o arquivo versionado: {caminho}")
        raise SystemExit(1)
    print("Nenhum arquivo privado ou padrão de segredo detectado no índice Git.")
