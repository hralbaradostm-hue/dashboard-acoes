import pandas as pd
import requests
import warnings
from bs4 import BeautifulSoup

warnings.filterwarnings('ignore')

print("Baixando dados da B3 e tratando valores financeiros...")

url = "https://www.fundamentus.com.br/resultado.php"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

resposta = requests.get(url, headers=headers, timeout=20)

soup = BeautifulSoup(resposta.text, 'html.parser')
tabela = soup.find('table', {'id': 'resultado'})

linhas = []
for tr in tabela.find_all('tr'):
    cols = [td.text.strip() for td in tr.find_all(['td', 'th'])]
    if cols:
        linhas.append(cols)

# Cria o DataFrame
df = pd.DataFrame(linhas[1:], columns=linhas[0])

# Mapeia os nomes das colunas limpando espaços e pontos
mapa_colunas = {}
for col in df.columns:
    col_limpa = str(col).lower().replace('.', '').replace(' ', '')
    if 'mrgliq' in col_limpa:
        mapa_colunas[col] = "Margem Líquida"
    elif 'mrgebit' in col_limpa:
        mapa_colunas[col] = "Margem EBIT"
    elif 'patrim' in col_limpa or 'pl' in col_limpa:
        mapa_colunas[col] = "Patrimônio Líquido"
    elif 'papel' in col_limpa:
        mapa_colunas[col] = "Ticker"
    elif 'cotacao' in col_limpa:
        mapa_colunas[col] = "Cotação"
    elif 'roic' in col_limpa:
        mapa_colunas[col] = "ROIC"
    elif 'roe' in col_limpa:
        mapa_colunas[col] = "ROE"
    elif 'liq' in col_limpa and '2m' in col_limpa:
        mapa_colunas[col] = "Liquidez Diária"

df.rename(columns=mapa_colunas, inplace=True)

# Remove colunas duplicadas que possam surgir da raspagem
df = df.loc[:, ~df.columns.duplicated()].copy()

# Função para converter taxas/porcentagens e valores monetários para float
def converter_para_numero(valor):
    try:
        val_str = str(valor).strip().replace('%', '')
        if not val_str or val_str in ['-', 'None', 'nan']:
            return 0.0
        # Substitui ponto de milhar por nada e vírgula decimal por ponto
        val_str = val_str.replace('.', '').replace(',', '.')
        return float(val_str)
    except Exception:
        return 0.0

colunas_financeiras = ["Cotação", "ROIC", "ROE", "Margem EBIT", "Margem Líquida", "Patrimônio Líquido", "Liquidez Diária"]

for col in colunas_financeiras:
    if col in df.columns:
        df[col] = df[col].astype(str).map(converter_para_numero)

df["Tipo"] = df["Ticker"].apply(lambda t: "ON" if str(t).endswith(("3","7")) else "PN")

def obter_nome_empresa(ticker):
    prefixo = str(ticker)[:4].upper()
    nomes = {
        "WEGE": "WEG S.A.", "PETR": "Petrobras", "VALE": "Vale S.A.",
        "ITUB": "Itaú Unibanco", "BBDC": "Bradesco", "BBAS": "Banco do Brasil",
        "SANB": "Santander Brasil", "BPAC": "BTG Pactual", "BBSE": "BB Seguridade",
        "CXSE": "Caixa Seguridade", "PSSA": "Porto Seguro", "IRBR": "IRB Brasil",
        "ELET": "Eletrobras", "CMIG": "Cemig", "CPLE": "Copel", "TAEE": "Taesa",
        "TRPL": "ISA CTEEP", "EGIE": "Engie Brasil", "EQTL": "Equatorial Energia",
        "SBSP": "Sabesp", "SAPR": "Sanepar", "CSMG": "Copasa", "PRIO": "Prio",
        "UGPA": "Ultrapar", "CSAN": "Cosan", "GGBR": "Gerdau", "GOAU": "Metalúrgica Gerdau",
        "CSNA": "Siderúrgica Nacional", "USIM": "Usiminas", "CMIN": "CSN Mineração",
        "MGLU": "Magazine Luiza", "LREN": "Lojas Renner", "BHIA": "Casas Bahia",
        "PETZ": "Petz", "RADL": "Raia Drogasil", "FLRY": "Fleury", "HYPE": "Hypera",
        "RDOR": "Rede D'Or", "JBSS": "JBS", "MRFG": "Marfrig", "BRFS": "BRF",
        "BEEF": "Minerva", "MDIA": "M. Dias Branco", "SLCE": "SLC Agrícola",
        "RENT": "Localiza", "RAIL": "Rumo Logística", "CCRO": "CCR", "AZUL": "Azul Linhas Aéreas",
        "GOLL": "GOL Linhas Aéreas", "SUZB": "Suzano", "KLBN": "Klabin", "CYRE": "Cyrela",
        "EZTC": "EZTec", "MRVE": "MRV Engenharia", "MULT": "Multiplan", "IGTI": "Iguatemi"
    }
    return nomes.get(prefixo, f"Empresa {prefixo}")

