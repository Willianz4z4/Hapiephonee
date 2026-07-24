import os
import sys
import subprocess
import time
import json
import uuid
import signal
from datetime import datetime

# ==========================================
# 🛡️ WATCHDOG: O CÃO DE GUARDA INTELIGENTE
# ==========================================
if os.environ.get("HAPIE_WATCHDOG") != "1":
    os.environ["HAPIE_WATCHDOG"] = "1"
    os.system("clear" if os.name == "posix" else "cls")
    print("🛡️ [Watchdog] Escudo de Resiliência ativado. O bot agora é imortal a crashs de código.")

    p_process = None

    def handle_watchdog_sigterm(signum, frame):
        if p_process:
            try: p_process.terminate()
            except: pass
        sys.exit(0)
    signal.signal(signal.SIGTERM, handle_watchdog_sigterm)

    while True:
        try:
            p_process = subprocess.Popen([sys.executable, __file__] + sys.argv[1:])
            p_process.wait()

            if p_process.returncode in (0, -15, 143):
                print("🛡️ [Watchdog] Desligamento seguro detectado (Sinal ou CTRL+C). Encerrando o nó.")
                sys.exit(0)
            elif p_process.returncode == 2:
                print("\n⚠️ [Watchdog] CONFIGURAÇÃO INCOMPLETA: Faltam os IDs de Autenticação!")
                print("👉 Execute o comando assim na primeira vez: python import.py <GUILD_ID> <OWNER_ID>")
                sys.exit(2)
            elif p_process.returncode == 3:
                print("\n⚠️ [Watchdog] ERRO DE AMBIENTE: Dispositivo sem permissão ROOT!")
                sys.exit(3)
            elif p_process.returncode == 4:
                print("\n⚠️ [Watchdog] Conexão recusada pelo Servidor Central (Shutdown).")
                sys.exit(4)
            else:
                print(f"\n💀 [Watchdog] CRASH DE CÓDIGO DETECTADO (Código {p_process.returncode})!")
                print("🔄 [Watchdog] A versão atual está quebrada. Buscando correções no GitHub em 10 segundos...")
                time.sleep(10)
                os.system("git pull > /dev/null 2>&1")
                print("🚀 [Watchdog] Tentando ressuscitar o bot com o código novo...\n")
        except KeyboardInterrupt:
            print("\n🛡️ [Watchdog] Interrompido à força pelo usuário.")
            if p_process:
                try: p_process.terminate()
                except: pass
            sys.exit(0)

# ==========================================
# 🤖 CÓDIGO NORMAL DO BOT COMEÇA AQUI
# ==========================================

def handle_child_sigterm(signum, frame):
    raise KeyboardInterrupt
signal.signal(signal.SIGTERM, handle_child_sigterm)

try:
    import requests
    import gdown
    from rich.console import Console
    from rich.panel import Panel
    from halo import Halo
except ImportError:
    os.system("pip install requests gdown rich halo colorama --upgrade -q > /dev/null 2>&1")
    import requests
    import gdown
    from rich.console import Console
    from rich.panel import Panel
    from halo import Halo

HAPIEPHONE_VERSION = "10.5 (Motor de Dados Integrado)"
console = Console()
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
sys.path.insert(0, BASE_DIR)

