import smtplib
from email.mime.text import MIMEText
import pandas as pd

# ==========================================
# 1. CONFIGURAÇÕES DO SEU E-MAIL
# ==========================================
SEU_EMAIL = "hralbaradostm@gmail.com"  # Digite seu Gmail aqui
SENHA_APP = "ceiv jpdy wmhz ptjd"  # A senha de 16 letras que o Google vai te dar
DESTINATARIO = "hralbaradostm@gmail.com" # E-mail que vai receber o alerta

def verificar_bolsa():
    print("🤖 Iniciando varredura silenciosa da Bolsa...")
    
    try:
        # 1. Lê a mesma base de dados do seu painel
        df = pd.read_excel("acoes_b3.xlsx")
        
        # 2. Faz a Matemática do Barsi
        df["Dividendo Pago (R$)"] = df["Cotação"] * (df["Dividend Yield"] / 100)
        df["Preço Teto (6%)"] = df["Dividendo Pago (R$)"] / 0.06
        df["Margem de Segurança (%)"] = df.apply(
            lambda row: ((row["Preço Teto (6%)"] / row["Cotação"]) - 1) * 100 if row["Cotação"] > 0 else 0,
            axis=1
        )
        
        # 3. Aplica o "Filtro de Ouro" (Ajuste como preferir)
        df_filtrado = df[
            (df["Margem de Segurança (%)"] >= 10.0) &  # Margem mínima de 10%
            (df["Dividend Yield"] >= 6.0) &            # DY mínimo de 6%
            (df["Liquidez Diária"] >= 500000)          # Evita ações fantasmas
        ]
        
        if len(df_filtrado) > 0:
            print(f"💎 {len(df_filtrado)} oportunidade(s) encontrada(s)! Disparando e-mail...")
            enviar_email(df_filtrado)
        else:
            print("Nenhuma ação passou no filtro hoje. O dinheiro continua no caixa.")
            
    except Exception as e:
        print(f"❌ Erro ao ler a planilha: {e}")

def enviar_email(df_aprovadas):
    # Monta o texto do e-mail com os dados reais
    texto = "O Robô Sentinela do Prudence Invest encontrou as seguintes pechinchas hoje:\n\n"
    
    for index, row in df_aprovadas.iterrows():
        texto += f"📌 {row['Ticker']} ({row['Empresa']})\n"
        texto += f"   - Cotação Atual: R$ {row['Cotação']:.2f}\n"
        texto += f"   - Preço Teto: R$ {row['Preço Teto (6%)']:.2f}\n"
        texto += f"   - Margem de Desconto: {row['Margem de Segurança (%)']:.1f}%\n"
        texto += f"   - Dividend Yield: {row['Dividend Yield']:.1f}%\n\n"
        
    texto += "Abra o seu Dashboard na nuvem para analisar o Raio-X dos Lucros!"
    
    msg = MIMEText(texto)
    msg['Subject'] = f"🚨 Alerta Prudence Invest: {len(df_aprovadas)} Ações Aprovadas!"
    msg['From'] = SEU_EMAIL
    msg['To'] = DESTINATARIO
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SEU_EMAIL, SENHA_APP)
        server.sendmail(SEU_EMAIL, DESTINATARIO, msg.as_string())
        server.quit()
        print("✅ Alerta enviado para o seu e-mail com sucesso!")
    except Exception as e:
        print(f"❌ Erro de conexão com o Gmail: {e}")

if __name__ == "__main__":
    verificar_bolsa()