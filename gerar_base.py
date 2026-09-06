import pandas as pd
import requests
import warnings
import re
import sys
from bs4 import BeautifulSoup

warnings.filterwarnings('ignore')

print("⏳ Conectando ao Fundamentus para baixar dados atualizados da B3...")

url = "https://www.fundamentus.com.br/resultado.php"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 1. VALIDAÇÃO DE CONEXÃO
try:
    resposta = requests.get(url, headers=headers, timeout=15)
    resposta.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"\n❌ ERRO DE CONEXÃO: Não foi possível acessar o Fundamentus.")
    print(f"👉 Detalhe: {e}")
    sys.exit(1)

# 2. VALIDAÇÃO DE ESTRUTURA HTML (LAYOUT)
soup = BeautifulSoup(resposta.text, 'html.parser')
tabela = soup.find('table', {'id': 'resultado'})

if not tabela:
    print("\n⚠️ ALERTA DE MUDANÇA DE LAYOUT:")
    print("❌ A tabela de resultados ('table id=resultado') não foi encontrada no HTML da página.")
    sys.exit(1)

# 3. EXTRAÇÃO DAS LINHAS
linhas = []
for tr in tabela.find_all('tr'):
    cols = [td.text.strip() for td in tr.find_all(['td', 'th'])]
    if cols:
        linhas.append(cols)

if len(linhas) < 2:
    print("\n⚠️ ALERTA DE DADOS VAZIOS:")
    print("❌ A tabela foi encontrada, mas não contém linhas de dados das ações.")
    sys.exit(1)

df = pd.DataFrame(linhas[1:], columns=linhas[0])

# 4. MAPEAMENTO DE COLUNAS FLEXÍVEL (Com ou sem acento)
colunas_no_site = {col.strip().lower(): col for col in df.columns}

def encontrar_coluna(alternativas):
    for alt in alternativas:
        alt_norm = alt.lower()
        if alt_norm in colunas_no_site:
            return colunas_no_site[alt_norm]
    return None

mapa_desejado = {
    "Ticker": ["Papel"],
    "Cotação": ["Cotação", "Cotacao"],
    "P/L": ["P/L"],
    "P/VP": ["P/VP"],
    "Dividend Yield": ["Div.Yield", "Div. Yield"],
    "Margem EBIT": ["Mrg Ebit", "Mrg. Ebit"],
    "Margem Líquida": ["Mrg. Líq.", "Mrg. Liq.", "Mrg.Líq."],
    "ROIC": ["ROIC"],
    "ROE": ["ROE"],
    "Liquidez Diária": ["Liq.2meses", "Liq. 2 meses"],
    "Patrimônio Líquido": ["Patrim. Líq", "Patrim. Liq"],
    "Cresc. 5 Anos (%)": ["Cresc. Rec.5a", "Cresc.Rec.5a"]
}

renomear_dict = {}
colunas_faltantes = []

for nome_final, alternativas in mapa_desejado.items():
    col_encontrada = encontrar_coluna(alternativas)
    if col_encontrada:
        renomear_dict[col_encontrada] = nome_final
    else:
        colunas_faltantes.append(nome_final)

if colunas_faltantes:
    print("\n⚠️ ALERTA DE MUDANÇA NAS COLUNAS:")
    print(f"❌ As seguintes colunas essenciais não foram encontradas: {colunas_faltantes}")
    sys.exit(1)

df.rename(columns=renomear_dict, inplace=True)
df = df.loc[:, ~df.columns.duplicated()].copy()

# 5. CONVERSÃO NUMÉRICA
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

MAPA_SETORES_B3 = {
    "ITUB": "Bancos", "BBDC": "Bancos", "BBAS": "Bancos", "SANB": "Bancos", "BPAC": "Bancos",
    "ELET": "Energia Elétrica", "CMIG": "Energia Elétrica", "CPLE": "Energia Elétrica", "TAEE": "Energia Elétrica",
    "PETR": "Petróleo e Gás", "PRIO": "Petróleo e Gás", "UGPA": "Petróleo e Gás",
    "VALE": "Mineração e Siderurgia", "GGBR": "Mineração e Siderurgia", "CSNA": "Mineração e Siderurgia",
    "SBSP": "Saneamento", "SAPR": "Saneamento", "CSMG": "Saneamento",
    "BBSE": "Seguradoras", "CXSE": "Seguradoras", "PSSA": "Seguradoras",
    "WEGE": "Máquinas e Equipamentos", "SUZB": "Papel e Celulose", "KLBN": "Papel e Celulose",
    "RENT": "Transporte e Logística", "MGLU": "Varejo e Comércio", "LREN": "Varejo e Comércio"
}

def obter_setor_oficial(ticker):
    prefixo = str(ticker)[:4].upper()
    return MAPA_SETORES_B3.get(prefixo, "Outros Setores")

def obter_nome_empresa(ticker):
    prefixo = str(ticker)[:4].upper()
    nomes = {
        "WEGE": "WEG S.A.", "PETR": "Petrobras", "VALE": "Vale S.A.",
        "ITUB": "Itaú Unibanco", "BBDC": "Bradesco", "BBAS": "Banco do Brasil"
    }
    return nomes.get(prefixo, f"Empresa {prefixo}")

df["Empresa"] = df["Ticker"].map(obter_nome_empresa)
df["Segmento"] = df["Ticker"].map(obter_setor_oficial)

colunas_ordenadas = [
    "Ticker", "Empresa", "Tipo", "Cotação", "Segmento", "P/L", "P/VP", 
    "Dividend Yield", "Patrimônio Líquido", "Liquidez Diária", "Margem EBIT", 
    "Margem Líquida", "ROIC", "ROE", "Cresc. 5 Anos (%)"
]
colunas_presentes = [col for col in colunas_ordenadas if col in df.columns]
df = df[colunas_presentes]

df.to_excel("acoes_b3.xlsx", index=False)

print(f"✅ SUCESSO! Base validada e salva em 'acoes_b3.xlsx' com {len(df)} ações.")