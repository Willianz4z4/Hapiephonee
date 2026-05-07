import os
import json
import subprocess
import time
import sys
import re

SAVE_FILE = os.path.expanduser("~/last_opened_apps.json")

def run_su(cmd):
    return subprocess.getoutput(f"su -c '{cmd}'")

def get_currently_open_apps():
    # CORREÇÃO: Busca expandida para telas divididas e Androids recentes (-i para ignorar maiúsculas/minúsculas)
    cmd = "dumpsys activity activities | grep -iE 'resumedactivity|pausedactivity|topresumedactivity|focusedapp'"
    output = run_su(cmd)
    
    apps_to_restore = []
    
    matches = re.findall(r'([a-zA-Z0-9_]+\.[a-zA-Z0-9_.]+/[a-zA-Z0-9_.]+)', output)
    
    for match in matches:
        # Evita salvar o Termux, interface do sistema e a Tela Inicial (Launchers)
        if "com.android.systemui" not in match and "com.termux" not in match and "launcher" not in match.lower():
            apps_to_restore.append(match.strip())
            
    return list(set(apps_to_restore))

def save_state():
    apps = get_currently_open_apps()
    if apps:
        with open(SAVE_FILE, "w") as f:
            json.dump(apps, f)
        print(f"✅ Checkpoint: {len(apps)} apps saved for restoration.")
        print(f"📱 Apps: {apps}")
    else:
        print("⚠️ No foreground app detected to save.")

def restore_state():
    if not os.path.exists(SAVE_FILE):
        print("ℹ️ No restoration file found.")
        return

    try:
        with open(SAVE_FILE, "r") as f:
            apps = json.load(f)
        
        print(f"🚀 Restoring {len(apps)} apps...")
        for app in apps:
            print(f"🔄 Opening: {app}")
            run_su(f"am start -n {app}")
            time.sleep(2)
            
        os.remove(SAVE_FILE)
        print("✅ Restoration complete.")
        
    except Exception as e:
        print(f"❌ Restoration error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_state()
    else:
        save_state()
