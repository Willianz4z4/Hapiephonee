import os
import sys
import subprocess
import time

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

while True:
    try:
        try:
            import requests
        except ImportError:
            print("⏳ Instalando dependências de rede...")
            os.system("pip install requests -q > /dev/null 2>&1")
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
        
        resposta = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=10)
        
        if resposta.status_code == 200:
            print("🚀 Dispositivo sincronizado com sucesso!")
            break
        else:
            print(f"⚠️ Servidor ocupado ({resposta.status_code}). Tentando novamente em 5 segundos...")
            time.sleep(5)
            
    except Exception as e:
        print("📡 Sem conexão ou erro na rede. Reconectando em 5 segundos...")
        time.sleep(5)
