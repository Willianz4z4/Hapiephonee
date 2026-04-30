import sys
import time
import subprocess
import requests
import os

# Verifica se os IDs foram passados corretamente pelo import.py
if len(sys.argv) < 3:
    print("Uso incorreto. Faltando device_id ou guild_id.")
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]

# LEMBRETE: Se o seu servidor oficial agora for o Termux+Serveo, 
# troque a URL da Vercel pelo seu link do Serveo (ex: ...serveousercontent.com/copy)
URL_WEBHOOK_COPY = "https://hapiephoneugph.vercel.app/api/copy"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"

def get_clipboard():
    """Lê o texto atual da área de transferência (Control+C) do Termux"""
    try:
        return subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except:
        return ""

last_clipboard = get_clipboard()

print(f"📋 Monitor de Área de Transferência iniciado (Device: {device_id})")

while True:
    try:
        current_clipboard = get_clipboard()

        # Se o texto copiado não for vazio e for diferente da última coisa copiada
        if current_clipboard and current_clipboard != last_clipboard:
            
            # Monta o pacote apenas com o texto e as IDs. 
            # Quem vai olhar no banco de dados para achar o "channel_id" é o servidor!
            payload = {
                "texto": current_clipboard,
                "device_id": device_id,
                "guild_id": guild_id
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": AUTH_SECRET
            }

            # Envia a cópia para a rota /copy do seu Servidor
            resp = requests.post(URL_WEBHOOK_COPY, json=payload, headers=headers, timeout=5)
            
            if resp.status_code == 200:
                last_clipboard = current_clipboard 
                
                # 👉 A MÁGICA DO PING INTELIGENTE 👈
                # Cria/atualiza esse arquivo invisível. O 'import.py' vai ver a hora desse 
                # arquivo e saberá que o celular já enviou um sinal de vida recentemente!
                try:
                    with open("last_activity.txt", "w") as f:
                        f.write(str(time.time()))
                except:
                    pass
                    
    except Exception:
        # Se der erro de internet (ou se o servidor cair), ele apenas ignora e tenta de novo no próximo loop
        pass 

    # Pausa de 3 segundos antes de checar a área de transferência de novo
    time.sleep(3)
