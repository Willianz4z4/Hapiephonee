import sys
import time
import subprocess
import requests
import os

if len(sys.argv) < 3:
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]

URL_WEBHOOK_COPY = "https://hapiephoneugph.vercel.app/api/copy"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"

def get_clipboard_root():
    """Lê o clipboard usando ROOT para burlar o bloqueio de segundo plano do Android"""
    try:
        # Comando de força bruta do Root para ler o teclado
        comando = "su -c 'cmd clipboard get-text'"
        output = subprocess.check_output(comando, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        
        # O Android costuma retornar "Text: [conteudo]", vamos limpar isso
        if "Text: " in output:
            return output.split("Text: ", 1)[1].strip()
        return output
    except:
        # Se o comando acima falhar, tenta o plano B (Termux API)
        try:
            return subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        except:
            return ""

last_clipboard = get_clipboard_root()

while True:
    try:
        current_clipboard = get_clipboard_root()

        # Só envia se for um link (contendo http) ou se houver mudança
        if current_clipboard and current_clipboard != last_clipboard:
            
            payload = {
                "texto": current_clipboard,
                "device_id": device_id,
                "guild_id": guild_id
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": AUTH_SECRET
            }

            # Envia para a Vercel/Flask
            resp = requests.post(URL_WEBHOOK_COPY, json=payload, headers=headers, timeout=5)
            
            if resp.status_code == 200:
                last_clipboard = current_clipboard 
                
                # Sinal de vida para o import.py
                try:
                    with open("last_activity.txt", "w") as f:
                        f.write(str(time.time()))
                except:
                    pass
                    
    except Exception:
        pass 

    # Checa a cada 2 segundos se você copiou algo novo
    time.sleep(2)
