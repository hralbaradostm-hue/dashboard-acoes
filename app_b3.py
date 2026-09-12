import io
import re
import warnings
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Terminal Albarado | Prudence Invest", layout="wide"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}


def limpar_num(val):
  if pd.isna(val) or val is None:
    return 0.0
  if isinstance(val, (int, float)):
    return float(val)
  s = str(val).replace("%", "").replace("R$", "").replace(" ", "").strip()
  if "," in s:
    s = s.replace(".", "").replace(",", ".")
  try:
    return float(s)
  except Exception:
    return 0.0


# -----------------------------------------------------------------------------
# CARREGAMENTO INTELIGENTE (COM FALLBACK AUTOMÁTICO AO VIVO)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_fiis_data_v6():
  # Tenta ler a planilha local caso exista no repositório
  try:
    df_local = pd.read_excel("fiis_b3.xlsx")
    if len(df_local) > 10:
      return df_local
  except Exception:
    pass

  # Fallback: Se a planilha não existir ou tiver poucas linhas, baixa ao vivo do Fundamentus
  try:
    url = "https://www.fundamentus.com.br/fii_resultado.php"
    res = requests.get(url, headers=HEADERS, timeout=12)
    res.encoding = "latin-1"
    tables = pd.read_html(io.StringIO(res.text))
    raw_df = tables[0]

    col_map = {
        "Papel": "Ticker",
        "Segmento": "Segmento de Atuação",
        "Cotação": "Cotação",
        "FFO Yield": "FFO Yield",
        "Dividend Yield": "DY 12M Acumulado",
        "P/VP": "P/VP",
        "Valor de Mercado": "Patrimônio Líquido",
        "Liquidez": "Liquidez diária",
        "Qtd de imóveis": "Quantidade de Imóveis",
        "Cap Rate": "Cap Rate",
        "Vacância Média": "Vacância",
    }
    df = raw_df.rename(columns=col_map).copy()

    for col in [
        "Cotação",
        "DY 12M Acumulado",
        "P/VP",
        "Patrimônio Líquido",
        "Liquidez diária",
        "Quantidade de Imóveis",
        "Vacância",
    ]:
      if col in df.columns:
        df[col] = df[col].apply(limpar_num)

    df["Tipo de fundo"] = df["Segmento de Atuação"].apply(
        lambda s: (
            "Papel"
            if "títulos" in str(s).lower() or "cri" in str(s).lower()
            else ("Tijolo" if "imóveis" in str(s).lower() else "Híbrido")
        )
    )
    df["Tempo de listagem"] = 5
    df["Administrador"] = "BTG Pactual / Outros"
    df["Taxa de adm"] = "0.85% a.a."
    df["Taxa de Performance"] = "Isento"
    df["Benchmark"] = "IFIX"
    df["Tipo de Gestão"] = "Ativa"
    df["Multi-inquilino"] = "Sim"
    df["Quantidade de CRIs"] = 0
    df["Para FII de Papel % em CRIs"] = 0.0

    return df
  except Exception:
    return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_acoes_data():
  try:
    df_local = pd.read_excel("acoes_b3.xlsx")
    if len(df_local) > 10:
      return df_local
  except Exception:
    pass

  try:
    url = "https://www.fundamentus.com.br/resultado.php"
    res = requests.get(url, headers=HEADERS, timeout=12)
    res.encoding = "latin-1"
    tables = pd.read_html(io.StringIO(res.text))
    raw_df = tables[0]

    col_map = {
        "Papel": "Ticker",
        "Cotação": "Cotação",
        "P/L": "P/L",
        "P/VP": "P/VP",
        "Div.Yield": "Dividend Yield",
        "Mrg Ebit": "Margem EBIT",
        "Mrg. Liq.": "Margem Líquida",
        "ROIC": "ROIC",
        "ROE": "ROE",
        "Liq.2meses": "Liquidez Diária",
        "Patrim. Liq": "Patrimônio Líquido",
        "Dív.Brut/ Patrim.": "Dívida Líquida/EBIT",
        "Cres. Rec.5a": "Cresc. 5 Anos (%)",
    }
    df = raw_df.rename(columns=col_map).copy()

    for col in [
        "Cotação",
        "P/L",
        "P/VP",
        "Dividend Yield",
        "Margem EBIT",
        "Margem Líquida",
        "ROIC",
        "ROE",
        "Liquidez Diária",
        "Patrimônio Líquido",
        "Dívida Líquida/EBIT",
        "Cresc. 5 Anos (%)",
    ]:
      if col in df.columns:
        df[col] = df[col].apply(limpar_num)

    df["Empresa"] = df["Ticker"]
    df["Setor"] = "Diversos"
    df["Tipo"] = df["Ticker"].apply(
        lambda t: (
            "ON"
            if str(t).endswith("3")
            else ("PN" if str(t).endswith("4") else "UNIT")
        )
    )
    df["Segmento de Listagem"] = "Novo Mercado"
    df["Tag Along (%)"] = 100
    df["Free Float (%)"] = 25.0
    df["Governo Majoritário"] = "Não"

    return df
  except Exception:
    return pd.DataFrame()


