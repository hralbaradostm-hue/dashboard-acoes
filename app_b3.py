import streamlit as st
import pandas as pd
import io
import yfinance as yf

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO E CARREGAMENTO DE DADOS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Terminal Albarado | Prudence Invest", layout="wide")

@st.cache_data
def load_cofre_acoes():
    try:
        return pd.read_excel("cofre_lucros.xlsx")
    except:
        return pd.DataFrame()

@st.cache_data
def load_acoes_data():
    try:
        df = pd.read_excel("acoes_b3.xlsx")
    except Exception as e:
        return pd.DataFrame()
    
    if "Patrimônio Líquido" in df.columns:
        df = df[df["Patrimônio Líquido"] > 0].copy()

    # Cálculos defensivos para Ações
    if "Dividend Yield" in df.columns and "Cresc. 5 Anos (%)" in df.columns:
        df["Yield + CAGR (%)"] = df["Dividend Yield"] + df["Cresc. 5 Anos (%)"]
    else:
        df["Yield + CAGR (%)"] = 0.0
    
    if "Cotação" in df.columns and "Dividend Yield" in df.columns:
        df["Dividendo Pago (R$)"] = df["Cotação"] * (df["Dividend Yield"] / 100)
    else:
        df["Dividendo Pago (R$)"] = 0.0
    
    if "Dividendo Pago (R$)" in df.columns:
        df["Preço Teto (6%)"] = df["Dividendo Pago (R$)"] / 0.06
    else:
        df["Preço Teto (6%)"] = 0.0
    
    if "Preço Teto (6%)" in df.columns and "Cotação" in df.columns:
        df["Margem de Segurança (%)"] = df.apply(
            lambda row: ((row["Preço Teto (6%)"] / row["Cotação"]) - 1) * 100 if row["Cotação"] > 0 else 0,
            axis=1
        )
    else:
        df["Margem de Segurança (%)"] = 0.0
    
    return df

@st.cache_data
def load_fiis_data():
    try:
        df = pd.read_excel("fiis_b3.xlsx")
    except Exception:
        # FALLBACK AUTOMÁTICO: Caso o arquivo não esteja no GitHub, carrega os dados em memória
        dados_default = {
            "Ticker": ["HGLG11", "KNCR11", "MXRF11", "XPML11", "BTLG11", "VISC11", "TRXF11", "ALZR11", "CPTS11", "KNSC11"],
            "Tipo de fundo": ["Tijolo", "Papel", "Papel", "Tijolo", "Tijolo", "Tijolo", "Tijolo", "Tijolo", "Papel", "Papel"],
            "Segmento de Atuação": ["Logística", "Títulos e Val. Mob.", "Títulos e Val. Mob.", "Shoppings", "Logística", "Shoppings", "Híbrido", "Híbrido", "Títulos e Val. Mob.", "Títulos e Val. Mob."],
            "Cotação": [161.50, 102.30, 10.45, 112.80, 101.20, 120.50, 108.90, 116.40, 8.55, 91.20],
            "P/VP": [0.98, 1.01, 1.03, 0.97, 0.99, 0.96, 1.02, 1.04, 0.91, 0.98],
            "DY 12M Acumulado": [9.35, 12.40, 13.10, 9.75, 10.15, 9.60, 10.50, 9.80, 12.85, 12.20],
            "Liquidez diária": [4500000.0, 9200000.0, 12500000.0, 3800000.0, 5200000.0, 3100000.0, 2600000.0, 2100000.0, 6400000.0, 4100000.0],
            "Patrimônio Líquido": [3600000000.0, 5800000000.0, 3300000000.0, 3700000000.0, 3100000000.0, 2500000000.0, 1500000000.0, 1100000000.0, 2800000000.0, 1200000000.0],
            "Quantidade de Imóveis": [25, 0, 0, 22, 18, 20, 50, 15, 0, 0],
            "Multi-inquilino": ["Sim", "Não", "Não", "Sim", "Sim", "Sim", "Sim", "Sim", "Não", "Não"],
            "Vacância": [4.5, 0.0, 0.0, 5.2, 2.1, 4.0, 1.0, 0.0, 0.0, 0.0],
            "Para FII de Papel % em CRIs": [0.0, 95.0, 85.0, 0.0, 0.0, 0.0, 0.0, 0.0, 91.0, 93.5],
            "Administrador": ["Credit Suisse", "Kinea", "BTG Pactual", "BTG Pactual", "BTG Pactual", "BRL Trust", "BRL Trust", "BTG Pactual", "BTG Pactual", "Kinea"],
            "Tempo de listagem": [14, 12, 10, 6, 8, 10, 5, 6, 5, 4],
            "Tipo de Gestão": ["Ativa", "Ativa", "Ativa", "Ativa", "Ativa", "Ativa", "Ativa", "Ativa", "Ativa", "Ativa"],
            "Taxa de adm": ["0.60% a.a.", "1.00% a.a.", "0.90% a.a.", "0.95% a.a.", "0.90% a.a.", "1.00% a.a.", "1.00% a.a.", "0.20% a.a.", "1.05% a.a.", "1.00% a.a."],
            "Taxa de Performance": ["Não tem", "Não tem", "Não tem", "20% exceder IFIX", "Não tem", "20% exceder IFIX", "20% exceder IPCA+6%", "20% exceder IPCA+6%", "Não tem", "Não tem"],
            "Benchmark": ["IFIX", "CDI", "CDI", "IFIX", "IFIX", "IFIX", "IPCA + 6%", "IPCA + 6%", "CDI", "CDI"]
        }
        df = pd.DataFrame(dados_default)

    if "Patrimônio Líquido" in df.columns:
        df = df[df["Patrimônio Líquido"] > 0].copy()

    # Cálculos defensivos para FIIs
    if "DY 12M Acumulado" in df.columns and "Cotação" in df.columns:
        df["Rendimento 12M (R$)"] = df["Cotação"] * (df["DY 12M Acumulado"] / 100)
    else:
        df["Rendimento 12M (R$)"] = 0.0

    if "Rendimento 12M (R$)" in df.columns:
        df["Preço Teto (9%)"] = df["Rendimento 12M (R$)"] / 0.09
    else:
        df["Preço Teto (9%)"] = 0.0

    if "Preço Teto (9%)" in df.columns and "Cotação" in df.columns:
        df["Margem Teto (%)"] = df.apply(
            lambda row: ((row["Preço Teto (9%)"] / row["Cotação"]) - 1) * 100 if row["Cotação"] > 0 else 0,
            axis=1
        )
    else:
        df["Margem Teto (%)"] = 0.0

    if "P/VP" in df.columns:
        df["Desconto VP (%)"] = (1 - df["P/VP"]) * 100
    else:
        df["Desconto VP (%)"] = 0.0

    return df

