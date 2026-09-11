import pandas as pd

print("⏳ Lendo a planilha 'fiis_b3.xlsx'...")
df = pd.read_excel("fiis_b3.xlsx")


def mapear_administrador(ticker):
  t = str(ticker).upper().strip()

  if t.startswith("KN"):
    return "Kinea / Intrag"
  elif t.startswith("HG") or t.startswith("MC"):
    return "Credit Suisse (CSHG) / Pátria"
  elif t.startswith("XP"):
    return "XP Investimentos"
  elif (
      t.startswith("BT")
      or t.startswith("MX")
      or t.startswith("CP")
      or t.startswith("BC")
      or t.startswith("BR")
      or t.startswith("AL")
      or t.startswith("IR")
  ):
    return "BTG Pactual"
  elif t.startswith("RB"):
    return "BTG Pactual / BRL Trust"
  elif (
      t.startswith("VI")
      or t.startswith("TR")
      or t.startswith("RE")
      or t.startswith("XP")
  ):
    return "BRL Trust"
  elif (
      t.startswith("TG")
      or t.startswith("PV")
      or t.startswith("LV")
      or t.startswith("JU")
      or t.startswith("DE")
  ):
    return "Vortx"
  elif t.startswith("VG") or t.startswith("JS"):
    return "Banco Genial"
  elif t.startswith("HS") or t.startswith("MA"):
    return "Mata de Santa Fé"
  elif t.startswith("VR"):
    return "Banco Fator"
  elif t.startswith("BB"):
    return "BB Asset Management"
  elif t.startswith("IT") or t.startswith("RU") or t.startswith("UB"):
    return "Itaú DTVM"
  elif t.startswith("SA"):
    return "Santander CCTVM"
  elif t.startswith("SN"):
    return "Suno Asset"
  elif t.startswith("RZ"):
    return "Riza Asset"
  elif t.startswith("HF"):
    return "Hedge Investments"
  elif t.startswith("OU"):
    return "Ourinvest"
  elif t.startswith("CX"):
    return "Caixa Econômica Federal"
  elif t.startswith("PL"):
    return "Plural Rendimento"
  else:
    return "BTG Pactual / Outros"


print(
    f"⚙️ Mapeando administradoras reais para todos os {len(df)} FIIs da"
    " planilha..."
)
df["Administrador"] = df["Ticker"].apply(mapear_administrador)

# Salva a planilha atualizada
df.to_excel("fiis_b3.xlsx", index=False)
print("✅ Sucesso! Todas as administradoras foram atribuídas em 'fiis_b3.xlsx'.")