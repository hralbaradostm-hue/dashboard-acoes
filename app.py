import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📊 Dashboard de Ações - Ranking + Busca")

# =========================
# 🔍 BUSCA (ALINHAMENTO PERFEITO)
# =========================
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] {
    align-items: center;
}
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([6,1])

with col1:
    ticker_input = st.text_input(
        "Buscar ação",
        placeholder="Digite o ticker (ex: PETR4, VALE3, ITUB3)",
        label_visibility="collapsed"
    )

with col2:
    buscar_btn = st.button("🔎 Pesquisar", use_container_width=True)


# =========================
# 🔍 FUNÇÃO BUSCA
# =========================
@st.cache_data
def buscar_acao(ticker):
    try:
        t = yf.Ticker(f"{ticker.upper()}.SA")
        info = t.info

        df = pd.DataFrame([{
            "Ticker": ticker.upper(),
            "Preço": info.get("currentPrice"),
            "P/L": info.get("trailingPE"),
            "P/VP": info.get("priceToBook"),
            "ROE": info.get("returnOnEquity"),
            "DY": info.get("dividendYield"),
            "Dívida": info.get("debtToEquity"),
            "Margem": info.get("profitMargins"),
        }])

        for col in ["ROE","DY","Margem","Dívida","P/L"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.fillna(0)

        df["ROE"] *= 100
        df["DY"] *= 100
        df["Margem"] *= 100

        return df

    except Exception as e:
        st.error(f"Erro: {e}")
        return None


# =========================
# 🌐 UNIVERSO DE AÇÕES
# =========================
acoes = [
"PETR4.SA","VALE3.SA","ITUB3.SA","BBDC3.SA","BBAS3.SA","WEGE3.SA","B3SA3.SA",
"ABEV3.SA","RENT3.SA","LREN3.SA","MGLU3.SA","RADL3.SA","RAIL3.SA","SUZB3.SA",
"EGIE3.SA","TAEE3.SA","CMIG3.SA","CPLE3.SA","ENEV3.SA","EQTL3.SA","SBSP3.SA",
"JBSS3.SA","BRFS3.SA","MRFG3.SA","PRIO3.SA","PETR3.SA",
"CYRE3.SA","CURY3.SA","DIRR3.SA","EZTC3.SA","TEND3.SA","MRVE3.SA",
"HAPV3.SA","FLRY3.SA","ODPV3.SA","QUAL3.SA","TOTS3.SA","POSI3.SA",
"USIM3.SA","CSNA3.SA","GGBR3.SA","GOAU3.SA","KLBN3.SA",
"ARZZ3.SA","SOMA3.SA","ASAI3.SA","PETZ3.SA"
]


# =========================
# 📊 CARREGAR DADOS
# =========================
@st.cache_data
def carregar_dados():
    dados = []

    for ticker in acoes:
        try:
            info = yf.Ticker(ticker).info

            dados.append({
                "Ticker": ticker.replace(".SA",""),
                "Preço": info.get("currentPrice"),
                "P/L": info.get("trailingPE"),
                "P/VP": info.get("priceToBook"),
                "ROE": info.get("returnOnEquity"),
                "DY": info.get("dividendYield"),
                "Dívida": info.get("debtToEquity"),
                "Margem": info.get("profitMargins"),
            })

        except:
            continue

    df = pd.DataFrame(dados)

    if df.empty:
        return df

    for col in ["ROE","DY","Margem","Dívida","P/L"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["ROE","P/L"])
    df = df.fillna(0)

    df["ROE"] *= 100
    df["DY"] *= 100
    df["Margem"] *= 100

    df["Score"] = (
        df["ROE"] * 2.5 +
        df["DY"] * 2 +
        df["Margem"] * 1.5 -
        df["Dívida"] * 0.8 -
        df["P/L"] * 0.6
    )

    return df.sort_values(by="Score", ascending=False)


df = carregar_dados()


# =========================
# 🔎 EXECUTA BUSCA
# =========================
if buscar_btn and ticker_input:
    resultado = buscar_acao(ticker_input)

    if resultado is not None:
        st.subheader(f"📊 Análise: {ticker_input.upper()}")
        st.dataframe(resultado)

        hist = yf.Ticker(f"{ticker_input}.SA").history(period="1y")

        if not hist.empty:
            st.line_chart(hist["Close"])


st.divider()


# =========================
# 🏆 TOP 30 AUTOMÁTICO
# =========================
if not df.empty:
    top30 = df.head(30)

    col1, col2, col3 = st.columns(3)
    col1.metric("🏆 Melhor Ação", df.iloc[0]["Ticker"])
    col2.metric("📈 Score Máximo", round(df["Score"].max(),2))
    col3.metric("📊 Ativos Analisados", len(df))

    st.subheader("🥇 TOP 30 Ações por Fundamentos")
    st.dataframe(top30)

    # 📊 GRÁFICO BARRAS (TRAVADO)
    fig = px.bar(top30, x="Ticker", y="Score")

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"staticPlot": True, "displayModeBar": False}
    )

    # 🧺 CARTEIRA
    top30["Peso"] = top30["Score"] / top30["Score"].sum()

    fig2 = px.pie(top30, values="Peso", names="Ticker")

    st.plotly_chart(
        fig2,
        use_container_width=True,
        config={"staticPlot": True, "displayModeBar": False}
    )

    # 🎯 SINAIS
    def sinal(row):
        if row["ROE"] > 15 and row["DY"] > 4 and row["Dívida"] < 100:
            return "🟢 FORTE COMPRA"
        elif row["ROE"] > 10:
            return "🟡 MANTER"
        else:
            return "🔴 EVITAR"

    top30["Sinal"] = top30.apply(sinal, axis=1)

    st.subheader("🎯 Sinais do TOP 30")
    st.dataframe(top30[["Ticker","Score","Sinal"]])
