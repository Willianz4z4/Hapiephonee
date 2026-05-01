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
headers = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}

def get_clip():
    try:
        return subprocess.check_output("termux-clipboard-get", shell=True).decode('utf-8').strip()
    except:
        return ""

last_clip = get_clip()

# Monitor via Logcat (Ouvindo o sistema)
cmd = 'su -c "logcat -b events | grep CLIPBOARD_CHANGED"'
process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

while True:
    # Este comando bloqueia o loop até que algo mude no sistema (não gasta bateria)
    line = process.stdout.readline()
    if line:
        time.sleep(0.5) # Espera o Android terminar de escrever
        current = get_clip()
        if current and current != last_clip:
            try:
                requests.post(URL_WEBHOOK, json={"texto": current, "device_id": device_id, "guild_id": guild_id}, headers=headers, timeout=5)
                last_clip = current
            except:
                pass
    
    # Se o logcat morrer, reinicia
    if process.poll() is not None:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
