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
WEBHOOK_CACHE = os.path.join(CURRENT_DIR, ".webhook_cache")
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

# Identifica se é o Daemon rodando
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

    try:
        debug_log_path = os.path.join(CURRENT_DIR, "debug_macrodroid.log")
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ID: {msg_id} | Recebido: {texto_recebido}\n")
    except: pass

    if not check_local_status():
        print("🔴 [GATILHO] Painel desligado. Ignorando envio para nuvem.", flush=True)
        sys.exit(0)

    try:
        from security_system.core import gerar_assinatura_hmac, obter_dna_dispositivo
    except ImportError:
        print("❌ [FALHA] Falha de segurança ao carregar o Cofre.")
        sys.exit(5)

    try:
        with open(WEBHOOK_CACHE, "r") as f:
            URL_WEBHOOK = f.read().strip()
    except:
        URL_WEBHOOK = "https://pandanaceous-meghann-nonincarnate.ngrok-free.dev/webhook"

    def enviar_para_nuvem(unique_id, texto_copiado):
        dna_seguro = obter_dna_dispositivo()
        ts_agora = int(time.time())
        assinatura = gerar_assinatura_hmac(dna_seguro, ts_agora)

        payload = {
            "event": "clipboard_sync",
            "message_id": unique_id,
            "device_dna": dna_seguro,
            "timestamp": ts_agora,
            "clipboard_text": texto_copiado
        }
        envelope_seguro = {
            "signature": assinatura,
            "payload": payload
        }

        try:
            print(f"📤 Enviando para o Webhook...", flush=True)
            headers = {"Content-Type": "application/json", "ngrok-skip-browser-warning": "true"}
            requests.post(URL_WEBHOOK, json=envelope_seguro, headers=headers, timeout=10)
        except: pass

    enviar_para_nuvem(msg_id, texto_recebido)
    sys.exit(0)

# =========================================================
# MODO 2: DAEMON (CÃO DE GUARDA RESPEITANDO O USUÁRIO)
# =========================================================
if not is_daemon:
    sys.exit(1)

try:
    with open(WEBHOOK_CACHE, "w") as f:
        f.write(sys.argv[4])
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
    print("📡 Hapiephone Copy System Online (Watchdog Inteligente)...", flush=True)
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
            
            # --- O CÃO DE GUARDA ---
            # Se estiver ligado no painel e o Android matar o MacroDroid, o script ressuscita ele.
            if not is_macrodroid_running():
                print("⚠️ [WATCHDOG] O Android fechou o MacroDroid! Ressuscitando em background...", flush=True)
                forcar_acessibilidade()
                verificar_e_iniciar_macrodroid()
                
        else:
            if estado_ativo:
                print("🔴 [GATILHO] Sistema de Cópia DESLIGADO pelo usuário.", flush=True)
                estado_ativo = False
            # Se estiver False no painel, o script fica em modo de espera silencioso, sem forçar nada.
            
        time.sleep(5)

if __name__ == "__main__":
    main()
