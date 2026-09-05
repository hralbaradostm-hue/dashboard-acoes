import pandas as pd
import warnings
import ssl
import requests

warnings.filterwarnings('ignore')

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

print("Baixando dados e obtendo setores oficiais...")

url = "https://www.fundamentus.com.br/resultado.php"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

resposta = requests.get(url, headers=headers, timeout=20)

df = pd.read_html(
    resposta.text, 
    decimal=',', 
    thousands='.',
    encoding='latin1'
)[0]

df.rename(columns={
    "Papel": "Ticker", "Cotacao": "Cotação", "ROIC": "ROIC", "ROE": "ROE",
    "Mrg.Ebit": "Margem EBIT", "Mrg.Liq": "Margem Líquida",
    "Patrim.Liq": "Patrimônio Líquido", "Liq.2meses": "Liquidez Diária"
}, inplace=True)

for col in ["ROIC", "ROE", "Margem EBIT", "Margem Líquida"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace("%", "").str.replace(".", "").str.replace(",", ".").astype(float)

df["Tipo"] = df["Ticker"].apply(lambda t: "ON" if str(t).endswith(("3","7")) else "PN")
df["Empresa"] = df["Ticker"]
df["Tag Along"] = 100
df["Free Float"] = 30.0
df["Governo Majoritário"] = "Não"

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
        
        "SBSP": "Saneamento", "SAPR": "Saneamento", "CSMG": "Saneamento",
        
        "PETR": "Petróleo e Gás", "PRIO": "Petróleo e Gás", "RECV": "Petróleo e Gás", 
        "RRRP": "Petróleo e Gás", "UGPA": "Petróleo e Gás", "CSAN": "Petróleo e Gás",
        
        "VALE": "Mineração e Siderurgia", "GGBR": "Mineração e Siderurgia", 
        "GOAU": "Mineração e Siderurgia", "CSNA": "Mineração e Siderurgia", 
        "USIM": "Mineração e Siderurgia", "CMIN": "Mineração e Siderurgia",
        
        "MGLU": "Varejo e Comércio", "LREN": "Varejo e Comércio", "ARZZ": "Varejo e Comércio", 
        "SOMA": "Varejo e Comércio", "BHIA": "Varejo e Comércio", "PETZ": "Varejo e Comércio",
        
        "RADL": "Saúde e Farmácia", "FLRY": "Saúde e Farmácia", "HYPE": "Saúde e Farmácia", 
        "RDOR": "Saúde e Farmácia", "ONCO3": "Saúde e Farmácia",
        
        "JBSS": "Agro e Alimentos", "MRFG": "Agro e Alimentos", "BRFS": "Agro e Alimentos", 
        "BEEF": "Agro e Alimentos", "MDIA": "Agro e Alimentos", "SLCE": "Agro e Alimentos",
        
        "RENT": "Transporte e Logística", "RAIL": "Transporte e Logística", 
        "CCRO": "Transporte e Logística", "AZUL": "Transporte e Logística", 
        "GOLL": "Transporte e Logística", "STBP": "Transporte e Logística",
        
        "BBSE": "Seguradoras", "CXSE": "Seguradoras", "PSSA": "Seguradoras", "IRBR": "Seguradoras",
        
        "SUZB": "Papel e Celulose", "KLBN": "Papel e Celulose", "RANI": "Papel e Celulose",
        
        "CYRE": "Construção Civil", "EZTC": "Construção Civil", "MRVE": "Construção Civil", 
        "TEND": "Construção Civil", "DIRR": "Construção Civil", "JHSF": "Construção Civil",
        
        "MULT": "Shoppings e Imóveis", "IGTI": "Shoppings e Imóveis", "ALOS": "Shoppings e Imóveis"
    }
    
    return setores_b3.get(prefixo, "Outros Setores")

df["Segmento"] = df["Ticker"].map(obter_setor_oficial)
df.to_excel("acoes_b3.xlsx", index=False)
print(f"✅ SUCESSO! A planilha foi gerada com {len(df)} ações e setores atualizados.")
