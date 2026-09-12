import io
import logging
import warnings
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

warnings.filterwarnings("ignore")
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E CHAVE BRAPI
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Terminal Albarado | Prudence Invest", layout="wide"
)

BRAPI_TOKEN = "sk_cd7bcb7a9ea454fedd7f8f2b4fcb6d9039c7958a0eb4e26e"


def limpar_num(val):
  if pd.isna(val) or val is None:
    return 0.0
  if isinstance(val, (int, float)):
    return float(val)
  s = str(val).replace("%", "").replace("R$", "").replace(" ", "").strip()
  if not s or s == "-":
    return 0.0
  if "," in s:
    s = s.replace(".", "").replace(",", ".")
  else:
    parts = s.split(".")
    if len(parts) > 2:
      s = "".join(parts)
    elif len(parts) == 2 and len(parts[1]) == 3 and len(parts[0]) <= 3:
      s = "".join(parts)
  try:
    return float(s)
  except Exception:
    return 0.0


def limpar_cache_global():
  st.cache_data.clear()


@st.cache_data(ttl=600)
def load_cofre_acoes():
  for f in ["cofre_lucros.csv", "cofre_lucros.xlsx"]:
    try:
      if f.endswith(".csv"):
        return pd.read_csv(f, encoding="utf-8-sig")
      return pd.read_excel(f)
    except Exception:
      pass
  return pd.DataFrame()


@st.cache_data(ttl=600)
def load_acoes_data():
  df_acoes = pd.DataFrame()
  try:
    url = f"https://brapi.dev/api/quote/list?type=stock&token={BRAPI_TOKEN}"
    res = requests.get(url, timeout=15)
    data = res.json()
    stocks = data.get("stocks", [])
    if stocks:
      df_acoes = pd.DataFrame(stocks)
      col_map = {
          "stock": "Ticker",
          "name": "Empresa",
          "close": "Cotação",
          "volume": "Liquidez Diária",
          "marketCap": "Patrimônio Líquido",
          "pe": "P/L",
          "vp": "P/VP",
          "dividendYield": "Dividend Yield",
          "sector": "Setor",
      }
      df_acoes = df_acoes.rename(columns=col_map)
      if "Dividend Yield" in df_acoes.columns:
        df_acoes["Dividend Yield"] = (
            df_acoes["Dividend Yield"].fillna(0) * 100.0
        )
  except Exception as e:
    st.error(f"Erro ao carregar ações da Brapi: {e}")

  # Colunas padrão essenciais para o scanner
  cols_padrao = {
      "Empresa": "N/A",
      "Setor": "Outros",
      "Tipo": "ON",
      "Segmento de Listagem": "Tradicional",
      "Tag Along (%)": 100.0,
      "Free Float (%)": 0.0,
      "Governo Majoritário": "Não",
      "Dívida Líquida/EBIT": 0.0,
      "Cotação": 0.0,
      "P/L": 0.0,
      "P/VP": 0.0,
      "Dividend Yield": 0.0,
      "Margem EBIT": 0.0,
      "Margem Líquida": 0.0,
      "ROIC": 0.0,
      "ROE": 0.0,
      "Liquidez Diária": 0.0,
      "Patrimônio Líquido": 0.0,
      "Cresc. 5 Anos (%)": 0.0,
  }
  for col, val_default in cols_padrao.items():
    if col not in df_acoes.columns:
      df_acoes[col] = val_default

  return df_acoes


