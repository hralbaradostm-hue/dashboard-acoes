from pathlib import Path
import pandas as pd
import streamlit as st
import requests
import urllib3
import yfinance as yf
import plotly.express as px

# Ocultar avisos de SSL se houver
urllib3.disable_warnings()

# --- CONFIGURAÇÃO DA CHAVE BOLSAI ---
CHAVE_BOLSAI = st.secrets["CHAVE_BOLSAI"]

# Configuração da página
st.set_page_config(page_title="Painel de Ações B3", page_icon="📊", layout="wide")
st.title("📊 Painel de Ações B3 - Filtro Livre")
st.caption("Filtre as ações na tabela e analise os fundamentos avançados no Raio-X abaixo.")

ARQUIVO = Path(__file__).resolve().parent / "acoes_b3.xlsx"

if not ARQUIVO.exists():
    st.error("Planilha 'acoes_b3.xlsx' não encontrada. Rode o script gerar_base.py primeiro.")
    st.stop()

@st.cache_data
def carregar_dados():
    df = pd.read_excel(ARQUIVO, engine="openpyxl")
    mapeamento = {
        "Mrg Ebit": "Margem EBIT", "Mrg.Ebit": "Margem EBIT", 
        "Mrg. Liq.": "Margem Líquida", "Mrg.Liq": "Margem Líquida", "Mrg. Líq.": "Margem Líquida",
        "Patrim. Liq": "Patrimônio Líquido", "Patrim.Liq": "Patrimônio Líquido", "Patrim. Líq": "Patrimônio Líquido",
        "Cotacao": "Cotação", "Liq.2meses": "Liquidez Diária"
    }
    df = df.rename(columns=mapeamento)
    
    if "Anos desde o IPO" not in df.columns: df["Anos desde o IPO"] = 0
    if "Dívida Líquida/EBIT" not in df.columns: df["Dívida Líquida/EBIT"] = 0.0
    
    colunas_num = ["Cotação", "Tag Along", "Free Float", "Patrimônio Líquido", "Liquidez Diária", 
                   "Margem EBIT", "Margem Líquida", "ROIC", "ROE", "Anos desde o IPO", "Dívida Líquida/EBIT"]
    
    for col in colunas_num:
        if col not in df.columns: df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            
    return df

df = carregar_dados()

# --- BARRA LATERAL: FILTROS DO USUÁRIO ---
st.sidebar.header("🔎 Filtros Iniciais")
f_ticker = st.sidebar.text_input("Ticker (ex: PETR4, VALE3)").strip().upper()
f_empresa = st.sidebar.text_input("Empresa (ex: Petrobras)").strip().upper()

if "Tipo" in df.columns:
    tipos = sorted([str(x) for x in df["Tipo"].dropna().unique()])
    f_tipo = st.sidebar.multiselect("Tipo de Ação", options=tipos, default=tipos)
else: f_tipo = []

if "Segmento" in df.columns:
    segmentos = sorted([str(x) for x in df["Segmento"].dropna().unique()])
    f_segmento = st.sidebar.multiselect("Segmento de Listagem", options=segmentos, default=segmentos)
else: f_segmento = []

st.sidebar.markdown("---")
st.sidebar.subheader("💰 Cotação e Liquidez")
c_min, c_max = st.sidebar.columns(2)
with c_min: f_preco_min = st.number_input("Preço Mín", value=0.0, step=1.0)
with c_max: f_preco_max = st.number_input("Preço Máx", value=0.0, step=1.0)
f_liquidez = st.sidebar.number_input("Liquidez Média Mín (R$)", value=0, step=100000)

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Fundamentalistas Básicos")
f_roe = st.sidebar.number_input("ROE Mínimo (%)", value=-100.0, step=1.0)
f_roic = st.sidebar.number_input("ROIC Mínimo (%)", value=-100.0, step=1.0)

# --- APLICAÇÃO DOS FILTROS ---
f = df.copy()
if f_ticker and "Ticker" in f.columns: f = f[f["Ticker"].astype(str).str.upper().str.contains(f_ticker)]
if f_empresa and "Empresa" in f.columns: f = f[f["Empresa"].astype(str).str.upper().str.contains(f_empresa)]
if f_tipo and "Tipo" in f.columns: f = f[f["Tipo"].astype(str).isin(f_tipo)]
if f_segmento and "Segmento" in f.columns: f = f[f["Segmento"].astype(str).isin(f_segmento)]
if f_preco_min > 0 and "Cotação" in f.columns: f = f[f["Cotação"] >= f_preco_min]
if f_preco_max > 0 and "Cotação" in f.columns: f = f[f["Cotação"] <= f_preco_max]
if f_liquidez > 0 and "Liquidez Diária" in f.columns: f = f[f["Liquidez Diária"] >= f_liquidez]
if "ROE" in f.columns: f = f[f["ROE"] >= f_roe]
if "ROIC" in f.columns: f = f[f["ROIC"] >= f_roic]