df_cofre = load_cofre_acoes()
df_acoes = load_acoes_data()
df_fiis = load_fiis_data()

# -----------------------------------------------------------------------------
# DESIGN SYSTEM INSTITUCIONAL (SaaS)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stHeader"] { background-color: transparent; }
    [data-testid="stStatusWidget"] { visibility: hidden; display: none; }
    
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    [data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid #334155;
    }
    
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
        color: #38bdf8;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# BARRA LATERAL (FILTROS DE AÇÕES E FIIS EMPILHADOS)
# -----------------------------------------------------------------------------
st.sidebar.title("🛡️ Terminal Albarado")
st.sidebar.caption("Scanner Fundamentalista B3")

# =============================================================================
# 1. FILTROS COMPLETOS DE AÇÕES (1 a 19)
# =============================================================================
st.sidebar.markdown("## 🎯 Filtros de Ações")

tipos_acoes = list(df_acoes["Tipo"].unique()) if "Tipo" in df_acoes.columns else []
segmentos_acoes = list(df_acoes["Segmento de Listagem"].unique()) if "Segmento de Listagem" in df_acoes.columns else []
setores_acoes = sorted(list(df_acoes["Setor"].unique())) if "Setor" in df_acoes.columns else []

def limpar_filtros_acoes():
    st.session_state.tipo_filtro = tipos_acoes
    st.session_state.seg_filtro = segmentos_acoes
    st.session_state.gov_filtro = "Ambos"
    st.session_state.setor_filtro = setores_acoes
    st.session_state.liq_min = 0.0
    st.session_state.pat_min = 0.0
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
    limpar_filtros_acoes()

st.sidebar.button("🔄 Resetar Filtros de Ações", on_click=limpar_filtros_acoes, use_container_width=True)

tipo_filtro = st.sidebar.multiselect("1. Tipo de Ação", tipos_acoes, key="tipo_filtro")
seg_filtro = st.sidebar.multiselect("2. Segmento B3", segmentos_acoes, key="seg_filtro")
gov_filtro = st.sidebar.radio("3. Governo Majoritário", ["Não", "Sim", "Ambos"], key="gov_filtro")
setor_filtro = st.sidebar.multiselect("4. Setor de Atuação", setores_acoes, key="setor_filtro")
liq_min = st.sidebar.number_input("5. Liquidez Diária Mín. (R$)", min_value=0.0, step=50000.0, key="liq_min")
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
margem_seg_min = st.sidebar.slider("19. Margem de Segurança Mín. (%)", -100.0, 100.0, key="margem_seg_min")

