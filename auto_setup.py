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
        # Permite que o Termux abra janelas sobre outros apps (Obrigatório para abrir sozinho)
        os.system("su -c 'appops set com.termux SYSTEM_ALERT_WINDOW allow'")
        os.system("su -c 'appops set com.termux RUN_IN_BACKGROUND allow'")
        os.system("su -c 'appops set com.termux RUN_ANY_IN_BACKGROUND allow'")
        # Tira o Termux do modo de economia de energia
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
        write_log(f"❌ Bashrc error: {e}")

def setup_immortal_boot():
    write_log("Attempting to inject boot script...")
    spinner = Halo(text='Injecting Boot Script...', spinner='dots')
    spinner.start()
    
    # Lista de pastas onde o Android/Magisk aceita scripts de boot
    possible_dirs = ["/data/adb/service.d", "/data/adb/post-fs-data.d", "/data/local/userinit.d"]
    target_dir = None

    for d in possible_dirs:
        # Tenta criar a pasta na marra
        os.system(f"su -c 'mkdir -p {d}'")
        if os.system(f"su -c '[ -d {d} ]'") == 0:
            target_dir = d
            break

    if not target_dir:
        # Fallback para pasta root do sistema se as outras falharem
        os.system("su -c 'mount -o rw,remount /'")
        os.system("su -c 'mkdir -p /etc/init.d'")
        if os.system(f"su -c '[ -d /etc/init.d ]'") == 0:
            target_dir = "/etc/init.d"

    if not target_dir:
        spinner.fail("Could not find or create any boot directory.")
        write_log("❌ Error: No boot directory accessible even with Root.")
        return

    script_path = os.path.join(target_dir, "99start_hapie")

    boot_sh = """#!/system/bin/sh
(
    # Aguarda o sistema estar pronto
    until [ $(getprop sys.boot_completed) -eq 1 ]; do
        sleep 5
    done
    sleep 15

    # Acorda a tela e desbloqueia
    input keyevent 26
    sleep 1
    input swipe 500 1000 500 200
    sleep 1
    input keyevent 82
    
    # Abre o Termux (Forçado)
    am start --user 0 -n com.termux/com.termux.app.TermuxActivity -a android.intent.action.MAIN -c android.intent.category.LAUNCHER
) &
"""

    try:
        with open("temp_boot.sh", "w") as f:
            f.write(boot_sh)
        
        os.system(f"su -c 'mv temp_boot.sh {script_path}'")
        os.system(f"su -c 'chmod 755 {script_path}'")
        os.system(f"su -c 'chown root:root {script_path}'")
        
        spinner.succeed(f"Boot script injected at {target_dir}!")
        write_log(f"✅ Boot script injected successfully at {script_path}")
    except Exception as e:
        spinner.fail(f"Injection failed: {e}")
        write_log(f"❌ Injection failed: {e}")

if __name__ == "__main__":
    with open(LOG_FILE, "w") as f:
        f.write(f"--- Persistence Setup Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        
    console.print("[bold cyan]--- Evollogic Persistence Setup ---[/bold cyan]")
    force_android_permissions()
    setup_termux_bashrc()
    setup_immortal_boot()
    console.print("\n[bold green]✅ Configuration Finished![/bold green]")
    console.print("[dim]Reboot your UgPhone now to test auto-start.[/dim]\n")
    write_log("✅ Setup Finished.")
