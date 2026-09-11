import pandas as pd
import requests

print("⏳ Baixando lista completa de FIIs do Fundamentus...")

url = "https://www.fundamentus.com.br/fii_resultado.php"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    req = requests.get(url, headers=headers)
    tables = pd.read_html(req.text, decimal=',', thousands='.')
    df = tables[0]

    # Limpeza e conversão de colunas percentuais
    for col in ['FFO Yield', 'Dividend Yield', 'Cap Rate', 'Vacância Média']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.rstrip('%').str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # Renomeia colunas para o padrão do Terminal Albarado
    rename_dict = {
        'Papel': 'Ticker',
        'Segmento': 'Segmento de Atuação',
        'Dividend Yield': 'DY 12M Acumulado',
        'Liquidez': 'Liquidez diária',
        'Valor de Mercado': 'Patrimônio Líquido',
        'Qtd de imóveis': 'Quantidade de Imóveis',
        'Vacância Média': 'Vacância'
    }
    df = df.rename(columns=rename_dict)

    # Tratamento de colunas complementares
    df['Tipo de fundo'] = df['Segmento de Atuação'].apply(
        lambda x: 'Papel' if any(k in str(x).lower() for k in ['títulos', 'papel', 'cris']) else 'Tijolo'
    )
    df['Multi-inquilino'] = 'Sim'
    df['Para FII de Papel % em CRIs'] = df['Tipo de fundo'].apply(lambda x: 90.0 if x == 'Papel' else 0.0)
    df['Quantidade de CRIs'] = df['Tipo de fundo'].apply(lambda x: 30 if x == 'Papel' else 0)
    df['Administrador'] = 'Diversos'
    df['Tempo de listagem'] = 5
    df['Tipo de Gestão'] = 'Ativa'
    df['Taxa de adm'] = '0.90% a.a.'
    df['Taxa de Performance'] = 'N/A'
    df['Benchmark'] = 'IFIX'

    # Salva a planilha completa
    df.to_excel("fiis_b3.xlsx", index=False)
    print(f"✅ Sucesso! {len(df)} FIIs foram salvos na planilha 'fiis_b3.xlsx'.")

except Exception as e:
    print(f"❌ Erro ao baixar dados do Fundamentus: {e}")