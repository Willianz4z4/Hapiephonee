import os
import json
import subprocess
import re
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
    """Save clean logs to a text file without rich formatting tags."""
    try:
        clean_msg = re.sub(r'\[.*?\]', '', str(msg))
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            ts = datetime.now().strftime("%H:%M:%S")
            f.write(f"[{ts}] {clean_msg}\n")
    except:
        pass

def force_android_permissions():
    """Uses Root to grant Termux ultimate background and overlay permissions"""
    write_log("Starting Android permission override...")
    spinner = Halo(text='Forcing Android system permissions via Root...', spinner='dots')
    spinner.start()
    try:
        os.system("su -c 'appops set com.termux SYSTEM_ALERT_WINDOW allow'")
        os.system("su -c 'appops set com.termux RUN_IN_BACKGROUND allow'")
        os.system("su -c 'appops set com.termux RUN_ANY_IN_BACKGROUND allow'")
        os.system("su -c 'dumpsys deviceidle whitelist +com.termux'")
        
        spinner.succeed("System permissions successfully forced!")
        write_log("✅ System permissions successfully forced!")
    except Exception as e:
        spinner.fail(f"Failed to force permissions: {e}")
        write_log(f"❌ Failed to force permissions: {e}")

def setup_termux_bashrc():
    """Garante que o código corre mal o Termux abra"""
    write_log("Configuring .bashrc logic...")
    spinner = Halo(text='Setting up .bashrc logic...', spinner='dots')
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
        sleep 5
    done
fi
"""
    try:
        if os.path.exists(bashrc_path):
            with open(bashrc_path, "r") as f:
                if "Evollogic Auto-Start" in f.read():
                    spinner.succeed(".bashrc already configured.")
                    write_log("✅ .bashrc already configured (skipped).")
                    return

        with open(bashrc_path, "a") as f:
            f.write(startup_code)
        spinner.succeed(".bashrc configured!")
        write_log("✅ .bashrc configured successfully!")
    except Exception as e:
        spinner.fail(f"Failed to write .bashrc: {e}")
        write_log(f"❌ Failed to write .bashrc: {e}")

def setup_immortal_boot():
    """Script de Boot agressivo para Magisk com quebra de lockscreen"""
    write_log("Configuring Magisk immortal boot script...")
    magisk_dir = "/data/adb/service.d"
    script_path = os.path.join(magisk_dir, "99start_hapie")

    if os.system(f"su -c '[ -d {magisk_dir} ]'") != 0:
        console.print("[bold red]❌ Magisk service.d not found! Is the phone rooted?[/bold red]")
        write_log("❌ Error: Magisk service.d not found.")
        return

    boot_sh = """#!/system/bin/sh
(
    until [ $(getprop sys.boot_completed) -eq 1 ]; do
        sleep 2
    done
    sleep 10 

    MAX_TRIES=10
    COUNT=0
    while [ $COUNT -lt $MAX_TRIES ]; do
        input keyevent 26
        sleep 1
        
        input swipe 500 1000 500 200
        sleep 1
        input keyevent 82
        sleep 1
        
        appops set com.termux SYSTEM_ALERT_WINDOW allow
        
        am start -n com.termux/com.termux.app.TermuxActivity -a android.intent.action.MAIN -c android.intent.category.LAUNCHER
        
        if dumpsys window windows | grep -q "mCurrentFocus.*TermuxActivity"; then
            exit 0
        fi
        
        COUNT=$((COUNT+1))
        sleep 5
    done
) &
"""

    spinner = Halo(text='Injecting aggressive Boot Script...', spinner='dots')
    spinner.start()

    try:
        with open("temp_boot.sh", "w") as f:
            f.write(boot_sh)
        
        os.system(f"su -c 'mv temp_boot.sh {script_path}'")
        os.system(f"su -c 'chmod 755 {script_path}'")
        os.system(f"su -c 'chown root:root {script_path}'")
        
        if os.path.exists("temp_boot.sh"):
            os.remove("temp_boot.sh")
            
        spinner.succeed("Boot Script injected successfully!")
        write_log(f"✅ Boot Script injected successfully at {script_path}")
    except Exception as e:
        spinner.fail(f"Injection failed: {e}")
        write_log(f"❌ Boot script injection failed: {e}")

if __name__ == "__main__":
    # Limpa o log antigo para uma nova sessão limpa
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"--- Evollogic Persistence Setup Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        
    console.print("[bold cyan]--- Evollogic Persistence Setup ---[/bold cyan]")
    force_android_permissions()
    setup_termux_bashrc()
    setup_immortal_boot()
    console.print("[bold green]✅ Ready! Reboot the phone to test.[/bold green]")
    write_log("✅ Setup process finished.")
