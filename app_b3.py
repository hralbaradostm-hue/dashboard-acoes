import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Dashboard Fundamentalista B3",
    page_icon="📊",
    layout="wide"
)

# Carrega a base de dados gerada pelo gerar_base.py
@st.cache_data
def carregar_dados():
    df = pd.read_excel("acoes_b3.xlsx")
    # Ordena inicialmente pelas ações mais líquidas
    if "Liquidez Diária" in df.columns:
        df = df.sort_values(by="Liquidez Diária", ascending=False).reset_index(drop=True)
    return df

df_raw = carregar_dados()

st.title("📊 Dashboard Fundamentalista da B3")
st.markdown("Analise e filtre ações brasileiras por fundamentos, rentabilidade e valoração.")

# =========================================================
# BARRA LATERAL (SIDEBAR) - FILTROS
# =========================================================
st.sidebar.header("🔍 Filtros Fundamentalistas")

# 1. Filtro por Ticker ou Nome da Empresa
busca_tabela = st.sidebar.text_input("Filtrar Tabela por Ticker/Empresa:", "").strip().upper()

# 2. Filtro por Setor/Segmento
setores_disponiveis = sorted(df_raw["Segmento"].dropna().unique().tolist())
setores_selecionados = st.sidebar.multiselect(
    "Filtrar por Setor:",
    options=setores_disponiveis,
    default=[]
)

st.sidebar.divider()

# 3. Sliders de Filtro
pl_max = st.sidebar.slider("P/L Máximo:", min_value=0.0, max_value=200.0, value=100.0, step=1.0)
dy_min = st.sidebar.slider("Dividend Yield Mínimo (%):", min_value=0.0, max_value=20.0, value=0.0, step=0.5)
roe_min = st.sidebar.slider("ROE Mínimo (%):", min_value=-50.0, max_value=50.0, value=-50.0, step=1.0)

liquidez_min = st.sidebar.select_slider(
    "Liquidez Diária Mínima (R$):",
    options=[0, 100_000, 500_000, 1_000_000, 5_000_000, 10_000_000, 50_000_000],
    value=0,
    format_func=lambda x: "Sem filtro" if x == 0 else f"R$ {x/1_000_000:.1f} M" if x >= 1_000_000 else f"R$ {x/1_000:.0f} k"
)

# =========================================================
# APLICAÇÃO DOS FILTROS
# =========================================================
df_filtrado = df_raw.copy()

if busca_tabela:
    df_filtrado = df_filtrado[
        df_filtrado["Ticker"].astype(str).str.contains(busca_tabela, case=False) |
        df_filtrado["Empresa"].astype(str).str.contains(busca_tabela, case=False)
    ]

if setores_selecionados:
    df_filtrado = df_filtrado[df_filtrado["Segmento"].isin(setores_selecionados)]

if "P/L" in df_filtrado.columns:
    df_filtrado = df_filtrado[(df_filtrado["P/L"] > 0) & (df_filtrado["P/L"] <= pl_max)]

if "Dividend Yield" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Dividend Yield"] >= dy_min]

if "ROE" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["ROE"] >= roe_min]

if "Liquidez Diária" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Liquidez Diária"] >= liquidez_min]

# =========================================================
# MÉTRICAS DE RESUMO NO TOPO (COM TRATAMENTO DE OUTLIERS)
# =========================================================
col1, col2, col3, col4 = st.columns(4)
col1.metric("Ações Encontradas", len(df_filtrado))

if not df_filtrado.empty:
    # Filtra valores realistas para o cálculo das médias do topo
    dy_val = df_filtrado[df_filtrado["Dividend Yield"] < 100]["Dividend Yield"]
    pl_val = df_filtrado[(df_filtrado["P/L"] > 0) & (df_filtrado["P/L"] < 100)]["P/L"]
    roe_val = df_filtrado[(df_filtrado["ROE"] > -100) & (df_filtrado["ROE"] < 100)]["ROE"]

    col2.metric("DY Médio", f"{dy_val.mean():.2f}%" if not dy_val.empty else "-")
    col3.metric("P/L Médio", f"{pl_val.mean():.2f}" if not pl_val.empty else "-")
    col4.metric("ROE Médio", f"{roe_val.mean():.2f}%" if not roe_val.empty else "-")
else:
    col2.metric("DY Médio", "-")
    col3.metric("P/L Médio", "-")
    col4.metric("ROE Médio", "-")

