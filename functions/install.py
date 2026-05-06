import os
import sys
import json
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "install_log.txt")

def log(msg):
    print(msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {msg}\n")
    except:
        pass

def run_su(cmd):
    result = subprocess.run(f"su -c '{cmd}'", shell=True, capture_output=True, text=True)
    if result.returncode != 0 and result.stderr:
        log(f"⚠️ Root Warning: {result.stderr.strip()}")
    return result

def install_apk(url, visibility):
    tmp_path = os.path.join(BASE_DIR, "temp_install.apk")
    
    log("📥 Starting APK download...")
    
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    
    if "drive.google.com" in url:
        os.system(f"gdown '{url}' -O {tmp_path}")
    else:
        os.system(f"curl -sL '{url}' -o {tmp_path}")

    if os.path.exists(tmp_path):
        log("⚙️ Installing package via Root...")
        run_su(f"pm install -r {tmp_path}")
        
        cmd_get_pkg = f"aapt dump badging {tmp_path} | grep package | awk '{{print $2}}' | sed s/name=//g | sed s/\\'//g"
        pkg_name = subprocess.getoutput(cmd_get_pkg).strip()
        
        if pkg_name:
            log(f"📦 Package identified: {pkg_name}")
            if visibility == "oculto":
                run_su(f"pm hide {pkg_name}")
                log(f"👻 Package {pkg_name} hidden from launcher.")
            else:
                run_su(f"pm unhide {pkg_name}")
                
        os.remove(tmp_path)
        return pkg_name
    else:
        log("❌ Download failed. APK file not found.")
        return None

def inject_data(data_url, package_name):
    if not data_url or not package_name:
        return
    
    tmp_data = os.path.join(BASE_DIR, "data_inject.tar.gz")
    target_path = f"/data/data/{package_name}"
    
    log(f"📁 Downloading and injecting data (.tar.gz) for {package_name}...")
    
    if os.path.exists(tmp_data):
        os.remove(tmp_data)
    
    if "drive.google.com" in data_url:
        os.system(f"gdown '{data_url}' -O {tmp_data}")
    else:
        os.system(f"curl -sL '{data_url}' -o {tmp_data}")

    if os.path.exists(tmp_data):
        run_su(f"am force-stop {package_name}")
        
        extraction = run_su(f"tar -xzf {tmp_data} -C {target_path}")
        if extraction.returncode == 0:
            run_su(f"chown -R $(stat -c %u {target_path}):$(stat -c %g {target_path}) {target_path}")
            log("✅ Data injected and permissions fixed successfully!")
        else:
            log("❌ Error extracting .tar.gz file in app directory.")
            
        os.remove(tmp_data)
    else:
        log("❌ Failed to download data file.")

def remove_app(package_name):
    log(f"🗑️ Removing application: {package_name}")
    run_su(f"pm uninstall {package_name}")
    log(f"✅ {package_name} uninstalled.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        log("❌ Critical error: No JSON data received by the script.")
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
        log(f"🚀 --- NEW JOB RECEIVED ---")
        
        if "instalar" in data:
            for item in data["instalar"]:
                apk_url = item[0]
                visibility = item[1]
                extra = item[3]
                
                pkg = install_apk(apk_url, visibility)
                
                if pkg and extra.get("data_link"):
                    inject_data(extra["data_link"], pkg)

        if "comandos" in data:
            for cmd in data["comandos"]:
                if cmd.startswith("remove "):
                    target_pkg = cmd.replace("remove ", "").strip()
                    remove_app(target_pkg)
                else:
                    run_su(cmd)
                    log(f"⚙️ Generic root command executed: {cmd}")

        log("🏁 Processing finished successfully.")

    except Exception as e:
        log(f"❌ Fatal error during execution: {e}")
