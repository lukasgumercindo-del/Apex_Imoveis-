"""
ingest_itbi.py  [PY]  

Lê um ou mais arquivos anuais de ITBI da Prefeitura de São Paulo (xlsx),
padroniza colunas e tipos, e MARCA problemas de qualidade com flags.
Regra de ouro: nenhuma linha é apagada aqui. Excluir é decisão da análise.

O que a v2 tolera (descoberto na auditoria de 2022-2025):
  - abas SEM linha de cabeçalho (JAN-2024 e OUT-2024): as colunas são
    atribuídas pela ordem padrão, depois de uma checagem de sanidade;
  - a coluna "Descrição do padrão (IPTU)" ausente em várias abas: ela é
    função do código do padrão, então fica fora da tabela de fatos e vive
    em referencias/padroes_iptu.csv.

Uso:
    python ingest_itbi.py [--saida PASTA] arquivo1.xlsx [arquivo2.xlsx ...]
"""
import argparse
import re
import sys
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

MESES = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN",
         "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]

ORDEM_ORIGINAL = [
    "N° do Cadastro (SQL)", "Nome do Logradouro", "Número", "Complemento",
    "Bairro", "Referência", "CEP", "Natureza de Transação",
    "Valor de Transação (declarado pelo contribuinte)", "Data de Transação",
    "Valor Venal de Referência", "Proporção Transmitida (%)",
    "Valor Venal de Referência (proporcional)", "Base de Cálculo adotada",
    "Tipo de Financiamento", "Valor Financiado", "Cartório de Registro",
    "Matrícula do Imóvel", "Situação do SQL", "Área do Terreno (m2)",
    "Testada (m)", "Fração Ideal", "Área Construída (m2)", "Uso (IPTU)",
    "Descrição do uso (IPTU)", "Padrão (IPTU)", "Descrição do padrão (IPTU)",
    "ACC (IPTU)",
]

COLUNAS = {
    "N° do Cadastro (SQL)": "sql",
    "Nome do Logradouro": "logradouro",
    "Número": "numero",
    "Complemento": "complemento",
    "Bairro": "bairro",
    "Referência": "referencia",
    "CEP": "cep",
    "Natureza de Transação": "natureza_transacao",
    "Valor de Transação (declarado pelo contribuinte)": "valor_transacao",
    "Data de Transação": "data_transacao",
    "Valor Venal de Referência": "vvr",
    "Proporção Transmitida (%)": "proporcao_transmitida",
    "Valor Venal de Referência (proporcional)": "vvr_proporcional",
    "Base de Cálculo adotada": "base_calculo",
    "Tipo de Financiamento": "tipo_financiamento",
    "Valor Financiado": "valor_financiado",
    "Cartório de Registro": "cartorio",
    "Matrícula do Imóvel": "matricula",
    "Situação do SQL": "situacao_sql",
    "Área do Terreno (m2)": "area_terreno",
    "Testada (m)": "testada",
    "Fração Ideal": "fracao_ideal",
    "Área Construída (m2)": "area_construida",
    "Uso (IPTU)": "uso_cod",
    "Descrição do uso (IPTU)": "uso_desc",
    "Padrão (IPTU)": "padrao_cod",
    "ACC (IPTU)": "ano_conclusao",
}

NUMERICAS = [
    "sql", "numero", "cep", "vvr", "proporcao_transmitida", "vvr_proporcional",
    "base_calculo", "valor_financiado", "area_terreno", "testada",
    "fracao_ideal", "area_construida", "uso_cod", "padrao_cod", "ano_conclusao",
]

def detectar_ano(xl: pd.ExcelFile) -> int:
    anos = {int(m.group(1)) for a in xl.sheet_names
            if (m := re.fullmatch(r"[A-Z]{3}-(\d{4})", a))}
    if len(anos) != 1:
        raise ValueError(f"não consegui determinar um ano único pelas abas: {anos}")
    return anos.pop()


def ler_aba(xl: pd.ExcelFile, aba: str) -> tuple[pd.DataFrame, bool]:
    primeira = pd.read_excel(xl, sheet_name=aba, header=None, nrows=1).iloc[0]
    tem_cabecalho = any("Cadastro (SQL)" in str(v) for v in primeira)

    if tem_cabecalho:
        d = pd.read_excel(xl, sheet_name=aba)
        d = d.loc[:, ~d.columns.astype(str).str.startswith("Unnamed")]
        d.columns = [str(c).strip() for c in d.columns]
    else:
        d = pd.read_excel(xl, sheet_name=aba, header=None)
        if d.shape[1] < len(ORDEM_ORIGINAL):
            raise ValueError(f"{aba}: sem cabeçalho e só {d.shape[1]} colunas")
        d = d.iloc[:, :len(ORDEM_ORIGINAL)]
        d.columns = ORDEM_ORIGINAL
      
        amostra = d["Natureza de Transação"].dropna().astype(str).head(300)
        if not amostra.str.match(r"^\d+\.").all():
            raise ValueError(f"{aba}: sem cabeçalho e a ordem das colunas não confere")

    faltando = set(COLUNAS) - set(d.columns)
    if faltando:
        raise ValueError(f"{aba}: colunas ausentes {sorted(faltando)}")
    return d[list(COLUNAS)].rename(columns=COLUNAS), tem_cabecalho