@st.cache_data(ttl=600)
def load_fiis_data_v6():
  df_fiis = pd.DataFrame()
  try:
    url = f"https://brapi.dev/api/quote/list?type=fund&token={BRAPI_TOKEN}"
    res = requests.get(url, timeout=15)
    data = res.json()
    funds = data.get("stocks", [])
    if funds:
      df_fiis = pd.DataFrame(funds)
      col_map = {
          "stock": "Ticker",
          "name": "Nome",
          "close": "Cotação",
          "volume": "Liquidez diária",
          "marketCap": "Patrimônio Líquido",
          "dividendYield": "DY 12M Acumulado",
          "sector": "Segmento de Atuação",
      }
      df_fiis = df_fiis.rename(columns=col_map)
      if "DY 12M Acumulado" in df_fiis.columns:
        df_fiis["DY 12M Acumulado"] = (
            df_fiis["DY 12M Acumulado"].fillna(0) * 100.0
        )
  except Exception as e:
    st.error(f"Erro ao carregar FIIs da Brapi: {e}")

  cols_padrao = {
      "Tipo de fundo": "Híbrido",
      "Segmento de Atuação": "Outros",
      "Cotação": 0.0,
      "P/VP": 0.0,
      "DY 12M Acumulado": 0.0,
      "Vacância": 0.0,
      "Quantidade de Imóveis": 0,
      "Multi-inquilino": "Sim",
      "Quantidade de CRIs": 0,
      "Para FII de Papel % em CRIs": 0.0,
      "Liquidez diária": 0.0,
      "Patrimônio Líquido": 0.0,
      "Tempo de listagem": 5,
      "Tipo de Gestão": "Ativa",
      "Administrador": "BTG Pactual",
      "Taxa de adm": "0.75% a.a.",
      "Taxa de Performance": "Isento",
      "Benchmark": "IFIX",
  }
  for col, val_default in cols_padrao.items():
    if col not in df_fiis.columns:
      df_fiis[col] = val_default

  return df_fiis


df_cofre = load_cofre_acoes()
df_acoes = load_acoes_data()
df_fiis = load_fiis_data_v6()

# CONVERSÕES NUMÉRICAS E CÁLCULOS
if not df_acoes.empty:
  for col in [
      "Cotação",
      "P/L",
      "P/VP",
      "Dividend Yield",
      "Liquidez Diária",
      "Patrimônio Líquido",
  ]:
    if col in df_acoes.columns:
      df_acoes[col] = df_acoes[col].apply(limpar_num)

  df_acoes["Yield + CAGR (%)"] = df_acoes.get(
      "Dividend Yield", 0
  ) + df_acoes.get("Cresc. 5 Anos (%)", 0)
  df_acoes["Dividendo Pago (R$)"] = df_acoes.get("Cotação", 0) * (
      df_acoes.get("Dividend Yield", 0) / 100.0
  )
  df_acoes["Preço Teto (6%)"] = df_acoes["Dividendo Pago (R$)"] / 0.06
  df_acoes["Margem de Segurança (%)"] = np.where(
      df_acoes.get("Cotação", 0) > 0,
      ((df_acoes["Preço Teto (6%)"] / df_acoes["Cotação"]) - 1.0) * 100.0,
      0,
  )

if not df_fiis.empty:
  for col in [
      "Cotação",
      "P/VP",
      "DY 12M Acumulado",
      "Liquidez diária",
      "Patrimônio Líquido",
  ]:
    if col in df_fiis.columns:
      df_fiis[col] = df_fiis[col].apply(limpar_num)

  df_fiis["Desconto VP (%)"] = (1.0 - df_fiis.get("P/VP", 1.0)) * 100.0
  df_fiis["Rendimento 12M (R$)"] = df_fiis.get("Cotação", 0) * (
      df_fiis.get("DY 12M Acumulado", 0) / 100.0
  )
  df_fiis["Preço Teto (9%)"] = df_fiis["Rendimento 12M (R$)"] / 0.09
  df_fiis["Margem Teto (%)"] = np.where(
      df_fiis.get("Cotação", 0) > 0,
      ((df_fiis["Preço Teto (9%)"] / df_fiis["Cotação"]) - 1.0) * 100.0,
      -100.0,
  )

