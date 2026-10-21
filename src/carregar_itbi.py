"""
carregar_itbi.py  [PY]

Carrega no PostgreSQL os CSVs gerados pelo ingest_itbi.py e a tabela de
referência de padrões. Pode ser rodado quantas vezes quiser: cada ano é
APAGADO e RECARREGADO dentro de uma única transação, então:
  - rodar duas vezes não duplica linhas;
  - se algo falhar no meio de um ano, nada fica pela metade (rollback).

Uso:
    python carregar_itbi.py --entrada PASTA_DOS_CSV --referencias PASTA_REFERENCIAS
    python carregar_itbi.py --entrada PASTA_DOS_CSV --referencias PASTA --anos 2024
"""
import argparse
import io
import sys
import time
from pathlib import Path

import pandas as pd

# colunas que o CSV guarda como decimal (100800297.0) mas o banco quer inteiras
INTEIROS = ["linha_origem", "sql", "numero", "cep",
            "uso_cod", "padrao_cod", "ano_conclusao", "natureza_cod"]


def colunas_da_tabela(cur) -> list[str]:
    """Lê do próprio banco a lista de colunas: o .sql é a fonte da verdade."""
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'staging' AND table_name = 'itbi_dti' "
        "ORDER BY ordinal_position"
    )
    return [linha[0] for linha in cur.fetchall()]


def preparar(caminho: Path, colunas: list[str]) -> tuple[int, pd.DataFrame]:
    """Lê o CSV, confere as colunas, ajusta tipos e descobre o ano."""
    df = pd.read_csv(caminho, low_memory=False)

    faltando = [c for c in colunas if c not in df.columns]
    if faltando:
        raise ValueError(f"{caminho.name}: colunas do banco ausentes no CSV: {faltando}")
    df = df[colunas].copy()          # só as colunas do banco, na ordem do banco

    for c in INTEIROS:               # falha alto se aparecer decimal de verdade
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")

    anos = pd.to_datetime(df["mes_pagamento"]).dt.year.unique()
    if len(anos) != 1:
        raise ValueError(f"{caminho.name}: esperava um único ano em mes_pagamento, achei {anos}")
    return int(anos[0]), df


def para_buffer(df: pd.DataFrame) -> io.StringIO:
    """Converte o DataFrame em CSV na memória, no formato que o COPY entende."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)      # vazio = NULL; textos com vírgula vão entre aspas
    buf.seek(0)
    return buf


def carregar_ano(conn, df: pd.DataFrame, ano: int, arquivo: str) -> tuple[int, int]:
    """Apaga o ano, insere de novo e registra. NÃO faz commit: quem chama decide."""
    cur = conn.cursor()
    inicio, fim = f"{ano}-01-01", f"{ano + 1}-01-01"

    cur.execute(
        "DELETE FROM staging.itbi_dti WHERE mes_pagamento >= %s AND mes_pagamento < %s",
        (inicio, fim),
    )
    apagadas = cur.rowcount

    colunas = ", ".join(df.columns)
    cur.copy_expert(
        f"COPY staging.itbi_dti ({colunas}) FROM STDIN WITH (FORMAT csv, HEADER true)",
        para_buffer(df),
    )

    cur.execute(
        "SELECT count(*) FROM staging.itbi_dti WHERE mes_pagamento >= %s AND mes_pagamento < %s",
        (inicio, fim),
    )
    no_banco = cur.fetchone()[0]
    if no_banco != len(df):          # reconciliação: o que entrou = o que estava no CSV
        raise RuntimeError(f"{ano}: CSV tem {len(df):,} linhas e o banco ficou com {no_banco:,}")

    cur.execute(
        "INSERT INTO staging.log_carga (ano_arquivo, arquivo_tratado, linhas_carregadas) "
        "VALUES (%s, %s, %s)",
        (ano, arquivo, len(df)),
    )
    return apagadas, no_banco


def carregar_referencias(conn, pasta: Path) -> None:
    """Recarrega a dimensão de padrões (32 linhas) a partir do CSV de referência."""
    df = pd.read_csv(pasta / "padroes_iptu.csv")
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM analytics.dim_padrao_iptu")
        cur.copy_expert(
            "COPY analytics.dim_padrao_iptu (padrao_cod, padrao_desc) "
            "FROM STDIN WITH (FORMAT csv, HEADER true)",
            para_buffer(df),
        )
        conn.commit()
        print(f"dim_padrao_iptu: {len(df)} códigos carregados")
    except Exception:
        conn.rollback()
        raise


def main() -> None:
    p = argparse.ArgumentParser(description="Carga do ITBI tratado no PostgreSQL")
    p.add_argument("--entrada", type=Path, default=Path("dados_tratados"),
                   help="pasta com os itbi_AAAA.csv.gz")
    p.add_argument("--referencias", type=Path, default=Path("referencias"),
                   help="pasta com padroes_iptu.csv")
    p.add_argument("--anos", type=int, nargs="*", help="carregar só estes anos")
    args = p.parse_args()

    arquivos = sorted(args.entrada.glob("itbi_*.csv.gz"))
    if args.anos:
        arquivos = [a for a in arquivos if int(a.name[5:9]) in args.anos]
    if not arquivos:
        sys.exit(f"Nenhum itbi_*.csv.gz encontrado em {args.entrada}")

    from database import get_engine   # importado aqui para o resto ser testável sem banco

    conn = get_engine().raw_connection()
    falhas = {}
    try:
        carregar_referencias(conn, args.referencias)
        colunas = colunas_da_tabela(conn.cursor())
        conn.rollback()                # encerra a transação aberta pela consulta acima

        for arq in arquivos:
            t0 = time.time()
            print(f"\n=== {arq.name}")
            try:
                ano, df = preparar(arq, colunas)
                apagadas, inseridas = carregar_ano(conn, df, ano, arq.name)
                conn.commit()          # só aqui o ano passa a existir de verdade
                print(f"  {ano}: apagadas {apagadas:,} | inseridas {inseridas:,} "
                      f"| {time.time() - t0:.0f}s")
            except Exception as e:     # um ano ruim não derruba os outros
                conn.rollback()
                falhas[arq.name] = str(e)
                print(f"  ERRO em {arq.name}: {e}")
    finally:
        conn.close()

    if falhas:
        print("\n=== ARQUIVOS COM ERRO (nada foi gravado para eles)")
        for nome, msg in falhas.items():
            print(f"  {nome}: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()