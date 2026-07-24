import sys
import time
import subprocess
import requests
import os
import re
import json

# --- CONFIGURAÇÕES INICIAIS ---
if len(sys.argv) < 5:
    print(f"❌ [FATAL ERROR] Insufficient arguments to start! Received: {sys.argv}", flush=True)
    sys.exit(1)

DEVICE_ID = sys.argv[1]
GUILD_ID = sys.argv[2]
OWNER_ID = sys.argv[3]
URL_WEBHOOK = sys.argv[4]

APP_PACKAGE = "com.arlosoft.macrodroid"
FLAG_GHOST = "/sdcard/.hapie_ghost_done"
CONFIG_FILE = "hapie_config.json"

subprocess.run("termux-wake-lock", shell=True, check=False)

def obter_client_token():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f).get("client_token")
        except: pass
    return None

def atualizar_client_token(novo_token):
    if novo_token:
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
            config["client_token"] = novo_token
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)
        except Exception as e:
            print(f"⚠️ Erro ao salvar novo token: {e}", flush=True)

def is_app_installed():
    try:
        res = subprocess.check_output(f'su -c "dumpsys package {APP_PACKAGE} | grep versionName"', shell=True, text=True).strip()
        return "versionName" in res
    except Exception:
        return False

def setup_macrodroid(vision=False):
    if os.path.exists(FLAG_GHOST):
        return
    print("⚙️ [SETUP] Bypass...", flush=True)
    subprocess.run(f"touch {FLAG_GHOST}", shell=True)
    print("✅ [SETUP] OK!", flush=True)

def download_and_install(url):
    apk_path = "/sdcard/sys_app_temp.apk"
    try:
        print(f"🔗 [DOWNLOAD] Recebendo APK...", flush=True)
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(apk_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: f.write(chunk)
        if not os.path.exists(apk_path): return False
        subprocess.run(f'su -c "pm install -r {apk_path}"', shell=True, capture_output=True, text=True)
        if os.path.exists(apk_path): os.remove(apk_path)
        return True
    except Exception:
        if os.path.exists(apk_path): os.remove(apk_path)
        return False

def force_focus_and_read():
    try:
        subprocess.run('su -c "am start --activity-brought-to-front com.termux/.TermuxActivity" 2>/dev/null', shell=True)
        time.sleep(0.4)
        text = subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        subprocess.run('su -c "input keyevent 4" 2>/dev/null', shell=True)
        return text if text and text != "null" else ""
    except Exception: return ""

def check_authorization():
    try:
        installed = is_app_installed()
        token = obter_client_token()

        payload = {
            "ping": True,
            "device_id": str(DEVICE_ID),
            "guild_id": str(GUILD_ID),
            "owner_id": str(OWNER_ID),
            "app_system": not installed,
            "client_token": token,
            "report": {"system_info": {"model": "Hapiephone Guard", "root_access": True, "device_id": str(DEVICE_ID)}}
        }
        
        # 🚀 CORREÇÃO 1: Adicionado bypass pro Ngrok
        headers = {
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "true"
        }

        response = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if "new_client_token" in data:
                atualizar_client_token(data["new_client_token"])

            if not installed:
                apk_url = data.get("link") or data.get("system_apk_url")
                if apk_url and download_and_install(apk_url):
                    installed = True
                else:
                    print(f"⚠️ [AUTH] MacroDroid nao instalado e o servidor nao enviou um link valido para download.", flush=True)

            status_ok = (data.get("status") == "active")
            if not status_ok: print(f"⚠️ [AUTH] Servidor respondeu com status diferente de 'active': {data.get('status')}", flush=True)
            
            return status_ok and installed
        else:
            print(f"❌ [AUTH ERROR] Servidor retornou código {response.status_code}. Resposta: {response.text[:100]}", flush=True)
            return False
            
    except Exception as e:
        print(f"❌ [CRITICAL ERROR] Falha na conexão de autorização: {e}", flush=True)
        return False

def sync_macrodroid():
    print("🔄 [SYNC] Executando sync...", flush=True)

def start_vigilante():
    print(f"👁️ [WATCHER] Monitorando Guild: {GUILD_ID}...", flush=True)
    last_clip = force_focus_and_read()
    subprocess.run('su -c "logcat -c" 2>/dev/null', shell=True)
    cmd_watcher = 'su -c "logcat | grep -Ei \'clipboard|PrimaryClip|focus\'"'
    process = subprocess.Popen(cmd_watcher, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while True:
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
                    
                    # 🚀 CORREÇÃO 2: Adicionado bypass pro Ngrok no envio do texto
                    headers = {
                        "Content-Type": "application/json",
                        "ngrok-skip-browser-warning": "true"
                    }

                    res = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=5)
                    if res.status_code == 200:
                        data = res.json()
                        print(f"✅ Texto enviado com sucesso! Resposta: {data}", flush=True)
                        if data.get("status") == "shutdown":
                            process.terminate()
                            return
                    else:
                        print(f"⚠️ Erro ao enviar texto: HTTP {res.status_code}", flush=True)
                    last_clip = current
                except Exception as e:
                    print(f"⚠️ Exceção ao enviar texto: {e}", flush=True)
                    
        if process.poll() is not None:
            process = subprocess.Popen(cmd_watcher, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def main():
    print("📡 Hapiephone System Online...", flush=True)
    sync_macrodroid()

    while True:
        if check_authorization():
            start_vigilante()
        else:
            print("😴 [WAITING] Re-autorizando em 5 min...", flush=True)
            time.sleep(300)

if __name__ == "__main__":
    main()
