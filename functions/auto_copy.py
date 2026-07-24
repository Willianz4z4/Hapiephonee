import sys
import time
import subprocess
import requests
import os
import json

# --- CONFIGURAÇÕES INICIAIS ---
if len(sys.argv) < 5:
    print(f"❌ [FATAL ERROR] Faltam argumentos! Recebido: {sys.argv}", flush=True)
    sys.exit(1)

DEVICE_ID = sys.argv[1]
GUILD_ID = sys.argv[2]
OWNER_ID = sys.argv[3]
URL_WEBHOOK = sys.argv[4]

APP_PACKAGE = "com.arlosoft.macrodroid"
CONFIG_FILE = "hapie_config.json"
FUNCTIONS_FILE = "functions.json"  # <-- NOVO ARQUIVO DE AVISOS
FLAG_GHOST = "/sdcard/.hapie_ghost_done"

subprocess.run("termux-wake-lock", shell=True, check=False)

def obter_client_token():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f).get("client_token")
        except: pass
    return None

def check_local_status():
    """Lê o quadro de avisos (functions.json) para saber se deve trabalhar"""
    if os.path.exists(FUNCTIONS_FILE):
        try:
            with open(FUNCTIONS_FILE, "r") as f:
                config = json.load(f)
                # 🔥 AQUI ESTÁ A CORREÇÃO: Aceita "auto_copy" ou "autocopy"
                return config.get("auto_copy", config.get("autocopy", False))
        except: pass
    return False

def setup_app_e_cliques():
    if os.path.exists(FLAG_GHOST):
        subprocess.run(f'su -c "monkey -p {APP_PACKAGE} -c android.intent.category.LAUNCHER 1" > /dev/null 2>&1', shell=True)
        return

    print("⚙️ [SETUP] Abrindo app e executando bypass...", flush=True)
    subprocess.run(f'su -c "monkey -p {APP_PACKAGE} -c android.intent.category.LAUNCHER 1" > /dev/null 2>&1', shell=True)
    time.sleep(3)
    subprocess.run(f"touch {FLAG_GHOST}", shell=True)
    print("✅ [SETUP] App aberto e pronto!", flush=True)

def force_focus_and_read():
    try:
        subprocess.run('su -c "am start --activity-brought-to-front com.termux/.TermuxActivity" > /dev/null 2>&1', shell=True)
        time.sleep(0.4)
        text = subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        subprocess.run('su -c "input keyevent 4" > /dev/null 2>&1', shell=True)
        return text if text and text != "null" else ""
    except Exception: return ""

def start_vigilante():
    print(f"👁️ [WATCHER] Monitorando área de transferência para Guild: {GUILD_ID}...", flush=True)
    last_clip = force_focus_and_read()
    subprocess.run('su -c "logcat -c" > /dev/null 2>&1', shell=True)
    cmd_watcher = 'su -c "logcat | grep -Ei \'clipboard|PrimaryClip|focus\'"'
    process = subprocess.Popen(cmd_watcher, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while True:
        if not check_local_status():
            print("⏸️ [WATCHER] Ordem recebida do import.py para pausar.", flush=True)
            process.terminate()
            return

        line = process.stdout.readline()
        if line:
            time.sleep(0.5)
            current = force_focus_and_read()
            if current and current != last_clip:
                try:
                    token = obter_client_token()
                    payload = {
                        "texto": current,
                        "device_id": str(DEVICE_ID),
                        "guild_id": str(GUILD_ID),
                        "owner_id": str(OWNER_ID),
                        "client_token": token
                    }
                    headers = {
                        "Content-Type": "application/json",
                        "ngrok-skip-browser-warning": "true"
                    }
                    res = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=5)
                    if res.status_code == 200:
                        data = res.json()
                        print(f"✅ Copiado e enviado! Status: {data.get('status')}", flush=True)
                        if data.get("status") == "shutdown":
                            process.terminate()
                            return
                    last_clip = current
                except Exception as e:
                    print(f"⚠️ Erro ao enviar texto: {e}", flush=True)

        if process.poll() is not None:
            process = subprocess.Popen(cmd_watcher, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def main():
    print("📡 Hapiephone Copy System Online...", flush=True)
    setup_app_e_cliques()

    while True:
        if check_local_status():
            start_vigilante()
        else:
            print("😴 [WAITING] Aguardando ordem no functions.json (auto_copy=true)...", flush=True)
            time.sleep(30)

if __name__ == "__main__":
    main()
