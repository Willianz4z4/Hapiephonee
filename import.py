import os
import sys
import subprocess
import time
import json

try:
    import requests
except ImportError:
    print("📦 Instalando dependências de rede...")
    os.system("pip install requests -q > /dev/null 2>&1")
    import requests

CONFIG_FILE = "hapie_config.json"
saved_config = {}

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
    print("❌ IDs ausentes. Encerrando.")
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
            os.system(f"pkg install {pkgs} -y -q > /dev/null 2>&1")
            report["steps"]["pkg_packages"] = "Success"
    else:
        os.system("pkg install curl openssl tsu -y -q > /dev/null 2>&1")
        report["steps"]["pkg_packages"] = "Skipped"
except:
    report["steps"]["pkg_packages"] = "Failed"

try:
    URL_PIP = "https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/reqs_pip.txt"
    os.system(f"curl -sL {URL_PIP} -o reqs_pip.txt > /dev/null 2>&1")
    if os.path.exists("reqs_pip.txt"):
        os.system("pip install -r reqs_pip.txt -q > /dev/null 2>&1")
        report["steps"]["pip_packages"] = "Success"
    else:
        report["steps"]["pip_packages"] = "Skipped"
except:
    report["steps"]["pip_packages"] = "Failed"

def get_data(command):
    try:
        return subprocess.check_output(f"su -c '{command}' 2>/dev/null", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
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

print("🚀 Iniciando serviços em background (Auto-Copy)...")
try:
    os.system("pkill -f auto_copy.py > /dev/null 2>&1")
    os.system("rm -rf functions/auto_copy.py > /dev/null 2>&1")
    
    os.makedirs("functions", exist_ok=True)
    v_cache = int(time.time())
    URL_COPY_PY = f"https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/functions/auto_copy.py?v={v_cache}"
    os.system(f"curl -sL '{URL_COPY_PY}' -o functions/auto_copy.py > /dev/null 2>&1")
    
    caminho_python = sys.executable
    caminho_script = os.path.abspath("functions/auto_copy.py")
    
    subprocess.run('su -c "appops set com.termux READ_CLIPBOARD allow" 2>/dev/null', shell=True)
    
    env_vars = f"LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib PATH=/data/data/com.termux/files/usr/bin:$PATH"
    comando_daemon = f"su -c '{env_vars} {caminho_python} {caminho_script} {device_id} {guild_id} > /dev/null 2>&1 &' 2>/dev/null"
    
    os.system(comando_daemon)
    print(f"✅ Módulo Invisível ejetado com sucesso!")
except Exception as e:
    pass

registrado_no_banco = False
INTERVALO_PING = 1200 
ultima_checagem = 0 

def obter_ultima_atividade():
    try:
        if os.path.exists("last_activity.txt"): return os.path.getmtime("last_activity.txt")
    except: pass
    return 0

while True:
    agora = time.time()
    ultima_acao = max(ultima_checagem, obter_ultima_atividade())
    
    if agora - ultima_acao >= INTERVALO_PING or not registrado_no_banco:
        try:
            report_payload = report if not registrado_no_banco else {"system_info": {"device_id": device_id}}
            payload = {"type": 1 if registrado_no_banco else 0, "guild_id": guild_id, "owner_id": owner_id, "status": "online", "report": report_payload}
            headers = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}
            
            response = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                if not registrado_no_banco:
                    print("🚀 Device synchronized and actively listening for commands!")
                    registrado_no_banco = True
                ultima_checagem = time.time() 
            else:
                print(f"⚠️ Vercel recusou a conexão! Código HTTP: {response.status_code}")
                print(f"Detalhes da Vercel: {response.text}")
        except Exception as e:
            print(f"📡 Erro de rede ou servidor fora do ar: {e}")
            
    time.sleep(10) # Reduzi para 10s para tentar reconectar rápido em vez de esperar 1 minuto
