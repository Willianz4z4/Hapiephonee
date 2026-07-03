import os
import sys
import json
import subprocess
import re
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
except ImportError:
    class DummyConsole:
        def print(self, msg, *args, **kwargs): print(msg)
    console = DummyConsole()

# ==========================================
# 📍 ROTAS ATUALIZADAS E ORGANIZADAS
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)

DATA_DIR = os.path.join(REPO_ROOT, "Data")
os.makedirs(DATA_DIR, exist_ok=True)

LOG_FILE = os.path.join(DATA_DIR, "install_log.txt")
REPORT_FILE = os.path.join(DATA_DIR, "install_report.json")

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
    cmd = f"aapt dump badging {tmp_path} 2>/dev/null | grep 'application-label:' | head -n 1 | cut -d\' -f2"
    app_name = subprocess.getoutput(cmd).strip()
    return app_name if app_name else default_pkg

def install_apk(url, visibility):
    tmp_path = os.path.join(BASE_DIR, "temp_install.apk")
    if os.path.exists(tmp_path): os.remove(tmp_path)

    console.print(Panel(f"Baixando APK...\n[dim]{url}[/dim]", style="yellow", title="📥 DOWNLOAD INICIADO"))

    if "play.google.com" in url:
        log("❌ A URL fornecida é uma página da loja, não um link direto de APK.", "bold red")
        return None, None, False

    # Download GDrive totalmente focado no CURL para burlar limite do Roblox
    if "drive.google.com" in url:
        file_id = None
        match_d = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
        if match_d:
            file_id = match_d.group(1)
        else:
            match_id = re.search(r'id=([a-zA-Z0-9_-]+)', url)
            if match_id:
                file_id = match_id.group(1)

        if file_id:
            cookie_path = os.path.join(BASE_DIR, "gdrive_cookies.txt")
            os.system(f"curl -sL -c '{cookie_path}' 'https://docs.google.com/uc?export=download&id={file_id}' -o '{tmp_path}'")
            
            if os.path.exists(tmp_path):
                try:
                    with open(tmp_path, 'r', errors='ignore') as f:
                        head = f.read(15000)
                    confirm_match = re.search(r'confirm=([A-Za-z0-9_-]+)', head)
                    if confirm_match:
                        token = confirm_match.group(1)
                        os.system(f"curl -sL -b '{cookie_path}' 'https://docs.google.com/uc?export=download&confirm={token}&id={file_id}' -o '{tmp_path}'")
                except:
                    pass
            if os.path.exists(cookie_path): os.remove(cookie_path)
        else:
            os.system(f"curl -sL '{url}' -o {tmp_path}")
    else:
        os.system(f"curl -sL '{url}' -o {tmp_path}")

    if not os.path.exists(tmp_path):
        log("❌ Erro: O arquivo APK não pôde ser baixado (falha de rede).", "bold red")
        return None, None, False

    if os.path.getsize(tmp_path) < 500000:
        log("❌ Erro: Arquivo corrompido ou bloqueio de download detectado.", "bold red")
        os.remove(tmp_path)
        return None, None, False

    console.print("[bold yellow]⚙️ Processando pacote e burlando Play Protect...[/bold yellow]")

    cmd_get_pkg = f"aapt dump badging {tmp_path} 2>/dev/null | grep package | awk '{{print $2}}' | sed s/name=//g | sed s/\\'//g"
    pkg_name = subprocess.getoutput(cmd_get_pkg).strip()

    if not pkg_name or "not found" in pkg_name or "W/zipro" in pkg_name:
        log("❌ ERRO FATAL: Arquivo APK inválido ou corrompido.", "bold red")
        if os.path.exists(tmp_path): os.remove(tmp_path)
        return None, None, False

    app_name = get_app_name(tmp_path, pkg_name)

    run_su("pm disable-user --user 0 com.android.vending > /dev/null 2>&1")
    run_su("settings put global package_verifier_enable 0")

    install_result = run_su(f"pm install -r -g -d {tmp_path}")

    run_su("settings put global package_verifier_enable 1")
    run_su("pm enable com.android.vending > /dev/null 2>&1")

    success_flag = False
    if "Success" in install_result.stdout:
        success_flag = True
        if visibility == "oculto":
            run_su(f"pm hide {pkg_name}")
            log(f"✅ {app_name} ({pkg_name}) - Instalado & Oculto", "bold green")
        else:
            run_su(f"pm unhide {pkg_name}")
            log(f"✅ {app_name} ({pkg_name}) - Instalado com Sucesso", "bold green")
    else:
        log(f"❌ Falha ao instalar {app_name}: {install_result.stderr}", "bold red")

    os.remove(tmp_path)
    return pkg_name, app_name, success_flag

