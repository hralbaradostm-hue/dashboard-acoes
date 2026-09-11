from datetime import datetime
import io
import pandas as pd
import requests

print(
    "⏳ Buscando datas oficiais de registro na CVM para calcular o tempo real de"
    " listagem..."
)

url_cvm = "http://dados.cvm.gov.br/dados/FII/CAD/DADOS/cad_fii.csv"

try:
  response = requests.get(url_cvm, timeout=20)
  response.encoding = "latin-1"
  df_cvm = pd.read_csv(io.StringIO(response.text), sep=";", dtype=str)

  # Localiza as colunas de Ticker e Data de Registro CVM
  col_ticker = next(
      (
          c
          for c in df_cvm.columns
          if "NEGOC" in c.upper() or "TICKER" in c.upper()
      ),
      None,
  )
  col_dt_reg = next(
      (c for c in df_cvm.columns if "DT_REG_CVM" in c.upper()), None
  )

  if not col_ticker or not col_dt_reg:
    print("⚠️ Não foi possível localizar as colunas de data/ticker no CSV.")
  else:
    df_cvm_clean = df_cvm[[col_ticker, col_dt_reg]].dropna()
    df_cvm_clean[col_ticker] = df_cvm_clean[col_ticker].str.strip().str.upper()

    ano_atual = datetime.now().year
    mapa_tempo_real = {}

    for _, row in df_cvm_clean.iterrows():
      ticker = row[col_ticker]
      dt_str = str(row[col_dt_reg]).strip()
      try:
        dt = pd.to_datetime(dt_str, errors="coerce")
        if pd.notnull(dt):
          # Calcula a idade do fundo em anos completos
          anos = max(1, ano_atual - dt.year)
          mapa_tempo_real[ticker] = anos
      except Exception:
        pass

    print("⏳ Carregando 'fiis_b3.xlsx' local...")
    df_local = pd.read_excel("fiis_b3.xlsx")

    def atribuir_tempo_real(row):
      ticker = str(row.get("Ticker", "")).strip().upper()
      # Retorna o tempo real da CVM ou mantém o valor existente se não houver no cadastro CVM
      return mapa_tempo_real.get(ticker, row.get("Tempo de listagem", 5))

    df_local["Tempo de listagem"] = df_local.apply(atribuir_tempo_real, axis=1)

    df_local.to_excel("fiis_b3.xlsx", index=False)
    print(
        "✅ Sucesso! Tempo de listagem real (via CVM) atualizado para todos os"
        " FIIs em 'fiis_b3.xlsx'."
    )

except Exception as e:
  print(f"❌ Erro ao conectar com a CVM: {e}")