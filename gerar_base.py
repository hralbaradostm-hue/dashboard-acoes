import pandas as pd
import warnings
import ssl
import requests # <-- O nosso novo disfarce

warnings.filterwarnings('ignore')

# Ignorar o erro de SSL do Fundamentus
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

print("Baixando dados e classificando setores...")

url = "https://www.fundamentus.com.br/resultado.php"

# --- DISFARCE ATIVADO ---
# Simulando exatamente um navegador Google Chrome no Windows 11
cabecalho = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# O requests acessa o site "vestido" de Chrome
resposta = requests.get(url, headers=cabecalho, timeout=20)

# O pandas agora apenas lê o texto que o requests já baixou (sem tentar acessar a internet sozinho)
df = pd.read_html(
    resposta.text, 
    decimal=',', 
    thousands='.',
    encoding='latin1'
)[0]
# --- FIM DO DISFARCE ---

# Renomeando as colunas
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

# --- INTELIGÊNCIA PARA DEFINIR O SEGMENTO DA AÇÃO ---
def definir_segmento(ticker):
    prefixo = str(ticker)[:4].upper()
    
    bancos = ["ITUB", "BBDC", "BBAS", "SANB", "BPAC", "BRSR", "ABCB", "BPAN", "BGIP", "BSLI", "PINE", "BMGB"]
    energia = ["ELET", "CMIG", "CPLE", "TAEE", "TRPL", "EGIE", "ENBR", "EQTL", "NEOE", "AESB", "AURE", "ALUP", "ENEV"]
    saneamento = ["SBSP", "SAPR", "CSMG"]
    petroleo = ["PETR", "PRIO", "ENAT", "RECV", "RRRP", "UGPA", "CSAN", "VBRA", "RPMG"]
    mineracao = ["VALE", "GGBR", "GOAU", "CSNA", "USIM", "CMIN", "FESA", "BRAP"]
    varejo = ["MGLU", "LREN", "ARZZ", "SOMA", "CEAB", "GUAR", "BHIA", "VIVA", "AMER", "CGRA", "PETZ", "ALPA"]
    saude = ["RADL", "FLRY", "HYPE", "RDOR", "MATD", "PNVL", "ODPV", "AALR", "QUAL", "PARD", "BLAU"]
    alimentos = ["JBSS", "MRFG", "BRFS", "BEEF", "MDIA", "SMTO", "CAML", "AGRO", "SLCE", "TTEN"]
    tecnologia = ["TOTS", "LWSA", "CASH", "INTB", "MLAS", "POSI"]
    construcao = ["CYRE", "EZTC", "MRVE", "TEND", "DIRR", "JHSF", "HBOR", "PDGR", "GFSA", "TCSA"]
    logistica = ["WEGE", "RENT", "RAIL", "CCRO", "AZUL", "GOLL", "POMO", "TGMA", "STBP", "ECOR", "JSLG"]
    seguros = ["BBSE", "CXSE", "PSSA", "SULA", "WIZC", "IRBR"]
    papel = ["SUZB", "KLBN", "RANI", "DXCO"]
    telecom = ["VIVT", "TIMS", "OIBR", "DESK"]
    educacao = ["YDUQ", "COGN", "SEER", "ANIM", "BAHI"]
    shoppings = ["MULT", "IGTI", "ALOS", "SYNE", "BRPR"]

    if prefixo in bancos: return "Bancos"
    if prefixo in energia: return "Energia Elétrica"
    if prefixo in saneamento: return "Saneamento"
    if prefixo in petroleo: return "Petróleo e Gás"
    if prefixo in mineracao: return "Mineração e Siderurgia"
    if prefixo in varejo: return "Varejo e Comércio"
    if prefixo in saude: return "Saúde e Farmácia"
    if prefixo in alimentos: return "Agro e Alimentos"
    if prefixo in tecnologia: return "Tecnologia"
    if prefixo in construcao: return "Construção Civil"
    if prefixo in logistica: return "Transporte e Logística"
    if prefixo in seguros: return "Seguradoras"
    if prefixo in papel: return "Papel e Celulose"
    if prefixo in telecom: return "Telecomunicações"
    if prefixo in educacao: return "Educação"
    if prefixo in shoppings: return "Shoppings e Imóveis"
    
    return "Outros"

# Aplica a inteligência na tabela
df["Segmento"] = df["Ticker"].map(definir_segmento)

# Exportando a planilha
df.to_excel("acoes_b3.xlsx", index=False)
print(f"✅ SUCESSO! A planilha foi gerada com {len(df)} ações e os segmentos classificados.")