st.divider()

# =========================================================
# SEÇÃO 1: BUSCA AVANÇADA / RAIO-X DA AÇÃO
# =========================================================
st.subheader("🔎 Raio-X da Ação")
lista_tickers = sorted(df_raw["Ticker"].dropna().unique().tolist())
ticker_selecionado = st.selectbox("Selecione um papel para análise detalhada:", options=[""] + lista_tickers)

if ticker_selecionado:
    acao = df_raw[df_raw["Ticker"] == ticker_selecionado].iloc[0]
    
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Cotação", f"R$ {acao.get('Cotação', 0):.2f}")
    m2.metric("P/L", f"{acao.get('P/L', 0):.2f}")
    m3.metric("P/VP", f"{acao.get('P/VP', 0):.2f}")
    m4.metric("DY (%)", f"{acao.get('Dividend Yield', 0):.2f}%")
    m5.metric("ROE", f"{acao.get('ROE', 0):.2f}%")
    m6.metric("Margem Líquida", f"{acao.get('Margem Líquida', 0):.2f}%")
    
    st.info(f"**Empresa:** {acao.get('Empresa', '-')} | **Setor:** {acao.get('Segmento', '-')} | **Patrimônio Líquido:** R$ {acao.get('Patrimônio Líquido', 0):,.0f}")

st.divider()

# =========================================================
# SEÇÃO 2: GRÁFICOS INTERATIVOS (SEM OUTLIERS DE ROE)
# =========================================================
st.subheader("📈 Análise Gráfica Setorial")

if not df_filtrado.empty:
    col_graf1, col_graf2 = st.columns(2)
    
    # Filtra dados para o gráfico espalhado (P/L < 100 e ROE entre -50% e 100%)
    df_graf = df_filtrado[
        (df_filtrado["P/L"] <= 100) & 
        (df_filtrado["ROE"] >= -50) & 
        (df_filtrado["ROE"] <= 100)
    ]
    
    with col_graf1:
        fig_roe = px.scatter(
            df_graf,
            x="P/L",
            y="ROE",
            size="Liquidez Diária",
            color="Segmento",
            hover_name="Ticker",
            title="Relação P/L vs. ROE (Filtrado de Outliers)",
            labels={"P/L": "Preço / Lucro", "ROE": "ROE (%)"}
        )
        st.plotly_chart(fig_roe, use_container_width=True)
        
    with col_graf2:
        df_setor = df_filtrado[df_filtrado["Dividend Yield"] < 100].groupby("Segmento")["Dividend Yield"].mean().reset_index().sort_values(by="Dividend Yield", ascending=False)
        fig_dy = px.bar(
            df_setor,
            x="Segmento",
            y="Dividend Yield",
            title="Dividend Yield Médio por Setor (%)",
            labels={"Dividend Yield": "DY Médio (%)", "Segmento": "Setor"},
            color="Dividend Yield",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_dy, use_container_width=True)

st.divider()

# =========================================================
# SEÇÃO 3: TABELA DE RESULTADOS
# =========================================================
st.subheader(f"📋 Tabela Completa de Ações ({len(df_filtrado)} papéis)")

st.dataframe(
    df_filtrado,
    column_config={
        "Cotação": st.column_config.NumberColumn("Cotação", format="R$ %.2f"),
        "P/L": st.column_config.NumberColumn("P/L", format="%.2f"),
        "P/VP": st.column_config.NumberColumn("P/VP", format="%.2f"),
        "Dividend Yield": st.column_config.NumberColumn("DY (%)", format="%.2f%%"),
        "Margem Líquida": st.column_config.NumberColumn("Margem Líquida (%)", format="%.2f%%"),
        "Margem EBIT": st.column_config.NumberColumn("Margem EBIT (%)", format="%.2f%%"),
        "ROIC": st.column_config.NumberColumn("ROIC (%)", format="%.2f%%"),
        "ROE": st.column_config.NumberColumn("ROE (%)", format="%.2f%%"),
        "Patrimônio Líquido": st.column_config.NumberColumn("Patrimônio Líquido (R$)", format="R$ %,.0f"),
        "Liquidez Diária": st.column_config.NumberColumn("Liquidez Diária (R$)", format="R$ %,.0f"),
    },
    use_container_width=True,
    hide_index=True
)