# ==========================================
# 🚀 GATILHO DE PRIMEIRA VIAGEM (AUTO SETUP)
# ==========================================
arquivo_comprovante = os.path.join(BASE_DIR, "setup_concluido.txt")
if not os.path.exists(arquivo_comprovante):
    console.print("\n[bold yellow]🛠️ Primeira execução detectada! Rodando a blindagem do sistema...[/bold yellow]")
    caminho_setup = os.path.join(BASE_DIR, "auto_setup.py")

    if os.path.exists(caminho_setup):
        try:
            subprocess.run([sys.executable, caminho_setup], check=True)
            with open(arquivo_comprovante, "w") as f:
                f.write("Setup de persistencia feito com sucesso em: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            console.print("[bold green]✅ Blindagem concluída com sucesso! Iniciando o sistema principal...[/bold green]\n")
        except Exception as e:
            console.print(f"[bold red]❌ Erro ao rodar a blindagem inicial: {e}[/bold red]\n")
    else:
        console.print("[bold red]⚠️ Arquivo auto_setup.py não encontrado! Pulando blindagem...[/bold red]\n")

CONFIG_FILE = os.path.join(BASE_DIR, "hapie_config.json")
FUNCTIONS_JSON_FILE = os.path.join(BASE_DIR, "functions.json")

FUNCTIONS_DIR = os.path.join(BASE_DIR, "functions")
HAPIE_APPS_DIR = os.path.join(BASE_DIR, "hapie_apps")
DATA_DIR = os.path.join(BASE_DIR, "Data")
ESSENCIAL_DIR = os.path.join(BASE_DIR, "essencial")
PROTOCOLS_DIR = os.path.join(BASE_DIR, "Protocols")
TELEMETRIA_DIR = os.path.join(BASE_DIR, "telemetria")

os.makedirs(FUNCTIONS_DIR, exist_ok=True)
os.makedirs(HAPIE_APPS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ESSENCIAL_DIR, exist_ok=True)
os.makedirs(TELEMETRIA_DIR, exist_ok=True)

init_file = os.path.join(TELEMETRIA_DIR, "__init__.py")
if not os.path.exists(init_file):
    with open(init_file, "w") as f: f.write("")

REPORT_FILE = os.path.join(DATA_DIR, "install_report.json")
APPS_JSON_FILE = os.path.join(DATA_DIR, "apps_install.json")
PENDING_TASKS_FILE = os.path.join(DATA_DIR, "pending_tasks.json")
PAYLOAD_FILE = os.path.join(DATA_DIR, "payload.json")
PENDING_APPS_FILE = os.path.join(DATA_DIR, "pending_apps.json")
REPORT_ORDERS_FILE = os.path.join(DATA_DIR, "report_orders.json")

def set_function_status(func_name, is_active):
    data = {}
    if os.path.exists(FUNCTIONS_JSON_FILE):
        try:
            with open(FUNCTIONS_JSON_FILE, "r") as f:
                data = json.load(f)
        except: pass
    data[func_name] = is_active
    try:
        with open(FUNCTIONS_JSON_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except: pass

saved_config = {}
console.print(Panel.fit(f"[bold cyan]Hapiephone Cloud Node[/bold cyan]\n[dim]Version {HAPIEPHONE_VERSION} | Powered by Evollogic[/dim]", border_style="cyan"))

if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f:
            saved_config = json.load(f)
    except: pass

if len(sys.argv) > 2:
    guild_id = str(sys.argv[1]).strip()
    owner_id = str(sys.argv[2]).strip()
elif len(sys.argv) > 1:
    guild_id = str(sys.argv[1]).strip()
    owner_id = saved_config.get("owner_id", "")
else:
    guild_id = saved_config.get("guild_id", "")
    owner_id = saved_config.get("owner_id", "")

client_token = saved_config.get("client_token", None)

if guild_id and owner_id:
    try:
        config_to_save = {"guild_id": guild_id, "owner_id": owner_id}
        if client_token: config_to_save["client_token"] = client_token
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_to_save, f)
    except: pass
else:
    console.print("[bold red]❌ Authentication IDs missing. Exiting.[/bold red]")
    sys.exit(2)

URL_WEBHOOK = "https://pandanaceous-meghann-nonincarnate.ngrok-free.dev/webhook"
report = {"installation_status": "pending", "steps": {}, "system_info": {}}

console.print("[bold yellow]⏳ Executando e verificando Protocolos...[/bold yellow]")
if os.path.exists(PROTOCOLS_DIR):
    for file_name in os.listdir(PROTOCOLS_DIR):
        if file_name.endswith(".py"):
            script_path = os.path.join(PROTOCOLS_DIR, file_name)
            try: subprocess.run([sys.executable, script_path], check=True)
            except subprocess.CalledProcessError:
                console.print(f"[bold red]❌ Falha ao executar o protocolo: {file_name}. Abortando inicialização.[/bold red]")
                sys.exit(1)

protocol_file = os.path.join(PROTOCOLS_DIR, "active_protocol.txt")
if os.path.exists(protocol_file):
    with open(protocol_file, "r") as f: current_protocol = f.read().strip()
else:
    current_protocol = f"protocol_{uuid.uuid4().hex[:8]}"
    try:
        with open(protocol_file, "w") as f: f.write(current_protocol)
    except: pass

spinner = Halo(text=f'Preparing Cloud Phone environment (Protocol: {current_protocol})...', spinner='dots')
spinner.start()
os.system("pkg update -y -q > /dev/null 2>&1 && pkg upgrade -y -q > /dev/null 2>&1")

try:
    pkg_file = os.path.join(ESSENCIAL_DIR, "reqs_pkg.txt")
    URL_PKG = "https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/essencial/reqs_pkg.txt"
    os.system(f"curl -sL {URL_PKG} -o {pkg_file} > /dev/null 2>&1")
    if os.path.exists(pkg_file):
        with open(pkg_file, "r") as f: pkgs = f.read().replace('\n', ' ')
        if pkgs.strip(): os.system(f"pkg install {pkgs} -y -q > /dev/null 2>&1")
    else: os.system("pkg install curl openssl tsu -y -q > /dev/null 2>&1")
except: pass

try:
    pip_file = os.path.join(ESSENCIAL_DIR, "reqs_pip.txt")
    URL_PIP = "https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/essencial/reqs_pip.txt"
    os.system(f"curl -sL {URL_PIP} -o {pip_file} > /dev/null 2>&1")
    if os.path.exists(pip_file): os.system(f"pip install -r {pip_file} --upgrade -q > /dev/null 2>&1")
except: pass

spinner.succeed("Environment verified and updated.")
spinner = Halo(text='Scanning hardware data...', spinner='dots')
spinner.start()

def get_prop(command):
    try: return subprocess.check_output(command, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except: return "Unknown"

def get_root_data(command):
    try: return subprocess.check_output(f"su -c '{command}'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except: return "Unknown"

def get_last_activity():
    timestamp_path = os.path.join(FUNCTIONS_DIR, "last_activity.txt")
    try:
        if os.path.exists(timestamp_path):
            with open(timestamp_path, "r") as f: return float(f.read().strip())
    except: pass
    return 0.0

try:
    has_root = True if get_root_data("echo root_ok") == "root_ok" else False
    if not has_root:
        spinner.fail("Root Permission Check Failed")
        console.print("\n[bold white on red] ❌ ERRO CRÍTICO: DISPOSITIVO SEM ROOT [/bold white on red]")
        sys.exit(3)

    model = get_prop("getprop ro.product.model")
    android_version = get_prop("getprop ro.build.version.release")
    region = get_prop("getprop persist.sys.locale")
    if region == "Unknown" or not region: region = get_prop("getprop ro.product.locale")
    cpu_abi = get_prop("getprop ro.product.cpu.abi")
    processor = "64 bits" if "64" in cpu_abi else ("32 bits" if cpu_abi != "Unknown" and cpu_abi else "Unknown")
    device_id = get_root_data("settings get secure android_id")
    if device_id == "Unknown" or not device_id: device_id = get_prop("settings get secure android_id")
    if device_id == "Unknown" or not device_id:
        id_file = os.path.join(PROTOCOLS_DIR, "ugphone_id.txt")
        if os.path.exists(id_file):
            with open(id_file, "r") as f: device_id = f.read().strip()
        else:
            device_id = "ug_" + uuid.uuid4().hex[:12]
            try:
                with open(id_file, "w") as f: f.write(device_id)
            except: pass
    if android_version != "Unknown" and "." in android_version: android_version = android_version.split(".")[0]

    report["system_info"] = {
        "root_access": has_root, "model": model, "android_version": android_version,
        "device_id": device_id, "region": region, "processor": processor, "active_protocol": current_protocol
    }
except Exception: device_id = "Unknown"

report["installation_status"] = "Completed"
spinner.succeed(f"Hardware scan complete! Device ID: \033[1m{device_id}\033[0m")

def update_client_token(new_token):
    global client_token
    if new_token and new_token != client_token:
        client_token = new_token
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f: config = json.load(f)
            config["client_token"] = client_token
            with open(CONFIG_FILE, "w") as f: json.dump(config, f)
        except: pass

spinner = Halo(text='Deploying background modules...', spinner='dots')
spinner.start()
try:
    python_path = sys.executable
    v_cache = int(time.time())

    os.system("pkill -f auto_copy.py > /dev/null 2>&1")
    copy_script_path = os.path.join(FUNCTIONS_DIR, "auto_copy.py")
    log_script_path = os.path.join(FUNCTIONS_DIR, "copy_log.txt")
    URL_COPY_PY = f"https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/functions/auto_copy.py?v={v_cache}"
    os.system(f"curl -sL '{URL_COPY_PY}' -o {copy_script_path} > /dev/null 2>&1")

    subprocess.run('su -c "appops set com.termux READ_CLIPBOARD allow" 2>/dev/null', shell=True)
    daemon_cmd = f"nohup {python_path} {copy_script_path} {device_id} {guild_id} {owner_id} '{URL_WEBHOOK}' > {log_script_path} 2>&1 &"
    os.system(daemon_cmd)

    # 🔥 OPERÁRIO DORMINDO: Só vai trabalhar quando o install.py liberar a TAG 'autocopy'
    set_function_status("auto_copy", False)

    os.system("pkill -f monitor_apps.py > /dev/null 2>&1")
    monitor_script_path = os.path.join(HAPIE_APPS_DIR, "monitor_apps.py")
    monitor_log_path = os.path.join(DATA_DIR, "monitor_log.txt")
    URL_MONITOR = f"https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/hapie_apps/monitor_apps.py?v={v_cache}"
    os.system(f"curl -sL '{URL_MONITOR}' -o {monitor_script_path} > /dev/null 2>&1")

    sensores_script_path = os.path.join(TELEMETRIA_DIR, "sensores.py")
    URL_SENSORES = f"https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/telemetria/sensores.py?v={v_cache}"
    os.system(f"curl -sL '{URL_SENSORES}' -o {sensores_script_path} > /dev/null 2>&1")

    monitor_cmd = f"nohup {python_path} {monitor_script_path} > {monitor_log_path} 2>&1 &"
    os.system(monitor_cmd)

    spinner.succeed("Invisible modules (Copy & Monitor) deployed successfully!")
except Exception as e: spinner.fail(f"Error deploying modules: {e}")

registered_in_db = False
PING_INTERVAL = 60
last_check = 0
last_applied_size = ""

console.print("\n[bold green]📡 Connection established. Awaiting commands from Control Panel...[/bold green]")
console.print("[dim](Press CTRL+C at any time to disconnect safely)[/dim]\n")

try:
    while True:
        now = time.time()
        last_action = max(last_check, get_last_activity())

        if now - last_action >= PING_INTERVAL or not registered_in_db:
            try:
                install_success = []
                install_failed = []
                order_success = []
                order_failed = []
                apps_installed_data = {}
                telemetry_data = {}

                if os.path.exists(REPORT_FILE):
                    try:
                        with open(REPORT_FILE, "r") as f: relatorio = json.load(f)
                        install_success = relatorio.get("install_success", [])
                        install_failed = relatorio.get("install_failed", [])
                        os.remove(REPORT_FILE)
                    except: pass

                if os.path.exists(REPORT_ORDERS_FILE):
                    try:
                        with open(REPORT_ORDERS_FILE, "r") as f: relatorio_ordens = json.load(f)
                        order_success = relatorio_ordens.get("success", [])
                        order_failed = relatorio_ordens.get("failed", [])
                        os.remove(REPORT_ORDERS_FILE)
                    except: pass

                if os.path.exists(APPS_JSON_FILE):
                    try:
                        with open(APPS_JSON_FILE, "r") as f: apps_installed_data = json.load(f)
                    except: pass

                try:
                    if BASE_DIR not in sys.path: sys.path.insert(0, BASE_DIR)
                    import importlib.util
                    sensores_path = os.path.join(TELEMETRIA_DIR, "sensores.py")
                    spec = importlib.util.spec_from_file_location("sensores", sensores_path)
                    sensores_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(sensores_module)
                    telemetry_data = sensores_module.coletar_telemetria_completa()
                except Exception as e: telemetry_data = {"erro": str(e)}

                payload = {
                    "type": 1 if registered_in_db else 0,
                    "guild_id": str(guild_id), "owner_id": str(owner_id),
                    "device_id": str(device_id), "protocol": str(current_protocol),
                    "status": "online", "client_token": client_token, "version": HAPIEPHONE_VERSION,
                    "install_success": install_success, "install_failed": install_failed,
                    "order_success": order_success, "order_failed": order_failed,
                    "apps_installed": apps_installed_data, "telemetry": telemetry_data
                }

                headers = {"Content-Type": "application/json", "ngrok-skip-browser-warning": "true"}
                response = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=30)

                if response.status_code == 200:
                    response_json = response.json()

                    if "ordens" in response_json:
                        lista_ordens = response_json["ordens"]
                        if isinstance(lista_ordens, list) and len(lista_ordens) > 0:
                            brain_script_path = os.path.join(FUNCTIONS_DIR, "task_orchestrator.py")
                            if os.path.exists(brain_script_path):
                                try:
                                    with open(PAYLOAD_FILE, "w") as pf: json.dump(response_json, pf)
                                    subprocess.run([sys.executable, brain_script_path, "--file", PAYLOAD_FILE], check=True)
                                except: pass
                                
                    if response_json.get("mudo") == True:
                        git_cmd = response_json.get("comando_terminal", "git pull")
                        os.system("pkill -f auto_copy.py > /dev/null 2>&1")
                        set_function_status("auto_copy", False) # Desliga no update
                        os.system("pkill -f monitor_apps.py > /dev/null 2>&1")
                        subprocess.run(git_cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        os.execv(sys.executable, ['python'] + sys.argv)

                    if "new_client_token" in response_json:
                        update_client_token(response_json["new_client_token"])

                    if response_json.get("status") == "shutdown":
                        sys.exit(4)
                        
                    registered_in_db = True
                    last_check = time.time()

                    has_tasks = any(k in response_json for k in ["install", "commands", "remove", "instalar", "comandos"])
                    if has_tasks:
                        install_script_path = os.path.join(HAPIE_APPS_DIR, "install.py")
                        with Halo(text='Updating Install Engine...', spinner='dots'):
                            v_cache_install = int(time.time())
                            URL_INSTALL = f"https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/hapie_apps/install.py?v={v_cache_install}"
                            os.system(f"curl -sL '{URL_INSTALL}' -o {install_script_path}")
                        try:
                            with open(PAYLOAD_FILE, "w") as pf: json.dump(response_json, pf)
                            subprocess.run([sys.executable, install_script_path, "--file", PAYLOAD_FILE], check=True)
                        except: pass

                sys.stdout.write(f"\r\033[K\033[90m📡 {current_protocol} | Awaiting tasks...\033[0m")
                sys.stdout.flush()
            except Exception: pass
        time.sleep(2)

except KeyboardInterrupt:
    print("\n")
    shutdown_spinner = Halo(text='Shutting down background services safely...', spinner='dots')
    shutdown_spinner.start()
    os.system("pkill -f auto_copy.py > /dev/null 2>&1")
    # 🔥 ESCREVENDO NO functions.json PARA DESLIGAR O OPERÁRIO
    set_function_status("auto_copy", False)
    os.system("pkill -f monitor_apps.py > /dev/null 2>&1")
    time.sleep(1)
    shutdown_spinner.succeed('All Evollogic services stopped.')
    console.print("[bold green]✅ Node disconnected safely. Goodbye![/bold green]\n")
    sys.exit(0)