def ler_arquivo(caminho: Path) -> tuple[int, pd.DataFrame]:
    xl = pd.ExcelFile(caminho)
    ano = detectar_ano(xl)
    print(f"ano detectado pelas abas: {ano}")
    partes = []
    for i, mes in enumerate(MESES, start=1):
        aba = f"{mes}-{ano}"
        if aba not in xl.sheet_names:
            print(f"  aviso: aba {aba} não encontrada, pulando")
            continue
        d, tem_cab = ler_aba(xl, aba)
        if not tem_cab:
            print(f"  aviso: {aba} sem linha de cabeçalho; colunas atribuídas pela ordem padrão")
        d["aba_origem"] = aba
        d["linha_origem"] = d.index + (2 if tem_cab else 1)
        d["aba_sem_cabecalho"] = not tem_cab
        d["mes_pagamento"] = pd.Timestamp(ano, i, 1)
        partes.append(d)
    return ano, pd.concat(partes, ignore_index=True)

def padronizar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    valor_num = pd.to_numeric(df["valor_transacao"], errors="coerce")
    data_dt = pd.to_datetime(df["data_transacao"], errors="coerce")
    df["flag_linha_desalinhada"] = valor_num.isna() | data_dt.isna()
    df["valor_transacao"] = valor_num
    df["data_transacao"] = data_dt
    for c in NUMERICAS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df.loc[df["flag_linha_desalinhada"], ["complemento", "referencia"]] = None

    df["natureza_cod"] = pd.to_numeric(
        df["natureza_transacao"].astype(str).str.extract(r"^(\d+)\.")[0],
        errors="coerce")
    return df


def marcar_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["flag_compra_venda"] = df["natureza_cod"] == 1
    df["flag_apto_condominio"] = df["uso_cod"] == 20
    df["flag_terreno_com_unidade"] = (
        (df["uso_cod"] == 0)
        & df["complemento"].astype(str).str.upper()
        .str.contains(r"\bAP|\bAPTO|\bUN\b|\bUNID|\bCJ\b", regex=True)
    )
    df["flag_proporcao_total"] = df["proporcao_transmitida"] == 100
    df["flag_area_invalida"] = ~(df["area_construida"] > 0)
    df["flag_valor_baixo"] = df["valor_transacao"] <= 10_000
    df["flag_declarado_abaixo_vvr"] = df["base_calculo"] > df["valor_transacao"] * 1.0001
    df["razao_declarado_base"] = df["valor_transacao"] / df["base_calculo"]
    df["flag_sql_repetido_no_ano"] = df.duplicated("sql", keep=False)
    df["flag_ativo_predial"] = df["situacao_sql"] == "Ativo Predial"
    return df


def resumo(df: pd.DataFrame) -> dict:
    n = len(df)
    print(f"\nlinhas: {n:,}")
    stats = {"linhas": n}
    for f in [c for c in df.columns if c.startswith("flag_")]:
        qtd, pct = int(df[f].sum()), 100 * df[f].mean()
        print(f"  {f:<28} {qtd:>9,}  ({pct:5.1f}%)")
        stats[f] = pct
    return stats

def processar_arquivo(caminho: Path, saida: Path) -> tuple[int, dict]:
    ano, bruto = ler_arquivo(caminho)
    tratado = marcar_flags(padronizar(bruto))
    stats = resumo(tratado)
    destino = saida / f"itbi_{ano}.csv.gz"
    tratado.to_csv(destino, index=False, encoding="utf-8")
    print(f"salvo em: {destino}")
    return ano, stats


def main() -> None:
    p = argparse.ArgumentParser(description="Ingestão e padronização do ITBI (SP)")
    p.add_argument("arquivos", nargs="+", type=Path, help="um ou mais .xlsx anuais")
    p.add_argument("--saida", type=Path, default=Path("dados_tratados"),
                   help="pasta de saída (padrão: dados_tratados)")
    args = p.parse_args()
    args.saida.mkdir(parents=True, exist_ok=True)

    resultados, falhas = {}, {}
    for arq in args.arquivos:
        print(f"\n=== {arq.name}")
        try:
            ano, stats = processar_arquivo(arq, args.saida)
            resultados[ano] = stats
        except Exception as e:
            falhas[arq.name] = str(e)
            print(f"  ERRO em {arq.name}: {e}")

    if len(resultados) > 1:
        print("\n=== COMPARAÇÃO ENTRE ANOS (linhas e % de cada flag)")
        comp = pd.DataFrame(resultados).T.sort_index()
        comp["linhas"] = comp["linhas"].astype(int)
        print(comp.round(1).to_string())

    if falhas:
        print("\n=== ARQUIVOS COM ERRO")
        for nome, msg in falhas.items():
            print(f"  {nome}: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()