def obter_setor_oficial(ticker):
    prefixo = str(ticker)[:4].upper()
    setores_b3 = {
        "WEGE": "Máquinas e Equipamentos", "LEVE": "Máquinas e Equipamentos", 
        "MYPK": "Máquinas e Equipamentos", "TUPY": "Máquinas e Equipamentos", 
        "SHUL": "Máquinas e Equipamentos", "ROMI": "Máquinas e Equipamentos",
        "ITUB": "Bancos", "BBDC": "Bancos", "BBAS": "Bancos", "SANB": "Bancos", 
        "BPAC": "Bancos", "BRSR": "Bancos", "ABCB": "Bancos", "BPAN": "Bancos",
        "ELET": "Energia Elétrica", "CMIG": "Energia Elétrica", "CPLE": "Energia Elétrica", 
        "TAEE": "Energia Elétrica", "TRPL": "Energia Elétrica", "EGIE": "Energia Elétrica", 
        "EQTL": "Energia Elétrica", "ALUP": "Energia Elétrica", "ENEV": "Energia Elétrica",
        "SBSP": "Saneamento", "SAPR": "Sanepar", "CSMG": "Saneamento",
        "PETR": "Petróleo e Gás", "PRIO": "Petróleo e Gás", "RECV": "Petróleo e Gás", 
        "RRRP": "Petróleo e Gás", "UGPA": "Ultrapar", "CSAN": "Petróleo e Gás",
        "VALE": "Mineração e Siderurgia", "GGBR": "Mineração e Siderurgia", 
        "GOAU": "Mineração e Siderurgia", "CSNA": "Mineração e Siderurgia", 
        "USIM": "Mineração e Siderurgia", "CMIN": "Mineração e Siderurgia",
        "MGLU": "Varejo e Comércio", "LREN": "Varejo e Comércio", "ARZZ": "Varejo e Comércio", 
        "SOMA": "Varejo e Comércio", "BHIA": "Varejo e Comércio", "PETZ": "Varejo e Comércio",
        "RADL": "Saúde e Farmácia", "FLRY": "Saúde e Farmácia", "HYPE": "Saúde e Farmácia", 
        "RDOR": "Saúde e Farmácia", "ONCO3": "Saúde e Farmácia",
        "JBSS": "Agro e Alimentos", "MRFG": "Agro e Alimentos", "BRFS": "Agro e Alimentos", 
        "BEEF": "Agro e Alimentos", "MDIA": "M. Dias Branco", "SLCE": "SLC Agrícola",
        "RENT": "Transporte e Logística", "RAIL": "Transporte e Logística", 
        "CCRO": "Transporte e Logística", "AZUL": "Transporte e Logística", 
        "GOLL": "Transporte e Logística", "STBP": "Transporte e Logística",
        "BBSE": "Seguradoras", "CXSE": "Seguradoras", "PSSA": "Porto Seguro", "IRBR": "Seguradoras",
        "SUZB": "Papel e Celulose", "KLBN": "Papel e Celulose", "RANI": "Papel e Celulose",
        "CYRE": "Construção Civil", "EZTC": "Construção Civil", "MRVE": "Construção Civil", 
        "TEND": "Construção Civil", "DIRR": "Construção Civil", "JHSF": "Construção Civil",
        "MULT": "Shoppings e Imóveis", "IGTI": "Shoppings e Imóveis", "ALOS": "Shoppings e Imóveis"
    }
    return setores_b3.get(prefixo, "Outros Setores")

df["Empresa"] = df["Ticker"].map(obter_nome_empresa)
df["Segmento"] = df["Ticker"].map(obter_setor_oficial)

colunas_ordenadas = ["Ticker", "Empresa", "Tipo", "Cotação", "Segmento", "Patrimônio Líquido", "Liquidez Diária", "Margem EBIT", "Margem Líquida", "ROIC", "ROE"]
colunas_presentes = [col for col in colunas_ordenadas if col in df.columns]
df = df[colunas_presentes]

df.to_excel("acoes_b3.xlsx", index=False)

print(f"✅ SUCESSO! Planilha gerada com {len(df)} ações.")

if "Margem Líquida" in df.columns:
    wege = df[df['Ticker'] == 'WEGE3']
    if not wege.empty:
        mrg_liq = wege['Margem Líquida'].values[0]
        print(f"   Exemplo WEGE3 - Margem Líquida: {mrg_liq:.2f}%")