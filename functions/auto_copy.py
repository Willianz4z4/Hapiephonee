import sys
import time
import subprocess
import requests

if len(sys.argv) < 4:
    sys.exit(1)

DEVICE_ID = sys.argv[1]
GUILD_ID = sys.argv[2]
OWNER_ID = sys.argv[3]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
HEADERS = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}

subprocess.run("termux-wake-lock", shell=True, check=False)

def force_focus_and_read():
    try:
        subprocess.run('su -c "am start --activity-brought-to-front com.termux/.TermuxActivity" 2>/dev/null', shell=True)
        time.sleep(0.4)
        texto = subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        subprocess.run('su -c "input keyevent 4" 2>/dev/null', shell=True)
        return texto if texto and texto != "null" else ""
    except Exception:
        return ""

def check_authorization():
    try:
        payload = {
            "ping": True,
            "device_id": DEVICE_ID,
            "guild_id": GUILD_ID,
            "owner_id": OWNER_ID,
            "report": {
                "system_info": {
                    "model": "AutoCopy Ping",
                    "root_access": True
                }
            }
        }
        response = requests.post(URL_WEBHOOK, json=payload, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "active"
        return False
    except Exception:
        return False

def start_vigilante():
    print(f"🚀 [ACTIVE] Vigilante iniciado para Guild: {GUILD_ID}")
    last_clip = force_focus_and_read()
    
    subprocess.run('su -c "logcat -c" 2>/dev/null', shell=True)
    cmd_vigia = 'su -c "logcat | grep -Ei \'clipboard|PrimaryClip|focus\'"'
    process = subprocess.Popen(cmd_vigia, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while True:
        line = process.stdout.readline()
        if line:
            time.sleep(0.5)
            current = force_focus_and_read()
            
            if current and current != last_clip:
                try:
                    payload = {
                        "texto": current, 
                        "device_id": DEVICE_ID, 
                        "guild_id": GUILD_ID,
                        "owner_id": OWNER_ID
                    }
                    res = requests.post(URL_WEBHOOK, json=payload, headers=HEADERS, timeout=5)
                    
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("status") == "shutdown":
                            print("🛑 [SHUTDOWN] Permissão revogada pelo servidor.")
                            process.terminate()
                            return
                            
                    last_clip = current
                except Exception:
                    process.terminate()
                    return

        if process.poll() is not None:
            process = subprocess.Popen(cmd_vigia, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def main():
    print("📡 Iniciando sistema com Ping Inteligente...")
    while True:
        if check_authorization():
            start_vigilante()
        else:
            print("😴 [WAITING] Auto-Copy desativado ou sem permissão. Re-checando em 5 min...")
            time.sleep(300) 

if __name__ == "__main__":
    main()
