import os
import json
import subprocess
import sys
import time

SAVE_FILE = os.path.expanduser("~/last_opened_apps.json")

def run_su(cmd):
    return subprocess.getoutput(f"su -c '{cmd}'")

def get_currently_open_apps():
    cmd = "dumpsys activity activities | grep 'mResumedActivity'"
    output = run_su(cmd)
    
    apps_to_restore = []
    
    for line in output.split('\n'):
        if "u0 " in line:
            try:
                target = line.split("u0 ")[1].split(" ")[0]
                if "/" in target:
                    apps_to_restore.append(target)
            except Exception:
                continue
                
    return list(set(apps_to_restore))

def save_state():
    apps = get_currently_open_apps()
    if apps:
        with open(SAVE_FILE, "w") as f:
            json.dump(apps, f)
        print(f"✅ Checkpoint updated: {apps}")
    else:
        print("⚠️ No foreground app detected to save.")

def monitor_apps():
    print("👁️ Monitoring Android activity events...")
    
    logcat_cmd = ["su", "-c", "logcat -b events am_resume_activity:I am_pause_activity:I *:S"]
    process = subprocess.Popen(logcat_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True)

    try:
        for line in process.stdout:
            if "am_" in line:
                time.sleep(0.5)
                save_state()
    except KeyboardInterrupt:
        process.terminate()
        print("\n🛑 Monitoring stopped.")

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
    if len(sys.argv) > 1:
        if sys.argv[1] == "restore":
            restore_state()
        elif sys.argv[1] == "monitor":
            monitor_apps()
    else:
        save_state()
