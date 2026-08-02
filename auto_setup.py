import os
import json
import subprocess
import re
import time
from datetime import datetime

try:
    from rich.console import Console
    from halo import Halo
except ImportError:
    os.system("pip install rich halo -q > /dev/null 2>&1")
    from rich.console import Console
    from halo import Halo

console = Console()
LOG_FILE = "setup_log.txt"

def write_log(msg):
    try:
        clean_msg = re.sub(r'\[.*?\]', '', str(msg))
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            ts = datetime.now().strftime("%H:%M:%S")
            f.write(f"[{ts}] {clean_msg}\n")
    except:
        pass

def force_android_permissions():
    write_log("Forcing UI and Background permissions...")
    spinner = Halo(text='Forcing System Permissions...', spinner='dots')
    spinner.start()
    try:
        os.system("su -c 'appops set com.termux SYSTEM_ALERT_WINDOW allow'")
        os.system("su -c 'appops set com.termux RUN_IN_BACKGROUND allow'")
        os.system("su -c 'appops set com.termux RUN_ANY_IN_BACKGROUND allow'")
        os.system("su -c 'dumpsys deviceidle whitelist +com.termux'")
        spinner.succeed("Permissions forced successfully!")
        write_log("✅ Permissions forced successfully!")
    except Exception as e:
        spinner.fail(f"Permission error: {e}")
        write_log(f"❌ Permission error: {e}")

def setup_termux_bashrc():
    write_log("Updating .bashrc startup script with Process Scanner...")
    spinner = Halo(text='Configuring Termux Smart Startup...', spinner='dots')
    spinner.start()
    bashrc_path = os.path.expanduser("~/.bashrc")

    startup_code = """
# Verifica se já existe um processo do bot rodando no sistema
if pgrep -f "python import.py" > /dev/null; then
    echo "🤖 Hapiephone Bot já está rodando perfeitamente em outra aba/sessão!"
    echo "👉 Terminal livre para uso."
else
    clear
    while true; do
        echo "🔍 Procurando o arquivo import.py pelo Termux..."

        CAMINHO_ARQUIVO=$(find ~ -type f -name "import.py" 2>/dev/null | head -n 1)

        if [ -n "$CAMINHO_ARQUIVO" ]; then
            PASTA_ALVO=$(dirname "$CAMINHO_ARQUIVO")
            echo "✅ Encontrado na pasta: $PASTA_ALVO"

            cd "$PASTA_ALVO" || exit
            python import.py
        else
            echo "❌ ERRO CRÍTICO: Arquivo import.py não encontrado em lugar nenhum!"
        fi

        echo "🔄 O sistema parou. Reiniciando em 5 segundos..."
        sleep 5
    done
fi
"""
    try:
        with open(bashrc_path, "w") as f:
            f.write(startup_code)
        spinner.succeed(".bashrc updated with Process Scanner!")
        write_log("✅ .bashrc updated with Process Scanner!")
    except Exception as e:
        spinner.fail(f"Bashrc error: {e}")

def install_termux_boot():
    write_log("Setting up Termux:Boot engine...")
    spinner = Halo(text='Checking/Installing Termux:Boot Engine...', spinner='dots')
    spinner.start()

    check_pkg = subprocess.run("su -c 'pm list packages com.termux.boot'", shell=True, capture_output=True, text=True)

    if "com.termux.boot" in check_pkg.stdout:
        spinner.info("Termux:Boot is already installed. Skipping download.")
        write_log("ℹ️ Termux:Boot already installed.")
    else:
        write_log("Disabling Google Play Protect...")
        os.system("su -c 'settings put global package_verifier_enable 0'")
        os.system("su -c 'settings put global upload_apk_enable 0'")

        apk_url = "https://f-droid.org/repo/com.termux.boot_7.apk"
        apk_path = "/sdcard/termux_boot.apk"

        os.system(f"curl -sL '{apk_url}' -o {apk_path} > /dev/null 2>&1")

        if not os.path.exists(apk_path):
            spinner.fail("Failed to download Termux:Boot.")
            return

        os.system(f"su -c 'pm install -r {apk_path} > /dev/null 2>&1'")
        os.system(f"rm {apk_path}")

    os.system("su -c 'appops set com.termux.boot SYSTEM_ALERT_WINDOW allow'")
    os.system("su -c 'appops set com.termux.boot RUN_IN_BACKGROUND allow'")
    os.system("su -c 'dumpsys deviceidle whitelist +com.termux.boot'")

    boot_dir = os.path.expanduser("~/.termux/boot")
    os.system(f"mkdir -p {boot_dir}")

    script_path = os.path.join(boot_dir, "start_hapie.sh")
    boot_sh = """#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
sleep 10
su -c 'input keyevent 26'
sleep 1
su -c 'input swipe 500 1000 500 200'
sleep 1
su -c 'input keyevent 82'
sleep 1
su -c 'am start --user 0 -n com.termux/com.termux.app.TermuxActivity'
"""

    try:
        with open(script_path, "w") as f:
            f.write(boot_sh)
        os.system(f"chmod +x {script_path}")

        os.system("su -c 'am start -n com.termux.boot/com.termux.boot.BootActivity > /dev/null 2>&1'")

        write_log("Iniciando rotina anti-lag para ocultar o icone...")
        for tentativa in range(4):
            time.sleep(3)
            os.system("su -c 'pm disable com.termux.boot/com.termux.boot.BootActivity > /dev/null 2>&1'")

        os.system("su -c 'am start -n com.termux/com.termux.app.TermuxActivity > /dev/null 2>&1'")
        os.system("su -c 'settings put global package_verifier_enable 1'")

        spinner.succeed("Termux:Boot engine active and hidden aggressively!")
        write_log(f"✅ Termux:Boot engine active and hidden. Script at {script_path}")
    except Exception as e:
        spinner.fail(f"Failed to setup Termux:Boot: {e}")
        write_log(f"❌ Failed to setup Termux:Boot: {e}")

