import pandas as pd
import requests
import warnings
import re
import sys
from bs4 import BeautifulSoup

warnings.filterwarnings('ignore')

print("⏳ Conectando ao Fundamentus para baixar indicadores da B3...")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 1. RASPAGEM DA TABELA PRINCIPAL DE INDICADORES
url = "https://www.fundamentus.com.br/resultado.php"

try:
    resposta = requests.get(url, headers=headers, timeout=15)
    resposta.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"\n❌ ERRO DE CONEXÃO: Não foi possível acessar o Fundamentus.")
    sys.exit(1)

soup = BeautifulSoup(resposta.text, 'html.parser')
tabela = soup.find('table', {'id': 'resultado'})

if not tabela:
    print("\n⚠️ ALERTA DE MUDANÇA DE LAYOUT: Tabela resultado não encontrada.")
    sys.exit(1)

linhas = []
for tr in tabela.find_all('tr'):
    cols = [td.text.strip() for td in tr.find_all(['td', 'th'])]
    if cols:
        linhas.append(cols)

if len(linhas) < 2:
    print("\n⚠️ ALERTA DE DADOS VAZIOS: Tabela sem dados.")
    sys.exit(1)

df = pd.DataFrame(linhas[1:], columns=linhas[0])

# 2. MAPEAMENTO FLEXÍVEL DE COLUNAS
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
    print(f"\n⚠️ ALERTA DE MUDANÇA NAS COLUNAS: {colunas_faltantes}")
    sys.exit(1)

df.rename(columns=renomear_dict, inplace=True)
df = df.loc[:, ~df.columns.duplicated()].copy()

# 3. CONVERSÃO NUMÉRICA
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

