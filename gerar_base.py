import pandas as pd
import requests
import warnings
import re
import sys
from bs4 import BeautifulSoup

warnings.filterwarnings('ignore')

print("⏳ Conectando ao Fundamentus para baixar dados e aplicar mapeamento oficial da B3...")

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
    print(f"👉 Detalhe: {e}")
    sys.exit(1)

soup = BeautifulSoup(resposta.text, 'html.parser')
tabela = soup.find('table', {'id': 'resultado'})

if not tabela:
    print("\n⚠️ ALERTA DE MUDANÇA DE LAYOUT: A tabela 'resultado' não foi encontrada.")
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
    print(f"\n⚠️ ALERTA DE MUDANÇA NAS COLUNAS: Colunas não encontradas: {colunas_faltantes}")
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

# IDENTIFICAÇÃO DOS TIPOS DE AÇÃO (ON, PN, UNT)
def identificar_tipo_acao(ticker):
    t_str = str(ticker).strip().upper()
    if t_str.endswith("11"):
        return "UNT"  # Unit
    elif t_str.endswith(("3", "7")):
        return "ON"   # Ordinária
    elif t_str.endswith(("4", "5", "6", "8")):
        return "PN"   # Preferencial
    else:
        return "Outros"

df["Tipo"] = df["Ticker"].apply(identificar_tipo_acao)

