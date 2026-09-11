import io
import pandas as pd
import requests

print("⏳ Baixando base de dados oficiais de FIIs diretamente da CVM...")

url_cvm = "http://dados.cvm.gov.br/dados/FII/CAD/DADOS/cad_fii.csv"

try:
  # 1. Download do arquivo cadastral oficial da CVM
  response = requests.get(url_cvm, timeout=20)
  response.encoding = "latin-1"

  df_cvm = pd.read_csv(io.StringIO(response.text), sep=";", dtype=str)

  # Tratamento de colunas do cadastro CVM
  # A CVM utiliza 'CD_NEGOC' ou 'TICKER' para os códigos negociados na B3
  col_ticker = next(
      (c for c in df_cvm.columns if "NEGOC" in c.upper() or "TICKER" in c.upper()),
      None,
  )
  col_admin = next(
      (c for c in df_cvm.columns if "ADMIN" in c.upper() and "CNPJ" not in c.upper()),
      None,
  )
  col_cnpj_fund = next(
      (c for c in df_cvm.columns if "CNPJ" in c.upper() and "FUNDO" in c.upper()),
      "CNPJ_Fundo",
  )

  if not col_ticker or not col_admin:
    print(
        "⚠️ Colunas de Ticker ou Administrador não localizadas diretamente no CSV"
        " da CVM."
    )
  else:
    # Filtra e limpa registros válidos
    df_cvm_clean = df_cvm[[col_ticker, col_admin]].dropna()
    df_cvm_clean[col_ticker] = df_cvm_clean[col_ticker].str.strip().str.upper()

    # Dicionário de mapeamento Ticker -> Administrador Oficial CVM
    mapa_admin_cvm = dict(
        zip(df_cvm_clean[col_ticker], df_cvm_clean[col_admin])
    )

    # 2. Carrega a planilha local
    print("⏳ Carregando 'fiis_b3.xlsx' local...")
    df_local = pd.read_excel("fiis_b3.xlsx")

    # 3. Atualiza os administradores com os dados da CVM
    def buscar_admin_oficial(row):
      ticker = str(row.get("Ticker", "")).strip().upper()
      return mapa_admin_cvm.get(ticker, row.get("Administrador", "Diversos"))

    df_local["Administrador"] = df_local.apply(buscar_admin_oficial, axis=1)

    # Salva a planilha atualizada
    df_local.to_excel("fiis_b3.xlsx", index=False)
    print(
        "✅ Sucesso! Administradores oficiais da CVM integrados em"
        " 'fiis_b3.xlsx'."
    )

except Exception as e:
  print(f"❌ Erro ao conectar à CVM: {e}")