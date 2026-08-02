import sys
import os
import time
import json
import subprocess
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

FUNCTIONS_FILE = os.path.join(BASE_DIR, "functions.json")
DAEMON_CACHE = os.path.join(CURRENT_DIR, ".daemon_cache.json")
DATA_DIR = os.path.join(BASE_DIR, "Data")

def check_local_status():
    if os.path.exists(FUNCTIONS_FILE):
        try:
            with open(FUNCTIONS_FILE, "r") as f:
                config = json.load(f)
                return config.get("auto_copy", config.get("autocopy", False))
        except: pass
    return False

def is_macrodroid_running():
    """Verifica silenciosamente se o processo do MacroDroid está vivo"""
    try:
        res = subprocess.run('su -c "pidof com.arlosoft.macrodroid"', shell=True, capture_output=True, text=True)
        return bool(res.stdout.strip())
    except: 
        return False

# Identifica se é o Daemon rodando (Iniciado pelo import.py)
is_daemon = len(sys.argv) == 5 and sys.argv[4].startswith("http")

# =========================================================
# MODO 1: GATILHO MACRODROID
# =========================================================
if not is_daemon and len(sys.argv) >= 2:
    msg_id = sys.argv[1]
    texto_recebido = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    if not texto_recebido.strip():
        texto_recebido = "[TEXTO VAZIO OU BLOQUEADO PELO ANDROID]"

    print(f"🤖 [MACRODROID TRIGGER] ID: {msg_id} | Texto: {texto_recebido}", flush=True)

    if not check_local_status():
        print("🔴 [GATILHO] Painel desligado. Ignorando envio para nuvem.", flush=True)
        sys.exit(0)

    try:
        from security_system.core import gerar_assinatura_hmac, obter_dna_dispositivo
    except ImportError:
        print("❌ [FALHA] Falha de segurança ao carregar o Cofre.")
        sys.exit(5)

    # 1. Recupera as credenciais que o Daemon (import.py) salvou
    try:
        with open(DAEMON_CACHE, "r") as f:
            cache_data = json.load(f)
            DEVICE_ID = cache_data.get("device_id", "")
            GUILD_ID = cache_data.get("guild_id", "")
            OWNER_ID = cache_data.get("owner_id", "")
            URL_WEBHOOK = cache_data.get("webhook_url", "")
    except Exception as e:
        print(f"❌ [FALHA] Não foi possível ler as credenciais do Daemon: {e}")
        URL_WEBHOOK = "https://pandanaceous-meghann-nonincarnate.ngrok-free.dev/webhook"
        DEVICE_ID = ""
        GUILD_ID = ""
        OWNER_ID = ""

    def enviar_para_nuvem(unique_id, texto_copiado):
        dna_seguro = obter_dna_dispositivo()
        ts_agora = int(time.time())
        assinatura = gerar_assinatura_hmac(dna_seguro, ts_agora)

        # 2. Agora o payload envia as credenciais idênticas ao import.py
        payload = {
            "event": "clipboard_sync",
            "message_id": unique_id,
            "device_id": DEVICE_ID,
            "guild_id": GUILD_ID,
            "owner_id": OWNER_ID,
            "device_dna": dna_seguro,
            "timestamp": ts_agora,
            "clipboard_text": texto_copiado
        }
        envelope_seguro = {
            "signature": assinatura,
            "payload": payload
        }

        try:
            print(f"📤 Enviando para o Webhook com IDs completos...", flush=True)
            headers = {"Content-Type": "application/json", "ngrok-skip-browser-warning": "true"}
            requests.post(URL_WEBHOOK, json=envelope_seguro, headers=headers, timeout=10)
        except Exception as e:
            print(f"❌ [ERRO] Falha de conexão: {e}")

    enviar_para_nuvem(msg_id, texto_recebido)
    sys.exit(0)

# =========================================================
# MODO 2: DAEMON (CÃO DE GUARDA RESPEITANDO O USUÁRIO)
# =========================================================
if not is_daemon:
    sys.exit(1)

# 3. Salva os dados de autenticação passados pelo import.py
try:
    cache_data = {
        "device_id": sys.argv[1],
        "guild_id": sys.argv[2],
        "owner_id": sys.argv[3],
        "webhook_url": sys.argv[4]
    }
    with open(DAEMON_CACHE, "w") as f:
        json.dump(cache_data, f)
except: pass

def verificar_e_iniciar_macrodroid():
    os.makedirs(DATA_DIR, exist_ok=True)
    subprocess.run('su -c "pm unhide com.arlosoft.macrodroid > /dev/null 2>&1"', shell=True)
    time.sleep(1)
    print("🔄 Iniciando o serviço do MacroDroid em background...", flush=True)
    subprocess.run('su -c "am start-service -n com.arlosoft.macrodroid/com.arlosoft.macrodroid.triggers.services.MacroDroidAccessibilityServiceJellyBean > /dev/null 2>&1"', shell=True)

def forcar_acessibilidade():
    servicos = "com.arlosoft.macrodroid/com.arlosoft.macrodroid.triggers.services.MacroDroidAccessibilityServiceJellyBean:com.arlosoft.macrodroid/com.arlosoft.macrodroid.UIInteractionAccessibilityService:com.arlosoft.macrodroid/com.arlosoft.macrodroid.MacroDroidAccessibilityService"
    subprocess.run('su -c "settings put secure accessibility_enabled 0 > /dev/null 2>&1"', shell=True)
    subprocess.run(f'su -c "settings put secure enabled_accessibility_services {servicos} > /dev/null 2>&1"', shell=True)
    subprocess.run('su -c "settings put secure accessibility_enabled 1 > /dev/null 2>&1"', shell=True)
    subprocess.run('su -c "dumpsys deviceidle whitelist +com.arlosoft.macrodroid > /dev/null 2>&1"', shell=True)

def main():
    print("📡 Hapiephone Copy System Online (Watchdog Inteligente + Auth)...", flush=True)
    subprocess.run("termux-wake-lock", shell=True, check=False)
    
    estado_ativo = False
    
    while True:
        deve_rodar = check_local_status()
        
        if deve_rodar:
            if not estado_ativo:
                print("🟢 [GATILHO] Sistema de Cópia LIGADO pelo usuário. Ativando serviços...", flush=True)
                forcar_acessibilidade()
                verificar_e_iniciar_macrodroid()
                estado_ativo = True
            
            if not is_macrodroid_running():
                print("⚠️ [WATCHDOG] O Android fechou o MacroDroid! Ressuscitando em background...", flush=True)
                forcar_acessibilidade()
                verificar_e_iniciar_macrodroid()
                
        else:
            if estado_ativo:
                print("🔴 [GATILHO] Sistema de Cópia DESLIGADO pelo usuário.", flush=True)
                estado_ativo = False
            
        time.sleep(5)

if __name__ == "__main__":
    main()
