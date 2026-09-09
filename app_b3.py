import streamlit as st
import pandas as pd
import yfinance as yf

# ==========================================
# CONFIGURAÇÃO INICIAL
# ==========================================
st.set_page_config(page_title="Prudence Invest", page_icon="🦅", layout="wide")

@st.cache_data
def load_base():
    try:
        return pd.read_excel("acoes_b3.xlsx")
    except:
        return pd.DataFrame()

@st.cache_data
def load_cofre():
    try:
        return pd.read_excel("cofre_lucros.xlsx")
    except:
        return pd.DataFrame()

df_base = load_base()
df_cofre = load_cofre()

# ==========================================
# CABEÇALHO
# ==========================================
st.title("🦅 Prudence Invest")
st.markdown("### Scanner Institucional de Dividendos e Valor")
st.markdown("---")

if df_base.empty:
    st.warning("⚠️ Base de dados 'acoes_b3.xlsx' não encontrada. Execute o seu robô extrator primeiro.")
else:
    # ==========================================
    # BARRA LATERAL: FILTROS (MÉTODO BARSI)
    # ==========================================
    st.sidebar.header("Filtros de Qualidade")
    
    busca_ticker = st.sidebar.text_input("Buscar Ticker Específico (ex: BBAS3):").upper()
    
    df_filtrado = df_base.copy()
    
    if busca_ticker:
        df_filtrado = df_filtrado[df_filtrado["Ticker"].str.contains(busca_ticker, na=False)]
    
    if "P/VP" in df_filtrado.columns:
        pvp_max = st.sidebar.slider("P/VP Máximo", 0.0, 5.0, 1.5, 0.1)
        df_filtrado = df_filtrado[df_filtrado["P/VP"] <= pvp_max]
        
    if "Dividend Yield" in df_filtrado.columns:
        dy_min = st.sidebar.slider("Dividend Yield Mínimo (%)", 0.0, 20.0, 6.0, 0.5)
        # Ajuste inteligente: se o excel salvou 0.06 em vez de 6.0
        if df_filtrado["Dividend Yield"].max() < 2.0:
            df_filtrado = df_filtrado[df_filtrado["Dividend Yield"] >= (dy_min / 100)]
        else:
            df_filtrado = df_filtrado[df_filtrado["Dividend Yield"] >= dy_min]
            
    if "Liquidez Diária" in df_filtrado.columns:
        liq_min = st.sidebar.number_input("Liquidez Mínima (R$)", value=50000, step=10000)
        df_filtrado = df_filtrado[df_filtrado["Liquidez Diária"] >= liq_min]

    # ==========================================
    # TELA PRINCIPAL: RESULTADO DO SCANNER
    # ==========================================
    st.markdown(f"**Ações Aprovadas no Filtro:** {len(df_filtrado)}")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    
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
                try:
                    ticker_yf = yf.Ticker(f"{acao_selecionada}.SA")
                    
                    # Divide a tela em duas colunas para os gráficos (Indentação corrigida)
                    col1, col2 = st.columns(2)
                    
                    # --- GRÁFICO 1: LUCRO LÍQUIDO (DO COFRE EXCEL) ---
                    with col1:
                        st.markdown(f"**💰 Evolução do Lucro Líquido (Cofre Local)**")
                        if not df_cofre.empty and acao_selecionada in df_cofre["Ticker"].values:
                            df_lucro_acao = df_cofre[df_cofre["Ticker"] == acao_selecionada].copy()
                            
                            df_lucro_acao.set_index("Ano", inplace=True)
                            df_grafico_lucro = pd.DataFrame({"Lucro Líquido (R$)": df_lucro_acao["Lucro Líquido"]})
                            df_grafico_lucro.index = df_grafico_lucro.index.astype(str)
                            
                            st.line_chart(df_grafico_lucro, use_container_width=True)
                        else:
                            st.warning("Lucro Líquido não encontrado no Cofre de Dados.")

                    # --- GRÁFICO 2: DIVIDENDOS HISTÓRICOS MÁXIMOS (Linha) ---
                    with col2:
                        st.markdown(f"**💸 Histórico Máximo de Dividendos**")
                        historico_div = ticker_yf.dividends
                        
                        if not historico_div.empty:
                            div_anual = historico_div.groupby(historico_div.index.year).sum()
                            df_div = pd.DataFrame({"Dividendos Pagos (R$)": div_anual})
                            df_div.index = df_div.index.astype(str)
                            
                            st.line_chart(df_div, use_container_width=True)
                        else:
                            st.warning("Nenhum histórico de dividendos encontrado para este ativo.")
                            
                except Exception as e:
                    st.error("Erro ao processar os dados históricos.")