def install_and_hide_plugins():
    write_log("Setting up additional Termux Plugins...")
    spinner = Halo(text='Downloading & Hiding Extra Termux Plugins...', spinner='dots')
    spinner.start()

    os.system("su -c 'settings put global package_verifier_enable 0'")
    os.system("su -c 'settings put global upload_apk_enable 0'")

    # Dicionário mestre com os links dos plugins
    plugins = {
        "Termux:API": {"pkg": "com.termux.api", "url": "https://f-droid.org/repo/com.termux.api_51.apk"},
        "Termux:Widget": {"pkg": "com.termux.widget", "url": "https://f-droid.org/repo/com.termux.widget_14.apk"},
        "Termux:Float": {"pkg": "com.termux.float", "url": "https://f-droid.org/repo/com.termux.float_15.apk"},
        "Termux:Tasker": {"pkg": "com.termux.tasker", "url": "https://f-droid.org/repo/com.termux.tasker_5.apk"},
        "Termux:Styling": {"pkg": "com.termux.styling", "url": "https://f-droid.org/repo/com.termux.styling_29.apk"},
        "Termux:GUI": {"pkg": "com.termux.gui", "url": "https://github.com/termux/termux-gui/releases/download/v0.1.0/app-release.apk"}
    }

    for name, info in plugins.items():
        pkg = info["pkg"]
        url = info["url"]
        apk_path = f"/sdcard/{pkg}.apk"

        # Verifica se o plugin já existe no sistema
        check_pkg = subprocess.run(f"su -c 'pm list packages {pkg}'", shell=True, capture_output=True, text=True)
        
        if pkg not in check_pkg.stdout:
            write_log(f"Downloading {name}...")
            os.system(f"curl -sL '{url}' -o {apk_path} > /dev/null 2>&1")
            
            if os.path.exists(apk_path):
                write_log(f"Installing {name}...")
                os.system(f"su -c 'pm install -r {apk_path} > /dev/null 2>&1'")
                os.system(f"rm {apk_path}")
            else:
                write_log(f"❌ Failed to download {name}")
                continue
        else:
            write_log(f"ℹ️ {name} already installed.")

        # Força as permissões essenciais de sobreposição de tela e bateria
        os.system(f"su -c 'appops set {pkg} SYSTEM_ALERT_WINDOW allow'")
        os.system(f"su -c 'appops set {pkg} RUN_IN_BACKGROUND allow'")
        os.system(f"su -c 'dumpsys deviceidle whitelist +{pkg}'")

        # MAGIA AQUI: Ocultador Dinâmico. Descobre a tela inicial do app e desativa ela do menu do Android.
        hide_cmd = f"su -c 'ACTIVITY=$(cmd package resolve-activity --brief {pkg} | tail -n 1); pm disable $ACTIVITY > /dev/null 2>&1'"
        os.system(hide_cmd)
        write_log(f"✅ {name} installed and hidden successfully.")

    os.system("su -c 'settings put global package_verifier_enable 1'")
    spinner.succeed("All plugins installed and completely hidden!")

def run_opens_apps():
    write_log("Fetching opens_apps.py from GitHub...")
    spinner = Halo(text='Loading opens_apps.py...', spinner='dots')
    spinner.start()

    raw_url = "https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/Data/opens_apps.py"
    script_path = "opens_apps.py"

    os.system(f"curl -sL '{raw_url}' -o {script_path}")

    if os.path.exists(script_path) and os.path.getsize(script_path) > 0:
        spinner.succeed("Script loaded successfully!")
        write_log("✅ opens_apps.py running.")
        os.system(f"python {script_path}")
    else:
        spinner.fail("Failed to download opens_apps.py from GitHub.")
        write_log("❌ Failed to download opens_apps.py.")

if __name__ == "__main__":
    with open(LOG_FILE, "w") as f:
        f.write(f"--- Persistence Setup Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")

    console.print("[bold cyan]--- Evollogic Persistence Setup ---[/bold cyan]")
    force_android_permissions()
    setup_termux_bashrc()
    install_termux_boot()
    
    # Executa a nova função que baixa e esconde todos os plugins!
    install_and_hide_plugins()

    console.print("\n[bold green]✅ Main script import completed![/bold green]")
    write_log("✅ Main import completed.")

    run_opens_apps()
