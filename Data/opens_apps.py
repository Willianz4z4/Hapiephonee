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
        
        if ("ActivityRecord{" in line or "is_bubble" in line) and " u0 " in line:
            try:
                if "ActivityRecord{" in line:
                    target = line.split(" u0 ")[1].split(" ")[0]
                else:
                    target = line.split("realActivity=")[1].split(" ")[0]
                
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
    current_data = load_json()
    new_data = {}
    
    if focused:
        new_data[focused] = {"state": "focused", "score": 0}
        
    for bg in background:
        existing_score = current_data.get(bg, {}).get("score", 0)
        new_data[bg] = {"state": "background", "score": existing_score}
            
    with open(SAVE_FILE, "w") as f:
        json.dump(new_data, f, indent=4)
    
    write_log(f"SAVED: {new_data}")

def monitor_apps():
    print(f"Monitoring activities... Logging to {DEBUG_LOG}")
    logcat_cmd = ["su", "-c", "logcat -b events am_create_activity:I am_resume_activity:I wm_activity_resume:I *:S"]
    process = subprocess.Popen(logcat_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True)
    last_trigger = 0

    try:
        for line in process.stdout:
            now = time.time()
            if now - last_trigger > 3:
                save_state()
                last_trigger = now
    except KeyboardInterrupt:
        process.terminate()

def restore_state():
    data = load_json()
    if not data:
        print("No apps found.")
        return

    updated_data = {}
    bg_apps = []
    focus_apps = []

    for pkg, info in data.items():
        info["score"] += 1
        if info["score"] <= 5:
            updated_data[pkg] = info
            if info["state"] == "background":
                bg_apps.append(pkg)
            else:
                focus_apps.append(pkg)

    with open(SAVE_FILE, "w") as f:
        json.dump(updated_data, f, indent=4)

    for app in bg_apps:
        print(f"Restoring Background: {app}")
        run_su(f"am start -n {app}")
        time.sleep(1.5)
        
    for app in focus_apps:
        print(f"Restoring Focus: {app}")
        run_su(f"am start -n {app}")
        time.sleep(2)
        
    print("Restore complete. Focused app is now on top.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "restore":
            restore_state()
        elif sys.argv[1] == "monitor":
            monitor_apps()
    else:
        save_state()