# =============================================================================
# 2. FILTROS COMPLETOS DE FIIS (POSICIONADOS ABAIXO DAS AÇÕES)
# =============================================================================
st.sidebar.markdown("---")
st.sidebar.markdown("## 🏢 Filtros de FIIs")

tipos_fii = list(df_fiis["Tipo de fundo"].unique()) if "Tipo de fundo" in df_fiis.columns else []
segmentos_fii = sorted(list(df_fiis["Segmento de Atuação"].unique())) if "Segmento de Atuação" in df_fiis.columns else []
gestoes_fii = list(df_fiis["Tipo de Gestão"].unique()) if "Tipo de Gestão" in df_fiis.columns else []
multi_fii = list(df_fiis["Multi-inquilino"].unique()) if "Multi-inquilino" in df_fiis.columns else []
admins_fii = sorted(list(df_fiis["Administrador"].unique())) if "Administrador" in df_fiis.columns else []

def limpar_filtros_fiis():
    st.session_state.fii_tipo = tipos_fii
    st.session_state.fii_seg = segmentos_fii
    st.session_state.fii_gestao = gestoes_fii
    st.session_state.fii_multi = multi_fii
    st.session_state.fii_admin = admins_fii
    st.session_state.fii_pvp = (0.0, 2.0)
    st.session_state.fii_dy = 0.0
    st.session_state.fii_vacancia = 100.0
    st.session_state.fii_cris = 0.0
    st.session_state.fii_imoveis = 0
    st.session_state.fii_tempo = 0
    st.session_state.fii_liq = 0.0
    st.session_state.fii_pat = 0.0

if "fii_tipo" not in st.session_state:
    limpar_filtros_fiis()

st.sidebar.button("🔄 Resetar Filtros de FIIs", on_click=limpar_filtros_fiis, use_container_width=True)

fii_tipo_filtro = st.sidebar.multiselect("1. Tipo de Fundo (FII)", tipos_fii, key="fii_tipo")
fii_seg_filtro = st.sidebar.multiselect("2. Segmento de Atuação", segmentos_fii, key="fii_seg")
fii_gestao_filtro = st.sidebar.multiselect("3. Tipo de Gestão", gestoes_fii, key="fii_gestao")
fii_multi_filtro = st.sidebar.multiselect("4. Multi-inquilino", multi_fii, key="fii_multi")
fii_pvp_min, fii_pvp_max = st.sidebar.slider("5. Faixa de P/VP", 0.0, 2.0, key="fii_pvp")
fii_dy_min = st.sidebar.slider("6. DY 12M Acumulado Mín. (%)", 0.0, 25.0, key="fii_dy")
fii_vac_max = st.sidebar.slider("7. Vacância Máxima (%)", 0.0, 100.0, key="fii_vacancia")
fii_cris_min = st.sidebar.slider("8. % Mínimo em CRIs (Papel)", 0.0, 100.0, key="fii_cris")
fii_imoveis_min = st.sidebar.number_input("9. Qtd. Mínima de Imóveis", min_value=0, step=1, key="fii_imoveis")
fii_tempo_min = st.sidebar.number_input("10. Tempo Mín. Listagem (Anos)", min_value=0, step=1, key="fii_tempo")
fii_liq_min = st.sidebar.number_input("11. Liquidez Diária Mín. (R$)", min_value=0.0, step=50000.0, key="fii_liq")
fii_pat_min = st.sidebar.number_input("12. Patrimônio Líq. Mín. (R$)", min_value=0.0, step=50000000.0, key="fii_pat")
fii_admin_filtro = st.sidebar.multiselect("13. Administrador", admins_fii, key="fii_admin")

# -----------------------------------------------------------------------------
# CABEÇALHO DA APLICAÇÃO
# -----------------------------------------------------------------------------
st.title("🛡️ Prudence Invest | Terminal Albarado")
st.markdown("---")

# =============================================================================
# SEÇÃO 1: SCANNER DE AÇÕES B3
# =============================================================================
st.subheader("📈 Scanner Fundamentalista de Ações")

