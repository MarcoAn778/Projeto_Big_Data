"""Testa a conexão PostgreSQL configurada, sem expor seus parâmetros."""

from caged.banco import confirmar_tls, conectar
from caged.validacao import ErroValidacao
import psycopg


def main():
    try:
        with conectar() as conn, conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            confirmar_tls(conn)
            conn.execute("SELECT 1")
        print("Conexão PostgreSQL e TLS verificados.")
        return 0
    except (ErroValidacao, psycopg.Error):
        print("Não foi possível verificar a conexão. Confira se o serviço está ativo, o IP está autorizado e a CA e as credenciais são válidas.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
