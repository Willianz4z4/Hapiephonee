import os
import json
import subprocess
import time
import re
import sys

DUMPSYS = "/system/bin/dumpsys"
AM = "/system/bin/am"
SAVE_FILE = os.path.expanduser("~/last_opened_apps.json")

def run_su(cmd):
    """Executa comando com shell explícito para pipes funcionarem"""
    return subprocess.getoutput(f"su -c 'sh -c \"{cmd}\"'")

def get_currently_open_apps():
    """Estratégia multi-nível: busca app em foco via dumpsys window"""
    
    # Primeiro, tenta obter via window (mais confiável)
    raw_data = run_su(f"{DUMPSYS} window windows | grep -E 'mCurrentFocus|mFocusedApp'")
    
    if not raw_data.strip():
        # Fallback: tenta via activity
        raw_data = run_su(f"{DUMPSYS} activity activities | grep -E 'mResumedActivity|Recent #0'")
    
    # Regex mais flexível para capturar pacotes/classes
    # Aceita: com.example.app/.MainActivity ou com.example.app/com.example.app.MainActivity
    pattern = r'([a-zA-Z][a-zA-Z0-9_.]*\/[a-zA-Z0-9_.$]+)'
    matches = re.findall(pattern, raw_data)
    
    apps = []
    for app in matches:
        app = app.strip()
        # Filtra apenas apps reais (opcional - remova se quiser system apps)
        if "com.termux" not in app and "com.android.systemui" not in app:
            apps.append(app)
    
    # Remove duplicatas mantendo ordem
    ordered_apps = []
    for a in apps:
        if a not in ordered_apps:
            ordered_apps.append(a)
    
    return ordered_apps

def save_state():
    apps = get_currently_open_apps()
    if apps:
        with open(SAVE_FILE, "w") as f:
            json.dump(apps, f, indent=2)
        print(f"✅ Checkpoint: {len(apps)} apps salvos.")
        print(f"📱 Apps: {apps}")
    else:
        print("⚠️ Nenhum app detectado.")
        print("💡 Debug: Certifique-se de que:")
        print("   1. O device tem permissões de root")
        print("   2. Termux tem acesso ao dumpsys")
        print("   3. Um app real está aberto (não home screen)")

def restore_state():
    if not os.path.exists(SAVE_FILE):
        print("ℹ️ Arquivo de restauração não encontrado.")
        return

    with open(SAVE_FILE, "r") as f:
        apps = json.load(f)
    
    print(f"🚀 Restaurando {len(apps)} apps...")
    for app in apps:
        print(f"🔄 Abrindo: {app}")
        run_su(f"{AM} start -W -n {app}")
        time.sleep(1)
    
    os.remove(SAVE_FILE)
    print("✅ Restauração concluída.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_state()
    else:
        save_state()