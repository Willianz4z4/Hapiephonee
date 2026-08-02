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
INIT_MARKER_FILE = os.path.join(DATA_DIR, "macrodroid_initialized.json")

def check_local_status():
    if os.path.exists(FUNCTIONS_FILE):
        try:
            with open(FUNCTIONS_FILE, "r") as f:
                config = json.load(f)
                return config.get("auto_copy", config.get("autocopy", False))
        except: pass
    return False

# Identifica se é o Daemon rodando (Tem 5 argumentos e o último é o Webhook HTTP)
is_daemon = len(sys.argv) == 5 and sys.argv[4].startswith("http")

# =========================================================
# MODO 1: GATILHO MACRODROID
# =========================================================
if not is_daemon and len(sys.argv) >= 2:
    msg_id = sys.argv[1]

    # Junta tudo que vier depois do ID. Se o shell quebrar espaços, o Python conserta.
    texto_recebido = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    # Se mesmo assim estiver vazio, avisa no print para não ficar em branco
    if not texto_recebido.strip():
        texto_recebido = "[TEXTO VAZIO OU BLOQUEADO PELO ANDROID]"

    print(f"🤖 [MACRODROID TRIGGER] ID: {msg_id} | Texto: {texto_recebido}", flush=True)

    try:
        debug_log_path = os.path.join(CURRENT_DIR, "debug_macrodroid.log")
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ID: {msg_id} | Recebido: {texto_recebido}\n")
    except Exception as e:
        print(f"Erro ao salvar log de debug: {e}")

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
            print(f"📤 Enviando ID {unique_id} para o Webhook: {URL_WEBHOOK}...", flush=True)
            headers_seguros = {
                "Content-Type": "application/json",
                "ngrok-skip-browser-warning": "true"
            }
            resposta = requests.post(URL_WEBHOOK, json=envelope_seguro, headers=headers_seguros, timeout=10)
            print(f"✅ Webhook respondeu: {resposta.status_code}")
        except Exception as e:
            print(f"❌ Erro ao enviar webhook: {e}")

    enviar_para_nuvem(msg_id, texto_recebido)
    sys.exit(0)

# =========================================================
# MODO 2: DAEMON
# =========================================================
if not is_daemon:
    print(f"❌ [FATAL ERROR] Faltam argumentos para o Daemon! Recebido: {sys.argv}", flush=True)
    sys.exit(1)

DEVICE_ID = sys.argv[1]
GUILD_ID = sys.argv[2]
OWNER_ID = sys.argv[3]
URL_WEBHOOK = sys.argv[4]

try:
    with open(WEBHOOK_CACHE, "w") as f:
        f.write(URL_WEBHOOK)
except:
    pass

def verificar_e_iniciar_macrodroid():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # O "if os.path.exists(INIT_MARKER_FILE): return" foi removido daqui
    # para garantir que o MacroDroid sempre seja reaberto.
    
    subprocess.run('su -c "pm unhide com.arlosoft.macrodroid"', shell=True, capture_output=True)
    time.sleep(1)
    subprocess.run('su -c "monkey -p com.arlosoft.macrodroid 1"', shell=True, capture_output=True)
    time.sleep(5)
    subprocess.run('su -c "pm hide com.arlosoft.macrodroid"', shell=True, capture_output=True)
    
    try:
        with open(INIT_MARKER_FILE, "w") as f:
            json.dump({"initialized": True, "timestamp": time.time()}, f)
    except: pass

def forcar_acessibilidade():
    servicos = "com.arlosoft.macrodroid/com.arlosoft.macrodroid.triggers.services.MacroDroidAccessibilityServiceJellyBean:com.arlosoft.macrodroid/com.arlosoft.macrodroid.UIInteractionAccessibilityService:com.arlosoft.macrodroid/com.arlosoft.macrodroid.MacroDroidAccessibilityService"
    subprocess.run('su -c "settings put secure accessibility_enabled 0 > /dev/null 2>&1"', shell=True)
    subprocess.run(f'su -c "settings put secure enabled_accessibility_services {servicos} > /dev/null 2>&1"', shell=True)
    subprocess.run('su -c "settings put secure accessibility_enabled 1 > /dev/null 2>&1"', shell=True)
    subprocess.run('su -c "dumpsys deviceidle whitelist +com.arlosoft.macrodroid > /dev/null 2>&1"', shell=True)
    subprocess.run('su -c "dumpsys deviceidle whitelist +com.termux > /dev/null 2>&1"', shell=True)
    subprocess.run('su -c "am force-stop com.arlosoft.macrodroid"', shell=True)

def main():
    print("📡 Hapiephone Copy System Online (Modo Híbrido Seguro)...", flush=True)
    subprocess.run("termux-wake-lock", shell=True, check=False)
    forcar_acessibilidade()
    verificar_e_iniciar_macrodroid()
    estado_ativo = False
    while True:
        deve_rodar = check_local_status()
        if deve_rodar and not estado_ativo:
            print("🟢 [GATILHO] Sistema de Cópia LIGADO. Aguardando gatilho invisível...", flush=True)
            estado_ativo = True
        elif not deve_rodar and estado_ativo:
            print("🔴 [GATILHO] Sistema de Cópia DESLIGADO.", flush=True)
            estado_ativo = False
        time.sleep(5)

if __name__ == "__main__":
    main()