# Motor de Filtragem de Ações
cond_acoes = pd.Series(True, index=df_acoes.index)
if "Tipo" in df_acoes.columns: cond_acoes &= df_acoes["Tipo"].isin(tipo_filtro)
if "Segmento de Listagem" in df_acoes.columns: cond_acoes &= df_acoes["Segmento de Listagem"].isin(seg_filtro)
if "Setor" in df_acoes.columns: cond_acoes &= df_acoes["Setor"].isin(setor_filtro)
if "Liquidez Diária" in df_acoes.columns: cond_acoes &= df_acoes["Liquidez Diária"] >= liq_min
if "Patrimônio Líquido" in df_acoes.columns: cond_acoes &= df_acoes["Patrimônio Líquido"] >= pat_min
if "Tag Along (%)" in df_acoes.columns: cond_acoes &= df_acoes["Tag Along (%)"] >= tag_min
if "Free Float (%)" in df_acoes.columns: cond_acoes &= df_acoes["Free Float (%)"] >= ff_min
if "Dívida Líquida/EBIT" in df_acoes.columns: cond_acoes &= df_acoes["Dívida Líquida/EBIT"] <= div_max
if "P/L" in df_acoes.columns: cond_acoes &= df_acoes["P/L"].between(pl_min, pl_max)
if "P/VP" in df_acoes.columns: cond_acoes &= df_acoes["P/VP"].between(pvp_min, pvp_max)
if "ROE" in df_acoes.columns: cond_acoes &= df_acoes["ROE"] >= roe_min
if "ROIC" in df_acoes.columns: cond_acoes &= df_acoes["ROIC"] >= roic_min
if "Margem Líquida" in df_acoes.columns: cond_acoes &= df_acoes["Margem Líquida"] >= mrg_min
if "Margem EBIT" in df_acoes.columns: cond_acoes &= df_acoes["Margem EBIT"] >= mrg_ebit_min
if "Cresc. 5 Anos (%)" in df_acoes.columns: cond_acoes &= df_acoes["Cresc. 5 Anos (%)"] >= cresc_min
if "Dividend Yield" in df_acoes.columns: cond_acoes &= df_acoes["Dividend Yield"] >= dy_min
if "Yield + CAGR (%)" in df_acoes.columns: cond_acoes &= df_acoes["Yield + CAGR (%)"] >= soma_yc_min
if "Margem de Segurança (%)" in df_acoes.columns: cond_acoes &= df_acoes["Margem de Segurança (%)"] >= margem_seg_min
if gov_filtro != "Ambos" and "Governo Majoritário" in df_acoes.columns:
    cond_acoes &= df_acoes["Governo Majoritário"] == gov_filtro

df_acoes_filtrado = df_acoes[cond_acoes]

colunas_exib_acoes = [
    "Ticker", "Empresa", "Setor", "Cotação", "Preço Teto (6%)", "Margem de Segurança (%)",
    "Dividend Yield", "Dividendo Pago (R$)", "Tipo", "Segmento de Listagem", 
    "Tag Along (%)", "Free Float (%)", "Governo Majoritário", "Dívida Líquida/EBIT",
    "P/L", "P/VP", "Cresc. 5 Anos (%)", "Yield + CAGR (%)", 
    "ROIC", "ROE", "Margem EBIT", "Margem Líquida", "Patrimônio Líquido", "Liquidez Diária"
]
df_acoes_filtrado = df_acoes_filtrado[[c for c in colunas_exib_acoes if c in df_acoes_filtrado.columns]]

# KPIs Ações
total_acoes = len(df_acoes_filtrado)
media_dy_acoes = df_acoes_filtrado["Dividend Yield"].mean() if (total_acoes > 0 and "Dividend Yield" in df_acoes_filtrado.columns) else 0
mediana_margem_acoes = df_acoes_filtrado["Margem de Segurança (%)"].median() if (total_acoes > 0 and "Margem de Segurança (%)" in df_acoes_filtrado.columns) else 0
media_roe_acoes = df_acoes_filtrado["ROE"].mean() if (total_acoes > 0 and "ROE" in df_acoes_filtrado.columns) else 0

c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(f'<div class="metric-card"><div class="metric-title">🎯 Ações Aprovadas</div><div class="metric-value">{total_acoes}</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="metric-card"><div class="metric-title">💰 Média de Yield</div><div class="metric-value">{media_dy_acoes:.2f}%</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="metric-card"><div class="metric-title">🛡️ Margem Mediana</div><div class="metric-value">{mediana_margem_acoes:.1f}%</div></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="metric-card"><div class="metric-title">📊 ROE Médio</div><div class="metric-value">{media_roe_acoes:.2f}%</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tabela Ações
st.dataframe(
    df_acoes_filtrado,
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
    },
    hide_index=True
)

