import os
import json
import subprocess

try:
    from rich.console import Console
    from halo import Halo
except ImportError:
    os.system("pip install rich halo -q > /dev/null 2>&1")
    from rich.console import Console
    from halo import Halo

console = Console()

def setup_termux_bashrc():
    """Garante que o código corre mal o Termux abra"""
    spinner = Halo(text='Setting up .bashrc logic...', spinner='dots')
    spinner.start()
    bashrc_path = os.path.expanduser("~/.bashrc")
    
    startup_code = """
# === Hapiephone Auto-Start ===
if [ -z "$HAPIE_RUNNING" ]; then
    export HAPIE_RUNNING=1
    clear
    while true; do
        cd ~/Hapiephone 2>/dev/null || cd ~/hapiephone 2>/dev/null
        python import.py
        echo "🔄 Restarting in 5s..."
        sleep 5
    done
fi
"""
    if os.path.exists(bashrc_path):
        with open(bashrc_path, "r") as f:
            if "Hapiephone Auto-Start" in f.read():
                spinner.succeed(".bashrc already configured.")
                return

    with open(bashrc_path, "a") as f:
        f.write(startup_code)
    spinner.succeed(".bashrc configured!")

def setup_immortal_boot():
    """Script de Boot agressivo para Magisk"""
    magisk_dir = "/data/adb/service.d"
    script_path = os.path.join(magisk_dir, "99start_hapie")

    if os.system(f"su -c '[ -d {magisk_dir} ]'") != 0:
        console.print("[bold red]❌ Magisk service.d not found! Is the phone rooted?[/bold red]")
        return

    # SCRIPT SH QUE VAI CORRER NO ANDROID
    # Ele tenta abrir o Termux a cada 5 segundos até ter sucesso
    boot_sh = """#!/system/bin/sh
(
    # Aguarda o sistema estabilizar
    sleep 20 

    # Loop de tentativa de abertura
    MAX_TRIES=10
    COUNT=0
    while [ $COUNT -lt $MAX_TRIES ]; do
        # Tenta acordar a tela
        input keyevent 26
        input keyevent 82
        
        # Abre o Termux
        am start --user 0 -n com.termux/com.termux.app.TermuxActivity
        
        # Verifica se o processo do Termux está visível
        if dumpsys window windows | grep -q "com.termux"; then
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
        spinner.succeed("Boot Script injected successfully!")
    except Exception as e:
        spinner.fail(f"Injection failed: {e}")

if __name__ == "__main__":
    console.print("[bold cyan]Initializing Persistence Setup...[/bold cyan]")
    setup_termux_bashrc()
    setup_immortal_boot()
    console.print("[bold green]✅ Ready! Reboot the phone to test.[/bold green]")
