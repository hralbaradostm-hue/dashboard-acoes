import streamlit as st
import pandas as pd
import io
import yfinance as yf

@st.cache_data
def load_cofre_fiis():
    try:
        return pd.read_excel("cofre_fiis.xlsx")
    except:
        return pd.DataFrame()

df_cofre_fiis = load_cofre_fiis()

# Configuração da Página
st.set_page_config(page_title="Scanner Avançado de FIIs | Prudence Invest", layout="wide")

# --- DESIGN SYSTEM INSTITUCIONAL (SaaS) ---
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

@st.cache_data
def load_fiis_data():
    try:
        df = pd.read_excel("fiis_b3.xlsx")
    except Exception as e:
        st.error(f"Erro ao carregar 'fiis_b3.xlsx': {e}")
        return pd.DataFrame()
    
    # --- FILTRO BASE DE SEGURANÇA ---
    if "Patrimônio Líquido" in df.columns:
        df = df[df["Patrimônio Líquido"] > 0].copy()

    # --- DEFESA E CÁLCULOS MATEMÁTICOS ---
    if "DY 12M Acumulado" in df.columns and "Cotação" in df.columns:
        df["Rendimento 12M (R$)"] = df["Cotação"] * (df["DY 12M Acumulado"] / 100)
    else:
        df["Rendimento 12M (R$)"] = 0.0

    # Preço Teto baseado na meta de 9% a.a. em FIIs
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

    # Desconto sobre o Valor Patrimonial
    if "P/VP" in df.columns:
        df["Desconto VP (%)"] = (1 - df["P/VP"]) * 100
    else:
        df["Desconto VP (%)"] = 0.0

    return df

df_fiis = load_fiis_data()

