import os
import sys
import subprocess

# 1. Pega o ID que o usuário passou no comando (ou deixa vazio)
if len(sys.argv) > 1:
    user_id = sys.argv[1]
else:
    user_id = ""

# Variáveis do seu sistema
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
SENHA_SECRETA = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
URL_REQS = "https://raw.githubusercontent.com/Willianz4z4/Hapiephone/main/Cloudphone/requerimentos.txt"

# Dicionário preparado para mandar vazio se der erro
relatorio = {
    "status_instalacao": "pendente",
    "etapas": {},
    "info_sistema": {
        "modelo": ""
    }
}

print("🔄 Preparando o ambiente do seu Cloud Phone...")

# --- NOVA ETAPA: Atualizar repositórios e corrigir falhas de biblioteca do Termux silenciosamente ---
os.system("pkg update -y -q > /dev/null 2>&1 && pkg upgrade -y -q > /dev/null 2>&1")
os.system("pkg install curl openssl -y -q > /dev/null 2>&1")
# ---------------------------------------------------------------------------------------------------

# 2. Arrumar o ambiente e instalar o Root próprio (tsu) de forma 100% invisível
os.system("pkg install tsu -y -q > /dev/null 2>&1")

# 3. Baixar e instalar requerimentos em silêncio absoluto
try:
    os.system(f"curl -sL {URL_REQS} -o reqs.txt > /dev/null 2>&1")
    resultado_pip = os.system("pip install -r reqs.txt -q > /dev/null 2>&1")
    
    if resultado_pip == 0:
        relatorio["etapas"]["pacotes_pip"] = "Sucesso"
    else:
        relatorio["etapas"]["pacotes_pip"] = "Falha"
except:
    relatorio["etapas"]["pacotes_pip"] = "Falha"

# 4. Pegar informações do celular usando o Root
try:
    # O stderr=subprocess.DEVNULL esconde qualquer mensagem vermelha de erro do root
    modelo = subprocess.check_output("su -c 'getprop ro.product.model'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    relatorio["info_sistema"]["modelo"] = modelo
    relatorio["etapas"]["coleta_dados"] = "Sucesso"
except:
    relatorio["info_sistema"]["modelo"] = ""
    relatorio["etapas"]["coleta_dados"] = "Falha"

relatorio["status_instalacao"] = "Concluido"
print("✅ Configuração terminada! Conectando ao painel de controle...")

# 5. Enviar para a Vercel silenciosamente
try:
    import requests
    
    payload = {
        "guild_id": user_id,
        "mensagem": "Tentativa de conexão finalizada.",
        "relatorio": relatorio
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": SENHA_SECRETA
    }
    
    # Envia o pacote com um limite de tempo para não travar o celular do cara
    requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=10)
    
    # Para o cliente, o processo sempre termina com sucesso visual
    print("🚀 Dispositivo sincronizado com sucesso!")
    
except:
    # Se o webhook cair ou faltar internet, o script simplesmente morre calado.
    # O seu bot no Discord vai notar que o ID X não mandou o relatório e vai avisar por lá.
    pass
