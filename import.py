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

CONFIG_FILE = os.path.join(BASE_DIR, "hapie_config.json")
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
    with open(init_file, "w") as f:
        f.write("")

REPORT_FILE = os.path.join(DATA_DIR, "install_report.json")
APPS_JSON_FILE = os.path.join(DATA_DIR, "apps_install.json")
PENDING_TASKS_FILE = os.path.join(DATA_DIR, "pending_tasks.json")
PAYLOAD_FILE = os.path.join(DATA_DIR, "payload.json")

# 🔥 ARQUIVOS DE FILAS: Declarando pending_apps.json e report_orders.json
PENDING_APPS_FILE = os.path.join(DATA_DIR, "pending_apps.json")
REPORT_ORDERS_FILE = os.path.join(DATA_DIR, "report_orders.json")

saved_config = {}
console.print(Panel.fit(f"[bold cyan]Hapiephone Cloud Node[/bold cyan]\n[dim]Version {HAPIEPHONE_VERSION} | Powered by Evollogic[/dim]", border_style="cyan"))

if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f:
            saved_config = json.load(f)
    except:
        pass

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
        if client_token:
            config_to_save["client_token"] = client_token
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_to_save, f)
    except:
        pass
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
            try:
                subprocess.run([sys.executable, script_path], check=True)
            except subprocess.CalledProcessError:
                console.print(f"[bold red]❌ Falha ao executar o protocolo: {file_name}. Abortando inicialização.[/bold red]")
                sys.exit(1)
else:
    console.print("[bold red]❌ Pasta 'Protocols' não encontrada![/bold red]")

protocol_file = os.path.join(PROTOCOLS_DIR, "active_protocol.txt")
if os.path.exists(protocol_file):
    with open(protocol_file, "r") as f:
        current_protocol = f.read().strip()
else:
    current_protocol = f"protocol_{uuid.uuid4().hex[:8]}"
    try:
        with open(protocol_file, "w") as f:
            f.write(current_protocol)
    except:
        pass

spinner = Halo(text=f'Preparing Cloud Phone environment (Protocol: {current_protocol})...', spinner='dots')
spinner.start()
os.system("pkg update -y -q > /dev/null 2>&1 && pkg upgrade -y -q > /dev/null 2>&1")

try:
    pkg_file = os.path.join(ESSENCIAL_DIR, "reqs_pkg.txt")
    URL_PKG = "https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/essencial/reqs_pkg.txt"
    os.system(f"curl -sL {URL_PKG} -o {pkg_file} > /dev/null 2>&1")
    if os.path.exists(pkg_file):
        with open(pkg_file, "r") as f:
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
    pip_file = os.path.join(ESSENCIAL_DIR, "reqs_pip.txt")
    URL_PIP = "https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/essencial/reqs_pip.txt"
    os.system(f"curl -sL {URL_PIP} -o {pip_file} > /dev/null 2>&1")
    if os.path.exists(pip_file):
        os.system(f"pip install -r {pip_file} --upgrade -q > /dev/null 2>&1")
        report["steps"]["pip_packages"] = "Success"
    else:
        report["steps"]["pip_packages"] = "Skipped"
except:
    report["steps"]["pip_packages"] = "Failed"

spinner.succeed("Environment verified and updated.")
spinner = Halo(text='Scanning hardware data...', spinner='dots')
spinner.start()

