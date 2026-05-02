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
        res = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
        
        # 1º Tentativa (Padrão nativo do Android 10/11): {T:Texto Aqui}
        match1 = re.search(r'\{T:([^}]+)\}', res)
        if match1: return match1.group(1).strip()
        
        # 2º Tentativa (Padrão de variáveis mText ou text)
        match2 = re.search(r'(?:mText|text)=[\'"]?([^\'"\n\r]+)[\'"]?', res)
        if match2: return match2.group(1).strip()
        
        # 3º Tentativa (Padrão bruto de logs antigos)
        match3 = re.search(r'Text:\s*"(.*?)"', res)
        if match3: return match3.group(1).strip()
        
        return ""
    except Exception:
        return ""

last_clip = get_clip()

while True:
    try:
        current = get_clip()
        
        if current and current != last_clip:
            payload = {"texto": current, "device_id": device_id, "guild_id": guild_id}
            
            # Tenta enviar para a Vercel
            r = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=5)
            
            if r.status_code == 200:
                last_clip = current
                try:
                    with open("last_activity.txt", "w") as f: 
                        f.write(str(time.time()))
                except:
                    pass
    except Exception:
        pass
        
    time.sleep(3)