if not df_fiis.empty:
    # Opções para Filtros Multiselect
    tipos_fundo = list(df_fiis["Tipo de fundo"].unique()) if "Tipo de fundo" in df_fiis.columns else []
    segmentos = sorted(list(df_fiis["Segmento de Atuação"].unique())) if "Segmento de Atuação" in df_fiis.columns else []
    gestoes = list(df_fiis["Tipo de Gestão"].unique()) if "Tipo de Gestão" in df_fiis.columns else []
    multi_inq_opts = list(df_fiis["Multi-inquilino"].unique()) if "Multi-inquilino" in df_fiis.columns else []
    admins = sorted(list(df_fiis["Administrador"].unique())) if "Administrador" in df_fiis.columns else []

    # --- FUNÇÃO RESET DE FILTROS ---
    def limpar_filtros_fiis():
        st.session_state.fii_tipo = tipos_fundo
        st.session_state.fii_seg = segmentos
        st.session_state.fii_gestao = gestoes
        st.session_state.fii_multi = multi_inq_opts
        st.session_state.fii_admin = admins
        st.session_state.fii_pvp = (0.0, 1.5)
        st.session_state.fii_dy = 0.0
        st.session_state.fii_vacancia = 100.0
        st.session_state.fii_cris = 0.0
        st.session_state.fii_imoveis = 0
        st.session_state.fii_tempo = 0
        st.session_state.fii_liq = 0.0
        st.session_state.fii_pat = 0.0

    if "fii_tipo" not in st.session_state:
        limpar_filtros_fiis()

    # --- BARRA LATERAL (FILTROS INSTITUCIONAIS) ---
    st.sidebar.header("🏢 Filtros Fundamentalistas de FIIs")
    st.sidebar.button("🔄 Limpar Filtros", on_click=limpar_filtros_fiis, use_container_width=True)
    st.sidebar.markdown("---")

    tipo_filtro = st.sidebar.multiselect("1. Tipo de Fundo", tipos_fundo, key="fii_tipo")
    seg_filtro = st.sidebar.multiselect("2. Segmento de Atuação", segmentos, key="fii_seg")
    gestao_filtro = st.sidebar.multiselect("3. Tipo de Gestão", gestoes, key="fii_gestao")
    multi_filtro = st.sidebar.multiselect("4. Multi-inquilino", multi_inq_opts, key="fii_multi")
    
    pvp_min, pvp_max = st.sidebar.slider("5. Faixa de P/VP", 0.0, 2.0, key="fii_pvp")
    dy_min = st.sidebar.slider("6. DY 12M Acumulado Mín. (%)", 0.0, 25.0, key="fii_dy")
    vac_max = st.sidebar.slider("7. Vacância Máxima (%)", 0.0, 100.0, key="fii_vacancia")
    cris_min = st.sidebar.slider("8. % Mínimo em CRIs (FII Papel)", 0.0, 100.0, key="fii_cris")
    imoveis_min = st.sidebar.number_input("9. Qtd. Mínima de Imóveis", min_value=0, step=1, key="fii_imoveis")
    tempo_min = st.sidebar.number_input("10. Tempo Mín. Listagem (Anos)", min_value=0, step=1, key="fii_tempo")
    
    liq_min = st.sidebar.number_input("11. Liquidez Diária Mín. (R$)", min_value=0.0, step=50000.0, key="fii_liq")
    pat_min = st.sidebar.number_input("12. Patrimônio Líq. Mín. (R$)", min_value=0.0, step=50000000.0, key="fii_pat")
    admin_filtro = st.sidebar.multiselect("13. Administrador", admins, key="fii_admin")

    # --- MOTOR DE FILTRAGEM ---
    condicoes = pd.Series(True, index=df_fiis.index)
    
    if "Tipo de fundo" in df_fiis.columns: condicoes &= df_fiis["Tipo de fundo"].isin(tipo_filtro)
    if "Segmento de Atuação" in df_fiis.columns: condicoes &= df_fiis["Segmento de Atuação"].isin(seg_filtro)
    if "Tipo de Gestão" in df_fiis.columns: condicoes &= df_fiis["Tipo de Gestão"].isin(gestao_filtro)
    if "Multi-inquilino" in df_fiis.columns: condicoes &= df_fiis["Multi-inquilino"].isin(multi_filtro)
    if "Administrador" in df_fiis.columns: condicoes &= df_fiis["Administrador"].isin(admin_filtro)
    
    if "P/VP" in df_fiis.columns: condicoes &= df_fiis["P/VP"].between(pvp_min, pvp_max)
    if "DY 12M Acumulado" in df_fiis.columns: condicoes &= df_fiis["DY 12M Acumulado"] >= dy_min
    if "Vacância" in df_fiis.columns: condicoes &= df_fiis["Vacância"] <= vac_max
    if "Para FII de Papel % em CRIs" in df_fiis.columns: condicoes &= df_fiis["Para FII de Papel % em CRIs"] >= cris_min
    if "Quantidade de Imóveis" in df_fiis.columns: condicoes &= df_fiis["Quantidade de Imóveis"] >= imoveis_min
    if "Tempo de listagem" in df_fiis.columns: condicoes &= df_fiis["Tempo de listagem"] >= tempo_min
    
    if "Liquidez diária" in df_fiis.columns: condicoes &= df_fiis["Liquidez diária"] >= liq_min
    if "Patrimônio Líquido" in df_fiis.columns: condicoes &= df_fiis["Patrimônio Líquido"] >= pat_min

    df_filtrado = df_fiis[condicoes]

    # Ordenação das colunas para exibição fluida
    colunas_desejadas = [
        "Ticker", "Tipo de fundo", "Segmento de Atuação", "Cotação", "P/VP", "Desconto VP (%)",
        "DY 12M Acumulado", "Rendimento 12M (R$)", "Preço Teto (9%)", "Margem Teto (%)",
        "Vacância", "Quantidade de Imóveis", "Multi-inquilino", "Para FII de Papel % em CRIs",
        "Liquidez diária", "Patrimônio Líquido", "Tempo de listagem", "Tipo de Gestão",
        "Administrador", "Taxa de adm", "Taxa de Performance", "Benchmark"
    ]

    colunas_finais = [c for c in colunas_desejadas if c in df_filtrado.columns]
    df_filtrado = df_filtrado[colunas_finais]

    # --- FUNÇÃO EXPORTAÇÃO EXCEL ---
    def converter_excel_fiis(df_export):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name='FIIs_Terminal_Albarado')
        return buffer.getvalue()

    # --- INTERFACE PRINCIPAL ---
    st.title("🏢 Terminal Albarado | Scanner de FIIs")
    st.markdown("---")

    total_aprovados = len(df_filtrado)
    media_dy = df_filtrado["DY 12M Acumulado"].mean() if (total_aprovados > 0 and "DY 12M Acumulado" in df_filtrado.columns) else 0
    mediana_pvp = df_filtrado["P/VP"].median() if (total_aprovados > 0 and "P/VP" in df_filtrado.columns) else 0
    vacancia_media = df_filtrado["Vacância"].mean() if (total_aprovados > 0 and "Vacância" in df_filtrado.columns) else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">🎯 FIIs Aprovados</div>
                <div class="metric-value">{total_aprovados}</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">💰 DY 12M Médio</div>
                <div class="metric-value">{media_dy:.2f}%</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">🏷️ P/VP Mediano</div>
                <div class="metric-value">{mediana_pvp:.2f}x</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">🏗️ Vacância Média</div>
                <div class="metric-value">{vacancia_media:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if total_aprovados > 0:
        col_vazio, col_btn = st.columns([4, 1])
        with col_btn:
            dados_excel = converter_excel_fiis(df_filtrado)
            st.download_button(
                label="📥 Baixar em Excel",
                data=dados_excel,
                file_name="FIIs_Albarado_Selecao.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # DATAFRAME COM CONFIGURAÇÃO DE TIPOS DE COLUNAS
    st.dataframe(
        df_filtrado,
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

    # --- RAIO-X HISTÓRICO DE DIVIDENDOS DO FII ---
    st.markdown("---")
    st.title("📊 Raio-X de Rendimentos Mensais")

    if total_aprovados > 0 and "Ticker" in df_filtrado.columns:
        fii_selecionado = st.selectbox("Selecione o FII para histórico de proventos ao vivo:", df_filtrado["Ticker"].tolist())

        if fii_selecionado:
            try:
                ticker_yf = yf.Ticker(f"{fii_selecionado}.SA")
                hist_div = ticker_yf.dividends

                if not hist_div.empty:
                    div_mensal = hist_div.resample('ME').sum()
                    df_grafico = pd.DataFrame({"Rendimento Mensal (R$)": div_mensal})
                    df_grafico.index = df_grafico.index.strftime('%Y-%m')
                    
                    st.bar_chart(df_grafico, use_container_width=True)
                else:
                    st.warning(f"Sem histórico de dividendos disponível via Yahoo Finance para {fii_selecionado}.")
            except Exception:
                st.warning(f"Não foi possível buscar dados ao vivo para {fii_selecionado}.")
else:
    st.warning("Insira o arquivo 'fiis_b3.xlsx' no diretório do projeto para carregar os dados dos fundos.")