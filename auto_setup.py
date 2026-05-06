import os
import json

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

def setup_root_boot():
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

(
    export PREFIX=/data/data/com.termux/files/usr
    export HOME=/data/data/com.termux/files/home
    export LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib
    export PATH=/data/data/com.termux/files/usr/bin:/system/bin:/system/xbin

    while true; do
        cd $HOME/Hapiephone
        python import.py
        sleep 10
    done
) &
"""

    spinner = Halo(text='Injecting immortal boot script via Root...', spinner='dots')
    spinner.start()

    try:
        with open("temp_boot.sh", "w", encoding="utf-8") as f:
            f.write(boot_script_content)
        
        os.system(f"su -c 'mv temp_boot.sh {script_path}'")
        os.system(f"su -c 'chmod 755 {script_path}'")
        os.system(f"su -c 'chown root:root {script_path}'")
        
        if os.path.exists("temp_boot.sh"):
            os.remove("temp_boot.sh")
            
        spinner.succeed(f"Immortal System activated! File saved at: {script_path}")
    except Exception as e:
        spinner.fail(f"Error configuring boot: {e}")

if __name__ == "__main__":
    setup_root_boot()
