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
    return subprocess.run(f"su -c '{cmd}'", shell=True, capture_output=True, text=True)

def get_app_name(tmp_path, default_pkg):
    cmd = f"aapt dump badging {tmp_path} | grep 'application-label:' | head -n 1 | cut -d\\' -f2"
    app_name = subprocess.getoutput(cmd).strip()
    return app_name if app_name else default_pkg

def install_apk(url, visibility):
    tmp_path = os.path.join(BASE_DIR, "temp_install.apk")
    
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    
    if "drive.google.com" in url:
        os.system(f"gdown '{url}' -O {tmp_path} > /dev/null 2>&1")
    else:
        os.system(f"curl -sL '{url}' -o {tmp_path} > /dev/null 2>&1")

    if os.path.exists(tmp_path):
        cmd_get_pkg = f"aapt dump badging {tmp_path} | grep package | awk '{{print $2}}' | sed s/name=//g | sed s/\\'//g"
        pkg_name = subprocess.getoutput(cmd_get_pkg).strip()
        
        if pkg_name:
            app_name = get_app_name(tmp_path, pkg_name)
            run_su(f"pm install -r {tmp_path}")
            
            if visibility == "oculto":
                run_su(f"pm hide {pkg_name}")
                log(f"📥 {app_name} - Installed & Hidden")
            else:
                run_su(f"pm unhide {pkg_name}")
                log(f"📥 {app_name} - Installed")
                
            os.remove(tmp_path)
            return pkg_name, app_name
            
    return None, None

def inject_data(data_url, package_name, app_name):
    tmp_data = os.path.join(BASE_DIR, "data_inject.tar.gz")
    target_path = f"/data/data/{package_name}"
    
    if os.path.exists(tmp_data):
        os.remove(tmp_data)
    
    if "drive.google.com" in data_url:
        os.system(f"gdown '{data_url}' -O {tmp_data} > /dev/null 2>&1")
    else:
        os.system(f"curl -sL '{data_url}' -o {tmp_data} > /dev/null 2>&1")

    if os.path.exists(tmp_data):
        run_su(f"am force-stop {package_name}")
        extraction = run_su(f"tar -xzf {tmp_data} -C {target_path}")
        
        if extraction.returncode == 0:
            run_su(f"chown -R $(stat -c %u {target_path}):$(stat -c %g {target_path}) {target_path}")
            log(f"📁 {app_name} - Data Injected")
            
        os.remove(tmp_data)

def remove_app(package_name):
    run_su(f"pm uninstall {package_name}")
    log(f"🗑️ {package_name} - Removed")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
        
        if "instalar" in data:
            for item in data["instalar"]:
                apk_url = item[0]
                visibility = item[1]
                extra = item[3]
                
                pkg, app_name = install_apk(apk_url, visibility)
                
                if pkg and extra.get("data_link"):
                    inject_data(extra["data_link"], pkg, app_name)

        if "comandos" in data:
            for cmd in data["comandos"]:
                if cmd.startswith("remove "):
                    target_pkg = cmd.replace("remove ", "").strip()
                    remove_app(target_pkg)
                else:
                    run_su(cmd)

    except Exception:
        pass
