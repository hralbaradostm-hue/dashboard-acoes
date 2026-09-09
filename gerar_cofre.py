import pandas as pd
import yfinance as yf

print("Iniciando a extração do Cofre de Lucros (Via API Oficial Yahoo Finance)...")

# 1. Lê os ativos do seu filtro
try:
    df_acoes = pd.read_excel("acoes_b3.xlsx")
    if "Liquidez Diária" in df_acoes.columns:
        df_acoes = df_acoes[df_acoes["Liquidez Diária"] > 50000]
    tickers = df_acoes["Ticker"].unique().tolist()
except Exception as e:
    print("Erro ao ler acoes_b3.xlsx. Arquivo não encontrado.")
    exit()

dados_historicos = []
print(f"Total de ativos para extrair via API: {len(tickers)}\n")

# 2. Puxa os dados livremente da API oficial
for ticker in tickers:
    print(f"Buscando {ticker}...", end=" ")
    try:
        acao_yf = yf.Ticker(f"{ticker}.SA")
        dre = acao_yf.financials
        
        # Valida se a empresa tem histórico de lucros
        if not dre.empty and "Net Income" in dre.T.columns:
            dre_t = dre.T.sort_index()
            
            df_lucro = pd.DataFrame({"Lucro Líquido": dre_t["Net Income"]})
            df_lucro.index = df_lucro.index.year
            df_lucro.reset_index(inplace=True)
            df_lucro.rename(columns={"index": "Ano"}, inplace=True)
            df_lucro['Ticker'] = ticker
            
            dados_historicos.append(df_lucro)
            print("✅ OK")
        else:
            print("❌ Sem dados na API")
            
    except Exception as e:
        print("⚠️ Erro de conexão com a API")

# 3. Salva no seu Cofre de Dados blindado
if dados_historicos:
    df_cofre = pd.concat(dados_historicos, ignore_index=True)
    df_cofre = df_cofre.drop_duplicates(subset=["Ano", "Ticker"])
    df_cofre.to_excel("cofre_lucros.xlsx", index=False)
    print("\n🚀 SUCESSO! 'cofre_lucros.xlsx' criado e blindado para o Dashboard.")
else:
    print("\n❌ Nenhum dado extraído.")