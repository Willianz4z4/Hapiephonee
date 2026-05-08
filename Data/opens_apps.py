import os
import subprocess
import time

SESSION_FILE = "/sdcard/Download/session_restore.txt"
BLACKLIST = ["com.termux", "com.og.launcher", "com.android.launcher", "com.android.systemui"]

def run_su(cmd):
    return subprocess.getoutput(f"su -c '{cmd}'")

def restore_session():
    if not os.path.exists(SESSION_FILE):
        return

    try:
        with open(SESSION_FILE, "r") as f:
            raw_text = f.read()
    except:
        return

    clean_text = raw_text.replace('\n', '').replace('\r', '').strip()
    if not clean_text:
        return

    apps = [app.strip() for app in clean_text.split(',') if app.strip()]
    
    apps_to_open = []
    for app in list(dict.fromkeys(apps)):
        if not any(blocked in app for blocked in BLACKLIST):
            apps_to_open.append(app)

    if not apps_to_open:
        return

    run_su("input keyevent 3")
    time.sleep(2)

    for app in apps_to_open:
        run_su(f"monkey -p {app} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1")
        time.sleep(3)

    try:
        os.remove(SESSION_FILE)
    except:
        pass

if __name__ == "__main__":
    time.sleep(12)
    restore_session()