# -----------------------------------------------------------------------------
# DESIGN SYSTEM INSTITUCIONAL (SaaS)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stHeader"] { background-color: transparent; }
    [data-testid="stStatusWidget"] { visibility: hidden; display: none; }
    .stApp { background-color: #0f172a; color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #1e293b; border-right: 1px solid #334155; }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155; padding: 20px; border-radius: 12px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); text-align: center; margin-bottom: 10px;
    }
    .metric-title { font-size: 13px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    .metric-value { font-size: 26px; font-weight: 700; color: #38bdf8; margin-top: 5px; }
    </style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# BARRA LATERAL (FILTROS)
# -----------------------------------------------------------------------------
st.sidebar.title("🛡️ Terminal Albarado")
st.sidebar.caption("Prudence Invest | API Brapi 100%")

st.sidebar.button(
    "🧹 Recarregar Base & Limpar Cache",
    on_click=limpar_cache_global,
    use_container_width=True,
)

st.sidebar.markdown("## 🎯 Filtros de Ações")
tipos_acoes = (
    sorted([str(x) for x in df_acoes["Tipo"].unique() if pd.notna(x)])
    if "Tipo" in df_acoes.columns
    else []
)
segmentos_acoes = (
    sorted(
        [
            str(x)
            for x in df_acoes["Segmento de Listagem"].unique()
            if pd.notna(x)
        ]
    )
    if "Segmento de Listagem" in df_acoes.columns
    else []
)
setores_acoes = (
    sorted([str(x) for x in df_acoes["Setor"].unique() if pd.notna(x)])
    if "Setor" in df_acoes.columns
    else []
)


def limpar_filtros_acoes():
  st.session_state.tipo_filtro = []
  st.session_state.seg_filtro = []
  st.session_state.gov_filtro = "Ambos"
  st.session_state.setor_filtro = []
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

st.sidebar.button(
    "🔄 Resetar Filtros de Ações",
    on_click=limpar_filtros_acoes,
    use_container_width=True,
)

tipo_filtro = st.sidebar.multiselect(
    "1. Tipo de Ação", tipos_acoes, key="tipo_filtro"
)
seg_filtro = st.sidebar.multiselect(
    "2. Segmento B3", segmentos_acoes, key="seg_filtro"
)
gov_filtro = st.sidebar.radio(
    "3. Governo Majoritário", ["Não", "Sim", "Ambos"], key="gov_filtro"
)
setor_filtro = st.sidebar.multiselect(
    "4. Setor de Atuação", setores_acoes, key="setor_filtro"
)
liq_min = st.sidebar.number_input(
    "5. Liquidez Diária Mín. (R$)", min_value=0.0, step=50000.0, key="liq_min"
)
pat_min = st.sidebar.number_input(
    "6. Patrimônio Líq. Mín. (R$)",
    min_value=-10000000000.0,
    step=100000000.0,
    key="pat_min",
)
tag_min = st.sidebar.slider("7. Tag Along Mínimo (%)", 0, 100, key="tag_min")
ff_min = st.sidebar.slider(
    "8. Free Float Mínimo (%)", 0.0, 100.0, key="ff_min"
)
div_max = st.sidebar.number_input(
    "9. Dívida Líq./EBIT Máxima (x)",
    min_value=-50.0,
    max_value=100.0,
    key="div_max",
)
pl_min, pl_max = st.sidebar.slider(
    "10. P/L (Preço/Lucro)", -50.0, 150.0, key="pl_range"
)
pvp_min, pvp_max = st.sidebar.slider(
    "11. P/VP (Preço/VPA)", -10.0, 20.0, key="pvp_range"
)
roe_min = st.sidebar.slider("12. ROE Mínimo (%)", -50.0, 100.0, key="roe_min")
roic_min = st.sidebar.slider(
    "13. ROIC Mínimo (%)", -50.0, 100.0, key="roic_min"
)
mrg_min = st.sidebar.slider(
    "14. Margem Líquida Mín. (%)", -50.0, 100.0, key="mrg_min"
)
mrg_ebit_min = st.sidebar.slider(
    "15. Margem EBIT Mín. (%)", -50.0, 100.0, key="mrg_ebit_min"
)
cresc_min = st.sidebar.slider(
    "16. Cresc. 5 Anos Mín. (%)", -50.0, 100.0, key="cresc_min"
)
dy_min = st.sidebar.slider(
    "17. Dividend Yield Mín. (%)", 0.0, 50.0, key="dy_min"
)
soma_yc_min = st.sidebar.slider(
    "18. Soma Yield + CAGR Mín. (%)", -50.0, 100.0, key="soma_yc_min"
)
margem_seg_min = st.sidebar.slider(
    "19. Margem de Segurança Mín. (%)", -100.0, 100.0, key="margem_seg_min"
)

st.sidebar.markdown("---")
st.sidebar.markdown("## 🏢 Filtros de FIIs")
tipos_fii = (
    sorted([str(x) for x in df_fiis["Tipo de fundo"].unique() if pd.notna(x)])
    if "Tipo de fundo" in df_fiis.columns
    else []
)
segmentos_fii = (
    sorted(
        [str(x) for x in df_fiis["Segmento de Atuação"].unique() if pd.notna(x)]
    )
    if "Segmento de Atuação" in df_fiis.columns
    else []
)
gestoes_fii = (
    sorted([str(x) for x in df_fiis["Tipo de Gestão"].unique() if pd.notna(x)])
    if "Tipo de Gestão" in df_fiis.columns
    else []
)
multi_fii = (
    sorted(
        [str(x) for x in df_fiis["Multi-inquilino"].unique() if pd.notna(x)]
    )
    if "Multi-inquilino" in df_fiis.columns
    else []
)
admins_fii = (
    sorted([str(x) for x in df_fiis["Administrador"].unique() if pd.notna(x)])
    if "Administrador" in df_fiis.columns
    else []
)


def limpar_filtros_fiis():
  st.session_state.fii_tipo = []
  st.session_state.fii_seg = []
  st.session_state.fii_gestao = []
  st.session_state.fii_multi = []
  st.session_state.fii_admin = []
  st.session_state.fii_pvp = (0.0, 10.0)
  st.session_state.fii_dy = 0.0
  st.session_state.fii_vacancia = 100.0
  st.session_state.fii_liq = 0.0
  st.session_state.fii_pat = 0.0


if "fii_tipo" not in st.session_state:
  limpar_filtros_fiis()

st.sidebar.button(
    "🔄 Resetar Filtros de FIIs",
    on_click=limpar_filtros_fiis,
    use_container_width=True,
)

fii_tipo_filtro = st.sidebar.multiselect(
    "1. Tipo de Fundo", tipos_fii, key="fii_tipo"
)
fii_seg_filtro = st.sidebar.multiselect(
    "2. Segmento de Atuação", segmentos_fii, key="fii_seg"
)
fii_gestao_filtro = st.sidebar.multiselect(
    "3. Tipo de Gestão", gestoes_fii, key="fii_gestao"
)
fii_multi_filtro = st.sidebar.multiselect(
    "4. Multi-inquilino", multi_fii, key="fii_multi"
)
fii_pvp_min, fii_pvp_max = st.sidebar.slider(
    "5. Faixa de P/VP", 0.0, 10.0, key="fii_pvp"
)
fii_dy_min = st.sidebar.slider(
    "6. DY 12M Acumulado Mín. (%)", 0.0, 25.0, key="fii_dy"
)
fii_vac_max = st.sidebar.slider(
    "7. Vacância Máxima (%)", 0.0, 100.0, key="fii_vacancia"
)
fii_liq_min = st.sidebar.number_input(
    "8. Liquidez Diária Mín. (R$)", min_value=0.0, step=50000.0, key="fii_liq"
)
fii_pat_min = st.sidebar.number_input(
    "9. Patrimônio Líq. Mín. (R$)", min_value=0.0, step=50000000.0, key="fii_pat"
)
fii_admin_filtro = st.sidebar.multiselect(
    "10. Administrador", admins_fii, key="fii_admin"
)

# -----------------------------------------------------------------------------
# CORPO PRINCIPAL
# -----------------------------------------------------------------------------
st.title("🛡️ Prudence Invest | Terminal Albarado")
st.markdown("---")

st.subheader("📈 Scanner Fundamentalista de Ações")
if not df_acoes.empty:
  cond_acoes = pd.Series(True, index=df_acoes.index)
  if "Tipo" in df_acoes.columns and tipo_filtro:
    cond_acoes &= df_acoes["Tipo"].isin(tipo_filtro)
  if "Segmento de Listagem" in df_acoes.columns and seg_filtro:
    cond_acoes &= df_acoes["Segmento de Listagem"].isin(seg_filtro)
  if "Setor" in df_acoes.columns and setor_filtro:
    cond_acoes &= df_acoes["Setor"].isin(setor_filtro)
  if "Liquidez Diária" in df_acoes.columns:
    cond_acoes &= df_acoes["Liquidez Diária"] >= liq_min
  if "Patrimônio Líquido" in df_acoes.columns:
    cond_acoes &= df_acoes["Patrimônio Líquido"] >= pat_min
  if "P/L" in df_acoes.columns:
    cond_acoes &= df_acoes["P/L"].between(pl_min, pl_max)
  if "P/VP" in df_acoes.columns:
    cond_acoes &= df_acoes["P/VP"].between(pvp_min, pvp_max)
  if "Dividend Yield" in df_acoes.columns:
    cond_acoes &= df_acoes["Dividend Yield"] >= dy_min

  df_acoes_filtrado = df_acoes[cond_acoes]

  colunas_exib_acoes = [
      "Ticker",
      "Empresa",
      "Setor",
      "Cotação",
      "Preço Teto (6%)",
      "Margem de Segurança (%)",
      "Dividend Yield",
      "Dividendo Pago (R$)",
      "P/L",
      "P/VP",
      "Patrimônio Líquido",
      "Liquidez Diária",
  ]
  df_acoes_filtrado = df_acoes_filtrado[
      [c for c in colunas_exib_acoes if c in df_acoes_filtrado.columns]
  ]

  total_acoes = len(df_acoes_filtrado)
  media_dy_acoes = (
      df_acoes_filtrado["Dividend Yield"].mean()
      if (total_acoes > 0 and "Dividend Yield" in df_acoes_filtrado.columns)
      else 0
  )

  c1, c2, c3, c4 = st.columns(4)
  with c1:
    st.markdown(
        '<div class="metric-card"><div class="metric-title">🎯 Ações'
        f' Aprovadas</div><div class="metric-value">{total_acoes}</div></div>',
        unsafe_allow_html=True,
    )
  with c2:
    st.markdown(
        '<div class="metric-card"><div class="metric-title">💰 Média de'
        f' Yield</div><div class="metric-value">{media_dy_acoes:.2f}%</div></div>',
        unsafe_allow_html=True,
    )
  with c3:
    st.markdown(
        '<div class="metric-card"><div class="metric-title">🛡️ Status</div><div'
        ' class="metric-value">Online</div></div>',
        unsafe_allow_html=True,
    )
  with c4:
    st.markdown(
        '<div class="metric-card"><div class="metric-title">📊 Fonte</div><div'
        ' class="metric-value">Brapi API</div></div>',
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)
  st.dataframe(
      df_acoes_filtrado,
      column_config={
          "Cotação": st.column_config.NumberColumn(format="R$ %.2f"),
          "Preço Teto (6%)": st.column_config.NumberColumn(format="R$ %.2f"),
          "Dividendo Pago (R$)": st.column_config.NumberColumn(
              format="R$ %.2f"
          ),
          "Liquidez Diária": st.column_config.NumberColumn(format="R$ %.2f"),
          "Patrimônio Líquido": st.column_config.NumberColumn(
              format="R$ %.2f"
          ),
          "Dividend Yield": st.column_config.NumberColumn(format="%.2f %%"),
          "P/L": st.column_config.NumberColumn(format="%.2f x"),
          "P/VP": st.column_config.NumberColumn(format="%.2f x"),
      },
      hide_index=True,
  )

st.markdown("---")
st.subheader("🏢 Scanner Fundamentalista de FIIs (Fundos Imobiliários)")
if not df_fiis.empty:
  cond_fiis = pd.Series(True, index=df_fiis.index)
  if "Tipo de fundo" in df_fiis.columns and fii_tipo_filtro:
    cond_fiis &= df_fiis["Tipo de fundo"].isin(fii_tipo_filtro)
  if "Segmento de Atuação" in df_fiis.columns and fii_seg_filtro:
    cond_fiis &= df_fiis["Segmento de Atuação"].isin(fii_seg_filtro)
  if "P/VP" in df_fiis.columns:
    cond_fiis &= df_fiis["P/VP"].between(fii_pvp_min, fii_pvp_max)
  if "DY 12M Acumulado" in df_fiis.columns:
    cond_fiis &= df_fiis["DY 12M Acumulado"] >= fii_dy_min
  if "Liquidez diária" in df_fiis.columns:
    cond_fiis &= df_fiis["Liquidez diária"] >= fii_liq_min

  df_fiis_filtrado = df_fiis[cond_fiis]
  total_fiis = len(df_fiis_filtrado)

  st.markdown(
      f"**FIIs Aprovados:** {total_fiis} fundos encontrados via API Brapi."
  )
  st.dataframe(df_fiis_filtrado, hide_index=True)

st.markdown(
    """
    <div style='position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0f172a; color: #64748b; text-align: center; font-size: 14px; padding: 6px 0; border-top: 1px solid #1e293b; z-index: 99999;'>
        © 2026 Prudence Invest. Todos os direitos reservados.
    </div>
    """,
    unsafe_allow_html=True,
)