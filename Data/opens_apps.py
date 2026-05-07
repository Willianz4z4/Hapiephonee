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

def load_json():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

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
        
    return focused_app, bg_list

def save_state():
    focused, background = get_currently_open_apps()
    old_data = load_json()
    new_data = {}
    
    if focused:
        new_data[focused] = {"state": "focused", "score": 0}
        
    for bg in background:
        new_data[bg] = {"state": "background", "score": 0}
        
    for pkg, data in old_data.items():
        if pkg not in new_data:
            new_data[pkg] = data
            
    write_log(f"SAVING STATE: {new_data}")
    
    with open(SAVE_FILE, "w") as f:
        json.dump(new_data, f, indent=4)
        
    print(f"Checkpoint updated. Tracking {len(new_data)} apps.")

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
    data = load_json()
    if not data:
        print("No apps to restore.")
        return

    valid_apps = {}
    for pkg, info in data.items():
        info["score"] += 1
        if info["score"] <= 5:
            valid_apps[pkg] = info
        else:
            write_log(f"DROPPED APP (Score > 5): {pkg}")

    with open(SAVE_FILE, "w") as f:
        json.dump(valid_apps, f, indent=4)

    bg_apps = [pkg for pkg, info in valid_apps.items() if info["state"] == "background"]
    focus_apps = [pkg for pkg, info in valid_apps.items() if info["state"] == "focused"]

    print(f"Restoring {len(bg_apps)} background apps...")
    for app in bg_apps:
        print(f"Opening Background: {app}")
        run_su(f"am start -n {app}")
        time.sleep(2)
        
    print(f"Restoring {len(focus_apps)} focused apps...")
    for app in focus_apps:
        print(f"Opening Focused: {app}")
        run_su(f"am start -n {app}")
        time.sleep(2)

    print("Returning focus to Termux...")
    run_su("am start -n com.termux/com.termux.app.TermuxActivity")
    time.sleep(1)
        
    print("Restoration sequence complete.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "restore":
            restore_state()
        elif sys.argv[1] == "monitor":
            monitor_apps()
    else:
        save_state()
