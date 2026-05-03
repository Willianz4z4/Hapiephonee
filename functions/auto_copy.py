import sys
import time
import subprocess
import requests
import os
import re

if len(sys.argv) < 4:
    print(f"❌ [ERRO FATAL] Argumentos insuficientes para iniciar! Recebido: {sys.argv}", flush=True)
    sys.exit(1)

DEVICE_ID = sys.argv[1]
GUILD_ID = sys.argv[2]
OWNER_ID = sys.argv[3]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
HEADERS = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}
APP_PACKAGE = "com.arlosoft.macrodroid"

subprocess.run("termux-wake-lock", shell=True, check=False)

def is_app_installed():
    try:
        # Usa dumpsys: é muito mais preciso e não pega restos de apps desinstalados
        res = subprocess.check_output(f'su -c "dumpsys package {APP_PACKAGE} | grep versionName"', shell=True, text=True).strip()
        return "versionName" in res
    except Exception:
        return False

def download_and_install(url):
    apk_path = os.path.join(os.getcwd(), "sys_app_temp.apk")
    try:
        if "drive.google.com" in url:
            match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
            if match:
                url = f"https://drive.google.com/uc?export=download&id={match.group(1)}"
        
        response = requests.get(url, stream=True, timeout=30)
        with open(apk_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: 
                    f.write(chunk)
                
        res = subprocess.run(f'su -c "pm install {apk_path}"', shell=True, capture_output=True, text=True)
        
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
        texto = subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        subprocess.run('su -c "input keyevent 4" 2>/dev/null', shell=True)
        return texto if texto and texto != "null" else ""
    except Exception:
        return ""

def check_authorization():
    try:
        installed = is_app_installed()
        
        if not installed:
            print("⚠️ [APP SYSTEM] MacroDroid não encontrado no aparelho. Solicitando link ao servidor...", flush=True)
        else:
            print("✅ [APP SYSTEM] MacroDroid já está instalado.", flush=True)

        payload = {
            "ping": True,
            "device_id": DEVICE_ID,
            "guild_id": GUILD_ID,
            "owner_id": OWNER_ID,
            "app_system": not installed,
            "report": {
                "system_info": {
                    "model": "AutoCopy Ping",
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
                    print(f"📥 [DOWNLOAD] Baixando APK do Drive...", flush=True)
                    if download_and_install(data["system_apk_url"]):
                        print("🚀 [SUCESSO] Instalação silenciosa concluída!", flush=True)
                        installed = True
                    else:
                        print("❌ [ERRO] Falha ao instalar o APK.", flush=True)
                else:
                    # Se o servidor responder, mas NÃO enviar o link, ele avisa aqui!
                    print("❌ [ERRO DO SERVIDOR] O servidor NÃO enviou o link do app (system_apk_url)!", flush=True)
                    print("👉 Verifique se o MacroDroid está cadastrado no MongoDB com is_system_app: True", flush=True)
                    
            return data.get("status") == "active" and installed
        return False
    except Exception as e:
        print(f"❌ [ERRO DE CONEXÃO] {e}", flush=True)
        return False

def start_vigilante():
    print(f"👁️ [VIGILANTE] Ativado para Guild: {GUILD_ID}. Aguardando textos...", flush=True)
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
                if not is_app_installed():
                    print("🛑 [VIGILANTE] MacroDroid foi desinstalado! Parando operação.", flush=True)
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
                            print("🛑 [SHUTDOWN] Permissão revogada pelo servidor.", flush=True)
                            process.terminate()
                            return
                            
                    last_clip = current
                except Exception:
                    process.terminate()
                    return

        if process.poll() is not None:
            process = subprocess.Popen(cmd_vigia, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def main():
    print("📡 Iniciando sistema com Ping Inteligente...", flush=True)
    while True:
        if check_authorization():
            start_vigilante()
        else:
            print("😴 [WAITING] Re-checando em 5 min...", flush=True)
            time.sleep(300) 

if __name__ == "__main__":
    main()