# =============================================================================
# SEÇÃO 2: RAIO-X HISTÓRICO (LUCROS E DIVIDENDOS DE AÇÕES)
# =============================================================================
st.markdown("---")
st.subheader("📊 Raio-X Histórico: Lucros e Dividendos (Ações)")

if total_acoes > 0 and "Ticker" in df_acoes_filtrado.columns:
    acao_sel = st.selectbox("Escolha uma ação aprovada para o Raio-X:", df_acoes_filtrado["Ticker"].tolist(), key="select_acao_rx")

    if acao_sel:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**💰 Evolução do Lucro Líquido (Cofre Local)**")
            if not df_cofre.empty and "Ticker" in df_cofre.columns and acao_sel in df_cofre["Ticker"].values:
                df_lucro = df_cofre[df_cofre["Ticker"] == acao_sel].copy()
                if "Ano" in df_lucro.columns and "Lucro Líquido" in df_lucro.columns:
                    df_lucro.set_index("Ano", inplace=True)
                    st.line_chart(pd.DataFrame({"Lucro Líquido (R$)": df_lucro["Lucro Líquido"]}), use_container_width=True)
                else: st.warning("Dados incompletos no cofre.")
            else: st.warning("Lucro não encontrado no cofre local.")

        with col2:
            st.markdown("**💸 Histórico Máximo de Dividendos (Ao Vivo)**")
            try:
                hist_div = yf.Ticker(f"{acao_sel}.SA").dividends
                if not hist_div.empty:
                    div_anual = hist_div.groupby(hist_div.index.year).sum()
                    st.line_chart(pd.DataFrame({"Dividendos Pagos (R$)": div_anual}), use_container_width=True)
                else: st.warning("Nenhum histórico disponível.")
            except: st.warning("Erro ao consultar Yahoo Finance.")

# =============================================================================
# SEÇÃO 3: SCANNER FUNDAMENTALISTA DE FIIS (POSICIONADO ABAIXO DO RAIO-X)
# =============================================================================
st.markdown("---")
st.subheader("🏢 Scanner Fundamentalista de FIIs (Fundos Imobiliários)")