def inject_data(data_url, package_name, app_name):
    tmp_data = os.path.join(BASE_DIR, "data_inject.tar.gz")
    target_path = f"/data/data/{package_name}"
    if os.path.exists(tmp_data): os.remove(tmp_data)

    console.print(Panel(f"Baixando Dados Extras para [bold]{app_name}[/bold]...", style="magenta", title="📁 INJEÇÃO DE DADOS"))

    if "drive.google.com" in data_url:
        file_id = None
        match_d = re.search(r'/d/([a-zA-Z0-9_-]+)', data_url)
        if match_d:
            file_id = match_d.group(1)
        else:
            match_id = re.search(r'id=([a-zA-Z0-9_-]+)', data_url)
            if match_id:
                file_id = match_id.group(1)

        if file_id:
            cookie_path = os.path.join(BASE_DIR, "gdrive_cookies.txt")
            os.system(f"curl -sL -c '{cookie_path}' 'https://docs.google.com/uc?export=download&id={file_id}' -o '{tmp_data}'")
            if os.path.exists(tmp_data):
                try:
                    with open(tmp_data, 'r', errors='ignore') as f:
                        head = f.read(15000)
                    confirm_match = re.search(r'confirm=([A-Za-z0-9_-]+)', head)
                    if confirm_match:
                        token = confirm_match.group(1)
                        os.system(f"curl -sL -b '{cookie_path}' 'https://docs.google.com/uc?export=download&confirm={token}&id={file_id}' -o '{tmp_data}'")
                except:
                    pass
            if os.path.exists(cookie_path): os.remove(cookie_path)
        else:
            os.system(f"curl -sL '{data_url}' -o {tmp_data}")
    else:
        os.system(f"curl -sL '{data_url}' -o {tmp_data}")

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
        success_list = []
        failed_list = []

        if "remove" in data:
            for pkg in data["remove"]:
                print("\n")
                console.print(Panel(f"Processando remoção...\n[dim]{pkg}[/dim]", style="red", title="🗑️ DESINSTALAÇÃO ACIONADA"))
                remove_app(pkg)

        lista_instalar = data.get("install", []) + data.get("instalar", [])
        if lista_instalar:
            for item in lista_instalar:
                apk_url, visibility, _, extra = item[0], item[1], item[2], item[3]
                print("\n")
                pkg, app_name, success = install_apk(apk_url, visibility)

                if success and pkg:
                    success_list.append(pkg)
                    if extra.get("data_link"):
                        inject_data(extra["data_link"], pkg, app_name)
                elif pkg:
                    failed_list.append(pkg)

        if "comandos" in data:
            for cmd in data["comandos"]:
                if cmd.startswith("remove "):
                    target_pkg = cmd.replace("remove ", "").strip()
                    remove_app(target_pkg)
                else:
                    run_su(cmd)
                    log(f"⚡ Comando executado: {cmd}", "cyan")

        if success_list or failed_list:
            with open(REPORT_FILE, "w", encoding="utf-8") as f:
                json.dump({"install_success": success_list, "install_failed": failed_list}, f)

    except Exception as e:
        log(f"❌ Erro fatal no script de instalacao: {e}", "bold red")
