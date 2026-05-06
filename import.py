import os
import sys
import subprocess
import time
import json

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

HAPIEPHONE_VERSION = "10"

console = Console()

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
CONFIG_FILE = os.path.join(BASE_DIR, "hapie_config.json")
FUNCTIONS_DIR = os.path.join(BASE_DIR, "functions")

saved_config = {}

console.print(Panel.fit(f"[bold cyan]Hapiephone Cloud Node[/bold cyan]\n[dim]Version {HAPIEPHONE_VERSION} | Powered by Evollogic[/dim]", border_style="cyan"))

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
    sys.exit(1)

URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
report = {"installation_status": "pending", "steps": {}, "system_info": {}}

spinner = Halo(text='Preparing Cloud Phone environment...', spinner='dots')
spinner.start()

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

    if android_version != "Unknown" and "." in android_version:
        android_version = android_version.split(".")[0]

    report["system_info"] = {
        "root_access": has_root, 
        "model": model, 
        "android_version": android_version, 
        "device_id": device_id, 
        "region": region, 
        "processor": processor
    }
    report["steps"]["data_collection"] = "Success"
except Exception as e:
    report["steps"]["data_collection"] = "Failed"
    device_id = "Unknown"

report["installation_status"] = "Completed"
spinner.succeed(f"Hardware scan complete! Device ID: [bold]{device_id}[/bold]")

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
            console.print("[bold yellow]🔑 [AUTH] New security license installed on the device.[/bold yellow]")
        except Exception as e:
            console.print(f"[bold red]⚠️ [AUTH] Error saving new token: {e}[/bold red]")

spinner = Halo(text='Deploying background modules...', spinner='dots')
spinner.start()
try:
    os.system("pkill -f auto_copy.py > /dev/null 2>&1")
    os.system(f"mkdir -p {FUNCTIONS_DIR}")
    
    copy_script_path = os.path.join(FUNCTIONS_DIR, "auto_copy.py")
    log_script_path = os.path.join(FUNCTIONS_DIR, "copy_log.txt")
    os.system(f"rm -rf {copy_script_path} > /dev/null 2>&1")
    
    v_cache = int(time.time())
    URL_COPY_PY = f"https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/functions/auto_copy.py?v={v_cache}"
    os.system(f"curl -sL '{URL_COPY_PY}' -o {copy_script_path} > /dev/null 2>&1")
    
    python_path = sys.executable
    subprocess.run('su -c "appops set com.termux READ_CLIPBOARD allow" 2>/dev/null', shell=True)
    
    daemon_cmd = f"nohup {python_path} {copy_script_path} {device_id} {guild_id} {owner_id} > {log_script_path} 2>&1 &"
    os.system(daemon_cmd)
    spinner.succeed("Invisible module deployed successfully! (Listening in background)")
except Exception as e:
    spinner.fail(f"Error deploying module: {e}")

registered_in_db = False
PING_INTERVAL = 15 
last_check = 0 

console.print("\n[bold green]📡 Connection established. Awaiting commands from Control Panel...[/bold green]\n[dim](Press CTRL+C at any time to disconnect safely)[/dim]\n")

try:
    while True:
        now = time.time()
        last_action = max(last_check, get_last_activity())
        
        if now - last_action >= PING_INTERVAL or not registered_in_db:
            try:
                payload = {
                    "type": 1 if registered_in_db else 0, 
                    "guild_id": guild_id, 
                    "owner_id": owner_id, 
                    "device_id": device_id,
                    "status": "online", 
                    "report": report,
                    "client_token": client_token,
                    "version": HAPIEPHONE_VERSION
                }
                
                headers = {"Content-Type": "application/json"}
                response = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    response_json = response.json()
                    
                    if "instalar" in response_json or "comandos" in response_json:
                        console.print(f"[bold magenta]📦 Vercel Payload Received:[/bold magenta] {response_json}")
                    
                    if "new_client_token" in response_json:
                        update_client_token(response_json["new_client_token"])
                    
                    if response_json.get("status") == "shutdown":
                         console.print(f"[bold red]🛑 [SYSTEM] Server refused connection: {response_json.get('motivo')}[/bold red]")
                         console.print("[dim]Shutting down services...[/dim]")
                         sys.exit(1)
                         
                    if not registered_in_db:
                        console.print("[bold cyan]🚀 Device synchronized and actively listening![/bold cyan]")
                        registered_in_db = True
                        
                    last_check = time.time() 

                    if "instalar" in response_json or "comandos" in response_json:
                        os.system(f"mkdir -p {FUNCTIONS_DIR}")
                        install_script_path = os.path.join(FUNCTIONS_DIR, "install.py")
                        
                        if not os.path.exists(install_script_path):
                            with Halo(text='Downloading Install Engine...', spinner='dots'):
                                v_cache_install = int(time.time())
                                URL_INSTALL = f"https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/functions/install.py?v={v_cache_install}"
                                os.system(f"curl -sL '{URL_INSTALL}' -o {install_script_path}") 

                        tasks_str = json.dumps(response_json)
                        try:
                            console.print("[bold yellow]⚡ Triggering installation engine...[/bold yellow]")
                            subprocess.run([sys.executable, install_script_path, tasks_str], check=True)
                        except subprocess.CalledProcessError as err:
                            console.print(f"[bold red]❌ Install engine failed. Error code: {err.returncode}[/bold red]")
                        except Exception as err:
                            console.print(f"[bold red]❌ Unexpected failure when calling the engine: {err}[/bold red]")

                else:
                    console.print(f"[bold red]⚠️ Connection refused by server! HTTP Code: {response.status_code}[/bold red]")
            except Exception as e:
                pass
                
        time.sleep(2)

except KeyboardInterrupt:
    console.print("\n\n[bold red]🛑 Stop signal received (CTRL+C).[/bold red]")
    shutdown_spinner = Halo(text='Shutting down background services safely...', spinner='dots')
    shutdown_spinner.start()
    os.system("pkill -f auto_copy.py > /dev/null 2>&1")
    time.sleep(1)
    shutdown_spinner.succeed('All Evollogic services stopped.')
    console.print("[bold green]✅ Node disconnected safely. Goodbye![/bold green]\n")
    sys.exit(0)
