import os
import subprocess
import uuid

# Identifica a pasta onde este script está (agora é a pasta 'Protocols')
PROTOCOL_DIR = os.path.dirname(os.path.abspath(__file__))

def get_root_data(command):
    try:
        return subprocess.check_output(f"su -c '{command}'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except:
        return "Unknown"

def get_prop(command):
    try:
        return subprocess.check_output(command, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except:
        return "Unknown"

def get_phone_id():
    """Busca o Android ID nativo ou cria um artificial para o sistema"""
    device_id = get_root_data("settings get secure android_id")
    
    if device_id == "Unknown" or not device_id:
        device_id = get_prop("settings get secure android_id")

    if device_id == "Unknown" or not device_id:
        id_file = os.path.join(PROTOCOL_DIR, "ugphone_id.txt")
        if os.path.exists(id_file):
            with open(id_file, "r") as f:
                device_id = f.read().strip()
        else:
            device_id = "ug_" + uuid.uuid4().hex[:12]
            try:
                with open(id_file, "w") as f:
                    f.write(device_id)
            except:
                pass
                
    return device_id

def get_protocol():
    """Gera um protocolo único (protocol_xxxx) ou lê o existente"""
    protocol_file = os.path.join(PROTOCOL_DIR, "active_protocol.txt")
    
    if os.path.exists(protocol_file):
        with open(protocol_file, "r") as f:
            return f.read().strip()
    else:
        current_protocol = f"protocol_{uuid.uuid4().hex[:8]}"
        try:
            with open(protocol_file, "w") as f:
                f.write(current_protocol)
        except:
            pass
        return current_protocol

if __name__ == "__main__":
    print(f"✅ Phone ID : {get_phone_id()}")
    print(f"✅ Protocol : {get_protocol()}")
