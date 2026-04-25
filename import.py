import os
import sys
import subprocess
import time

if len(sys.argv) > 1:
    user_id = sys.argv[1]
else:
    user_id = ""

URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
URL_REQS = "https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/requerimentos.txt"


report = {
    "installation_status": "pending",
    "steps": {},
    "system_info": {}
}

print("🔄 Preparing your Cloud Phone environment...")

os.system("pkg update -y -q > /dev/null 2>&1 && pkg upgrade -y -q > /dev/null 2>&1")
os.system("pkg install curl openssl -y -q > /dev/null 2>&1")
os.system("pkg install tsu -y -q > /dev/null 2>&1")

try:
    os.system(f"curl -sL {URL_REQS} -o reqs.txt > /dev/null 2>&1")
    pip_result = os.system("pip install -r reqs.txt -q > /dev/null 2>&1")
    
    if pip_result == 0:
        report["steps"]["pip_packages"] = "Success"
    else:
        report["steps"]["pip_packages"] = "Failed"
except:
    report["steps"]["pip_packages"] = "Failed"

def get_data(command):
    try:
        return subprocess.check_output(f"su -c '{command}'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except:
        return "Unknown"

try:
    root_test = get_data("echo root_ok")
    has_root = True if root_test == "root_ok" else False
except:
    has_root = False

try:
    model = get_data("getprop ro.product.model")
    android_version = get_data("getprop ro.build.version.release")
    device_id = get_data("settings get secure android_id")
    
    region = get_data("getprop persist.sys.locale")
    if region == "Unknown" or not region:
        region = get_data("getprop ro.product.locale")
        
    cpu_abi = get_data("getprop ro.product.cpu.abi")
    if "64" in cpu_abi:
        processor = "64 bits"
    elif cpu_abi != "Unknown" and cpu_abi:
        processor = "32 bits"
    else:
        processor = "Unknown"

    report["system_info"] = {
        "root_access": has_root,
        "model": model,
        "android_version": android_version,
        "device_id": device_id,
        "region": region,
        "processor": processor
    }
    report["steps"]["data_collection"] = "Success"
except:
    report["steps"]["data_collection"] = "Failed"

report["installation_status"] = "Completed"
print("✅ Configuration finished! Connecting to control panel...")

while True:
    try:
        try:
            import requests
        except ImportError:
            print("⏳ Installing network dependencies...")
            os.system("pip install requests -q > /dev/null 2>&1")
            import requests

        payload = {
            "guild_id": user_id,
            "message": "Connection attempt finalized.",
            "report": report
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": AUTH_SECRET
        }
        
        response = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("🚀 Device synchronized successfully!")
            break
        else:
            print(f"⚠️ Server busy ({response.status_code}). Retrying in 5 seconds...")
            time.sleep(5)
            
    except Exception as e:
        print("📡 No connection or network error. Reconnecting in 5 seconds...")
        time.sleep(5)
