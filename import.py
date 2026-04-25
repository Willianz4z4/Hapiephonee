import os
import sys
import subprocess

if len(sys.argv) > 1:
    user_id = sys.argv[1]
else:
    user_id = ""

URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
SENHA_SECRETA = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
URL_REQS = "https://raw.githubusercontent.com/Willianz4z4/Hapiephone/main/Cloudphone/requerimentos.txt"

relatorio = {
    "status_instalacao": "pendente",
    "etapas": {},
    "info_sistema": {
        "modelo": ""
    }
}

print("🔄 Preparando o ambiente do seu Cloud Phone...")

os.system("pkg update -y -q > /dev/null 2>&1 && pkg upgrade -y -q > /dev/null 2>&1")
os.system("pkg install curl openssl -y -q > /dev/null 2>&1")

os.system("pkg install tsu -y -q > /dev/null 2>&1")

try:
    os.system(f"curl -sL {URL_REQS} -o reqs.txt > /dev/null 2>&1")
    resultado_pip = os.system("pip install -r reqs.txt -q > /dev/null 2>&1")
    
    if resultado_pip == 0:
        relatorio["etapas"]["pacotes_pip"] = "Sucesso"
    else:
        relatorio["etapas"]["pacotes_pip"] = "Falha"
except:
    relatorio["etapas"]["pacotes_pip"] = "Falha"

try:
    modelo = subprocess.check_output("su -c 'getprop ro.product.model'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    relatorio["info_sistema"]["modelo"] = modelo
    relatorio["etapas"]["coleta_dados"] = "Sucesso"
except:
    relatorio["info_sistema"]["modelo"] = ""
    relatorio["etapas"]["coleta_dados"] = "Falha"

relatorio["status_instalacao"] = "Concluido"
print("✅ Configuração terminada! Conectando ao painel de controle...")

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
    
    requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=10)
    print("🚀 Dispositivo sincronizado com sucesso!")
    
except:
    pass
