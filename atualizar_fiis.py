import io
import pandas as pd
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}


def atualizar():
  url = "https://www.fundamentus.com.br/fii_resultado.php"
  res = requests.get(url, headers=HEADERS, timeout=15)
  res.encoding = "latin-1"

  tables = pd.read_html(io.StringIO(res.text), decimal=",", thousands=".")
  df = tables[0]

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
  df = df.rename(columns=col_map)

  df.to_csv("fiis_b3.csv", index=False, encoding="utf-8-sig")
  df.to_excel("fiis_b3.xlsx", index=False)
  print("✅ fiis_b3.csv e fiis_b3.xlsx atualizados com sucesso!")


if __name__ == "__main__":
  atualizar()