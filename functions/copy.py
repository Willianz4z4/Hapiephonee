import sys
import time
import subprocess
import requests
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from data.mongodb import db_read
except ImportError:
    print("Error: Could not import data.mongodb")
    sys.exit(1)

if len(sys.argv) < 3:
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]

URL_WEBHOOK_COPY = "https://hapiephoneugph.vercel.app/api/copy"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"

def get_clipboard():
    try:
        return subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except:
        return ""

last_clipboard = get_clipboard()

while True:
    try:
        config_list = db_read.obter_dados("HapiephoneDB", "server_config", guild_id)
        
        if config_list and len(config_list) > 0:
            config = config_list[0]
            
            copy_send = config.get("copy_Send", False)
            auto_copy_channel = config.get("auto_copy_channel")

            if copy_send and auto_copy_channel:
                current_clipboard = get_clipboard()

                if current_clipboard and current_clipboard != last_clipboard:
                    payload = {
                        "texto": current_clipboard,
                        "channel_id": auto_copy_channel,
                        "device_id": device_id,
                        "guild_id": guild_id
                    }
                    
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": AUTH_SECRET
                    }

                    resp = requests.post(URL_WEBHOOK_COPY, json=payload, headers=headers, timeout=5)
                    
                    if resp.status_code == 200:
                        last_clipboard = current_clipboard 
                        
    except Exception:
        pass 

    time.sleep(3)
