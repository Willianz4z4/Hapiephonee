import os
import sys
import subprocess
import time
import json

CONFIG_FILE = "hapie_config.json"
saved_config = {}

# 1. Tenta puxar da memória
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f:
            saved_config = json.load(f)
    except:
        pass

if len(sys.argv) > 2:
    guild_id = sys.argv[1]
    owner_id = sys.argv[2]
elif len(sys.argv) > 1:
    guild_id = sys.argv[1]
    owner_id = sys.argv[1] 
else:
    guild_id = saved_config.get("guild_id", "")
    owner_id = saved_config.get("owner_id", "")

if guild_id and owner_id:
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"guild_id": guild_id, "owner_id": owner_id}, f)
    except:
        pass
else:
    print("⚠️ Configuração ausente! Forneça as IDs.")
    sys.exit(1)

URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"

report = {"installation_status": "pending", "steps": {}, "system_info": {}}
print("🔄 Preparing your Cloud Phone environment...")

os.system("pkg update -y -q > /dev/null 2>&1 && pkg upgrade -y -q > /dev/null 2>&1")

try:
    URL_PKG = "https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/reqs_pkg.txt"
    os.system(f"curl -sL {URL_PKG} -o reqs_pkg.txt > /dev/null 2>&1")
    if os.path.exists("reqs_pkg.txt"):
        with open("reqs_pkg.txt", "r") as f:
            pkgs = f.read().replace('\n', ' ')
        if pkgs.strip():
            pkg_result = os.system(f"pkg install {pkgs} -y -q > /dev/null 2>&1")
            report["steps"]["pkg_packages"] = "Success" if pkg_result == 0 else "Failed"
    else:
        os.system("pkg install curl openssl tsu -y -q > /dev/null 2>&1")
        report["steps"]["pkg_packages"] = "Skipped"
except:
    report["steps"]["pkg_packages"] = "Failed"

try:
    URL_PIP = "https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/reqs_pip.txt"
    os.system(f"curl -sL {URL_PIP} -o reqs_pip.txt > /dev/null 2>&1")
    if os.path.exists("reqs_pip.txt"):
        pip_result = os.system("pip install -r reqs_pip.txt -q > /dev/null 2>&1")
        report["steps"]["pip_packages"] = "Success" if pip_result == 0 else "Failed"
    else:
        report["steps"]["pip_packages"] = "Skipped"
except:
    report["steps"]["pip_packages"] = "Failed"

def get_data(command):
    try:
        return subprocess.check_output(f"su -c '{command}'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except:
        return "Unknown"

try:
    has_root = True if get_data("echo root_ok") == "root_ok" else False
    model = get_data("getprop ro.product.model")
    android_version = get_data("getprop ro.build.version.release")
    device_id = get_data("settings get secure android_id")
    region = get_data("getprop persist.sys.locale")
    if region == "Unknown" or not region: region = get_data("getprop ro.product.locale")
    cpu_abi = get_data("getprop ro.product.cpu.abi")
    processor = "64 bits" if "64" in cpu_abi else ("32 bits" if cpu_abi != "Unknown" and cpu_abi else "Unknown")

    report["system_info"] = {"root_access": has_root, "model": model, "android_version": android_version, "device_id": device_id, "region": region, "processor": processor}
    report["steps"]["data_collection"] = "Success"
except:
    report["steps"]["data_collection"] = "Failed"
    device_id = "Unknown"

report["installation_status"] = "Completed"
print("✅ Configuration finished! Connecting to control panel...")

# ==========================================
# INICIALIZAÇÃO DO AUTO-COPY (MODO FANTASMA - SCRIPT LANÇADOR)
# ==========================================
print("🚀 Iniciando serviços em background (Auto-Copy)...")
try:
    os.makedirs("functions", exist_ok=True)
    URL_COPY_PY = "https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/functions/auto_copy.py"
    os.system(f"curl -sL {URL_COPY_PY} -o functions/auto_copy.py > /dev/null 2>&1")
    
    caminho_python = sys.executable
    caminho_script = os.path.abspath("functions/auto_copy.py")
    caminho_log = os.path.abspath("copy_log.txt")
    sh_path = os.path.abspath("start_fantasma.sh")
    
    # Cria um mini-script Bash blindado para o Root executar
    with open(sh_path, "w") as f:
        f.write("#!/system/bin/sh\n")
        f.write("export LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib\n")
        f.write("export PATH=/data/data/com.termux/files/usr/bin:$PATH\n")
        f.write(f"nohup {caminho_python} {caminho_script} {device_id} {guild_id} > {caminho_log} 2>&1 &\n")
    
    # Dá permissão e manda o Root rodar o arquivo
    os.system(f"chmod +x {sh_path}")
    os.system(f"su -c '{sh_path}'")
    
    print(f"✅ Módulo Auto-Copy ejetado! Logs criados em: {caminho_log}")
except Exception as e:
    print(f"⚠️ Aviso: Não foi possível iniciar o Auto-Copy. Erro: {e}")

registrado_no_banco = False
INTERVALO_PING = 1200 
ultima_checagem = 0 

def obter_ultima_atividade():
    try:
        if os.path.exists("last_activity.txt"): return os.path.getmtime("last_activity.txt")
    except: pass
    return 0

import requests

while True:
    agora = time.time()
    ultima_acao = max(ultima_checagem, obter_ultima_atividade())
    
    if agora - ultima_acao >= INTERVALO_PING or not registrado_no_banco:
        try:
            report_payload = report if not registrado_no_banco else {"system_info": {"device_id": device_id}}
            payload = {"type": 1 if registrado_no_banco else 0, "guild_id": guild_id, "owner_id": owner_id, "status": "online", "report": report_payload}
            headers = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}
            
            response = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                if not registrado_no_banco:
                    print("🚀 Device synchronized and actively listening for commands!")
                    registrado_no_banco = True
                ultima_checagem = time.time() 
        except:
            print("📡 No connection or network error. Retrying...")
    time.sleep(60)
