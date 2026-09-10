import streamlit as st
import pandas as pd
import io
import yfinance as yf

@st.cache_data
def load_cofre():
    try:
        return pd.read_excel("cofre_lucros.xlsx")
    except:
        return pd.DataFrame() # Retorna vazio se o cofre não existir

df_cofre = load_cofre()

# Configuração da Página
st.set_page_config(page_title="Scanner Fundamentalista B3 | Prudence Invest", layout="wide")

# --- DESIGN SYSTEM INSTITUCIONAL (SaaS) ---
st.markdown("""
    <style>
    /* Esconde elementos padrão do Streamlit que denunciam a plataforma */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Fundo geral da aplicação mais limpo e moderno */
    .stApp {
        background-color: #0f172a; /* Azul Noite Profundo / Estilo Bloomberg/TradingView */
        color: #f8fafc;
    }
    
    /* Estilização da Sidebar (Menu Lateral) */
    [data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid #334155;
    }
    
    /* Cards de Métricas Estilo SaaS */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-title {
        font-size: 13px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #38bdf8; /* Azul Neon Executivo */
        margin-top: 5px;
    }
    
    /* Tabelas e Dataframes com visual corporativo */
    dataframe {
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_excel("acoes_b3.xlsx")
    
    # 1. CRIA O INDICADOR CHOWDER RULE
    df["Yield + CAGR (%)"] = df["Dividend Yield"] + df["Cresc. 5 Anos (%)"]
    
    # 2. CALCULA O DIVIDENDO EM REAIS (R$)
    df["Dividendo Pago (R$)"] = df["Cotação"] * (df["Dividend Yield"] / 100)
    
    # 3. CÁLCULO DO PREÇO TETO DE 6% (Método Barsi/Bazin)
    df["Preço Teto (6%)"] = df["Dividendo Pago (R$)"] / 0.06
    
    # 4. CÁLCULO DA MARGEM DE SEGURANÇA (%)
    df["Margem de Segurança (%)"] = df.apply(
        lambda row: ((row["Preço Teto (6%)"] / row["Cotação"]) - 1) * 100 if row["Cotação"] > 0 else 0,
        axis=1
    )
    
    return df

df = load_data()

tipos_todos = list(df["Tipo"].unique())
segmentos_todos = list(df["Segmento de Listagem"].unique())
setores_todos = sorted(list(df["Setor"].unique()))

# --- FUNÇÃO PARA LIMPAR FILTROS (RESET) ---
def limpar_filtros():
    st.session_state.tipo_filtro = tipos_todos
    st.session_state.seg_filtro = segmentos_todos
    st.session_state.gov_filtro = "Ambos"
    st.session_state.setor_filtro = setores_todos
    st.session_state.liq_min = 0.0
    st.session_state.pat_min = -10000000000.0
    st.session_state.tag_min = 0
    st.session_state.ff_min = 0.0
    st.session_state.div_max = 100.0
    st.session_state.pl_range = (-50.0, 150.0)
    st.session_state.pvp_range = (-10.0, 20.0)
    st.session_state.roe_min = -50.0
    st.session_state.roic_min = -50.0
    st.session_state.mrg_min = -50.0
    st.session_state.mrg_ebit_min = -50.0
    st.session_state.cresc_min = -50.0
    st.session_state.dy_min = 0.0
    st.session_state.soma_yc_min = -50.0
    st.session_state.margem_seg_min = -100.0

if "tipo_filtro" not in st.session_state:
    limpar_filtros()

# --- BARRA LATERAL ---
st.sidebar.header("🎯 Filtros Fundamentalistas")

st.sidebar.button("🔄 Limpar Filtros (Mostrar Tudo)", on_click=limpar_filtros, use_container_width=True)
st.sidebar.markdown("---")

tipo_filtro = st.sidebar.multiselect("1. Tipo de Ação", tipos_todos, key="tipo_filtro")
seg_filtro = st.sidebar.multiselect("2. Segmento B3", segmentos_todos, key="seg_filtro")
gov_filtro = st.sidebar.radio("3. Governo Majoritário", ["Não", "Sim", "Ambos"], key="gov_filtro")
setor_filtro = st.sidebar.multiselect("4. Setor de Atuação", setores_todos, key="setor_filtro")
liq_min = st.sidebar.number_input("5. Liquidez Diária Mín. (R$)", min_value=0.0, step=500000.0, key="liq_min")
pat_min = st.sidebar.number_input("6. Patrimônio Líq. Mín. (R$)", min_value=-10000000000.0, step=100000000.0, key="pat_min")
tag_min = st.sidebar.slider("7. Tag Along Mínimo (%)", 0, 100, key="tag_min")
ff_min = st.sidebar.slider("8. Free Float Mínimo (%)", 0.0, 100.0, key="ff_min")
div_max = st.sidebar.number_input("9. Dívida Líq./EBIT Máxima (x)", min_value=-50.0, max_value=100.0, key="div_max")
pl_min, pl_max = st.sidebar.slider("10. P/L (Preço/Lucro)", -50.0, 150.0, key="pl_range")
pvp_min, pvp_max = st.sidebar.slider("11. P/VP (Preço/VPA)", -10.0, 20.0, key="pvp_range")
roe_min = st.sidebar.slider("12. ROE Mínimo (%)", -50.0, 100.0, key="roe_min")
roic_min = st.sidebar.slider("13. ROIC Mínimo (%)", -50.0, 100.0, key="roic_min")
mrg_min = st.sidebar.slider("14. Margem Líquida Mín. (%)", -50.0, 100.0, key="mrg_min")
mrg_ebit_min = st.sidebar.slider("15. Margem EBIT Mín. (%)", -50.0, 100.0, key="mrg_ebit_min")
cresc_min = st.sidebar.slider("16. Cresc. 5 Anos Mín. (%)", -50.0, 100.0, key="cresc_min")
dy_min = st.sidebar.slider("17. Dividend Yield Mín. (%)", 0.0, 50.0, key="dy_min")
soma_yc_min = st.sidebar.slider("18. Soma Yield + CAGR Mín. (%)", -50.0, 100.0, key="soma_yc_min")

st.sidebar.markdown("---")
st.sidebar.markdown("### 💎 Método Barsi")
margem_seg_min = st.sidebar.slider("19. Margem de Segurança Mín. (%)", -100.0, 100.0, key="margem_seg_min")
st.sidebar.caption("Selecione '0%' para mostrar apenas ações negociadas ABAIXO do Preço Teto de 6%.")

# --- MOTOR DE FILTRAGEM ---
df_filtrado = df[
    (df["Tipo"].isin(tipo_filtro)) &
    (df["Segmento de Listagem"].isin(seg_filtro)) &
    (df["Setor"].isin(setor_filtro)) &
    (df["Liquidez Diária"] >= liq_min) &
    (df["Patrimônio Líquido"] >= pat_min) &
    (df["Tag Along (%)"] >= tag_min) &
    (df["Free Float (%)"] >= ff_min) &
    (df["Dívida Líquida/EBIT"] <= div_max) &
    (df["P/L"].between(pl_min, pl_max)) &
    (df["P/VP"].between(pvp_min, pvp_max)) &
    (df["ROE"] >= roe_min) &
    (df["ROIC"] >= roic_min) &
    (df["Margem Líquida"] >= mrg_min) &
    (df["Margem EBIT"] >= mrg_ebit_min) &
    (df["Cresc. 5 Anos (%)"] >= cresc_min) &
    (df["Dividend Yield"] >= dy_min) &
    (df["Yield + CAGR (%)"] >= soma_yc_min) &
    (df["Margem de Segurança (%)"] >= margem_seg_min)
]

if gov_filtro != "Ambos":
    df_filtrado = df_filtrado[df_filtrado["Governo Majoritário"] == gov_filtro]

colunas_exibicao = [
    "Ticker", "Empresa", "Setor", "Cotação", "Preço Teto (6%)", "Margem de Segurança (%)",
    "Dividend Yield", "Dividendo Pago (R$)", "Tipo", "Segmento de Listagem", 
    "Tag Along (%)", "Free Float (%)", "Governo Majoritário", "Dívida Líquida/EBIT",
    "P/L", "P/VP", "Cresc. 5 Anos (%)", "Yield + CAGR (%)", 
    "ROIC", "ROE", "Margem EBIT", "Margem Líquida", "Patrimônio Líquido", "Liquidez Diária"
]

df_filtrado = df_filtrado[[col for col in colunas_exibicao if col in df_filtrado.columns]]

# --- FUNÇÃO DE EXPORTAÇÃO ---
def converter_para_excel(df_export):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Prudence_Invest')
    return buffer.getvalue()

# --- INTERFACE PRINCIPAL ---
st.title("🛡️ Prudence Invest | Institutional Terminal")
st.markdown("---")

# ==========================================
# PAINEL DE INDICADORES (KPIs COM CARDS SaaS)
# ==========================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🎯 Ações Aprovadas</div>
            <div class="metric-value">{len(df_filtrado)}</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    media_dy = df_filtrado["Dividend Yield"].mean() if len(df_filtrado) > 0 else 0
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">💰 Média de Yield</div>
            <div class="metric-value">{media_dy:.2f}%</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    maior_margem = df_filtrado["Margem de Segurança (%)"].max() if len(df_filtrado) > 0 else 0
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">💎 Maior Margem Seg.</div>
            <div class="metric-value">{maior_margem:.1f}%</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
    if len(df_filtrado) > 0:
        dados_excel = converter_para_excel(df_filtrado)
        st.download_button(
            label="📥 Baixar em Excel",
            data=dados_excel,
            file_name="Prudence_Invest_Selecao.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

st.markdown("<br>", unsafe_allow_html=True)

# Tabela com as Novas Colunas em Destaque
st.dataframe(
    df_filtrado,
    column_config={
        "Cotação": st.column_config.NumberColumn(format="R$ %.2f"),
        "Preço Teto (6%)": st.column_config.NumberColumn(format="R$ %.2f"),
        "Dividendo Pago (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
        "Margem de Segurança (%)": st.column_config.NumberColumn(format="%.2f %%"),
        "Liquidez Diária": st.column_config.NumberColumn(format="R$ %.2f"),
        "Patrimônio Líquido": st.column_config.NumberColumn(format="R$ %.2f"),
        "Tag Along (%)": st.column_config.NumberColumn(format="%.0f %%"),
        "Free Float (%)": st.column_config.NumberColumn(format="%.2f %%"),
        "ROE": st.column_config.NumberColumn(format="%.2f %%"),
        "ROIC": st.column_config.NumberColumn(format="%.2f %%"),
        "Margem Líquida": st.column_config.NumberColumn(format="%.2f %%"),
        "Margem EBIT": st.column_config.NumberColumn(format="%.2f %%"),
        "Dividend Yield": st.column_config.NumberColumn(format="%.2f %%"),
        "Cresc. 5 Anos (%)": st.column_config.NumberColumn(format="%.2f %%"),
        "Yield + CAGR (%)": st.column_config.NumberColumn(format="%.2f %%"),
        "P/L": st.column_config.NumberColumn(format="%.2f x"),
        "P/VP": st.column_config.NumberColumn(format="%.2f x"),
        "Dívida Líquida/EBIT": st.column_config.NumberColumn(format="%.2f x")
    }
)

# ==========================================
# SISTEMA DE ALERTA NA TELA (RADAR DE OURO)
# ==========================================
if len(df_filtrado) > 0 and len(df_filtrado) <= 3 and margem_seg_min >= 10.0:
    st.toast("🚨 Radar Barsi: Oportunidade(s) de Ouro detectada(s)!", icon="💎")
    st.balloons()

# ==========================================
# SEÇÃO: RAIO-X HISTÓRICO (LUCRO E DIVIDENDOS)
# ==========================================
st.markdown("---")
st.title("📊 Raio-X Histórico: Lucros e Dividendos")
st.markdown("Selecione uma ação aprovada para ver a evolução do Lucro e o histórico Máximo de Dividendos.")

if len(df_filtrado) > 0:
    acao_selecionada = st.selectbox("Escolha a Ação para gerar os gráficos:", df_filtrado["Ticker"].tolist())

    if acao_selecionada:
        with st.spinner(f"Processando histórico de {acao_selecionada}..."):
            col1, col2 = st.columns(2)
            
            # --- GRÁFICO 1: LUCRO LÍQUIDO (DO COFRE EXCEL) ---
            with col1:
                st.markdown("**💰 Evolução do Lucro Líquido (Cofre Local)**")
                if not df_cofre.empty and acao_selecionada in df_cofre["Ticker"].values:
                    df_lucro_acao = df_cofre[df_cofre["Ticker"] == acao_selecionada].copy()
                    
                    df_lucro_acao.set_index("Ano", inplace=True)
                    df_grafico_lucro = pd.DataFrame({"Lucro Líquido (R$)": df_lucro_acao["Lucro Líquido"]})
                    df_grafico_lucro.index = df_grafico_lucro.index.astype(str)
                    
                    st.line_chart(df_grafico_lucro, use_container_width=True)
                else:
                    st.warning("Lucro Líquido não encontrado no Cofre de Dados.")

            # --- GRÁFICO 2: DIVIDENDOS (YAHOO FINANCE AO VIVO) ---
            with col2:
                st.markdown("**💸 Histórico Máximo de Dividendos**")
                try:
                    ticker_yf = yf.Ticker(f"{acao_selecionada}.SA")
                    historico_div = ticker_yf.dividends
                    
                    if not historico_div.empty:
                        div_anual = historico_div.groupby(historico_div.index.year).sum()
                        df_div = pd.DataFrame({"Dividendos Pagos (R$)": div_anual})
                        df_div.index = df_div.index.astype(str)
                        
                        st.line_chart(df_div, use_container_width=True)
                    else:
                        st.warning("Nenhum histórico de dividendos encontrado.")
                except Exception:
                    st.warning("O Yahoo Finance não reconhece este Ticker (Ação extinta ou sem dados).")