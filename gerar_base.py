import pandas as pd
import requests
import warnings
import re
from bs4 import BeautifulSoup

warnings.filterwarnings('ignore')

print("Baixando dados da B3 e reclassificando setores automaticamente...")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 1. Raspagem da Tabela Principal de Indicadores
url_resultado = "https://www.fundamentus.com.br/resultado.php"
resposta = requests.get(url_resultado, headers=headers, timeout=20)
soup = BeautifulSoup(resposta.text, 'html.parser')
tabela = soup.find('table', {'id': 'resultado'})

linhas = []
for tr in tabela.find_all('tr'):
    cols = [td.text.strip() for td in tr.find_all(['td', 'th'])]
    if cols:
        linhas.append(cols)

df = pd.DataFrame(linhas[1:], columns=linhas[0])

# Mapeamento de Colunas
mapa_exato = {
    "Papel": "Ticker",
    "Cotacao": "Cotação",
    "P/L": "P/L",
    "P/VP": "P/VP",
    "Div.Yield": "Dividend Yield",
    "Mrg Ebit": "Margem EBIT",
    "Mrg. Líq.": "Margem Líquida",
    "ROIC": "ROIC",
    "ROE": "ROE",
    "Liq.2meses": "Liquidez Diária",
    "Patrim. Líq": "Patrimônio Líquido",
    "Cresc. Rec.5a": "Cresc. 5 Anos (%)"
}

df.rename(columns=mapa_exato, inplace=True)
df = df.loc[:, ~df.columns.duplicated()].copy()

# 2. Raspagem Automática de Setores Globais do Fundamentus
print("Mapeando setores oficiais da B3...")
mapa_setores_auto = {}

try:
    url_setores = "https://www.fundamentus.com.br/busca_resultado.php"
    resp_setores = requests.get(url_setores, headers=headers, timeout=20)
    soup_setores = BeautifulSoup(resp_setores.text, 'html.parser')
    tabela_setores = soup_setores.find('table', {'id': 'resultado'})
    
    if tabela_setores:
        for tr in tabela_setores.find_all('tr')[1:]:
            tds = tr.find_all('td')
            if len(tds) >= 2:
                ticker_cod = tds[0].text.strip()
                setor_nome = tds[1].text.strip()
                if ticker_cod and setor_nome:
                    mapa_setores_auto[ticker_cod] = setor_nome
except Exception as e:
    print(f"Aviso ao buscar setores automáticos: {e}")

# 3. Conversão Numérica
def converter_para_numero(valor):
    if pd.isna(valor) or valor is None:
        return 0.0
    val_str = str(valor).replace('\xa0', '').replace('%', '').strip()
    if not val_str or val_str in ['-', '--', 'None', 'nan', 'null']:
        return 0.0
    try:
        if ',' in val_str:
            val_str = val_str.replace('.', '').replace(',', '.')
        val_limpo = re.sub(r'[^0-9.-]', '', val_str)
        return float(val_limpo) if val_limpo else 0.0
    except Exception:
        return 0.0

colunas_financeiras = [
    "Cotação", "P/L", "P/VP", "Dividend Yield", "ROIC", "ROE", 
    "Margem EBIT", "Margem Líquida", "Patrimônio Líquido", "Liquidez Diária", "Cresc. 5 Anos (%)"
]

for col in colunas_financeiras:
    if col in df.columns:
        df[col] = df[col].apply(converter_para_numero)

df["Tipo"] = df["Ticker"].apply(lambda t: "ON" if str(t).endswith(("3","7")) else "PN")

# Dicionário Auxiliar para Nomes de Empresas Principais
nomes_base = {
    "WEGE": "WEG S.A.", "PETR": "Petrobras", "VALE": "Vale S.A.",
    "ITUB": "Itaú Unibanco", "BBDC": "Bradesco", "BBAS": "Banco do Brasil",
    "SANB": "Santander Brasil", "BPAC": "BTG Pactual", "BBSE": "BB Seguridade",
    "ELET": "Eletrobras", "CMIG": "Cemig", "CPLE": "Copel", "TAEE": "Taesa",
    "RENT": "Localiza", "SUZB": "Suzano", "KLBN": "Klabin", "MGLU": "Magazine Luiza"
}

def atribuir_nome(ticker):
    prefixo = str(ticker)[:4].upper()
    return nomes_base.get(prefixo, f"Empresa {prefixo}")

def atribuir_setor(ticker):
    # Tenta obter do mapeamento automático do Fundamentus
    if ticker in mapa_setores_auto:
        return mapa_setores_auto[ticker]
    
    # Caso seja código ON/PN derivado (ex: PETR4 busca PETR3)
    prefixo = str(ticker)[:4].upper()
    for t_cod, s_nome in mapa_setores_auto.items():
        if t_cod.startswith(prefixo):
            return s_nome
            
    return "Outros Setores"

df["Empresa"] = df["Ticker"].apply(atribuir_nome)
df["Segmento"] = df["Ticker"].apply(atribuir_setor)

colunas_ordenadas = [
    "Ticker", "Empresa", "Tipo", "Cotação", "Segmento", "P/L", "P/VP", 
    "Dividend Yield", "Patrimônio Líquido", "Liquidez Diária", "Margem EBIT", 
    "Margem Líquida", "ROIC", "ROE", "Cresc. 5 Anos (%)"
]
colunas_presentes = [col for col in colunas_ordenadas if col in df.columns]
df = df[colunas_presentes]

df.to_excel("acoes_b3.xlsx", index=False)

print(f"✅ SUCESSO! Base atualizada com {len(df)} ações e setores categorizados.")