# 4. DICIONÁRIO EXAUSTIVO COM NOMENCLATURA SETORIAL OFICIAL DA B3
SETORES_OFICIAIS_B3 = {
    # Utilidade Pública / Energia Elétrica
    "ELET": "Energia Elétrica", "CMIG": "Energia Elétrica", "CPLE": "Energia Elétrica", "TAEE": "Energia Elétrica",
    "TRPL": "Energia Elétrica", "EGIE": "Energia Elétrica", "EQTL": "Energia Elétrica", "ALUP": "Energia Elétrica",
    "ENEV": "Energia Elétrica", "NEOE": "Energia Elétrica", "AURE": "Energia Elétrica", "CPFE": "Energia Elétrica",
    "LIGT": "Energia Elétrica", "AESB": "Energia Elétrica", "ENGI": "Energia Elétrica", "MEGA": "Energia Elétrica",
    "GEPA": "Energia Elétrica", "CLSA": "Energia Elétrica", "COCE": "Energia Elétrica", "CSRN": "Energia Elétrica",
    "EKTR": "Energia Elétrica", "ELEK": "Energia Elétrica", "EMAE": "Energia Elétrica", "RNEW": "Energia Elétrica",
    "TRAN": "Energia Elétrica", "CEEB": "Energia Elétrica", "CEED": "Energia Elétrica", "CEBR": "Energia Elétrica",
    "LPSB": "Energia Elétrica", "ENMT": "Energia Elétrica", "ENBR": "Energia Elétrica", "CBEE": "Energia Elétrica",

    # Utilidade Pública / Água e Saneamento
    "SBSP": "Água e Saneamento", "SAPR": "Água e Saneamento", "CSMG": "Água e Saneamento",
    "AMBP": "Água e Saneamento", "ORVR": "Água e Saneamento", "CASN": "Água e Saneamento",

    # Financeiro / Bancos
    "ITUB": "Bancos", "BBDC": "Bancos", "BBAS": "Bancos", "SANB": "Bancos", "BPAC": "Bancos",
    "BRSR": "Bancos", "ABCB": "Bancos", "BPAN": "Bancos", "BAZA": "Bancos", "BMIN": "Bancos",
    "BNBR": "Bancos", "BSLI": "Bancos", "PINE": "Bancos", "BMEB": "Bancos", "BEES": "Bancos",
    "BGIP": "Bancos", "RPAD": "Bancos",

    # Financeiro / Exploração de Imóveis
    "ALOS": "Exploração de Imóveis", "MULT": "Exploração de Imóveis", "IGTI": "Exploração de Imóveis",
    "LOGG": "Exploração de Imóveis", "SYNE": "Exploração de Imóveis", "HBOR": "Exploração de Imóveis",
    "ALLD": "Exploração de Imóveis", "SCAR": "Exploração de Imóveis", "CORR": "Exploração de Imóveis",

    # Financeiro / Previdência e Seguros
    "BBSE": "Previdência e Seguros", "CXSE": "Previdência e Seguros", "PSSA": "Previdência e Seguros",
    "IRBR": "Previdência e Seguros", "WIZC": "Previdência e Seguros", "CSAB": "Previdência e Seguros",

    # Financeiro / Serviços Financeiros Diversos
    "B3SA": "Serviços Financeiros Diversos", "CIEL": "Serviços Financeiros Diversos", "CASH": "Serviços Financeiros Diversos",
    "CLEI": "Serviços Financeiros Diversos",

    # Petróleo, Gás e Biocombustíveis
    "PETR": "Petróleo, Gás e Biocombustíveis", "PRIO": "Petróleo, Gás e Biocombustíveis",
    "RECV": "Petróleo, Gás e Biocombustíveis", "RRRP": "Petróleo, Gás e Biocombustíveis",
    "UGPA": "Petróleo, Gás e Biocombustíveis", "CSAN": "Petróleo, Gás e Biocombustíveis",
    "VBBR": "Petróleo, Gás e Biocombustíveis", "OPCT": "Petróleo, Gás e Biocombustíveis",
    "RAIZ": "Petróleo, Gás e Biocombustíveis", "DMMO": "Petróleo, Gás e Biocombustíveis",

    # Materiais Básicos / Mineração, Siderurgia e Papel
    "VALE": "Mineração", "CMIN": "Mineração", "BRAP": "Mineração", "MNSA": "Mineração",
    "GGBR": "Siderurgia e Metalurgia", "GOAU": "Siderurgia e Metalurgia", "CSNA": "Siderurgia e Metalurgia",
    "USIM": "Siderurgia e Metalurgia", "FESA": "Siderurgia e Metalurgia", "TKNO": "Siderurgia e Metalurgia",
    "SUZB": "Papel e Celulose", "KLBN": "Papel e Celulose", "RANI": "Papel e Celulose", "DXCO": "Papel e Celulose",
    "EUCA": "Papel e Celulose", "CRPG": "Químicos", "UNIP": "Químicos", "BRKM": "Químicos", "FHER": "Químicos",

    # Bens Industriais
    "WEGE": "Máquinas e Equipamentos", "LEVE": "Máquinas e Equipamentos", "MYPK": "Máquinas e Equipamentos",
    "TUPY": "Máquinas e Equipamentos", "SHUL": "Máquinas e Equipamentos", "ROMI": "Máquinas e Equipamentos",
    "KEPL": "Máquinas e Equipamentos", "EALT": "Máquinas e Equipamentos", "BALM": "Máquinas e Equipamentos",
    "RENT": "Transporte e Logística", "RAIL": "Transporte e Logística", "CCRO": "Transporte e Logística",
    "AZUL": "Transporte e Logística", "GOLL": "Transporte e Logística", "STBP": "Transporte e Logística",
    "POMO": "Transporte e Logística", "JSLG": "Transporte e Logística", "SIMH": "Transporte e Logística",
    "TGMA": "Transporte e Logística", "VAMO": "Transporte e Logística", "PORT": "Transporte e Logística",
    "ECOR": "Transporte e Logística", "LUXM": "Transporte e Logística", "RAPT": "Material de Transporte",
    "FRAS": "Material de Transporte",

    # Consumo Cíclico / Comércio, Varejo e Construção Civil
    "MGLU": "Comércio / Varejo", "LREN": "Comércio / Varejo", "ARZZ": "Comércio / Varejo",
    "SOMA": "Comércio / Varejo", "BHIA": "Comércio / Varejo", "PETZ": "Comércio / Varejo",
    "VULC": "Comércio / Varejo", "ALPA": "Comércio / Varejo", "ASAI": "Comércio / Varejo",
    "CRFB": "Comércio / Varejo", "GMAT": "Comércio / Varejo", "LJQQ": "Comércio / Varejo",
    "SBFG": "Comércio / Varejo", "AMER": "Comércio / Varejo", "GUAR": "Comércio / Varejo",
    "CEAB": "Comércio / Varejo", "VLID": "Comércio / Varejo", "AMAR": "Comércio / Varejo",
    "CYRE": "Construção Civil", "EZTC": "Construção Civil", "MRVE": "Construção Civil",
    "TEND": "Construção Civil", "DIRR": "Construção Civil", "JHSF": "Construção Civil",
    "EVEN": "Construção Civil", "CURY": "Construção Civil", "PLPL": "Construção Civil",
    "LAVV": "Construção Civil", "MELK": "Construção Civil", "TRIS": "Construção Civil",
    "GFSA": "Construção Civil", "PDGR": "Construção Civil", "RDNI": "Construção Civil",
    "TCNO": "Construção Civil", "HOOT": "Hotelaria e Restaurantes", "BKBR": "Hotelaria e Restaurantes",
    "ZAMP": "Hotelaria e Restaurantes", "CNEW": "Viagens e Lazer", "SHOW": "Viagens e Lazer",

    # Consumo Não Cíclico / Alimentos Processados e Agropecuária
    "JBSS": "Alimentos Processados", "MRFG": "Alimentos Processados", "BRFS": "Alimentos Processados",
    "BEEF": "Alimentos Processados", "MDIA": "Alimentos Processados", "CAML": "Alimentos Processados",
    "MNPR": "Alimentos Processados", "BAHI": "Alimentos Processados",
    "ABEV": "Bebidas", "SLCE": "Agropecuária", "SMTO": "Agropecuária", "AGRO": "Agropecuária",
    "JALL": "Agropecuária", "SOJA": "Agropecuária", "TTEN": "Agropecuária", "FRTA": "Agropecuária",

    # Saúde e Farmácia
    "RADL": "Comércio / Varejo", "FLRY": "Serviços Médico-Hospitalares", "HYPE": "Medicamentos",
    "RDOR": "Serviços Médico-Hospitalares", "ONCO": "Serviços Médico-Hospitalares",
    "VVEO": "Serviços Médico-Hospitalares", "MATD": "Serviços Médico-Hospitalares",
    "PARD": "Serviços Médico-Hospitalares", "QUAL": "Serviços Médico-Hospitalares",
    "BLAU": "Medicamentos", "PNVL": "Comércio / Varejo", "ODPV": "Serviços Médico-Hospitalares",
    "HAPV": "Serviços Médico-Hospitalares", "DMVF": "Serviços Médico-Hospitalares",

    # Tecnologia e Telecom
    "TOTS": "Tecnologia da Informação", "LWSA": "Tecnologia da Informação", "POSI": "Tecnologia da Informação",
    "INTB": "Tecnologia da Informação", "NVTTS": "Tecnologia da Informação", "IFCM": "Tecnologia da Informação",
    "VIVT": "Telecomunicações", "TIMS": "Telecomunicações", "FIQE": "Telecomunicações",
    "DESK": "Telecomunicações", "OIBR": "Telecomunicações", "TELB": "Telecomunicações"
}

def atribuir_setor(ticker):
    prefixo = str(ticker)[:4].upper()
    return SETORES_OFICIAIS_B3.get(prefixo, "Outros Setores")

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

print(f"\n✅ SUCESSO! Base atualizada com a Nomenclatura Oficial da B3 e salva em 'acoes_b3.xlsx'.")
print("\n--- Distribuição por Nomenclatura Oficial B3 ---")
print(df["Segmento"].value_counts())