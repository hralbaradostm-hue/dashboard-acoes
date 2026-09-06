import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da Página
st.set_page_config(
    page_title="Dashboard Fundamentalista B3",
    page_icon="📊",
    layout="wide"
)

# Carregamento de Dados com Cache
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_excel("acoes_b3.xlsx")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo 'acoes_b3.xlsx': {e}")
        return pd.DataFrame()

df = carregar_dados()

if df.empty:
    st.warning("A base de dados está vazia ou não foi encontrada. Execute o script 'gerar_base.py' primeiro.")
    st.stop()

# Cabeçalho Principal
st.title("📊 Dashboard Fundamentalista da B3")
st.markdown("Análise quantitativa de indicadores de ações listadas na bolsa de valores brasileira.")

# =========================================================
# BARRA LATERAL: FILTROS
# =========================================================
st.sidebar.header("🔍 Filtros Fundamentalistas")

# 1. Filtro por Ticker / Nome da Empresa
busca = st.sidebar.text_input("Filtrar Ticker ou Empresa:")

# 2. Filtro por Setor
setores_disponiveis = sorted(df["Segmento"].unique().tolist())
setores_selecionados = st.sidebar.multiselect("Filtrar por Setor:", setores_disponiveis)

# 3. Filtro por Tipo de Ação (ON, PN, UNT)
tipos_disponiveis = sorted(df["Tipo"].unique().tolist())
tipos_selecionados = st.sidebar.multiselect(
    "Filtrar por Tipo de Ação:", 
    tipos_disponiveis, 
    default=tipos_disponiveis
)

# Sliders de Métricas Financeiras
pl_max = st.sidebar.slider("P/L Máximo:", 0.0, 100.0, 100.0)
dy_min = st.sidebar.slider("Dividend Yield Mínimo (%):", 0.0, 30.0, 0.0)
roe_min = st.sidebar.slider("ROE Mínimo (%):", -50.0, 100.0, -50.0)
liq_min = st.sidebar.slider("Liquidez Diária Mínima (R$):", 0, 10000000, 0, step=100000)

# =========================================================
# APLICAÇÃO DOS FILTROS NO DATAFRAME
# =========================================================
df_filtrado = df.copy()

if busca:
    df_filtrado = df_filtrado[
        df_filtrado["Ticker"].str.contains(busca, case=False, na=False) |
        df_filtrado["Empresa"].str.contains(busca, case=False, na=False)
    ]

if setores_selecionados:
    df_filtrado = df_filtrado[df_filtrado["Segmento"].isin(setores_selecionados)]

if tipos_selecionados:
    df_filtrado = df_filtrado[df_filtrado["Tipo"].isin(tipos_selecionados)]

df_filtrado = df_filtrado[
    (df_filtrado["P/L"] <= pl_max) &
    (df_filtrado["Dividend Yield"] >= dy_min) &
    (df_filtrado["ROE"] >= roe_min) &
    (df_filtrado["Liquidez Diária"] >= liq_min)
]

# =========================================================
# SEÇÃO 1: MÉTRICAS RESUMIDAS
# =========================================================
m1, m2, m3, m4 = st.columns(4)
m1.metric("Ações Filtradas", len(df_filtrado))
m2.metric("P/L Médio", f"{df_filtrado['P/L'].mean():.2f}" if not df_filtrado.empty else "0.00")
m3.metric("DY Médio", f"{df_filtrado['Dividend Yield'].mean():.2f}%" if not df_filtrado.empty else "0.00%")
m4.metric("ROE Médio", f"{df_filtrado['ROE'].mean():.2f}%" if not df_filtrado.empty else "0.00%")

st.divider()

# =========================================================
# SEÇÃO 2: GRÁFICOS INTERATIVOS DINÂMICOS
# =========================================================
st.subheader("📈 Análise Gráfica Dinâmica")

