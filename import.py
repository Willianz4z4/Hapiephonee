import os
import sys
import subprocess
import time
import json

try:
    import requests
except ImportError:
    print("📦 Installing network dependencies...")
    os.system("pip install requests --upgrade -q > /dev/null 2>&1")
    import requests

try:
    import gdown
except ImportError:
    print("📦 Installing download engine...")
    os.system("pip install gdown --upgrade -q > /dev/null 2>&1")
    import gdown

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

# Recupera o Token JWT do arquivo de configuração (se existir)
client_token = saved_config.get("client_token", None)

if guild_id and owner_id:
    try:
        # Apenas salva a configuração se houver IDs válidos
        config_to_save = {"guild_id": guild_id, "owner_id": owner_id}
        if client_token:
            config_to_save["client_token"] = client_token
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_to_save, f)
    except:
        pass
else:
    print("❌ IDs missing. Exiting.")
    sys.exit(1)

URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
# AUTH_SECRET foi removida daqui, agora usamos o client_token (JWT) dinâmico

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
        os.system("pip install -r reqs_pip.txt --upgrade -q > /dev/null 2>&1")
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

# FUNÇÃO PARA SALVAR O NOVO TOKEN QUANDO ELE CHEGAR DO VERCEL
def atualizar_client_token(novo_token):
    global client_token
    if novo_token and novo_token != client_token:
        client_token = novo_token
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            config["client_token"] = client_token
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)
            print("🔑 [AUTH] Nova licença de segurança instalada no aparelho.")
        except Exception as e:
            print(f"⚠️ [AUTH] Erro ao salvar o novo token: {e}")

print("🚀 Starting background services (Auto-Copy)...")
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
    
    # O auto_copy agora deve ler o JSON ou receber o TOKEN por argumento.
    # Por padrão ele pode ser configurado para ler o 'hapie_config.json' diretamente, 
    # pois o token é dinâmico e muda.
    comando_daemon = f"nohup {caminho_python} {caminho_script} {device_id} {guild_id} {owner_id} > functions/copy_log.txt 2>&1 &"
    
    os.system(comando_daemon)
    print(f"✅ Invisible module deployed successfully! (Logs at functions/copy_log.txt)")
except Exception as e:
    print(f"⚠️ Error deploying module: {e}")

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
            
            # --- O NOVO PAYLOAD AGORA ENVIA A CHAVE PARA O VERCEL VERIFICAR ---
            payload = {
                "type": 1 if registrado_no_banco else 0, 
                "guild_id": guild_id, 
                "owner_id": owner_id, 
                "device_id": device_id,  # Necessário para Vercel validar
                "status": "online", 
                "report": report_payload,
                "client_token": client_token # Aqui vai a chave de 15 dias do celular!
            }
            
            # A autorização antiga foi removida do header. Só enviamos JSON puro.
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                resposta_json = response.json()
                
                # Se o Vercel devolveu um token novo, a gente atualiza o arquivo
                if "new_client_token" in resposta_json:
                    atualizar_client_token(resposta_json["new_client_token"])
                
                # Se o servidor ordenou o desligamento
                if resposta_json.get("status") == "shutdown":
                     print(f"🛑 [SISTEMA] Servidor recusou a conexão: {resposta_json.get('motivo')}")
                     print("Encerrando serviços...")
                     sys.exit(1)
                     
                if not registrado_no_banco:
                    print("🚀 Device synchronized and actively listening for commands!")
                    registrado_no_banco = True
                    
                ultima_checagem = time.time() 
            else:
                print(f"⚠️ Connection refused by Vercel! HTTP Code: {response.status_code}")
                # Exibe detalhes apenas se for erro claro, para evitar encher a tela
                if response.status_code != 502: 
                    try:
                        print(f"Motivo: {response.json().get('motivo', 'Unknown Error')}")
                    except:
                        pass
        except Exception as e:
            print(f"📡 Network error or server down: {e}")
            
    time.sleep(10)
