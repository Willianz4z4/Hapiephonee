import sys
import os
import time
import json
import subprocess
import requests

# 1. Configura caminhos absolutos (Para o MacroDroid não se perder na hora de executar)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

FUNCTIONS_FILE = os.path.join(CURRENT_DIR, "functions.json")
WEBHOOK_CACHE = os.path.join(CURRENT_DIR, ".webhook_cache")

def check_local_status():
    """Lê o JSON para saber se o sistema de cópia está ativado no painel."""
    if os.path.exists(FUNCTIONS_FILE):
        try:
            with open(FUNCTIONS_FILE, "r") as f:
                config = json.load(f)
                return config.get("auto_copy", config.get("autocopy", False))
        except: pass
    return False

# =========================================================
# MODO 1: GATILHO MACRODROID (Executado via root)
# Ex: python auto_copy.py 'texto copiado'
# =========================================================
if len(sys.argv) == 2:
    texto_recebido = sys.argv[1]
    
    # ---------------------------------------------------------
    # DEBUG: Mostra no console e salva em arquivo para auditoria
    # ---------------------------------------------------------
    print(f"🤖 [MACRODROID TRIGGER] Texto interceptado: {texto_recebido}", flush=True)
    
    try:
        debug_log_path = os.path.join(CURRENT_DIR, "debug_macrodroid.log")
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Recebido: {texto_recebido}\n")
    except Exception as e:
        print(f"Erro ao salvar log de debug: {e}")
    # ---------------------------------------------------------

    # Se o botão no seu painel estiver desligado, o script morre sem enviar nada
    if not check_local_status():
        print("🔴 [GATILHO] Painel desligado. Ignorando envio para nuvem.", flush=True)
        sys.exit(0)

    try:
        # Acesso ao Cofre (Se o invasor interceptar, o Kamikaze detona aqui)
        from security_system.core import gerar_assinatura_hmac, obter_dna_dispositivo
    except ImportError:
        print("❌ [FALHA] Falha de segurança ao carregar o Cofre.")
        sys.exit(5)

    # Puxa a URL dinâmica salva pelo Daemon (evita quebrar se o Ngrok mudar)
    try:
        with open(WEBHOOK_CACHE, "r") as f:
            URL_WEBHOOK = f.read().strip()
    except:
        URL_WEBHOOK = "https://pandanaceous-meghann-nonincarnate.ngrok-free.dev/webhook"

    def enviar_para_nuvem(texto_copiado):
        dna_seguro = obter_dna_dispositivo()
        ts_agora = int(time.time())
        assinatura = gerar_assinatura_hmac(dna_seguro, ts_agora)

        payload = {
            "event": "clipboard_sync",
            "device_dna": dna_seguro,
            "timestamp": ts_agora,
            "clipboard_text": texto_copiado
        }

        envelope_seguro = {
            "signature": assinatura,
            "payload": payload
        }

        try:
            print(f"📤 Enviando para o Webhook: {URL_WEBHOOK}...", flush=True)
            resposta = requests.post(URL_WEBHOOK, json=envelope_seguro, headers={"Content-Type": "application/json"}, timeout=10)
            print(f"✅ Webhook respondeu: {resposta.status_code}")
        except Exception as e:
            print(f"❌ Erro ao enviar webhook: {e}")

    # Dispara a função com o texto que o MacroDroid passou e encerra a execução
    enviar_para_nuvem(texto_recebido)
    sys.exit(0)

# =========================================================
# MODO 2: DAEMON (Botão Ligado - Chamado pelo task_orchestrator)
# Ex: python auto_copy.py DEVICE_ID GUILD_ID OWNER_ID URL_WEBHOOK
# =========================================================
if len(sys.argv) < 5:
    print(f"❌ [FATAL ERROR] Faltam argumentos para o Daemon! Recebido: {sys.argv}", flush=True)
    sys.exit(1)

DEVICE_ID = sys.argv[1]
GUILD_ID = sys.argv[2]
OWNER_ID = sys.argv[3]
URL_WEBHOOK = sys.argv[4]

# Salva a URL dinamicamente para que o Modo 1 (MacroDroid) consiga ler com segurança
try:
    with open(WEBHOOK_CACHE, "w") as f:
        f.write(URL_WEBHOOK)
except: pass

def forcar_acessibilidade():
    print("🔧 [SETUP] Injetando permissões de Acessibilidade no sistema...", flush=True)
    servicos = "com.arlosoft.macrodroid/com.arlosoft.macrodroid.triggers.services.MacroDroidAccessibilityServiceJellyBean:com.arlosoft.macrodroid/com.arlosoft.macrodroid.UIInteractionAccessibilityService:com.arlosoft.macrodroid/com.arlosoft.macrodroid.MacroDroidAccessibilityService"
    subprocess.run('su -c "settings put secure accessibility_enabled 0 > /dev/null 2>&1"', shell=True)
    subprocess.run(f'su -c "settings put secure enabled_accessibility_services {servicos} > /dev/null 2>&1"', shell=True)
    subprocess.run('su -c "settings put secure accessibility_enabled 1 > /dev/null 2>&1"', shell=True)

def main():
    print("📡 Hapiephone Copy System Online (Modo Híbrido Seguro)...", flush=True)
    subprocess.run("termux-wake-lock", shell=True, check=False)

    forcar_acessibilidade()
    estado_ativo = False

    while True:
        deve_rodar = check_local_status()

        if deve_rodar and not estado_ativo:
            print("🟢 [GATILHO] Sistema de Cópia LIGADO. Aguardando gatilho invisível do MacroDroid...", flush=True)
            estado_ativo = True

        elif not deve_rodar and estado_ativo:
            print("🔴 [GATILHO] Sistema de Cópia DESLIGADO.", flush=True)
            estado_ativo = False

        time.sleep(5)

if __name__ == "__main__":
    main()
