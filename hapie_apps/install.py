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
    cmd = f"aapt dump badging {tmp_path} 2>/dev/null | grep 'application-label:' | head -n 1 | cut -d\\' -f2"
    app_name = subprocess.getoutput(cmd).strip()
    return app_name if app_name else default_pkg

def install_apk(url, visibility):
    tmp_path = os.path.join(BASE_DIR, "temp_install.apk")
    if os.path.exists(tmp_path): os.remove(tmp_path)

    console.print(Panel(f"Baixando APK...\n[dim]{url}[/dim]", style="yellow", title="📥 DOWNLOAD INICIADO"))

    # 1. Barreira contra links web da Play Store (Impede falha silenciosa)
    if "play.google.com" in url:
        log("❌ A URL fornecida é uma página da loja, não um link direto de APK.", "bold red")
        return None, None, False

    # 2. Download melhorado (Gdown fuzzy p/ Drive, Curl silencioso p/ resto)
    if "drive.google.com" in url:
        os.system(f"gdown -q --fuzzy '{url}' -O {tmp_path}")
    else:
        os.system(f"curl -sL '{url}' -o {tmp_path}")

    # 3. Verifica se o arquivo foi realmente criado
    if not os.path.exists(tmp_path):
        log("❌ Erro: O arquivo APK não pôde ser baixado (falha de rede).", "bold red")
        return None, None, False

    # 4. Verifica o tamanho (Evita falsos downloads de HTML de 100kb do Google Drive)
    if os.path.getsize(tmp_path) < 500000:
        log("❌ Erro: Arquivo corrompido ou bloqueio de download detectado (provável página HTML de erro).", "bold red")
        os.remove(tmp_path)
        return None, None, False

    console.print("[bold yellow]⚙️ Processando pacote e burlando Play Protect...[/bold yellow]")
    
    # 5. Tratamento de erros do aapt
    cmd_get_pkg = f"aapt dump badging {tmp_path} 2>/dev/null | grep package | awk '{{print $2}}' | sed s/name=//g | sed s/\\'//g"
    pkg_name = subprocess.getoutput(cmd_get_pkg).strip()

    if not pkg_name or "not found" in pkg_name or "W/zipro" in pkg_name:
        log("❌ ERRO FATAL: Arquivo APK inválido ou corrompido (o aapt não conseguiu ler).", "bold red")
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
        os.system(f"gdown -q --fuzzy '{data_url}' -O {tmp_data}")
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
