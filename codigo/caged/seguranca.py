"""Detecta nomes privados e padrões de segredos sem exibir seu conteúdo."""

from pathlib import Path, PurePosixPath
import re
import subprocess


PADROES = (
    r"""(?i:\bpostgres(?:ql)?://[^\s'"<>/{]+)""",
    r"(?i:\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.aivencloud\.com\b)",
    r"-----BEGIN (?:ENCRYPTED |RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
    r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b|\b(?:gh[pousr]_[a-zA-Z0-9]{30,}|github_pat_[a-zA-Z0-9_]{30,})\b",
    r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{16,}\b",
    r"\bSCRAM-SHA-256\$\d+:[A-Za-z0-9+/=]+\$[A-Za-z0-9+/=]+:[A-Za-z0-9+/=]+",
    r"""(?i:^[ \t]*(?:export[ \t]+|\$env:)?(?:AIVEN_TOKEN|PGPASSWORD|DATABASE_URL|API_TOKEN|AWS_SECRET_ACCESS_KEY)[ \t]*=[ \t]*['"]?[^ \t\r\n'"#=\[{<$][^ \t\r\n'"#=]{2,}['"]?[ \t]*(?:#.*)?$)""",
    r"""(?i:\b(?:password|api_token|service_password)[ \t]*[:=][ \t]*['"][^'"\s{$]{6,}['"])""",
)
BUSCA = re.compile("|".join(PADROES), re.MULTILINE)


def caminho_privado(caminho):
    caminho = PurePosixPath(caminho)
    nome = caminho.name.lower()
    return (
        ".terraform" in caminho.parts
        or ".venv" in caminho.parts
        or "segredos" in caminho.parts
        or nome in {".renviron", ".pgpass", "pgpass.conf", "secrets.toml", "tfplan"}
        or bool(re.match(r"(?:aiven[-_ ]?token|token[-_ ]?aiven)", nome))
        or (nome.startswith(".env") and nome != ".env.example")
        or ".tfstate" in nome
        or nome.endswith((".tfvars", ".tfvars.json", ".tfplan", ".pem", ".key", ".p12", ".pfx"))
    )


def verificar_conteudo(raiz, arquivos):
    problemas = []
    for arquivo in arquivos:
        caminho = arquivo.relative_to(raiz).as_posix()
        if caminho_privado(caminho):
            problemas.append(caminho)
            continue
        if arquivo.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".pdf", ".zip"}:
            continue
        texto = arquivo.read_text(encoding="utf-8-sig", errors="replace")
        if BUSCA.search(texto):
            problemas.append(caminho)
    return sorted(set(problemas))


def verificar_indice(raiz: Path):
    argumentos = ["git", "-C", str(raiz)]
    arquivos = subprocess.check_output([*argumentos, "ls-files", "--cached", "-z"])
    problemas = {p for p in arquivos.decode("utf-8").split("\0") if p and caminho_privado(p)}
    busca = subprocess.run(
        [*argumentos, "grep", "--cached", "-I", "-l", "-z", "-P", "-e", "|".join(PADROES)],
        capture_output=True, check=False,
    )
    if busca.returncode not in (0, 1):
        raise RuntimeError("Falha ao verificar o índice Git.")
    problemas.update(p for p in busca.stdout.decode("utf-8").split("\0") if p)
    return sorted(problemas)
