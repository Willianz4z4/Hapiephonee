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
    write_log("Updating .bashrc startup script...")
    spinner = Halo(text='Configuring Termux startup...', spinner='dots')
    spinner.start()
    bashrc_path = os.path.expanduser("~/.bashrc")
    
    startup_code = """
# === Evollogic Auto-Start ===
if [ -z "$EVO_STARTED" ]; then
    export EVO_STARTED=1
    clear
    while true; do
        cd ~/Hapiephone 2>/dev/null || cd ~/hapiephone 2>/dev/null
        python import.py
        echo "🔄 Bot closed. Restarting in 5s..."
        sleep 5
    done
fi
"""
    try:
        content = ""
        if os.path.exists(bashrc_path):
            with open(bashrc_path, "r") as f:
                content = f.read()
        
        if "Evollogic Auto-Start" not in content:
            with open(bashrc_path, "a") as f:
                f.write(startup_code)
            spinner.succeed(".bashrc updated!")
            write_log("✅ .bashrc updated!")
        else:
            spinner.succeed(".bashrc already set.")
            write_log("✅ .bashrc already set.")
    except Exception as e:
        spinner.fail(f"Bashrc error: {e}")

def install_termux_boot():
    write_log("Setting up Termux:Boot engine...")
    spinner = Halo(text='Installing Termux:Boot Engine...', spinner='dots')
    spinner.start()
    
    # 1. DESATIVA O GOOGLE PLAY PROTECT (Bypass do Antivírus)
    write_log("Disabling Google Play Protect...")
    os.system("su -c 'settings put global package_verifier_enable 0'")
    os.system("su -c 'settings put global upload_apk_enable 0'")
    
    apk_url = "https://f-droid.org/repo/com.termux.boot_7.apk"
    apk_path = "/sdcard/termux_boot.apk"
    
    os.system(f"curl -sL '{apk_url}' -o {apk_path} > /dev/null 2>&1")
    
    if not os.path.exists(apk_path):
        spinner.fail("Failed to download Termux:Boot.")
        return

    # Instala o app silenciosamente
    os.system(f"su -c 'pm install -r {apk_path} > /dev/null 2>&1'")
    os.system(f"rm {apk_path}") 
    
    # Permissões do Termux Boot
    os.system("su -c 'appops set com.termux.boot SYSTEM_ALERT_WINDOW allow'")
    os.system("su -c 'appops set com.termux.boot RUN_IN_BACKGROUND allow'")
    os.system("su -c 'dumpsys deviceidle whitelist +com.termux.boot'")

    # Pasta de inicialização
    boot_dir = os.path.expanduser("~/.termux/boot")
    os.system(f"mkdir -p {boot_dir}")
    
    script_path = os.path.join(boot_dir, "start_hapie.sh")
    boot_sh = """#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
sleep 10
# Acorda a tela
su -c 'input keyevent 26'
sleep 1
su -c 'input swipe 500 1000 500 200'
sleep 1
su -c 'input keyevent 82'
sleep 1
# Puxa o Termux Principal para a tela
su -c 'am start --user 0 -n com.termux/com.termux.app.TermuxActivity'
"""
    
    try:
        with open(script_path, "w") as f:
            f.write(boot_sh)
        os.system(f"chmod +x {script_path}")
        
        # REGISTRO: Abre o app pela primeira vez
        os.system("su -c 'am start -n com.termux.boot/com.termux.boot.BootActivity > /dev/null 2>&1'")
        time.sleep(3)
        
        # OCULTAR: Desativa a interface do app para virar fantasma
        os.system("su -c 'pm disable com.termux.boot/com.termux.boot.BootActivity > /dev/null 2>&1'")
        
        # Volta para o Termux
        os.system("su -c 'am start -n com.termux/com.termux.app.TermuxActivity > /dev/null 2>&1'")

        # REATIVA O PLAY PROTECT (Opcional, mas bom para segurança geral do celular)
        os.system("su -c 'settings put global package_verifier_enable 1'")

        spinner.succeed("Termux:Boot installed, registered and hidden!")
        write_log(f"✅ Termux:Boot engine active and hidden. Script at {script_path}")
    except Exception as e:
        spinner.fail(f"Failed to setup Termux:Boot: {e}")
        write_log(f"❌ Failed to setup Termux:Boot: {e}")

if __name__ == "__main__":
    with open(LOG_FILE, "w") as f:
        f.write(f"--- Persistence Setup Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        
    console.print("[bold cyan]--- Evollogic Persistence Setup ---[/bold cyan]")
    force_android_permissions()
    setup_termux_bashrc()
    install_termux_boot()
    
    console.print("\n[bold green]✅ Ghost Configuration Finished![/bold green]")
    console.print("[dim]Reboot your UgPhone now to test auto-start.[/dim]\n")
    write_log("✅ Setup Finished.")
