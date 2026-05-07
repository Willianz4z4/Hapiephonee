import os
import json
import subprocess
import sys
import time
from datetime import datetime

SAVE_FILE = os.path.expanduser("~/last_opened_apps.json")
DEBUG_LOG = os.path.expanduser("~/debug_apps.log")
IGNORE_PKGS = [
    "com.termux", 
    "com.termux.boot", 
    "com.android.systemui", 
    "android",
    "com.og.launcher"
]

def write_log(msg):
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{ts}] {msg}\n")

def run_su(cmd):
    return subprocess.getoutput(f"su -c '{cmd}'")

def get_currently_open_apps():
    output = run_su("dumpsys activity activities")
    
    focused_app = ""
    background_apps = set()
    
    for line in output.split('\n'):
        if "ResumedActivity:" in line and " u0 " in line:
            try:
                target = line.split(" u0 ")[1].split(" ")[0]
                pkg_name = target.split("/")[0]
                
                if "/" in target and pkg_name not in IGNORE_PKGS:
                    focused_app = target
            except Exception:
                pass
                
        if "ActivityRecord{" in line and " u0 " in line:
            try:
                target = line.split(" u0 ")[1].split(" ")[0]
                pkg_name = target.split("/")[0]
                
                if "/" in target and pkg_name not in IGNORE_PKGS:
                    background_apps.add(target)
            except Exception:
                pass

    bg_list = list(background_apps)
    if focused_app in bg_list:
        bg_list.remove(focused_app)
        
    return {
        "focused": focused_app,
        "background": bg_list
    }

def save_state():
    apps_data = get_currently_open_apps()
    write_log(f"SAVING STATE: {apps_data}")
    
    if apps_data["focused"] or apps_data["background"]:
        with open(SAVE_FILE, "w") as f:
            json.dump(apps_data, f, indent=4)
        print(f"Checkpoint updated:\nFocus: {apps_data['focused']}\nBackground: {apps_data['background']}")
    else:
        print("Checkpoint clear or background apps ignored.")

def monitor_apps():
    print(f"Monitoring Android activity events... (Logging to {DEBUG_LOG})")
    write_log("STARTED MONITORING")
    
    logcat_cmd = [
        "su", "-c", 
        "logcat -b events am_create_activity:I am_destroy_activity:I am_resume_activity:I am_pause_activity:I wm_activity_resume:I *:S"
    ]
    process = subprocess.Popen(logcat_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True)

    last_trigger = 0

    try:
        for line in process.stdout:
            if "am_" in line or "wm_" in line:
                now = time.time()
                if now - last_trigger > 2.5:
                    write_log(f"TRIGGER: {line.strip()}")
                    time.sleep(1)
                    save_state()
                    last_trigger = time.time()
    except KeyboardInterrupt:
        process.terminate()
        write_log("STOPPED MONITORING")
        print("\nMonitoring stopped.")

def restore_state():
    if not os.path.exists(SAVE_FILE):
        print("No restoration file found.")
        return

    try:
        with open(SAVE_FILE, "r") as f:
            apps_data = json.load(f)
        
        focused = apps_data.get("focused", "")
        background = apps_data.get("background", [])
        
        if not focused and not background:
            print("No apps to restore.")
            return

        print(f"Restoring {len(background)} background apps...")
        for app in background:
            print(f"Opening Background: {app}")
            run_su(f"am start -n {app}")
            time.sleep(2)
            
        if focused:
            print(f"Restoring Focused App: {focused}")
            run_su(f"am start -n {focused}")
            time.sleep(2)
            
        os.remove(SAVE_FILE)
        print("Restoration complete.")
        
    except Exception as e:
        print(f"Restoration error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "restore":
            restore_state()
        elif sys.argv[1] == "monitor":
            monitor_apps()
    else:
        save_state()
