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

def setup_termux_bashrc():
    """Injects the auto-start command directly into Termux's brain (.bashrc)"""
    spinner = Halo(text='Configuring Termux auto-start (.bashrc)...', spinner='dots')
    spinner.start()
    try:
        bashrc_path = os.path.expanduser("~/.bashrc")
        
        # This code runs every time Termux opens
        trigger_code = """
# === Hapiephone Auto-Start ===
if [ -z "$HAPIE_RUNNING" ]; then
    export HAPIE_RUNNING=1
    clear
    echo "🚀 Starting Hapiephone in 3 seconds... (Press CTRL+C to cancel)"
    sleep 3
    while true; do
        cd ~/Hapiephone 2>/dev/null || cd ~/hapiephone 2>/dev/null
        python import.py
        echo "🔄 Restarting in 5 seconds..."
        sleep 5
    done
fi
"""
        # Prevent duplicate injections
        if os.path.exists(bashrc_path):
            with open(bashrc_path, "r", encoding="utf-8") as f:
                content = f.read()
            if "Hapiephone Auto-Start" in content:
                spinner.succeed("Termux auto-start already configured in .bashrc.")
                return
        
        with open(bashrc_path, "a", encoding="utf-8") as f:
            f.write(trigger_code)
        spinner.succeed("Termux auto-start injected successfully!")
    except Exception as e:
        spinner.fail(f"Failed to configure Termux: {e}")

def setup_root_boot():
    """Sets up Magisk to wake the screen and launch Termux on boot"""
    if not check_permission():
        console.print("[bold yellow]⚠️ Auto-restart permission denied in config.json.[/bold yellow]")
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
        console.print("[bold red]❌ Root boot folder not found. Check if Magisk is active.[/bold red]")
        return

    script_path = os.path.join(boot_dir, "99start_hapie")
        
    boot_script_content = """#!/system/bin/sh
until [ $(getprop sys.boot_completed) -eq 1 ]; do
    sleep 2
done

# Wake up screen (UgPhone safe sequence)
input keyevent 26
sleep 1
input keyevent 82
sleep 1

# Kill Termux if it's stuck in background from previous session
am force-stop com.termux
sleep 2

# Launch Termux (This will trigger the .bashrc script automatically)
am start -n com.termux/com.termux.app.TermuxActivity
"""

    spinner = Halo(text='Injecting screen wake script via Root...', spinner='dots')
    spinner.start()

    try:
        with open("temp_boot.sh", "w", encoding="utf-8") as f:
            f.write(boot_script_content)
        
        os.system(f"su -c 'mv temp_boot.sh {script_path}'")
        os.system(f"su -c 'chmod 755 {script_path}'")
        os.system(f"su -c 'chown root:root {script_path}'")
        
        if os.path.exists("temp_boot.sh"):
            os.remove("temp_boot.sh")
            
        spinner.succeed(f"Foreground Auto-Boot activated! File saved at: {script_path}")
    except Exception as e:
        spinner.fail(f"Error configuring boot: {e}")

if __name__ == "__main__":
    console.print("\n[bold cyan]--- System Persistency Setup ---[/bold cyan]")
    setup_termux_bashrc()
    setup_root_boot()
    console.print("[bold green]✅ All persistency modules loaded. Phone will auto-start on reboot.[/bold green]\n")
