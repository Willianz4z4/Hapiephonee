import os
import sys
import json
import subprocess
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
except ImportError:
    class DummyConsole:
        def print(self, msg, *args, **kwargs): print(msg)
    console = DummyConsole()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "install_log.txt")

def log(msg, color="cyan", write_file=True):
    console.print(f"[{color}]{msg}[/{color}]")
    if write_file:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {msg}\n")
        except:
            pass

def run_su(cmd):
    return subprocess.run(f"su -c '{cmd}'", shell=True, capture_output=True, text=True)

def get_app_name(tmp_path, default_pkg):
    cmd = f"aapt dump badging {tmp_path} | grep 'application-label:' | head -n 1 | cut -d\\' -f2"
    app_name = subprocess.getoutput(cmd).strip()
    return app_name if app_name else default_pkg

def install_apk(url, visibility):
    tmp_path = os.path.join(BASE_DIR, "temp_install.apk")
    if os.path.exists(tmp_path): os.remove(tmp_path)

    console.print(Panel(f"Baixando APK...\n[dim]{url}[/dim]", style="yellow", title="📥 DOWNLOAD INICIADO"))

    if "drive.google.com" in url:
        os.system(f"gdown '{url}' -O {tmp_path}")
    else:
        os.system(f"curl -L '{url}' -o {tmp_path}")

    if os.path.exists(tmp_path):
        console.print("[bold yellow]⚙️ Processando pacote e burlando Play Protect...[/bold yellow]")
        # AQUI ESTÁ A CORREÇÃO: Chaves duplas no awk!
        cmd_get_pkg = f"aapt dump badging {tmp_path} | grep package | awk '{{print $2}}' | sed s/name=//g | sed s/\\'//g"
        pkg_name = subprocess.getoutput(cmd_get_pkg).strip()

        if pkg_name:
            app_name = get_app_name(tmp_path, pkg_name)

            run_su("pm disable-user --user 0 com.android.vending > /dev/null 2>&1")
            run_su("settings put global package_verifier_enable 0")

            install_result = run_su(f"pm install -r -g -d {tmp_path}")

            run_su("settings put global package_verifier_enable 1")
            run_su("pm enable com.android.vending > /dev/null 2>&1")

            if "Success" in install_result.stdout:
                if visibility == "oculto" or visibility == "hidden":
                    run_su(f"pm hide {pkg_name}")
                    log(f"✅ {app_name} ({pkg_name}) - Instalado & Oculto", "bold green")
                else:
                    run_su(f"pm unhide {pkg_name}")
                    log(f"✅ {app_name} ({pkg_name}) - Instalado com Sucesso", "bold green")
            else:
                log(f"❌ Falha ao instalar {app_name}: {install_result.stderr}", "bold red")

            os.remove(tmp_path)
            return pkg_name, app_name
    else:
        log("❌ Erro: O arquivo APK não pôde ser baixado.", "bold red")

    return None, None

def inject_data(data_url, package_name, app_name):
    tmp_data = os.path.join(BASE_DIR, "data_inject.tar.gz")
    target_path = f"/data/data/{package_name}"
    if os.path.exists(tmp_data): os.remove(tmp_data)

    console.print(Panel(f"Baixando Dados Extras para [bold]{app_name}[/bold]...", style="magenta", title="📁 INJEÇÃO DE DADOS"))

    if "drive.google.com" in data_url:
        os.system(f"gdown '{data_url}' -O {tmp_data}")
    else:
        os.system(f"curl -L '{data_url}' -o {tmp_data}")

    if os.path.exists(tmp_data):
        console.print("[bold yellow]⚙️ Descompactando scripts e permissões...[/bold yellow]")
        run_su(f"am force-stop {package_name}")
        extraction = run_su(f"tar -xzf {tmp_data} -C {target_path}")

        if extraction.returncode == 0:
            run_su(f"chown -R $(stat -c %u {target_path}):$(stat -c %g {target_path}) {target_path}")
            log(f"✅ Dados injetados com perfeição em {target_path}", "bold green")
        else:
            log(f"❌ Erro ao extrair dados: {extraction.stderr}", "bold red")

        os.remove(tmp_data)

def remove_app(package_name):
    run_su(f"pm uninstall {package_name}")
    log(f"🗑️ {package_name} - Removido com sucesso", "bold red")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])

        install_tasks = data.get("install", []) + data.get("instalar", [])
        for item in install_tasks:
            apk_url, visibility, _, extra = item[0], item[1], item[2], item[3]

            print("\n")
            pkg, app_name = install_apk(apk_url, visibility)

            if pkg and extra.get("data_link"):
                inject_data(extra["data_link"], pkg, app_name)

        remove_tasks = data.get("remove", []) + data.get("remover", [])
        for target_pkg in remove_tasks:
            remove_app(target_pkg)

        command_tasks = data.get("commands", []) + data.get("comandos", [])
        for cmd in command_tasks:
            if cmd.startswith("remove "):
                target_pkg = cmd.replace("remove ", "").strip()
                remove_app(target_pkg)
            else:
                run_su(cmd)
                log(f"⚡ Comando executado: {cmd}", "cyan")

    except Exception as e:
        log(f"❌ Erro fatal no script de instalacao: {e}", "bold red")
