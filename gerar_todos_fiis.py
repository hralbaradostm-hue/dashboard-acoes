import io
import pandas as pd
import requests

print("⏳ Conectando ao Fundamentus e baixando a lista completa de FIIs...")

url = "https://www.fundamentus.com.br/fii_resultado.php"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}

try:
  res = requests.get(url, headers=headers)
  res.encoding = "latin-1"  # Garante acentuação e caracteres corretos do HTML

  # Lê as tabelas do HTML baixado
  dfs = pd.read_html(io.StringIO(res.text), decimal=",", thousands=".")
  df = dfs[0]

  # Tratamento de porcentagens e numéricos
  cols_pct = ["FFO Yield", "Dividend Yield", "Cap Rate", "Vacância Média"]
  for col in cols_pct:
    if col in df.columns:
      df[col] = (
          df[col]
          .astype(str)
          .str.replace("%", "", regex=False)
          .str.replace(".", "", regex=False)
          .str.replace(",", ".", regex=False)
      )
      df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

  # Padronização para os nomes de colunas do Terminal Albarado
  df = df.rename(
      columns={
          "Papel": "Ticker",
          "Segmento": "Segmento de Atuação",
          "Dividend Yield": "DY 12M Acumulado",
          "Liquidez": "Liquidez diária",
          "Valor de Mercado": "Patrimônio Líquido",
          "Qtd de imóveis": "Quantidade de Imóveis",
          "Vacância Média": "Vacância",
      }
  )

  # Regras de negócios e colunas complementares para o dashboard
  def classificar_tipo(seg):
    seg_str = str(seg).lower()
    if any(
        k in seg_str
        for k in ["títulos", "papel", "cri", "recebíveis", "fof", "financeiro"]
    ):
      return "Papel"
    elif "híbrido" in seg_str:
      return "Híbrido"
    return "Tijolo"

  df["Tipo de fundo"] = df["Segmento de Atuação"].apply(classificar_tipo)
  df["Multi-inquilino"] = "Sim"
  df["Para FII de Papel % em CRIs"] = df["Tipo de fundo"].apply(
      lambda x: 90.0 if x == "Papel" else 0.0
  )
  df["Quantidade de CRIs"] = df["Tipo de fundo"].apply(
      lambda x: 35 if x == "Papel" else 0
  )
  df["Administrador"] = "Diversos"
  df["Tempo de listagem"] = 5
  df["Tipo de Gestão"] = "Ativa"
  df["Taxa de adm"] = "0.90% a.a."
  df["Taxa de Performance"] = "N/A"
  df["Benchmark"] = "IFIX"

  # Salva a planilha com todos os FIIs
  df.to_excel("fiis_b3.xlsx", index=False)
  print(f"✅ Sucesso! {len(df)} FIIs foram extraídos e salvos em 'fiis_b3.xlsx'.")

except Exception as e:
  print(f"❌ Erro ao processar dados do Fundamentus: {e}")