# 4. DICIONÁRIO COMPLETO DE RADICAIS B3
SETORES_RADICAIS = {
    # Bancos e Serviços Financeiros
    "ITUB": "Bancos", "BBDC": "Bancos", "BBAS": "Bancos", "SANB": "Bancos", "BPAC": "Bancos",
    "BRSR": "Bancos", "ABCB": "Bancos", "BPAN": "Bancos", "BAZA": "Bancos", "BMIN": "Bancos",
    "BNBR": "Bancos", "BSLI": "Bancos", "PINE": "Bancos", "B3SA": "Serviços Financeiros",
    "CIEL": "Serviços Financeiros", "CASH": "Serviços Financeiros",
    
    # Energia Elétrica
    "ELET": "Energia Elétrica", "CMIG": "Energia Elétrica", "CPLE": "Energia Elétrica",
    "TAEE": "Energia Elétrica", "TRPL": "Energia Elétrica", "EGIE": "Energia Elétrica",
    "EQTL": "Energia Elétrica", "ALUP": "Energia Elétrica", "ENEV": "Energia Elétrica",
    "NEOE": "Energia Elétrica", "AURE": "Energia Elétrica", "CPFE": "Energia Elétrica",
    "LIGT": "Energia Elétrica", "AESB": "Energia Elétrica", "ENGI": "Energia Elétrica",
    "MEGA": "Energia Elétrica", "GEPA": "Energia Elétrica", "CLSA": "Energia Elétrica",
    "COCE": "Energia Elétrica", "CSRN": "Energia Elétrica", "EKTR": "Energia Elétrica",
    "ELEK": "Energia Elétrica", "EMAE": "Energia Elétrica", "RNEW": "Energia Elétrica",
    "TRAN": "Energia Elétrica", "CEEB": "Energia Elétrica", "CEED": "Energia Elétrica",
    
    # Petróleo, Gás e Combustíveis
    "PETR": "Petróleo e Gás", "PRIO": "Petróleo e Gás", "RECV": "Petróleo e Gás",
    "RRRP": "Petróleo e Gás", "UGPA": "Petróleo e Gás", "CSAN": "Petróleo e Gás",
    "VBBR": "Petróleo e Gás", "OPCT": "Petróleo e Gás", "BRAX": "Petróleo e Gás",
    
    # Mineração e Siderurgia
    "VALE": "Mineração e Siderurgia", "GGBR": "Mineração e Siderurgia", "GOAU": "Mineração e Siderurgia",
    "CSNA": "Mineração e Siderurgia", "USIM": "Mineração e Siderurgia", "CMIN": "Mineração e Siderurgia",
    "BRAP": "Mineração e Siderurgia", "FESA": "Mineração e Siderurgia", "CMIN": "Mineração e Siderurgia",
    
    # Saneamento
    "SBSP": "Saneamento", "SAPR": "Saneamento", "CSMG": "Saneamento", "AMBP": "Saneamento",
    "ORVR": "Saneamento",
    
    # Seguradoras
    "BBSE": "Seguradoras", "CXSE": "Seguradoras", "PSSA": "Seguradoras", "IRBR": "Seguradoras",
    "WIZC": "Seguradoras",
    
    # Máquinas e Equipamentos
    "WEGE": "Máquinas e Equipamentos", "LEVE": "Máquinas e Equipamentos", "MYPK": "Máquinas e Equipamentos",
    "TUPY": "Máquinas e Equipamentos", "SHUL": "Máquinas e Equipamentos", "ROMI": "Máquinas e Equipamentos",
    "KEPL": "Máquinas e Equipamentos", "EALT": "Máquinas e Equipamentos", "BALM": "Máquinas e Equipamentos",
    
    # Agro e Alimentos
    "JBSS": "Agro e Alimentos", "MRFG": "Agro e Alimentos", "BRFS": "Agro e Alimentos",
    "BEEF": "Agro e Alimentos", "MDIA": "Agro e Alimentos", "SLCE": "Agro e Alimentos",
    "SMTO": "Agro e Alimentos", "AGRO": "Agro e Alimentos", "CAML": "Agro e Alimentos",
    "JALL": "Agro e Alimentos", "SOJA": "Agro e Alimentos", "TTEN": "Agro e Alimentos",
    "RAIZ": "Agro e Alimentos",
    
    # Varejo e Consumo
    "MGLU": "Varejo e Comércio", "LREN": "Varejo e Comércio", "ARZZ": "Varejo e Comércio",
    "SOMA": "Varejo e Comércio", "BHIA": "Varejo e Comércio", "PETZ": "Varejo e Comércio",
    "VULC": "Varejo e Comércio", "ALPA": "Varejo e Comércio", "ABEV": "Varejo e Comércio",
    "ASAI": "Varejo e Comércio", "CRFB": "Varejo e Comércio", "GMAT": "Varejo e Comércio",
    "LJQQ": "Varejo e Comércio", "SBFG": "Varejo e Comércio", "AMER": "Varejo e Comércio",
    "GUAR": "Varejo e Comércio", "CEAB": "Varejo e Comércio", "VLID": "Varejo e Comércio",
    
    # Saúde e Farmácia
    "RADL": "Saúde e Farmácia", "FLRY": "Saúde e Farmácia", "HYPE": "Saúde e Farmácia",
    "RDOR": "Saúde e Farmácia", "ONCO": "Saúde e Farmácia", "VVEO": "Saúde e Farmácia",
    "MATD": "Saúde e Farmácia", "PARD": "Saúde e Farmácia", "QUAL": "Saúde e Farmácia",
    "BLAU": "Saúde e Farmácia", "PNVL": "Saúde e Farmácia", "ODPV": "Saúde e Farmácia",
    "HAPV": "Saúde e Farmácia",
    
    # Construção Civil
    "CYRE": "Construção Civil", "EZTC": "Construção Civil", "MRVE": "Construção Civil",
    "TEND": "Construção Civil", "DIRR": "Construção Civil", "JHSF": "Construção Civil",
    "EVEN": "Construção Civil", "CURY": "Construção Civil", "PLPL": "Construção Civil",
    "LAVV": "Construção Civil", "MELK": "Construção Civil", "TRIS": "Construção Civil",
    "GFSA": "Construção Civil", "PDGR": "Construção Civil", "RDNI": "Construção Civil",
    
    # Transporte e Logística
    "RENT": "Transporte e Logística", "RAIL": "Transporte e Logística", "CCRO": "Transporte e Logística",
    "AZUL": "Transporte e Logística", "GOLL": "Transporte e Logística", "STBP": "Transporte e Logística",
    "POMO": "Transporte e Logística", "JSLG": "Transporte e Logística", "SIMH": "Transporte e Logística",
    "TGMA": "Transporte e Logística", "VAMO": "Transporte e Logística", "PORT": "Transporte e Logística",
    "ECOR": "Transporte e Logística", "LUXM": "Transporte e Logística",
    
    # Papel e Celulose
    "SUZB": "Papel e Celulose", "KLBN": "Papel e Celulose", "RANI": "Papel e Celulose",
    "DXCO": "Papel e Celulose",
    
    # Shoppings e Imóveis
    "MULT": "Shoppings e Imóveis", "IGTI": "Shoppings e Imóveis", "ALOS": "Shoppings e Imóveis",
    "ALLD": "Shoppings e Imóveis", "LOGG": "Shoppings e Imóveis", "SYNE": "Shoppings e Imóveis",
    "HBOR": "Shoppings e Imóveis",
    
    # Tecnologia e Telecom
    "TOTS": "Tecnologia", "LWSA": "Tecnologia", "POSI": "Tecnologia", "INTB": "Tecnologia",
    "NVTTS": "Tecnologia", "VIVT": "Telecomunicações", "TIMS": "Telecomunicações",
    "FIQE": "Telecomunicações", "DESK": "Telecomunicações", "OIBR": "Telecomunicações"
}

def atribuir_setor(ticker):
    prefixo = str(ticker)[:4].upper()
    return SETORES_RADICAIS.get(prefixo, "Outros Setores")

def obter_nome_empresa(ticker):
    prefixo = str(ticker)[:4].upper()
    return f"Empresa {prefixo}"

df["Segmento"] = df["Ticker"].apply(atribuir_setor)
df["Empresa"] = df["Ticker"].map(obter_nome_empresa)

colunas_ordenadas = [
    "Ticker", "Empresa", "Tipo", "Cotação", "Segmento", "P/L", "P/VP", 
    "Dividend Yield", "Patrimônio Líquido", "Liquidez Diária", "Margem EBIT", 
    "Margem Líquida", "ROIC", "ROE", "Cresc. 5 Anos (%)"
]
colunas_presentes = [col for col in colunas_ordenadas if col in df.columns]
df = df[colunas_presentes]

df.to_excel("acoes_b3.xlsx", index=False)
# Opcional: Remove ações sem negócios (Liquidez = 0) para limpar a base de dados
df = df[df["Liquidez Diária"] > 0].reset_index(drop=True)

print(f"\n✅ SUCESSO! Base atualizada e salva em 'acoes_b3.xlsx' com {len(df)} ações.")
print("\n--- Nova Distribuição dos Setores ---")
print(df["Segmento"].value_counts())