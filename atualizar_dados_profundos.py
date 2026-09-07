import requests
import re
from bs4 import BeautifulSoup
import json
import time
import random
import os

print("🕵️ Iniciando o Caçador V2.1 (Correção de Setor e Segmento)...")
print("⚠️ Recapturando setores afetados pela mudança de layout do Status Invest.")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

ESTATAIS = [
    "BBAS", "PETR", "CMIG", "CSMG", "SAPR", "BRSR", "BAZA", "BNBR", 
    "BGIP", "CEBR", "CEPE", "CLSC", "COCE", "EKTR", "EMAE", "PSSA", 
    "CASN", "CEGR", "CGAS", "SBSP"
]

url_fundamentus = "https://www.fundamentus.com.br/resultado.php"
try:
    resposta = requests.get(url_fundamentus, headers=headers)
    soup = BeautifulSoup(resposta.text, 'html.parser')
except Exception:
    print("❌ Erro ao acessar Fundamentus.")
    exit()

radicais = set()
for tr in soup.find_all('tr')[1:]:
    tds = tr.find_all('td')
    if tds:
        t = tds[0].text.strip()
        if not re.search(r'(32|33|34|35|39)$', t):
            radicais.add(t[:4])

radicais = sorted(list(radicais))
arquivo_json = "dados_profundos.json"
dados_profundos = {}

if os.path.exists(arquivo_json):
    with open(arquivo_json, "r", encoding="utf-8") as f:
        dados_profundos = json.load(f)

for i, radical in enumerate(radicais):
    info_cache = dados_profundos.get(radical, {})
    
    # Força a re-raspagem se o Setor falhou ("Outros") ou Segmento veio vazio ("None")
    seg_cache = str(info_cache.get("Segmento", "")).strip()
    set_cache = str(info_cache.get("Setor", "")).strip()
    
    if set_cache != "Outros" and seg_cache.lower() != "none" and seg_cache != "Erro" and set_cache != "":
        continue
        
    ticker_busca = f"{radical}3"
    url_status = f"https://statusinvest.com.br/acoes/{ticker_busca}"
    
    info = {
        "Segmento": "Tradicional",
        "Setor": "Outros Setores",
        "Free_Float": "0,00%",
        "DivLiq_EBIT": "0,00",
        "Governo_Majoritario": "Sim" if radical in ESTATAIS else "Não"
    }
    
    try:
        r = requests.get(url_status, headers=headers, timeout=10)
        if r.status_code == 200:
            soup_si = BeautifulSoup(r.text, 'html.parser')
            
            # RASPAGEM ROBUSTA: Segmento (Evitando "None")
            tag_seg = soup_si.find(string=re.compile("Segmento de Listagem", re.IGNORECASE))
            if tag_seg and tag_seg.find_next("strong"):
                val = tag_seg.find_next("strong").text.strip()
                if val and val.lower() != "none" and val != "-":
                    info["Segmento"] = val
                
            # RASPAGEM ROBUSTA: Setor (Nova Regra baseada em Texto, não em Links)
            tag_setor = soup_si.find(string=re.compile("Setor de atua", re.IGNORECASE))
            if tag_setor and tag_setor.find_next("strong"):
                val_setor = tag_setor.find_next("strong").text.strip()
                if val_setor and val_setor.lower() != "none" and val_setor != "-":
                    info["Setor"] = val_setor
                
            # RASPAGEM ROBUSTA: Free Float
            tag_ff = soup_si.find(string=re.compile("Free Float", re.IGNORECASE))
            if tag_ff and tag_ff.find_next("strong"):
                info["Free_Float"] = tag_ff.find_next("strong").text.strip()
                
            # RASPAGEM ROBUSTA: Dívida Líquida / EBIT
            tag_div = soup_si.find(string=re.compile("quida/EBIT", re.IGNORECASE))
            if tag_div and tag_div.find_next("strong"):
                info["DivLiq_EBIT"] = tag_div.find_next("strong").text.strip()

        print(f"[{i+1}/{len(radicais)}] {radical} -> Seg: {info['Segmento']} | Setor: {info['Setor']}")
        dados_profundos[radical] = info
        
    except Exception:
        print(f"[{i+1}/{len(radicais)}] {radical} -> ❌ Erro de conexão.")
        info["Segmento"] = "Erro"
        dados_profundos[radical] = info
        
    # Pausa mais rápida (0.5 a 1.5s)
    time.sleep(random.uniform(0.5, 1.5))

with open(arquivo_json, "w", encoding="utf-8") as f:
    json.dump(dados_profundos, f, ensure_ascii=False, indent=4)

print(f"\n✅ Banco de dados V2.1 salvo com sucesso!")