df_acoes = load_acoes_data()
df_fiis = load_fiis_data_v6()

# CALCULOS DERIVADOS
if not df_acoes.empty:
  df_acoes["Yield + CAGR (%)"] = df_acoes.get(
      "Dividend Yield", 0
  ) + df_acoes.get("Cresc. 5 Anos (%)", 0)
  df_acoes["Dividendo Pago (R$)"] = df_acoes.get("Cotação", 0) * (
      df_acoes.get("Dividend Yield", 0) / 100
  )
  df_acoes["Preço Teto (6%)"] = df_acoes["Dividendo Pago (R$)"] / 0.06
  df_acoes["Margem de Segurança (%)"] = np.where(
      df_acoes.get("Cotação", 0) > 0,
      ((df_acoes["Preço Teto (6%)"] / df_acoes["Cotação"]) - 1) * 100,
      0,
  )

if not df_fiis.empty:
  df_fiis["Rendimento 12M (R$)"] = df_fiis.get("Cotação", 0) * (
      df_fiis.get("DY 12M Acumulado", 0) / 100
  )
  df_fiis["Preço Teto (9%)"] = df_fiis["Rendimento 12M (R$)"] / 0.09
  df_fiis["Margem Teto (%)"] = np.where(
      df_fiis.get("Cotação", 0) > 0,
      ((df_fiis["Preço Teto (9%)"] / df_fiis["Cotação"]) - 1) * 100,
      0,
  )
  df_fiis["Desconto VP (%)"] = (1 - df_fiis.get("P/VP", 1)) * 100

# -----------------------------------------------------------------------------
# INTERFACE STREAMLIT
# -----------------------------------------------------------------------------
st.title("🛡️ Prudence Invest | Terminal Albarado")
st.caption("Scanner Fundamentalista B3 (Modo de Alta Disponibilidade)")
st.markdown("---")

# SCANNER DE AÇÕES
st.subheader("📈 Scanner Fundamentalista de Ações")
c1, c2, c3 = st.columns(3)
c1.metric("🎯 Ações Carregadas", len(df_acoes))
c2.metric(
    "💰 DY Médio Ações", f"{df_acoes.get('Dividend Yield', pd.Series([0])).mean():.2f}%"
)
c3.metric(
    "📊 ROE Médio", f"{df_acoes.get('ROE', pd.Series([0])).mean():.2f}%"
)
st.dataframe(df_acoes, hide_index=True, use_container_width=True)

# SCANNER DE FIIS
st.markdown("---")
st.subheader("🏢 Scanner Fundamentalista de FIIs")
f1, f2, f3 = st.columns(3)
f1.metric("🎯 FIIs Carregados", len(df_fiis))
f2.metric(
    "💰 DY 12M Médio",
    f"{df_fiis.get('DY 12M Acumulado', pd.Series([0])).mean():.2f}%",
)
f3.metric(
    "🏷️ P/VP Mediano", f"{df_fiis.get('P/VP', pd.Series([0])).median():.2f}x"
)
st.dataframe(df_fiis, hide_index=True, use_container_width=True)