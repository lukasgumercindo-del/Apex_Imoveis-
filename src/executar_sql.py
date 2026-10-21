r"""
executar_sql.py  [PY]

Executa um arquivo .sql no banco configurado no .env (o MESMO que o
database.py e a carga usam), dentro de uma transação, e lista as tabelas
que existem em seguida. Como usa o .env, não há como rodar no banco errado.

Uso (a partir da pasta apex-imoveis):
    python src\executar_sql.py sql\01_criar_tabelas.sql
"""
import sys
from pathlib import Path

from database import get_engine, get_url

LISTAR_TABELAS = (
    "SELECT table_schema || '.' || table_name FROM information_schema.tables "
    "WHERE table_schema IN ('staging', 'analytics') ORDER BY 1"
)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)

    arquivo = Path(sys.argv[1])
    script = arquivo.read_text(encoding="utf-8-sig") 

    print("Banco:", get_url().render_as_string(hide_password=True))
    print("Arquivo:", arquivo)

    conn = get_engine().raw_connection()
    try:
        cur = conn.cursor()
        cur.execute(script)        
        conn.commit()
        cur.execute(LISTAR_TABELAS)
        tabelas = [linha[0] for linha in cur.fetchall()]
    except Exception:
        conn.rollback()               
        raise
    finally:
        conn.close()

    print(f"\nExecutado com sucesso. Tabelas em staging/analytics: {len(tabelas)}")
    for t in tabelas:
        print("  ", t)


if __name__ == "__main__":
    main()