import numpy as np
import pandas as pd

print("⏳ Lendo a planilha 'fiis_b3.xlsx'...")
df = pd.read_excel("fiis_b3.xlsx")


def gerar_dados_qualitativos(row):
  ticker = str(row.get("Ticker", "")).upper().strip()
  tipo = str(row.get("Tipo de fundo", "")).lower()
  seg = str(row.get("Segmento de Atuação", "")).lower()

  # Usa o hash do Ticker como semente determinística (mantém a mesma consistência)
  seed = sum(ord(c) for c in ticker)
  np.random.seed(seed)

  # 1. Tempo de listagem realista (entre 1 e 14 anos)
  tempo = int(
      np.random.choice(
          [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14],
          p=[0.1, 0.1, 0.15, 0.15, 0.15, 0.1, 0.08, 0.07, 0.05, 0.03, 0.02],
      )
  )

  # 2. Taxas e Benchmarks diversificados por tipo de fundo
  if "papel" in tipo or "títulos" in seg or "cri" in seg:
    benchmarks = ["CDI + 1.0%", "IPCA + 6.0%", "CDI", "IFIX"]
    perf_options = [
        "20% exc. CDI",
        "20% exc. IPCA + 6%",
        "Isento",
        "10% exc. CDI",
    ]
    taxa_adm = np.random.choice(
        ["0.80% a.a.", "0.90% a.a.", "1.00% a.a.", "1.10% a.a."]
    )
  elif "tijolo" in tipo or "logística" in seg or "shoppings" in seg:
    benchmarks = ["IFIX", "IPCA", "CDI"]
    perf_options = [
        "Isento",
        "20% exc. IFIX",
        "10% exc. IFIX",
        "Isento",
    ]
    taxa_adm = np.random.choice(
        ["0.75% a.a.", "0.85% a.a.", "0.95% a.a.", "1.00% a.a."]
    )
  else:  # FoFs e Híbridos
    benchmarks = ["IFIX", "CDI"]
    perf_options = ["20% exc. IFIX", "20% exc. CDI", "Isento"]
    taxa_adm = np.random.choice(["0.90% a.a.", "1.00% a.a.", "1.20% a.a."])

  benchmark = np.random.choice(benchmarks)
  perf = np.random.choice(perf_options)

  return pd.Series([tempo, taxa_adm, perf, benchmark])


print(
    f"⚙️ Gerando taxas e tempos de listagem diversificados para {len(df)}"
    " FIIs..."
)
df[["Tempo de listagem", "Taxa de adm", "Taxa de Performance", "Benchmark"]] = (
    df.apply(gerar_dados_qualitativos, axis=1)
)

# Limpeza e substituição de qualquer valor 'None' por 'Isento'
df["Taxa de Performance"] = (
    df["Taxa de Performance"]
    .fillna("Isento")
    .replace({"None": "Isento", "N/A": "Isento", "nan": "Isento", "": "Isento"})
)

df.to_excel("fiis_b3.xlsx", index=False)
print(
    "✅ Concluído! Planilha 'fiis_b3.xlsx' atualizada com taxas e benchmarks"
    " diversificados."
)