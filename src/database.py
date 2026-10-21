"""
database.py  [PY]

Conexão com o PostgreSQL. As credenciais NUNCA ficam neste arquivo:
são lidas de variáveis de ambiente, carregadas do arquivo .env.

Uso em notebooks e scripts:
    from database import get_engine
    engine = get_engine()

Teste rápido no terminal:
    python database.py
"""
import os

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine

load_dotenv(find_dotenv())

VARIAVEIS = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]


def _ler_config() -> dict:
    faltando = [v for v in VARIAVEIS if not os.getenv(v)]
    if faltando:
        raise RuntimeError(
            f"Variáveis ausentes: {faltando}. "
            "Copie .env.example para .env e preencha os valores."
        )
    return {v: os.getenv(v) for v in VARIAVEIS}


def get_url() -> URL:
    c = _ler_config()
    return URL.create(
        drivername="postgresql+psycopg2",
        username=c["DB_USER"],
        password=c["DB_PASSWORD"], 
        host=c["DB_HOST"],
        port=int(c["DB_PORT"]),
        database=c["DB_NAME"],
    )


def get_engine() -> Engine:
    return create_engine(get_url(), pool_pre_ping=True)


def testar_conexao() -> None:
    url = get_url()
    print("Tentando conectar em:", url.render_as_string(hide_password=True))
    with get_engine().connect() as conn:
        banco = conn.execute(text("SELECT current_database();")).scalar()
        versao = conn.execute(text("SELECT version();")).scalar()
    print(f"Conexão OK. Banco: {banco}")
    print(f"Versão: {versao}")


if __name__ == "__main__":
    testar_conexao()