if not df_fiis.empty:
    # Motor de Filtragem de FIIs
    cond_fiis = pd.Series(True, index=df_fiis.index)
    if "Tipo de fundo" in df_fiis.columns: cond_fiis &= df_fiis["Tipo de fundo"].isin(fii_tipo_filtro)
    if "Segmento de Atuação" in df_fiis.columns: cond_fiis &= df_fiis["Segmento de Atuação"].isin(fii_seg_filtro)
    if "Tipo de Gestão" in df_fiis.columns: cond_fiis &= df_fiis["Tipo de Gestão"].isin(fii_gestao_filtro)
    if "Multi-inquilino" in df_fiis.columns: cond_fiis &= df_fiis["Multi-inquilino"].isin(fii_multi_filtro)
    if "Administrador" in df_fiis.columns: cond_fiis &= df_fiis["Administrador"].isin(fii_admin_filtro)
    if "P/VP" in df_fiis.columns: cond_fiis &= df_fiis["P/VP"].between(fii_pvp_min, fii_pvp_max)
    if "DY 12M Acumulado" in df_fiis.columns: cond_fiis &= df_fiis["DY 12M Acumulado"] >= fii_dy_min
    if "Vacância" in df_fiis.columns: cond_fiis &= df_fiis["Vacância"] <= fii_vac_max
    if "Para FII de Papel % em CRIs" in df_fiis.columns: cond_fiis &= df_fiis["Para FII de Papel % em CRIs"] >= fii_cris_min
    if "Quantidade de Imóveis" in df_fiis.columns: cond_fiis &= df_fiis["Quantidade de Imóveis"] >= fii_imoveis_min
    if "Tempo de listagem" in df_fiis.columns: cond_fiis &= df_fiis["Tempo de listagem"] >= fii_tempo_min
    if "Liquidez diária" in df_fiis.columns: cond_fiis &= df_fiis["Liquidez diária"] >= fii_liq_min
    if "Patrimônio Líquido" in df_fiis.columns: cond_fiis &= df_fiis["Patrimônio Líquido"] >= fii_pat_min

    df_fiis_filtrado = df_fiis[cond_fiis]

    colunas_exib_fiis = [
        "Ticker", "Tipo de fundo", "Segmento de Atuação", "Cotação", "P/VP", "Desconto VP (%)",
        "DY 12M Acumulado", "Rendimento 12M (R$)", "Preço Teto (9%)", "Margem Teto (%)",
        "Vacância", "Quantidade de Imóveis", "Multi-inquilino", "Para FII de Papel % em CRIs",
        "Liquidez diária", "Patrimônio Líquido", "Tempo de listagem", "Tipo de Gestão",
        "Administrador", "Taxa de adm", "Taxa de Performance", "Benchmark"
    ]
    df_fiis_filtrado = df_fiis_filtrado[[c for c in colunas_exib_fiis if c in df_fiis_filtrado.columns]]

    # KPIs FIIs
    total_fiis = len(df_fiis_filtrado)
    media_dy_fiis = df_fiis_filtrado["DY 12M Acumulado"].mean() if (total_fiis > 0 and "DY 12M Acumulado" in df_fiis_filtrado.columns) else 0
    mediana_pvp_fiis = df_fiis_filtrado["P/VP"].median() if (total_fiis > 0 and "P/VP" in df_fiis_filtrado.columns) else 0
    vacancia_media_fiis = df_fiis_filtrado["Vacância"].mean() if (total_fiis > 0 and "Vacância" in df_fiis_filtrado.columns) else 0

    f1, f2, f3, f4 = st.columns(4)
    with f1: st.markdown(f'<div class="metric-card"><div class="metric-title">🎯 FIIs Aprovados</div><div class="metric-value">{total_fiis}</div></div>', unsafe_allow_html=True)
    with f2: st.markdown(f'<div class="metric-card"><div class="metric-title">💰 DY 12M Médio</div><div class="metric-value">{media_dy_fiis:.2f}%</div></div>', unsafe_allow_html=True)
    with f3: st.markdown(f'<div class="metric-card"><div class="metric-title">🏷️ P/VP Mediano</div><div class="metric-value">{mediana_pvp_fiis:.2f}x</div></div>', unsafe_allow_html=True)
    with f4: st.markdown(f'<div class="metric-card"><div class="metric-title">🏗️ Vacância Média</div><div class="metric-value">{vacancia_media_fiis:.1f}%</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Botão de Download FIIs
    if total_fiis > 0:
        def conv_excel_fiis(df_e):
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as w: df_e.to_excel(w, index=False, sheet_name='FIIs')
            return buf.getvalue()
        
        _, col_btn_fii = st.columns([4, 1])
        with col_btn_fii:
            st.download_button("📥 Baixar FIIs (Excel)", data=conv_excel_fiis(df_fiis_filtrado), file_name="FIIs_Albarado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabela Completa de FIIs
    st.dataframe(
        df_fiis_filtrado,
        column_config={
            "Cotação": st.column_config.NumberColumn(format="R$ %.2f"),
            "P/VP": st.column_config.NumberColumn(format="%.2f x"),
            "Desconto VP (%)": st.column_config.NumberColumn(format="%.2f %%"),
            "DY 12M Acumulado": st.column_config.NumberColumn(format="%.2f %%"),
            "Rendimento 12M (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
            "Preço Teto (9%)": st.column_config.NumberColumn(format="R$ %.2f"),
            "Margem Teto (%)": st.column_config.NumberColumn(format="%.2f %%"),
            "Vacância": st.column_config.NumberColumn(format="%.2f %%"),
            "Para FII de Papel % em CRIs": st.column_config.NumberColumn(format="%.2f %%"),
            "Liquidez diária": st.column_config.NumberColumn(format="R$ %.2f"),
            "Patrimônio Líquido": st.column_config.NumberColumn(format="R$ %.2f"),
            "Quantidade de Imóveis": st.column_config.NumberColumn(format="%d imóveis"),
            "Tempo de listagem": st.column_config.NumberColumn(format="%d anos")
        },
        hide_index=True
    )
else:
    st.info("💡 Insira o arquivo 'fiis_b3.xlsx' na pasta do projeto para exibir os dados de Fundos Imobiliários.")

# -----------------------------------------------------------------------------
# RODAPÉ INSTITUCIONAL
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div style='
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0f172a;
        color: #64748b;
        text-align: center;
        font-size: 14px;
        padding: 6px 0;
        border-top: 1px solid #1e293b;
        z-index: 99999;
    '>
        © 2026 Prudence Invest. Todos os direitos reservados.
    </div>
    """,
    unsafe_allow_html=True
)