def get_prop(command):
    try:
        return subprocess.check_output(command, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except:
        return "Unknown"

def get_root_data(command):
    try:
        return subprocess.check_output(f"su -c '{command}'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except:
        return "Unknown"

def get_last_activity():
    timestamp_path = os.path.join(FUNCTIONS_DIR, "last_activity.txt")
    try:
        if os.path.exists(timestamp_path):
            with open(timestamp_path, "r") as f:
                return float(f.read().strip())
        return 0.0
    except Exception:
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
    if region == "Unknown" or not region:
        region = get_prop("getprop ro.product.locale")

    cpu_abi = get_prop("getprop ro.product.cpu.abi")
    processor = "64 bits" if "64" in cpu_abi else ("32 bits" if cpu_abi != "Unknown" and cpu_abi else "Unknown")

    device_id = get_root_data("settings get secure android_id")
    if device_id == "Unknown" or not device_id:
        device_id = get_prop("settings get secure android_id")

    if device_id == "Unknown" or not device_id:
        id_file = os.path.join(PROTOCOLS_DIR, "ugphone_id.txt")
        if os.path.exists(id_file):
            with open(id_file, "r") as f:
                device_id = f.read().strip()
        else:
            device_id = "ug_" + uuid.uuid4().hex[:12]
            try:
                with open(id_file, "w") as f:
                    f.write(device_id)
            except:
                pass

    if android_version != "Unknown" and "." in android_version:
        android_version = android_version.split(".")[0]

    report["system_info"] = {
        "root_access": has_root,
        "model": model,
        "android_version": android_version,
        "device_id": device_id,
        "region": region,
        "processor": processor,
        "active_protocol": current_protocol
    }
    report["steps"]["data_collection"] = "Success"
except Exception as e:
    report["steps"]["data_collection"] = "Failed"
    device_id = "Unknown"

report["installation_status"] = "Completed"
spinner.succeed(f"Hardware scan complete! Device ID: \033[1m{device_id}\033[0m")

def update_client_token(new_token):
    global client_token
    if new_token and new_token != client_token:
        client_token = new_token
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
            config["client_token"] = client_token
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)
            console.print("\n[bold yellow]🔑 [AUTH] New security license installed on the device.[/bold yellow]")
        except Exception:
            pass

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
    daemon_cmd = f"nohup {python_path} {copy_script_path} {device_id} {guild_id} {owner_id} > {log_script_path} 2>&1 &"
    os.system(daemon_cmd)

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
except Exception as e:
    spinner.fail(f"Error deploying modules: {e}")

spinner.succeed("Persistent boot skipped (UgPhone compatibility module active).")
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
                        with open(REPORT_FILE, "r", encoding="utf-8") as f:
                            relatorio = json.load(f)
                        install_success = relatorio.get("install_success", [])
                        install_failed = relatorio.get("install_failed", [])
                        os.remove(REPORT_FILE)
                    except Exception:
                        pass
                
                # 📦 Coletando relatórios de ORDENS para enviar ao servidor
                if os.path.exists(REPORT_ORDERS_FILE):
                    try:
                        with open(REPORT_ORDERS_FILE, "r", encoding="utf-8") as f:
                            relatorio_ordens = json.load(f)
                        order_success = relatorio_ordens.get("success", [])
                        order_failed = relatorio_ordens.get("failed", [])
                        os.remove(REPORT_ORDERS_FILE)
                    except Exception:
                        pass

                if os.path.exists(APPS_JSON_FILE):
                    try:
                        with open(APPS_JSON_FILE, "r", encoding="utf-8") as f:
                            apps_installed_data = json.load(f)
                    except Exception:
                        pass

                try:
                    if BASE_DIR not in sys.path:
                        sys.path.insert(0, BASE_DIR)
                    import importlib.util
                    sensores_path = os.path.join(TELEMETRIA_DIR, "sensores.py")
                    spec = importlib.util.spec_from_file_location("sensores", sensores_path)
                    sensores_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(sensores_module)
                    telemetry_data = sensores_module.coletar_telemetria_completa()
                except Exception as e:
                    telemetry_data = {"erro": f"Falha na importacao/execucao: {str(e)}"}

                payload = {
                    "type": 1 if registered_in_db else 0,
                    "guild_id": str(guild_id),
                    "owner_id": str(owner_id),
                    "device_id": str(device_id),
                    "protocol": str(current_protocol),
                    "status": "online",
                    "report": report,
                    "client_token": client_token,
                    "version": HAPIEPHONE_VERSION,
                    "install_success": install_success,
                    "install_failed": install_failed,
                    "order_success": order_success,     # 👈 INJETADO NO PAYLOAD
                    "order_failed": order_failed,       # 👈 INJETADO NO PAYLOAD
                    "apps_installed": apps_installed_data,
                    "telemetry": telemetry_data
                }

                headers = {
                    "Content-Type": "application/json",
                    "ngrok-skip-browser-warning": "true"
                }
                response = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=30)

                if response.status_code == 200:
                    response_json = response.json()
                    
                    if "radius_width" in response_json and "radius_height" in response_json:
                        try:
                            rw = int(float(response_json["radius_width"]))
                            rh = int(float(response_json["radius_height"]))
                            new_size = f"{rw}x{rh}"

                            if new_size != last_applied_size:
                                console.print(f"\n[bold cyan]📏 Ajustando tamanho/proporção da tela para: {new_size}[/bold cyan]")
                                os.system(f"su -c 'wm size {new_size}' > /dev/null 2>&1")
                                last_applied_size = new_size
                        except Exception as e:
                            pass

                    # ==========================================
                    # NOVO BLOCO: MOTOR DE DADOS & UGCLONE
                    # ==========================================
                    if "data_command" in response_json:
                        cmd_data = response_json["data_command"]
                        action_type = cmd_data.get("action")
                        pacote_alvo = cmd_data.get("package")
                        url_servidor = cmd_data.get("url")
                        
                        if pacote_alvo and url_servidor:
                            try:
                                if HAPIE_APPS_DIR not in sys.path:
                                    sys.path.insert(0, HAPIE_APPS_DIR)
                                from apps_data import data_save, data_export, data_inject, add_ugclone_config

                                if action_type == "export":
                                    console.print(f"\n[bold magenta]📦 [DATA] Servidor ordenou a EXPORTAÇÃO dos dados de: {pacote_alvo}[/bold magenta]")
                                    if data_save(pacote_alvo):
                                        data_export(pacote_alvo, url_servidor, owner_id, device_id)

                                elif action_type == "inject":
                                    console.print(f"\n[bold magenta]💉 [DATA] Servidor ordenou a INJEÇÃO inteligente de dados em: {pacote_alvo}[/bold magenta]")
                                    data_inject(pacote_alvo, url_servidor)

                                elif action_type == "update_ugclone":
                                    console.print(f"\n[bold cyan]🧠 [UGCLONE] Lendo configurações para {pacote_alvo}...[/bold cyan]")
                                    json_path = os.path.join(DATA_DIR, f"ug_{pacote_alvo}.json")
                                    os.system(f"curl -sL '{url_servidor}' -o {json_path} > /dev/null 2>&1")
                                    if os.path.exists(json_path):
                                        with open(json_path, "r", encoding="utf-8") as f:
                                            ug_data = json.load(f)

                                        if "tasks" in ug_data:
                                            for ug_task in ug_data["tasks"]:
                                                alvo = ug_task.get("target_pkg")
                                                configs = ug_task.get("settings")
                                                if alvo and configs:
                                                    add_ugclone_config(alvo, configs)
                                        os.remove(json_path)
                                        console.print("[bold green]✅ Master do UGClone atualizado via JSON com sucesso![/bold green]")
                            except Exception as e:
                                console.print(f"\n[bold red]❌ Erro no motor de dados/ugclone: {e}[/bold red]")

                    if "upload_queue" in response_json:
                        lista_pendentes = response_json["upload_queue"]
                        if isinstance(lista_pendentes, list) and len(lista_pendentes) > 0:
                            with open(PENDING_TASKS_FILE, "w", encoding="utf-8") as pf:
                                json.dump(lista_pendentes, pf, indent=4)
                            console.print(f"\n[bold yellow] 📦 [FILA] Recebidas {len(lista_pendentes)} tarefas de extração de APK.[/bold yellow]")

                    if "pending_apps" in response_json:
                        lista_pending_apps = response_json["pending_apps"]
                        if isinstance(lista_pending_apps, list) and len(lista_pending_apps) > 0:
                            with open(PENDING_APPS_FILE, "w", encoding="utf-8") as pf:
                                json.dump(lista_pending_apps, pf, indent=4)
                            console.print(f"\n[bold yellow] 📥 [FILA] Recebidas {len(lista_pending_apps)} tarefas do UGClone/Automações.[/bold yellow]")

                    # 🚀 LÓGICA DAS ORDENS 
                    if "ordens" in response_json:
                        lista_ordens = response_json["ordens"]
                        if isinstance(lista_ordens, list) and len(lista_ordens) > 0:
                            console.print(f"\n[bold yellow]🚀 [ORDENS] Recebidas {len(lista_ordens)} novas ordens do servidor![/bold yellow]")

                    if response_json.get("mudo") == True:
                        git_cmd = response_json.get("comando_terminal", "git pull")
                        target_ver = response_json.get("nova_versao", "Desconhecida")

                        console.print(f"\n[bold yellow]🔄 UPDATE DETECTADO: O servidor ordenou a versão {target_ver}![/bold yellow]")
                        os.system("pkill -f auto_copy.py > /dev/null 2>&1")
                        os.system("pkill -f monitor_apps.py > /dev/null 2>&1")

                        spinner_git = Halo(text='Puxando atualizações via Git...', spinner='dots')
                        spinner_git.start()
                        try:
                            subprocess.run(git_cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            spinner_git.succeed("Código atualizado com sucesso!")
                        except Exception as e:
                            spinner_git.fail(f"Falha ao executar o Git: {e}")

                        console.print("[bold green]✅ Reiniciando o node para aplicar o novo código...[/bold green]\n")
                        time.sleep(1.5)
                        os.execv(sys.executable, ['python'] + sys.argv)

                    if "new_client_token" in response_json:
                        update_client_token(response_json["new_client_token"])

                    if response_json.get("status") == "shutdown":
                        print("\n")
                        console.print(f"[bold red]🛑 Server refused connection: {response_json.get('reason', 'Unknown reason')}[/bold red]")
                        sys.exit(4)
                        
                    if not registered_in_db:
                        registered_in_db = True

                    last_check = time.time()

                    # 🛠️ GATILHO: Agora ele aciona o motor de instalação se vier "ordens"
                    has_tasks = any(k in response_json for k in ["install", "commands", "remove", "instalar", "comandos", "ordens"])
                    
                    if has_tasks:
                        install_script_path = os.path.join(HAPIE_APPS_DIR, "install.py")
                        with Halo(text='Updating Install Engine...', spinner='dots'):
                            v_cache_install = int(time.time())
                            URL_INSTALL = f"https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/hapie_apps/install.py?v={v_cache_install}"
                            os.system(f"curl -sL '{URL_INSTALL}' -o {install_script_path}")
                        try:
                            console.print("\n[bold yellow]⚡ Triggering installation engine...[/bold yellow]")
                            with open(PAYLOAD_FILE, "w", encoding="utf-8") as pf:
                                json.dump(response_json, pf)
                            subprocess.run([sys.executable, install_script_path, "--file", PAYLOAD_FILE], check=True)
                        except Exception as err_install:
                            console.print(f"[bold red]❌ O motor de instalacao travou: {err_install}[/bold red]")

                current_time = datetime.now().strftime("%H:%M:%S")
                sys.stdout.write(f"\r\033[K\033[90m📡 {current_protocol} | Last connection: {current_time} - Awaiting tasks...\033[0m")
                sys.stdout.flush()
            except Exception as e:
                sys.stdout.write(f"\r\033[K")
                console.print(f"[bold red]❌ Falha na conexão com o Webhook: {e}[/bold red]")

        time.sleep(2)

except KeyboardInterrupt:
    print("\n")
    shutdown_spinner = Halo(text='Shutting down background services safely...', spinner='dots')
    shutdown_spinner.start()
    os.system("pkill -f auto_copy.py > /dev/null 2>&1")
    os.system("pkill -f monitor_apps.py > /dev/null 2>&1")
    time.sleep(1)
    shutdown_spinner.succeed('All Evollogic services stopped.')
    console.print("[bold green]✅ Node disconnected safely. Goodbye![/bold green]\n")
    sys.exit(0)