if not df_filtrado.empty:
    col_graf1, col_graf2 = st.columns(2)
    
    # Prepara dados limpos para Scatter Plot
    df_graf_scatter = df_filtrado[
        (df_filtrado["P/L"] > 0) & 
        (df_filtrado["P/L"] <= 100) & 
        (df_filtrado["ROE"] >= -50) & 
        (df_filtrado["ROE"] <= 100)
    ].copy()

    tem_setor_selecionado = len(setores_selecionados) > 0
    coluna_colorir = "Ticker" if tem_setor_selecionado else "Segmento"
    titulo_legenda = "Ação" if tem_setor_selecionado else "Setor"

    # --- GRÁFICO 1: Scatter Plot (P/L vs ROE) ---
    with col_graf1:
        if not df_graf_scatter.empty:
            s_min, s_max = df_graf_scatter["Liquidez Diária"].min(), df_graf_scatter["Liquidez Diária"].max()
            sizes = [20] * len(df_graf_scatter) if s_min == s_max else df_graf_scatter["Liquidez Diária"]

            fig_scatter = px.scatter(
                df_graf_scatter,
                x="P/L",
                y="ROE",
                size=sizes,
                color=coluna_colorir,
                hover_name="Ticker",
                title=f"Relação P/L vs. ROE (Colorido por {titulo_legenda})",
                labels={"P/L": "Preço / Lucro", "ROE": "ROE (%)", coluna_colorir: titulo_legenda}
            )
            fig_scatter.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Ações insuficientes para o Scatter Plot com os filtros atuais.")
        
    # --- GRÁFICO 2: Bar Chart (Dividend Yield) ---
    with col_graf2:
        df_graf_bar = df_filtrado[df_filtrado["Dividend Yield"] < 100].copy()

        if tem_setor_selecionado:
            df_bar_data = df_graf_bar.sort_values(by="Dividend Yield", ascending=False)
            fig_bar = px.bar(
                df_bar_data,
                x="Ticker",
                y="Dividend Yield",
                color="Dividend Yield",
                title=f"Dividend Yield Individual das Ações ({', '.join(setores_selecionados)})",
                labels={"Dividend Yield": "DY (%)", "Ticker": "Ação"},
                color_continuous_scale="Viridis"
            )
            fig_bar.update_layout(xaxis_tickangle=-45)
        else:
            df_setor_media = df_graf_bar.groupby("Segmento")["Dividend Yield"].mean().reset_index().sort_values(by="Dividend Yield", ascending=False)
            fig_bar = px.bar(
                df_setor_media,
                x="Segmento",
                y="Dividend Yield",
                color="Dividend Yield",
                title="Dividend Yield Médio por Setor (%)",
                labels={"Dividend Yield": "DY Médio (%)", "Segmento": "Setor"},
                color_continuous_scale="Viridis"
            )
            
        st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# =========================================================
# SEÇÃO 3: TABELA DE DADOS E RAIO-X
# =========================================================
st.subheader("📋 Tabela Complementar de Indicadores")

formatos = {
    "Cotação": "R$ {:.2f}",
    "P/L": "{:.2f}",
    "P/VP": "{:.2f}",
    "Dividend Yield": "{:.2f}%",
    "Margem EBIT": "{:.2f}%",
    "Margem Líquida": "{:.2f}%",
    "ROIC": "{:.2f}%",
    "ROE": "{:.2f}%",
    "Liquidez Diária": "R$ {:,.2f}",
    "Patrimônio Líquido": "R$ {:,.2f}",
    "Cresc. 5 Anos (%)": "{:.2f}%"
}

st.dataframe(
    df_filtrado.style.format(formatos, na_rep="-"),
    use_container_width=True,
    height=400
)

# Raio-X Individual
st.subheader("🔍 Raio-X da Ação")
ticker_escolhido = st.selectbox("Selecione um papel para análise detalhada:", options=[""] + df_filtrado["Ticker"].tolist())

if ticker_escolhido:
    acao = df[df["Ticker"] == ticker_escolhido].iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Preço Atual", f"R$ {acao['Cotação']:.2f}")
    c2.metric("Setor Oficial B3", acao["Segmento"])
    c3.metric("Tipo de Ação", acao["Tipo"])
    c4.metric("Dividend Yield", f"{acao['Dividend Yield']:.2f}%")