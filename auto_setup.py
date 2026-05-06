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

def check_permission():
    try:
        with open("Data/config.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("auto_restart", True)
    except Exception:
        return True

def setup_termux_auto_run():
    """Configura o cérebro do Termux (.bashrc) para rodar o bot mal a app abra"""
    spinner = Halo(text='Configuring Termux auto-run startup...', spinner='dots')
    spinner.start()
    try:
        bashrc_path = os.path.expanduser("~/.bashrc")
        
        # Comando que será injetado no início do Termux
        startup_cmd = """
# === Evollogic Auto-Start ===
if [ -z "$EVO_STARTED" ]; then
    export EVO_STARTED=1
    clear
    echo "🚀 Initializing Hapiephone Engine..."
    sleep 2
    while true; do
        cd ~/Hapiephone 2>/dev/null || cd ~/hapiephone 2>/dev/null
        python import.py
        echo "🔄 Restarting in 5 seconds..."
        sleep 5
    done
fi
"""
        # Verifica se já existe para não duplicar
        if os.path.exists(bashrc_path):
            with open(bashrc_path, "r") as f:
                if "Evollogic Auto-Start" in f.read():
                    spinner.succeed("Termux startup already configured.")
                    return

        with open(bashrc_path, "a") as f:
            f.write(startup_cmd)
        spinner.succeed("Termux startup injected into .bashrc!")
    except Exception as e:
        spinner.fail(f"Error configuring .bashrc: {e}")

def setup_root_boot():
    """Configura o Magisk para 'puxar' o Termux para a frente ao ligar"""
    if not check_permission():
        console.print("[bold yellow]⚠️ Auto-restart permission disabled.[/bold yellow]")
        return

    magisk_dir = "/data/adb/service.d"
    init_d_dir = "/system/etc/init.d"
    
    boot_dir = None
    if os.system(f"su -c '[ -d {magisk_dir} ]'") == 0:
        boot_dir = magisk_dir
    elif os.system(f"su -c '[ -d {init_d_dir} ]'") == 0:
        boot_dir = init_d_dir
        os.system("su -c 'mount -o rw,remount /system'")
    
    if not boot_dir:
        console.print("[bold red]❌ Root boot directory not found.[/bold red]")
        return

    script_path = os.path.join(boot_dir, "99start_hapie")
        
    # Script que o Android corre no boot
    boot_content = """#!/system/bin/sh
# Aguarda o sistema carregar completamente
until [ $(getprop sys.boot_completed) -eq 1 ]; do
    sleep 3
done

# Simula ligar a tela e deslizar (para garantir que a UI está ativa)
input keyevent 26
sleep 1
input keyevent 82
sleep 1

# Força a abertura do Termux em primeiro plano
am start --user 0 -n com.termux/com.termux.app.TermuxActivity
"""

    spinner = Halo(text='Injecting Magisk boot trigger...', spinner='dots')
    spinner.start()

    try:
        with open("temp_boot.sh", "w") as f:
            f.write(boot_content)
        
        # Move para a pasta do Magisk com permissões totais
        os.system(f"su -c 'mv temp_boot.sh {script_path}'")
        os.system(f"su -c 'chmod 755 {script_path}'")
        os.system(f"su -c 'chown root:root {script_path}'")
        
        spinner.succeed(f"Boot trigger active at: {script_path}")
    except Exception as e:
        spinner.fail(f"Boot injection failed: {e}")

if __name__ == "__main__":
    console.print("[bold cyan]Updating Persistency Modules...[/bold cyan]")
    setup_termux_auto_run()
    setup_root_boot()
    console.print("[bold green]✅ Done! The app will now open automatically on reboot.[/bold green]\n")
