import os
import sys
import subprocess
import time
import json
import uuid
import signal
import threading
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
sys.path.insert(0, BASE_DIR)

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

console = Console()
HAPIEPHONE_VERSION = "10.6 (Auto Input Engine + Cyber Security)"

if os.environ.get("HAPIE_WATCHDOG") != "1":
    os.environ["HAPIE_WATCHDOG"] = "1"
    os.system("clear" if os.name == "posix" else "cls")

    console.print(Panel.fit(f"[bold cyan]Hapiephone Cloud Node[/bold cyan]\n[dim]Version {HAPIEPHONE_VERSION} | Powered by Evollogic[/dim]", border_style="cyan"))

    spinner = Halo(text='[Watchdog] Escudo de Resiliência ativado. Checando atualizações...', spinner='dots', color='blue')
    spinner.start()

    subprocess.run(["bash", "update.sh"], cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    spinner.succeed('[Watchdog] Sistema central atualizado e purificado.')

    CACHE_FILE = os.path.join(BASE_DIR, "security_system", ".hash_cache.json")
    if not os.path.exists(CACHE_FILE):
        spinner = Halo(text='[Watchdog] DNA ausente. Gerando Matriz Oficial...', spinner='dots', color='yellow')
        spinner.start()
        subprocess.run([sys.executable, "security_system/build_hashes.py"], cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        spinner.succeed('🔒 Hapiephone HASH DNA atualizado! Arquivos assinados com sucesso.')

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
                console.print("\n[bold green]🛡️ [Watchdog] Desligamento seguro detectado. Encerrando o nó.[/bold green]")
                sys.exit(0)
            elif p_process.returncode == 2:
                console.print("\n[bold yellow]⚠️ [Watchdog] CONFIGURAÇÃO INCOMPLETA: Faltam os IDs de Autenticação![/bold yellow]")
                sys.exit(2)
            elif p_process.returncode == 3:
                console.print("\n[bold red]⚠️ [Watchdog] ERRO DE AMBIENTE: Dispositivo sem permissão ROOT![/bold red]")
                sys.exit(3)
            elif p_process.returncode == 4:
                console.print("\n[bold yellow]⚠️ [Watchdog] Conexão recusada pelo Servidor Central (Shutdown).[/bold yellow]")
                sys.exit(4)
            elif p_process.returncode == 5:
                console.print("\n[bold red]⚠️ [Watchdog] FALHA DE SEGURANÇA (Lockdown) detectada pelo C-Level![/bold red]")
                spinner = Halo(text='[Watchdog] Forçando limpeza extrema via Bash...', spinner='dots', color='red')
                spinner.start()
                subprocess.run(["bash", "update.sh"], cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(3)
                spinner.succeed('[Watchdog] Ameaça neutralizada. Tentando reinício...')
            else:
                console.print(f"\n[bold red]💀 [Watchdog] CRASH DE CÓDIGO DETECTADO (Código {p_process.returncode})![/bold red]")
                spinner = Halo(text='[Watchdog] Buscando correções automáticas...', spinner='dots', color='yellow')
                spinner.start()
                time.sleep(5)
                subprocess.run(["bash", "update.sh"], cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                spinner.succeed('🚀 [Watchdog] Tentando ressuscitar o bot com o código novo...\n')
        except KeyboardInterrupt:
            if p_process:
                try: p_process.terminate()
                except: pass
            sys.exit(0)

def handle_child_sigterm(signum, frame):
    raise KeyboardInterrupt
signal.signal(signal.SIGTERM, handle_child_sigterm)

try:
    from security_system.core import gerar_assinatura_hmac, obter_dna_dispositivo
except ImportError:
    console.print("\n[bold red]💀 [Security] Módulo de segurança compilado (core.so) ausente ou corrompido.[/bold red]")
    sys.exit(5)
except Exception as e:
    console.print(f"\n[bold red]💀 [Security] LOCKDOWN ATIVADO: Integridade violada! ({e})[/bold red]")
    sys.exit(5)

arquivo_comprovante = os.path.join(BASE_DIR, "setup_concluido.txt")
if not os.path.exists(arquivo_comprovante):
    spinner = Halo(text='🛠️ Primeira execução detectada! Rodando blindagem do sistema...', spinner='dots', color='cyan')
    spinner.start()
    caminho_setup = os.path.join(BASE_DIR, "auto_setup.py")
    if os.path.exists(caminho_setup):
        try:
            subprocess.run([sys.executable, caminho_setup], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            with open(arquivo_comprovante, "w") as f:
                f.write("Setup de persistencia feito com sucesso em: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            spinner.succeed('✅ Blindagem inicial concluída com sucesso!')
        except Exception as e:
            spinner.fail(f'❌ Erro ao rodar a blindagem inicial: {e}')
    else:
        spinner.warn('⚠️ Arquivo auto_setup.py não encontrado! Pulando blindagem...')
    print("")

def verificar_e_instalar_apps_essenciais():
    apps_essenciais = {
        "com.termux.boot": "install_termux_boot",
        "com.termux.api": "install_single_plugin",
        "com.termux.widget": "install_single_plugin",
        "com.termux.float": "install_single_plugin",
        "com.termux.tasker": "install_single_plugin",
        "com.termux.styling": "install_single_plugin",
        "com.termux.gui": "install_single_plugin"
    }

    spinner_apps = Halo(text='🔍 Verificando integridade dos plugins essenciais...', spinner='dots', color='cyan')
    spinner_apps.start()

    check_installed = subprocess.run("su -c 'pm list packages'", shell=True, capture_output=True, text=True).stdout

    faltando = []
    for pkg, func in apps_essenciais.items():
        if pkg not in check_installed:
            faltando.append((pkg, func))

    if faltando:
        spinner_apps.warn(f"⚠️ {len(faltando)} plugin(s) faltando no Android! Invocando auto_setup.py...")
        caminho_setup = os.path.join(BASE_DIR, "auto_setup.py")
        if os.path.exists(caminho_setup):
            try:
                import auto_setup
                for pkg, func_name in faltando:
                    spinner_inst = Halo(text=f'📦 Instalando plugin ausente: {pkg}...', spinner='dots', color='yellow')
                    spinner_inst.start()
                    if hasattr(auto_setup, func_name):
                        funcao_alvo = getattr(auto_setup, func_name)
                        if func_name == "install_single_plugin":
                            funcao_alvo(pkg)
                        else:
                            funcao_alvo()
                        spinner_inst.succeed(f'✅ {pkg} instalado e configurado.')
                    else:
                        if hasattr(auto_setup, "install_and_hide_plugins"):
                            auto_setup.install_and_hide_plugins()
                            spinner_inst.succeed('✅ Plugins atualizados via auto_setup.')
                            break
            except Exception as e:
                console.print(f"[bold red]❌ Erro ao instalar plugin individual: {e}[/bold red]")
    else:
        spinner_apps.succeed("✅ Todos os plugins essenciais já estão instalados!")

if not os.path.exists(os.path.join(BASE_DIR, "setup_concluido.txt")):
    verificar_e_instalar_apps_essenciais()

CONFIG_FILE = os.path.join(BASE_DIR, "hapie_config.json")
FUNCTIONS_JSON_FILE = os.path.join(BASE_DIR, "functions.json")
FUNCTIONS_DIR = os.path.join(BASE_DIR, "functions")
HAPIE_APPS_DIR = os.path.join(BASE_DIR, "hapie_apps")
DATA_DIR = os.path.join(BASE_DIR, "Data")
ESSENCIAL_DIR = os.path.join(BASE_DIR, "essencial")
PROTOCOLS_DIR = os.path.join(BASE_DIR, "Protocols")
TELEMETRIA_DIR = os.path.join(BASE_DIR, "telemetria")

for dr in [FUNCTIONS_DIR, HAPIE_APPS_DIR, DATA_DIR, ESSENCIAL_DIR, TELEMETRIA_DIR]:
    os.makedirs(dr, exist_ok=True)

init_file = os.path.join(TELEMETRIA_DIR, "__init__.py")
if not os.path.exists(init_file):
    with open(init_file, "w") as f: f.write("")

REPORT_FILE = os.path.join(DATA_DIR, "install_report.json")
APPS_JSON_FILE = os.path.join(DATA_DIR, "apps_install.json")
PENDING_TASKS_FILE = os.path.join(DATA_DIR, "pending_tasks.json")
PAYLOAD_FILE = os.path.join(DATA_DIR, "payload.json")
PAYLOAD_INSTALL_FILE = os.path.join(DATA_DIR, "payload_install.json")
PENDING_APPS_FILE = os.path.join(DATA_DIR, "pending_apps.json")
REPORT_ORDERS_FILE = os.path.join(DATA_DIR, "report_orders.json")
CAMPOS_FILE = os.path.join(DATA_DIR, "campos_mapeados.json") # Mantido apenas para evitar erro se outras partes chamarem, mas n lido.

def set_function_status(func_name, is_active):
    data = {}
    if os.path.exists(FUNCTIONS_JSON_FILE):
        try:
            with open(FUNCTIONS_JSON_FILE, "r") as f: data = json.load(f)
        except: pass
    data[func_name] = is_active
    try:
        with open(FUNCTIONS_JSON_FILE, "w") as f: json.dump(data, f, indent=4)
    except: pass

saved_config = {}

if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f: saved_config = json.load(f)
    except: pass

if len(sys.argv) > 2:
    guild_id, owner_id = str(sys.argv[1]).strip(), str(sys.argv[2]).strip()
elif len(sys.argv) > 1:
    guild_id, owner_id = str(sys.argv[1]).strip(), saved_config.get("owner_id", "")
else:
    guild_id, owner_id = saved_config.get("guild_id", ""), saved_config.get("owner_id", "")

client_token = saved_config.get("client_token", None)

if guild_id and owner_id:
    try:
        config_to_save = {"guild_id": guild_id, "owner_id": owner_id}
        if client_token: config_to_save["client_token"] = client_token
        with open(CONFIG_FILE, "w") as f: json.dump(config_to_save, f)
    except: pass
else:
    console.print("[bold red]❌ Authentication IDs missing. Exiting.[/bold red]")
    sys.exit(2)

URL_WEBHOOK = "https://pandanaceous-meghann-nonincarnate.ngrok-free.dev/webhook"
report = {"installation_status": "pending", "steps": {}, "system_info": {}}

spinner = Halo(text='Executando e verificando Protocolos...', spinner='dots', color='cyan')
spinner.start()

if os.path.exists(PROTOCOLS_DIR):
    for file_name in os.listdir(PROTOCOLS_DIR):
        if file_name.endswith(".py"):
            script_path = os.path.join(PROTOCOLS_DIR, file_name)
            try: subprocess.run([sys.executable, script_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                spinner.fail(f'❌ Falha ao executar o protocolo: {file_name}. Abortando.')
                sys.exit(1)

protocol_file = os.path.join(PROTOCOLS_DIR, "active_protocol.txt")
if os.path.exists(protocol_file):
    with open(protocol_file, "r") as f: current_protocol = f.read().strip()
else:
    current_protocol = f"protocol_{uuid.uuid4().hex[:8]}"
    try:
        with open(protocol_file, "w") as f: f.write(current_protocol)
    except: pass

spinner.text = f'Preparing Cloud Phone environment (Protocol: {current_protocol})...'
os.system("pkg update -y -q > /dev/null 2>&1 && pkg upgrade -y -q > /dev/null 2>&1")

try:
    pkg_file, URL_PKG = os.path.join(ESSENCIAL_DIR, "reqs_pkg.txt"), "https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/essencial/reqs_pkg.txt"
    os.system(f"curl -sL {URL_PKG} -o {pkg_file} > /dev/null 2>&1")
    if os.path.exists(pkg_file):
        with open(pkg_file, "r") as f: pkgs = f.read().replace('\n', ' ')
        if pkgs.strip(): os.system(f"pkg install {pkgs} -y -q > /dev/null 2>&1")
    else: os.system("pkg install curl openssl tsu -y -q > /dev/null 2>&1")
except: pass

try:
    pip_file, URL_PIP = os.path.join(ESSENCIAL_DIR, "reqs_pip.txt"), "https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/essencial/reqs_pip.txt"
    os.system(f"curl -sL {URL_PIP} -o {pip_file} > /dev/null 2>&1")
    if os.path.exists(pip_file): os.system(f"pip install -r {pip_file} --upgrade -q > /dev/null 2>&1")
except: pass

spinner.succeed("Environment verified and updated.")

spinner = Halo(text='Scanning hardware data...', spinner='dots', color='magenta')
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

def radar_de_updates():
    while True:
        time.sleep(300)
        try:
            resultado = subprocess.run(["bash", "update.sh"], cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if resultado.returncode == 10:
                sys.stdout.write("\r\033[K")
                console.print("\n[bold green][♻️] O Bash confirmou a atualização. Reiniciando o sistema...[/bold green]")
                os.execv(sys.executable, ['python'] + sys.argv)
        except Exception:
            pass

thread_radar = threading.Thread(target=radar_de_updates, daemon=True)
thread_radar.start()

spinner = Halo(text='Deploying background modules...', spinner='dots', color='blue')
spinner.start()
try:
    python_path = sys.executable
    v_cache = int(time.time())

    os.system("pkill -f auto_copy.py > /dev/null 2>&1")
    copy_script_path = os.path.join(FUNCTIONS_DIR, "auto_copy.py")
    log_script_path = os.path.join(FUNCTIONS_DIR, "copy_log.txt")
    URL_COPY_PY = f"https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/functions/auto_copy.py?v={v_cache}"
    os.system(f"curl -sL '{URL_COPY_PY}' -o {copy_script_path} > /dev/null 2>&1")

    termux_tasker_script = os.path.join(BASE_DIR, "termux_plugin", "termux_tasker.py")
    if os.path.exists(termux_tasker_script):
        subprocess.run([sys.executable, termux_tasker_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    subprocess.run('su -c "appops set com.termux READ_CLIPBOARD allow" 2>/dev/null', shell=True)
    daemon_cmd = f"nohup {python_path} {copy_script_path} {device_id} {guild_id} {owner_id} '{URL_WEBHOOK}' > {log_script_path} 2>&1 &"
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

registered_in_db = False
PING_INTERVAL = 60
last_check = 0

console.print("\n[bold green]📡 Connection established. Awaiting commands from Control Panel...[/bold green]")
console.print("[dim](Press CTRL+C at any time to disconnect safely)[/dim]\n")

try:
    while True:
        now = time.time()
        last_action = max(last_check, get_last_activity())

        if now - last_action >= PING_INTERVAL or not registered_in_db:
            try:
                install_success, install_failed = [], []
                order_success, order_failed = [], []
                apps_installed_data, telemetry_data = {}, {}

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

                    res_telemetria = sensores_module.coletar_telemetria_completa()
                    telemetry_data = res_telemetria[0] if isinstance(res_telemetria, tuple) else res_telemetria
                except Exception as e:
                    telemetry_data = {"erro": str(e)}

                dna_seguro = obter_dna_dispositivo()
                ts_agora = int(time.time())

                payload = {
                    "type": 1 if registered_in_db else 0,
                    "guild_id": str(guild_id), "owner_id": str(owner_id),
                    "device_id": str(device_id), "protocol": str(current_protocol),
                    "status": "online", "client_token": client_token, "version": HAPIEPHONE_VERSION,
                    "install_success": install_success, "install_failed": install_failed,
                    "order_success": order_success, "order_failed": order_failed,
                    "apps_installed": apps_installed_data, "telemetry": telemetry_data,
                    "device_dna": dna_seguro,
                    "timestamp": ts_agora
                }

                assinatura = gerar_assinatura_hmac(dna_seguro, ts_agora)
                envelope_seguro = {
                    "signature": assinatura,
                    "payload": payload
                }

                headers = {"Content-Type": "application/json", "ngrok-skip-browser-warning": "true"}
                response = requests.post(URL_WEBHOOK, json=envelope_seguro, headers=headers, timeout=30)

                if response.status_code == 200:
                    response_json = response.json()

                    if "data_command" in response_json:
                        d_cmd = response_json["data_command"]
                        if "auto_copy" in d_cmd:
                            ac_status = bool(d_cmd["auto_copy"])
                            set_function_status("auto_copy", ac_status)
                            estado_txt = "ATIVADO" if ac_status else "DESATIVADO"
                            sys.stdout.write("\r\033[K")
                            console.print(f"[bold green]✅ Permissão 'Auto Copy' -> {estado_txt}[/bold green]")

                    if "auto_input" in response_json:
                        ai_status = bool(response_json["auto_input"])
                        old_status = False
                        if os.path.exists(FUNCTIONS_JSON_FILE):
                            try:
                                with open(FUNCTIONS_JSON_FILE, "r") as f: old_status = json.load(f).get("auto_input", False)
                            except: pass

                        if old_status != ai_status:
                            set_function_status("auto_input", ai_status)
                            estado_txt = "ATIVADO" if ai_status else "DESATIVADO"
                            sys.stdout.write("\r\033[K")
                            console.print(f"[bold green]✅ Permissão 'Auto Input' -> {estado_txt}[/bold green]")

                        if ai_status:
                            if subprocess.run("pgrep -f auto_input.py", shell=True, stdout=subprocess.DEVNULL).returncode != 0:
                                ai_script_path = os.path.join(FUNCTIONS_DIR, "auto_input.py")
                                ai_log_path = os.path.join(DATA_DIR, "auto_input_daemon.txt")
                                if os.path.exists(ai_script_path):
                                    os.system(f"nohup {sys.executable} {ai_script_path} > {ai_log_path} 2>&1 &")
                                    sys.stdout.write("\r\033[K")
                                    console.print("[dim]⚙️ Serviço Auto Input iniciado em background...[/dim]")
                        else:
                            os.system("pkill -f auto_input.py > /dev/null 2>&1")

                    if "auto_input_cmd" in response_json:
                        cmd_data = response_json["auto_input_cmd"]
                        if "id_alvo" in cmd_data and "texto" in cmd_data:
                            sys.stdout.write("\r\033[K")
                            console.print(f"[bold yellow]⚡ Injetando texto no campo ID {cmd_data['id_alvo']}...[/bold yellow]")
                            trigger_inject_path = "/sdcard/Hapiephone/trigger_inject.txt"
                            try:
                                with open(trigger_inject_path, "w", encoding="utf-8") as tf:
                                    auto_enter_val = "1" if cmd_data.get("auto_enter", False) else "0"
                                    tf.write(f"{cmd_data['id_alvo']}|{auto_enter_val}|{cmd_data['texto']}")
                                console.print("[dim]💉 Gatilho enviado para o Daemon Auto Input.[/dim]")
                            except Exception as e:
                                console.print(f"[bold red]❌ Erro ao criar gatilho: {e}[/bold red]")

                    if "ordens" in response_json:
                        lista_ordens = response_json["ordens"]
                        if isinstance(lista_ordens, list) and len(lista_ordens) > 0:
                            brain_script_path = os.path.join(FUNCTIONS_DIR, "task_orchestrator.py")
                            if os.path.exists(brain_script_path):
                                try:
                                    with open(PAYLOAD_FILE, "w") as pf: json.dump(response_json, pf)
                                    subprocess.run([sys.executable, brain_script_path, "--file", PAYLOAD_FILE], check=True, stdout=subprocess.DEVNULL)
                                except: pass

                    if response_json.get("mudo") == True:
                        git_cmd = response_json.get("comando_terminal", "git pull")
                        os.system("pkill -f auto_copy.py > /dev/null 2>&1")
                        os.system("pkill -f auto_input.py > /dev/null 2>&1")
                        set_function_status("auto_copy", False)
                        os.system("pkill -f monitor_apps.py > /dev/null 2>&1")
                        subprocess.run(git_cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        os.execv(sys.executable, ['python'] + sys.argv)

                    if "new_client_token" in response_json:
                        update_client_token(response_json["new_client_token"])

                    if response_json.get("status") == "shutdown":
                        sys.stdout.write("\r\033[K")
                        console.print("[bold red]⚠️ Comando de Shutdown recebido.[/bold red]")
                        sys.exit(4)

                    registered_in_db = True
                    last_check = time.time()

                    has_tasks = any(k in response_json for k in ["install", "commands", "remove", "instalar", "comandos"])
                    if has_tasks:
                        install_script_path = os.path.join(HAPIE_APPS_DIR, "install.py")
                        with Halo(text='Atualizando motor de instalação...', spinner='dots', color='cyan'):
                            v_cache_install = int(time.time())
                            URL_INSTALL = f"https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/hapie_apps/install.py?v={v_cache_install}"
                            os.system(f"curl -sL '{URL_INSTALL}' -o {install_script_path} > /dev/null 2>&1")
                        try:
                            with open(PAYLOAD_INSTALL_FILE, "w") as pf: json.dump(response_json, pf)
                            subprocess.run([sys.executable, install_script_path, "--file", PAYLOAD_INSTALL_FILE], check=True, stdout=subprocess.DEVNULL)
                        except: pass

                sys.stdout.write(f"\r\033[K\033[90m📡 {current_protocol} | Awaiting tasks...\033[0m")
                sys.stdout.flush()
            except Exception: pass
        time.sleep(2)

except KeyboardInterrupt:
    print("\n")
    shutdown_spinner = Halo(text='Desligando serviços em segundo plano...', spinner='dots', color='red')
    shutdown_spinner.start()
    os.system("pkill -f auto_copy.py > /dev/null 2>&1")
    os.system("pkill -f auto_input.py > /dev/null 2>&1")
    set_function_status("auto_copy", False)
    os.system("pkill -f monitor_apps.py > /dev/null 2>&1")
    time.sleep(1)
    shutdown_spinner.succeed('Todos os serviços parados com segurança.')
    console.print("[bold green]✅ Node desconectado. Até logo![/bold green]\n")
    sys.exit(0)
