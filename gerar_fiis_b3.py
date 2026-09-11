import pandas as pd

# Dados estruturados dos principais FIIs da B3
dados_fiis = {
    "Ticker": ["HGLG11", "KNCR11", "MXRF11", "XPML11", "BTLG11", "VISC11", "TRXF11", "ALZR11", "CPTS11", "KNSC11"],
    "Tipo de fundo": ["Tijolo", "Papel", "Papel", "Tijolo", "Tijolo", "Tijolo", "Tijolo", "Tijolo", "Papel", "Papel"],
    "Segmento de Atuação": ["Logística", "Títulos e Val. Mob.", "Títulos e Val. Mob.", "Shoppings", "Logística", "Shoppings", "Híbrido", "Híbrido", "Títulos e Val. Mob.", "Títulos e Val. Mob."],
    "Cotação": [161.50, 102.30, 10.45, 112.80, 101.20, 120.50, 108.90, 116.40, 8.55, 91.20],
    "P/VP": [0.98, 1.01, 1.03, 0.97, 0.99, 0.96, 1.02, 1.04, 0.91, 0.98],
    "DY 12M Acumulado": [9.35, 12.40, 13.10, 9.75, 10.15, 9.60, 10.50, 9.80, 12.85, 12.20],
    "Liquidez diária": [4500000.0, 9200000.0, 12500000.0, 3800000.0, 5200000.0, 3100000.0, 2600000.0, 2100000.0, 6400000.0, 4100000.0],
    "Patrimônio Líquido": [3600000000.0, 5800000000.0, 3300000000.0, 3700000000.0, 3100000000.0, 2500000000.0, 1500000000.0, 1100000000.0, 2800000000.0, 1200000000.0],
    "Quantidade de Imóveis": [25, 0, 0, 22, 18, 20, 50, 15, 0, 0],
    "Multi-inquilino": ["Sim", "Não", "Não", "Sim", "Sim", "Sim", "Sim", "Sim", "Não", "Não"],
    "Vacância": [4.5, 0.0, 0.0, 5.2, 2.1, 4.0, 1.0, 0.0, 0.0, 0.0],
    "Para FII de Papel % em CRIs": [0.0, 95.0, 85.0, 0.0, 0.0, 0.0, 0.0, 0.0, 91.0, 93.5],
    "Administrador": ["Credit Suisse", "Kinea", "BTG Pactual", "BTG Pactual", "BTG Pactual", "BRL Trust", "BRL Trust", "BTG Pactual", "BTG Pactual", "Kinea"],
    "Tempo de listagem": [14, 12, 10, 6, 8, 10, 5, 6, 5, 4],
    "Tipo de Gestão": ["Ativa", "Ativa", "Ativa", "Ativa", "Ativa", "Ativa", "Ativa", "Ativa", "Ativa", "Ativa"],
    "Taxa de adm": ["0.60% a.a.", "1.00% a.a.", "0.90% a.a.", "0.95% a.a.", "0.90% a.a.", "1.00% a.a.", "1.00% a.a.", "0.20% a.a.", "1.05% a.a.", "1.00% a.a."],
    "Taxa de Performance": ["Não tem", "Não tem", "Não tem", "20% exceder IFIX", "Não tem", "20% exceder IFIX", "20% exceder IPCA+6%", "20% exceder IPCA+6%", "Não tem", "Não tem"],
    "Benchmark": ["IFIX", "CDI", "CDI", "IFIX", "IFIX", "IFIX", "IPCA + 6%", "IPCA + 6%", "CDI", "CDI"]
}

# Criando o DataFrame e exportando para Excel
df_fiis = pd.DataFrame(dados_fiis)
df_fiis.to_excel("fiis_b3.xlsx", index=False)

print("✅ Arquivo 'fiis_b3.xlsx' gerado com sucesso!")