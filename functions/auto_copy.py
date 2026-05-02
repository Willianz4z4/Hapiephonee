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

def get_clipboard_brute_force():
    try:
        # TENTATIVA 1: Comando padrão via ROOT
        res = subprocess.run(['su', '-c', 'service call clipboard 2'], capture_output=True, text=True, timeout=2)
        # Este comando retorna um dump hexadecimal, vamos tentar o básico primeiro:
        res_basic = subprocess.run(['su', '-c', 'cmd clipboard get-text'], capture_output=True, text=True, timeout=2)
        output = res_basic.stdout.strip()
        
        if output and output != "null":
            return output

        # TENTATIVA 2: Dumpsys Completo (Extração via Regex)
        # Procuramos por qualquer coisa dentro de 'items={' ou 'text='
        res_dump = subprocess.run(['su', '-c', 'dumpsys clipboard'], capture_output=True, text=True, timeout=3)
        dump_text = res_dump.stdout
        
        # Procura padrões comuns de texto no dump do Android
        matches = re.findall(r"text=([^,\}\n]+)", dump_text)
        if matches:
            return matches[-1].strip() # Pega o item mais recente
            
        return ""
    except:
        return ""

print(f"🚀 Monitoramento Bruto Iniciado (Device: {device_id})")
last_clip = get_clipboard_brute_force()

while True:
    try:
        current = get_clipboard_brute_force()
        
        if current and current != last_clip:
            # Filtra apenas se o texto for minimamente válido
            if len(current) > 0:
                requests.post(
                    URL_WEBHOOK, 
                    json={"texto": current, "device_id": device_id, "guild_id": guild_id}, 
                    headers=headers, 
                    timeout=5
                )
                last_clip = current
                with open("last_activity.txt", "w") as f: f.write(str(time.time()))
    except:
        pass
        
    time.sleep(2)
