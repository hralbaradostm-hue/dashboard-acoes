import pandas as pd
import requests
import warnings
import re
import sys
import json
import os
from bs4 import BeautifulSoup

warnings.filterwarnings('ignore')

print("⏳ Gerando base limpa e corrigida...")

arquivo_json = "dados_profundos.json"
dados_profundos = {}
if os.path.exists(arquivo_json):
    with open(arquivo_json, "r", encoding="utf-8") as f:
        dados_profundos = json.load(f)
else:
    print(f"⚠️ ATENÇÃO: '{arquivo_json}' não encontrado!")
    sys.exit(1)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

url = "https://www.fundamentus.com.br/resultado.php"
try:
    resposta = requests.get(url, headers=headers, timeout=15)
    resposta.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"\n❌ ERRO DE CONEXÃO: Não foi possível acessar o Fundamentus.")
    sys.exit(1)

soup = BeautifulSoup(resposta.text, 'html.parser')
tabela = soup.find('table', {'id': 'resultado'})
linhas = [[td.text.strip() for td in tr.find_all(['td', 'th'])] for tr in tabela.find_all('tr') if tr.find_all(['td', 'th'])]
df = pd.DataFrame(linhas[1:], columns=linhas[0])

colunas_no_site = {col.strip().lower(): col for col in df.columns}
mapa_desejado = {
    "Ticker": ["Papel"], "Cotação": ["Cotação", "Cotacao"], "P/L": ["P/L"], "P/VP": ["P/VP"],
    "Dividend Yield": ["Div.Yield", "Div. Yield"], "Margem EBIT": ["Mrg Ebit", "Mrg. Ebit"],
    "Margem Líquida": ["Mrg. Líq.", "Mrg. Liq.", "Mrg.Líq."], "ROIC": ["ROIC"], "ROE": ["ROE"],
    "Liquidez Diária": ["Liq.2meses", "Liq. 2 meses"], "Patrimônio Líquido": ["Patrim. Líq", "Patrim. Liq"],
    "Cresc. 5 Anos (%)": ["Cresc. Rec.5a", "Cresc.Rec.5a"]
}

renomear_dict = {colunas_no_site[alt.lower()]: nome_final for nome_final, alternativas in mapa_desejado.items() for alt in alternativas if alt.lower() in colunas_no_site}
df.rename(columns=renomear_dict, inplace=True)
df = df.loc[:, ~df.columns.duplicated()].copy()

df = df[~df["Ticker"].astype(str).str.contains(r'(?:32|33|34|35|39)$', regex=True)].reset_index(drop=True)

def converter_para_numero(valor):
    if pd.isna(valor) or valor is None: return 0.0
    val_str = str(valor).replace('\xa0', '').replace('%', '').strip()
    if not val_str or val_str in ['-', '--', 'None', 'nan', 'null']: return 0.0
    try:
        if ',' in val_str: val_str = val_str.replace('.', '').replace(',', '.')
        val_limpo = re.sub(r'[^0-9.-]', '', val_str)
        return float(val_limpo) if val_limpo else 0.0
    except: return 0.0

def converter_dado_profundo(valor_str):
    if not isinstance(valor_str, str) or valor_str.strip().lower() in ["-", "n/a", "null", "none", ""]: return 0.0
    v = valor_str.replace('%', '').replace('.', '').replace(',', '.').strip()
    try: return float(v)
    except: return 0.0

colunas_financeiras = ["Cotação", "P/L", "P/VP", "Dividend Yield", "ROIC", "ROE", "Margem EBIT", "Margem Líquida", "Patrimônio Líquido", "Liquidez Diária", "Cresc. 5 Anos (%)"]
for col in colunas_financeiras: df[col] = df[col].apply(converter_para_numero)

def identificar_tipo_acao(ticker):
    t_str = str(ticker).strip().upper()
    return "UNT" if t_str.endswith("11") else "ON" if t_str.endswith(("3", "7")) else "PN" if t_str.endswith(("4", "5", "6", "8")) else "Outros"
df["Tipo"] = df["Ticker"].apply(identificar_tipo_acao)
df["Empresa"] = df["Ticker"].map(lambda t: f"Empresa {str(t)[:4].upper()}")

def aplicar_dados_profundos(row):
    radical = str(row["Ticker"])[:4].upper()
    info = dados_profundos.get(radical, {})
    
    # Tratamento contra valores 'None' e strings vazias
    segmento = str(info.get("Segmento", "Tradicional")).strip()
    if segmento.lower() in ["none", "-", "erro", ""]: 
        segmento = "Tradicional"
        
    setor = str(info.get("Setor", "Outros")).strip()
    if setor.lower() in ["none", "-", "erro", ""]:
        setor = "Outros Setores"
        
    ff_str = info.get("Free_Float", "0")
    div_str = info.get("DivLiq_EBIT", "0")
    gov = info.get("Governo_Majoritario", "Não")
    
    if row["Tipo"] == "PN" and segmento == "Novo Mercado":
        segmento = "Nível 2"

    # Arredondando os números para limpar casas decimais visuais (ex: 36.650000 -> 36.65)
    ff_num = round(converter_dado_profundo(ff_str), 2)
    div_num = round(converter_dado_profundo(div_str), 2)

    return pd.Series([segmento, setor, ff_num, div_num, gov])

df[["Segmento de Listagem", "Setor", "Free Float (%)", "Dívida Líquida/EBIT", "Governo Majoritário"]] = df.apply(aplicar_dados_profundos, axis=1)

def calcular_tag_along(row):
    seg = row["Segmento de Listagem"]
    if seg in ["Novo Mercado", "Nível 2"]:
        return 100.0
    return 80.0

df["Tag Along (%)"] = df.apply(calcular_tag_along, axis=1)

colunas_ordenadas = [
    "Ticker", "Empresa", "Tipo", "Segmento de Listagem", "Cotação", "Setor", "Tag Along (%)", 
    "Free Float (%)", "Governo Majoritário", "Dívida Líquida/EBIT",
    "P/L", "P/VP", "Dividend Yield", "Patrimônio Líquido", "Liquidez Diária", 
    "Margem EBIT", "Margem Líquida", "ROIC", "ROE", "Cresc. 5 Anos (%)"
]
df = df[[col for col in colunas_ordenadas if col in df.columns]]
df.to_excel("acoes_b3.xlsx", index=False)

print(f"✅ Planilha salva com Sucesso: Setores preenchidos, 'None' removido e casas decimais limpas!")