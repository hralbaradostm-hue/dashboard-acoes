import streamlit as st
import pandas as pd
import io
import yfinance as yf  # <-- ADICIONE ESTA LINHA

# Configuração da Página
st.set_page_config(page_title="Scanner Fundamentalista B3 | Prudence Invest", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_excel("acoes_b3.xlsx")
    
    # 1. CRIA O INDICADOR CHOWDER RULE
    df["Yield + CAGR (%)"] = df["Dividend Yield"] + df["Cresc. 5 Anos (%)"]
    
    # 2. CALCULA O DIVIDENDO EM REAIS (R$)
    # Pega a Cotação (R$) e multiplica pelo Dividend Yield (transformado em decimal)
    df["Dividendo Pago (R$)"] = df["Cotação"] * (df["Dividend Yield"] / 100)
    
    # 3. CÁLCULO DO PREÇO TETO DE 6% (Método Barsi/Bazin)
    df["Preço Teto (6%)"] = df["Dividendo Pago (R$)"] / 0.06
    
    # 4. CÁLCULO DA MARGEM DE SEGURANÇA (%)
    # Evita divisão por zero caso a cotação seja 0 (improvável)
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
    st.session_state.margem_seg_min = -100.0 # Novo filtro

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
# 19. Filtro de Margem de Segurança
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
    (df["Margem de Segurança (%)"] >= margem_seg_min) # Novo filtro aplicado
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
st.title("🛡️ Prudence Invest | Scanner Institucional")

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"**Empresas Aprovadas:** `{len(df_filtrado)}` ativos na seleção atual.")
with col2:
    if len(df_filtrado) > 0:
        dados_excel = converter_para_excel(df_filtrado)
        st.download_button(
            label="📥 Baixar em Excel",
            data=dados_excel,
            file_name="Prudence_Invest_Selecao.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# Tabela com as Novas Colunas em Destaque
st.dataframe(
    df_filtrado,
    column_config={
        "Cotação": st.column_config.NumberColumn(format="R$ %.2f"),
        "Preço Teto (6%)": st.column_config.NumberColumn(format="R$ %.2f"), # NOVA
        "Dividendo Pago (R$)": st.column_config.NumberColumn(format="R$ %.2f"), # NOVA
        "Margem de Segurança (%)": st.column_config.NumberColumn(format="%.2f %%"), # NOVA
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
    use_container_width=True,
    hide_index=True
)

# ==========================================
# NOVA SEÇÃO: RAIO-X HISTÓRICO (DRE)
# ==========================================
st.markdown("---")
st.title("📊 Raio-X Histórico (DRE)")
st.markdown("Selecione uma das empresas aprovadas no seu filtro para analisar a evolução financeira (Estilo Status Invest).")

if len(df_filtrado) > 0:
    # Cria um menu dropdown com os tickers aprovados
    acao_selecionada = st.selectbox("Escolha a Ação para gerar o gráfico:", df_filtrado["Ticker"].tolist())

    if acao_selecionada:
        with st.spinner(f"Buscando histórico de {acao_selecionada} no Yahoo Finance..."):
            try:
                # Conecta na API (adiciona .SA para ações brasileiras)
                ticker_yf = yf.Ticker(f"{acao_selecionada}.SA")
                
                # Puxa a DRE (Financials)
                dre = ticker_yf.financials
                
                if not dre.empty:
                    # Inverte a tabela para que as datas fiquem em ordem cronológica (do mais antigo pro atual)
                    dre_t = dre.T.sort_index()
                    
                    # Prepara os dados para o gráfico
                    colunas_grafico = {}
                    if "Total Revenue" in dre_t.columns:
                        colunas_grafico["Receita Total"] = dre_t["Total Revenue"]
                    if "Net Income" in dre_t.columns:
                        colunas_grafico["Lucro Líquido"] = dre_t["Net Income"]
                    
                    if colunas_grafico:
                        df_grafico = pd.DataFrame(colunas_grafico)
                        # Formata o eixo X para mostrar apenas o Ano
                        df_grafico.index = df_grafico.index.year
                        
                        # Plota o gráfico de linha nativo do Streamlit
                        st.line_chart(df_grafico, use_container_width=True)
                        st.caption("Fonte: Yahoo Finance API (Últimos 4 anos reportados)")
                    else:
                        st.warning("Receita e Lucro não disponíveis na API gratuita para este ativo.")
                else:
                    st.warning("Demonstrativo de Resultados histórico não encontrado.")
            except Exception as e:
                st.error("Erro de conexão com a API de dados históricos.")