import sys
import time
import subprocess
import requests
import os

if len(sys.argv) < 3:
    print("Uso incorreto. Rode: python copy.py <device_id> <guild_id>")
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]

URL_WEBHOOK_COPY = "https://hapiephoneugph.vercel.app/api/copy"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"

def get_clipboard():
    try:
        resultado = subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        return resultado
    except Exception as e:
        print(f"⚠️ Erro ao tentar ler o teclado: {e}")
        return ""

last_clipboard = get_clipboard()

print(f"📋 Monitor Iniciado! (Device: {device_id} | Guilda: {guild_id})")
print(f"Última coisa copiada ao iniciar: '{last_clipboard}'\n")
print("⏳ Copie alguma coisa nova no celular agora...")

while True:
    try:
        current_clipboard = get_clipboard()

        if current_clipboard and current_clipboard != last_clipboard:
            print(f"\n📝 NOVO TEXTO DETECTADO: '{current_clipboard}'")
            print("🚀 Enviando para a Vercel...")
            
            payload = {
                "texto": current_clipboard,
                "device_id": device_id,
                "guild_id": guild_id
            }
            headers = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}

            resp = requests.post(URL_WEBHOOK_COPY, json=payload, headers=headers, timeout=10)
            
            print(f"📡 Resposta da Vercel: STATUS {resp.status_code}")
            
            if resp.status_code == 200:
                print("✅ Enviado com sucesso pro Servidor!")
                last_clipboard = current_clipboard 
                try:
                    with open("last_activity.txt", "w") as f:
                        f.write(str(time.time()))
                except:
                    pass
            else:
                print(f"❌ Erro! A Vercel recusou. Detalhes: {resp.text}")
                    
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de Conexão com a Vercel: {e}")
    except Exception as e:
        print(f"❌ Erro desconhecido: {e}")

    time.sleep(3)