ordem = ["Ticker", "Empresa", "Tipo", "Cotação", "Segmento", "Patrimônio Líquido", "Liquidez Diária", "Margem EBIT", "Margem Líquida", "ROIC", "ROE"]
ordem_existente = [col for col in ordem if col in f.columns]
f = f[ordem_existente].sort_values("Ticker").reset_index(drop=True)

# Renderização da Tabela
st.write("### Tabela Geral (Filtros Rápidos)")
c1, c2 = st.columns([1, 4])
with c1: st.metric("Total de Ações Filtradas", len(f))
with c2: st.download_button("⬇️ Baixar Tabela", data=f.to_csv(index=False).encode("utf-8-sig"), file_name="acoes.csv", mime="text/csv")

st.dataframe(
    f, use_container_width=True, height=350, hide_index=True,
    column_config={
        "Cotação": st.column_config.NumberColumn("Preço (R$)", format="R$ %.2f"),
        "Patrimônio Líquido": st.column_config.NumberColumn("Patrim. Liq", format="R$ %,d"),
        "Liquidez Diária": st.column_config.NumberColumn("Liquidez", format="R$ %,d"),
        "Margem EBIT": st.column_config.NumberColumn("Margem EBIT", format="%.2f%%"),
        "Margem Líquida": st.column_config.NumberColumn("Margem Líquida", format="%.2f%%"),
        "ROIC": st.column_config.NumberColumn("ROIC", format="%.2f%%"),
        "ROE": st.column_config.NumberColumn("ROE", format="%.2f%%"),
    }
)

# --- SEÇÃO HÍBRIDA: RAIO-X API BOLSAI ---
st.markdown("---")
st.header("🔍 Raio-X Profundo (API Bolsai)")
st.caption("Consulte indicadores avançados de uma empresa específica (Consome 1 requisição do seu limite diário).")

rx_col1, rx_col2 = st.columns([1, 3])
with rx_col1:
    rx_ticker = st.text_input("Digite o Ticker (ex: PETR4, VALE3):").strip().upper()
    btn_buscar = st.button("Buscar Dados", type="primary")

if btn_buscar:
    if rx_ticker:
        with st.spinner(f"Buscando {rx_ticker} na Bolsai..."):
            url = f"https://api.usebolsai.com/api/v1/fundamentals/{rx_ticker}"
            headers = {"X-API-Key": CHAVE_BOLSAI}
            
            try:
                res = requests.get(url, headers=headers, verify=False)
                if res.status_code == 200:
                    dados = res.json()
                    
                    st.success(f"Dados atualizados para {dados.get('corporate_name', rx_ticker)}")
                    
                    # Organizando os dados premium em cartões
                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Dívida Líq / EBIT", dados.get("net_debt_ebit", "-"))
                    m2.metric("EV / EBITDA", dados.get("ev_ebitda", "-"))
                    m3.metric("P/L", dados.get("pl", "-"))
                    m4.metric("P/VP", dados.get("pvp", "-"))
                    m5.metric("Dívida / Patrimônio", dados.get("debt_equity", "-"))
                    
                    st.write("") # Espaço
                    
                    m6, m7, m8, m9, m10 = st.columns(5)
                    m6.metric("Margem Bruta", f"{dados.get('gross_margin', 0)}%")
                    m7.metric("Margem EBITDA", f"{dados.get('ebitda_margin', 0)}%")
                    m8.metric("CAGR Receita (5a)", f"{dados.get('cagr_revenue_5y', 0)}%")
                    m9.metric("CAGR Lucros (5a)", f"{dados.get('cagr_earnings_5y', 0)}%")
                    m10.metric("Dívida Total", f"R$ {dados.get('total_debt', 0):,.0f}".replace(",", "."))
                    
                   # --- NOVO BLOCO: GRÁFICO DE 1 ANO ---
                st.markdown("---")
                st.subheader(f"📈 Evolução de Preço (1 Ano) - {rx_ticker}")
                
                ticker_yf = f"{rx_ticker}.SA"
                
                with st.spinner("Buscando histórico na bolsa..."):
                    try:
                        # Nova forma de buscar para evitar o erro das colunas duplas
                        acao_yf = yf.Ticker(ticker_yf)
                        historico = acao_yf.history(period="1y")
                        
                        if not historico.empty:
                            fig = px.line(
                                historico, 
                                x=historico.index, 
                                y='Close', 
                                labels={'Close': 'Preço de Fechamento (R$)', 'Date': 'Data', 'index': 'Data'}
                            )
                            fig.update_layout(
                                template="plotly_white",
                                xaxis_title="",
                                yaxis_title="Preço (R$)",
                                margin=dict(l=0, r=0, t=30, b=0)
                            ) 
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("Não foi possível carregar o histórico desta ação.")
                    except Exception as e:
                        st.error(f"Erro ao buscar gráfico: {e}")
                # --- FIM DO NOVO BLOCO ---
                
            elif res.status_code == 401:
                st.error("Erro: Chave da API inválida ou limite excedido.")
            else:
                st.error(f"Ação não encontrada ou erro na API ({res.status_code}).")
        except Exception as e:
            st.error(f"Erro ao conectar com a API: {e}")
else:
    st.warning("Por favor, digite um Ticker antes de buscar.")