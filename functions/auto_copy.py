import sys
import time
import subprocess
import requests
import re

if len(sys.argv) < 3:
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
headers = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}

def get_clip():
    try:
        # Puxa o dump completo do clipboard via Root
        cmd = 'su -c "dumpsys clipboard"'
        res = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8')
        
        # O Android guarda o texto dentro de aspas simples logo após 'mText=' ou 'text='
        # Vamos usar uma busca que pega o que está entre aspas simples
        match = re.search(r"mText='([^']*)'", res)
        if not match:
            match = re.search(r"text='([^']*)'", res)
            
        if match:
            return match.group(1).strip()
        return ""
    except:
        return ""

last_clip = get_clip()
# Log inicial para sabermos que o script está vivo
with open("functions/copy_log.txt", "a") as f:
    f.write(f"\n[{time.ctime()}] Monitoramento Iniciado. Clip atual: '{last_clip}'")

while True:
    try:
        current = get_clip()
        
        if current and current != last_clip:
            payload = {"texto": current, "device_id": device_id, "guild_id": guild_id}
            # Tenta enviar para a Vercel
            r = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=5)
            
            if r.status_code == 200:
                last_clip = current
                with open("last_activity.txt", "w") as f: f.write(str(time.time()))
    except:
        pass
        
    time.sleep(3) # Aumentei para 3s para evitar que o Android mate por alto consumo
