import sys
import time
import subprocess
import os
import json

if len(sys.argv) < 5:
    print(f"❌ [FATAL ERROR] Faltam argumentos! Recebido: {sys.argv}", flush=True)
    sys.exit(1)

DEVICE_ID = sys.argv[1]
GUILD_ID = sys.argv[2]
OWNER_ID = sys.argv[3]
URL_WEBHOOK = sys.argv[4]

CONFIG_FILE = "hapie_config.json"
FUNCTIONS_FILE = "functions.json"

def obter_client_token():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f).get("client_token", "")
        except: pass
    return ""

def check_local_status():
    if os.path.exists(FUNCTIONS_FILE):
        try:
            with open(FUNCTIONS_FILE, "r") as f:
                config = json.load(f)
                return config.get("auto_copy", config.get("autocopy", False))
        except: pass
    return False

def forcar_acessibilidade():
    """Força a permissão de Acessibilidade e Armazenamento via Root"""
    print("🔧 [SETUP] Injetando permissões de Acessibilidade no sistema...", flush=True)
    servicos = "com.arlosoft.macrodroid/com.arlosoft.macrodroid.triggers.services.MacroDroidAccessibilityServiceJellyBean:com.arlosoft.macrodroid/com.arlosoft.macrodroid.UIInteractionAccessibilityService:com.arlosoft.macrodroid/com.arlosoft.macrodroid.MacroDroidAccessibilityService"
    subprocess.run('su -c "settings put secure accessibility_enabled 0 > /dev/null 2>&1"', shell=True)
    subprocess.run(f'su -c "settings put secure enabled_accessibility_services {servicos} > /dev/null 2>&1"', shell=True)
    subprocess.run('su -c "settings put secure accessibility_enabled 1 > /dev/null 2>&1"', shell=True)

    print("📂 [SETUP] Liberando acesso ao armazenamento (Legado) para o MacroDroid...", flush=True)
    subprocess.run('su -c "pm grant com.arlosoft.macrodroid android.permission.WRITE_EXTERNAL_STORAGE > /dev/null 2>&1"', shell=True)
    subprocess.run('su -c "pm grant com.arlosoft.macrodroid android.permission.READ_EXTERNAL_STORAGE > /dev/null 2>&1"', shell=True)
    subprocess.run('su -c "appops set com.arlosoft.macrodroid LEGACY_STORAGE allow > /dev/null 2>&1"', shell=True)

def sync_com_macrodroid(ativar):
    token = obter_client_token()
    if ativar:
        print("🚀 [SYNC] Ligando MacroDroid e enviando variáveis...", flush=True)
        cmd = f"""su -c "am broadcast -a hapiephone.sync --es url_webhook '{URL_WEBHOOK}' --es device_id '{DEVICE_ID}' --es guild_id '{GUILD_ID}' --es owner_id '{OWNER_ID}' --es client_token '{token}'" > /dev/null 2>&1"""
    else:
        print("🛑 [SYNC] Pausando automação de cópia...", flush=True)
        cmd = f"""su -c "am broadcast -a hapiephone.stop_sync" > /dev/null 2>&1"""
    
    subprocess.run(cmd, shell=True)

def main():
    print("📡 Hapiephone Copy System (Modo Bridge MacroDroid) Online...", flush=True)
    subprocess.run("termux-wake-lock", shell=True, check=False)
    
    # Injeta todas as permissões no sistema ao iniciar
    forcar_acessibilidade()
    
    estado_ativo = False

    while True:
        deve_rodar = check_local_status()
        
        if deve_rodar and not estado_ativo:
            sync_com_macrodroid(True)
            estado_ativo = True
        elif not deve_rodar and estado_ativo:
            sync_com_macrodroid(False)
            estado_ativo = False

        time.sleep(5)

if __name__ == "__main__":
    main()
