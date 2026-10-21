r"""
carregar_ipca.py  [PY]
 
Baixa o IPCA do IBGE (API SIDRA, tabela 1737), CONFERE a série e carrega em
analytics.dim_ipca. A série só é gravada se passar nas conferências.
 
Uso (a partir da pasta apex-imoveis):
    python src\carregar_ipca.py --validar    # só baixa e confere, não grava
    python src\carregar_ipca.py              # baixa, confere e grava no banco
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from decimal import Decimal

URL = "https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/{variavel}/p/all"
VAR_INDICE, VAR_VARIACAO = 2266, 63

ANCORAS = {date(2021, 12, 1): 6120.045, date(2022, 3, 1): 6315.934}
TOL_ANCORA = 0.02
TOL_VARIACAO = 0.02
PADRAO_MES = re.compile(r"^(19|20)\d{2}(0[1-9]|1[0-2])$")


def extrair_mes(linha: dict):
    for chave, valor in linha.items():
        if re.fullmatch(r"D\d+C", chave) and PADRAO_MES.match(str(valor)):
            return date(int(valor[:4]), int(valor[4:]), 1)
    return None
 
 
def baixar_serie(variavel: int) -> dict:
    url = URL.format(variavel=variavel)
    pedido = urllib.request.Request(url, headers={"User-Agent": "apex-imoveis/1.0"})
    try:
        with urllib.request.urlopen(pedido, timeout=60) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(f"não consegui acessar a API do IBGE ({e}). Verifique a internet.")
 
    serie = {}
    for linha in dados:
        mes = extrair_mes(linha)
        if mes is None:                    
            continue
        try:
            serie[mes] = Decimal(str(linha["V"]))
        except Exception:                 
            continue
    if not serie:
        amostra = json.dumps(dados[:3], ensure_ascii=False)[:600]
        raise ValueError(f"variável {variavel}: nenhuma linha reconhecida. Amostra: {amostra}")
    return serie
 
 
def validar(indice: dict, variacao: dict) -> list[str]:
    ok = []
    for mes, esperado in ANCORAS.items():
        if mes not in indice:
            raise ValueError(f"âncora {mes:%Y-%m} ausente da série")
        dif = abs(float(indice[mes]) - esperado)
        if dif > TOL_ANCORA:
            raise ValueError(f"âncora {mes:%Y-%m}: série tem {indice[mes]}, esperado {esperado}")
    ok.append(f"âncoras conferem ({', '.join(f'{m:%Y-%m}' for m in ANCORAS)})")
 
    meses = sorted(indice)
    nums = [m.year * 12 + m.month for m in meses]
    buracos = [meses[i] for i in range(1, len(nums)) if nums[i] - nums[i - 1] != 1]
    if buracos:
        raise ValueError(f"meses faltando antes de: {[f'{m:%Y-%m}' for m in buracos[:5]]}")
    ok.append(f"sem meses faltando ({len(meses)} meses)")
 
    divergentes = []
    for i in range(1, len(meses)):
        m, anterior = meses[i], meses[i - 1]
        if m.year < 2010 or m not in variacao:
            continue
        calculada = (float(indice[m]) / float(indice[anterior]) - 1) * 100
        if abs(calculada - float(variacao[m])) > TOL_VARIACAO:
            divergentes.append((f"{m:%Y-%m}", round(calculada, 3), float(variacao[m])))
    if divergentes:
        raise ValueError(f"índice e variação publicada divergem (mês, calculada, publicada): {divergentes[:5]}")
    ok.append("índice e variação mensal publicada coerentes (desde 2010)")
    return ok
 
 
def gravar(linhas: list) -> None:
    from database import get_engine        
    conn = get_engine().raw_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM analytics.dim_ipca")
        cur.executemany(
            "INSERT INTO analytics.dim_ipca (mes, numero_indice, variacao_mensal_pct) "
            "VALUES (%s, %s, %s)", linhas)
        cur.execute("SELECT count(*) FROM analytics.dim_ipca")
        if cur.fetchone()[0] != len(linhas):
            raise RuntimeError("a contagem no banco difere da série baixada")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
 
 
def main() -> None:
    p = argparse.ArgumentParser(description="IPCA (IBGE/SIDRA) -> analytics.dim_ipca")
    p.add_argument("--validar", action="store_true", help="só baixa e confere, não grava")
    args = p.parse_args()
 
    print("Baixando número-índice e variação mensal do IPCA...")
    indice = baixar_serie(VAR_INDICE)
    variacao = baixar_serie(VAR_VARIACAO)
    for msg in validar(indice, variacao):
        print("  OK:", msg)
 
    meses = sorted(indice)
    print(f"\nSérie: {meses[0]:%Y-%m} a {meses[-1]:%Y-%m}")
    for m in meses[-3:]:
        print(f"  {m:%Y-%m}  índice {indice[m]}  variação {variacao.get(m, '-')}")
    a, b = date(2022, 1, 1), date(2025, 12, 1)
    if a in indice and b in indice:
        print(f"\nConferência de bom senso: R$ 100 de {a:%m/%Y} valem "
              f"R$ {100 * float(indice[b]) / float(indice[a]):.2f} em {b:%m/%Y} (esperado: cerca de 120)")
 
    if args.validar:
        print("\nModo --validar: nada foi gravado.")
        return
    gravar([(m, indice[m], variacao.get(m)) for m in meses])
    print(f"\nGravado em analytics.dim_ipca: {len(meses)} meses.")
 
 
if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as e:
        sys.exit(f"ERRO: {e}")