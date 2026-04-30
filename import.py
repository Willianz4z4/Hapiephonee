import os
import sys
import subprocess
import time

if len(sys.argv) > 2:
    guild_id = sys.argv[1]
    owner_id = sys.argv[2]
elif len(sys.argv) > 1:
    guild_id = sys.argv[1]
    owner_id = sys.argv[1] 
else:
    guild_id = ""
    owner_id = ""

URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
URL_REQS = "https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/requerimentos.txt"

report = {
    "installation_status": "pending",
    "steps": {},
    "system_info": {}
}

print("🔄 Preparing your Cloud Phone environment...")

os.system("pkg update -y -q > /dev/null 2>&1 && pkg upgrade -y -q > /dev/null 2>&1")
os.system("pkg install curl openssl -y -q > /dev/null 2>&1")
os.system("pkg install tsu -y -q > /dev/null 2>&1")

try:
    os.system(f"curl -sL {URL_REQS} -o reqs.txt > /dev/null 2>&1")
    pip_result = os.system("pip install -r reqs.txt -q > /dev/null 2>&1")
    report["steps"]["pip_packages"] = "Success" if pip_result == 0 else "Failed"
except:
    report["steps"]["pip_packages"] = "Failed"

def get_data(command):
    try:
        return subprocess.check_output(f"su -c '{command}'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except:
        return "Unknown"

try:
    root_test = get_data("echo root_ok")
    has_root = True if root_test == "root_ok" else False
except:
    has_root = False

try:
    model = get_data("getprop ro.product.model")
    android_version = get_data("getprop ro.build.version.release")
    device_id = get_data("settings get secure android_id")
    
    region = get_data("getprop persist.sys.locale")
    if region == "Unknown" or not region:
        region = get_data("getprop ro.product.locale")
        
    cpu_abi = get_data("getprop ro.product.cpu.abi")
    processor = "64 bits" if "64" in cpu_abi else ("32 bits" if cpu_abi != "Unknown" and cpu_abi else "Unknown")

    report["system_info"] = {
        "root_access": has_root,
        "model": model,
        "android_version": android_version,
        "device_id": device_id,
        "region": region,
        "processor": processor
    }
    report["steps"]["data_collection"] = "Success"
except:
    report["steps"]["data_collection"] = "Failed"
    device_id = "Unknown"

report["installation_status"] = "Completed"
print("✅ Configuration finished! Connecting to control panel...")

print("🚀 Iniciando serviços em background (Auto-Copy)...")
try:
    subprocess.Popen([sys.executable, "functions/copy.py", device_id, guild_id], 
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL)
    print("✅ Módulo Auto-Copy rodando em segundo plano.")
except Exception as e:
    print(f"⚠️ Aviso: Não foi possível iniciar o Auto-Copy. Erro: {e}")

registrado_no_banco = False
INTERVALO_PING = 1200 # 20 minutos
ultima_checagem = 0 

def obter_ultima_atividade():
    try:
        if os.path.exists("last_activity.txt"):
            return os.path.getmtime("last_activity.txt")
    except:
        pass
    return 0

try:
    import requests
except ImportError:
    os.system("pip install requests -q > /dev/null 2>&1")
    import requests

while True:
    agora = time.time()
    ultima_acao = max(ultima_checagem, obter_ultima_atividade())
    
    # Executa se já passou 20 minutos da última ação do celular OU se ainda não se registrou
    if agora - ultima_acao >= INTERVALO_PING or not registrado_no_banco:
        try:
            # O Ping leve vai vazio, exceto pelo device_id para o Flask conseguir atualizar a data no DB
            report_payload = report if not registrado_no_banco else {"system_info": {"device_id": device_id}}
            
            payload = {
                "type": 1 if registrado_no_banco else 0,
                "guild_id": guild_id,
                "owner_id": owner_id,
                "status": "online",
                "report": report_payload
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": AUTH_SECRET
            }
            
            response = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                if not registrado_no_banco:
                    print("🚀 Device synchronized and actively listening for commands!")
                    registrado_no_banco = True
                
                ultima_checagem = time.time() 
                
                try:
                    data = response.json()
                    comando_recebido = data.get("command")
                    
                    if comando_recebido:
                        print(f"📥 Executing received command: {comando_recebido}")
                        subprocess.Popen(comando_recebido, shell=True)
                except ValueError:
                    pass 
                    
            else:
                print(f"⚠️ Server busy ({response.status_code})...")
                
        except Exception as e:
            print("📡 No connection or network error. Retrying...")
    
    # Checa a cada 60 segundos
    time.sleep(60)
