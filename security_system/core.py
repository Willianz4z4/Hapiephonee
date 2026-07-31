import subprocess
import time
import hashlib
import hmac
import os
import sys
import ctypes
import shutil

# ==========================================
# 🛑 CONFIGURAÇÕES CRÍTICAS C-LEVEL
# ==========================================
HMAC_SECRET = b"Hapie_Super_Secret_Key_2026_!@#"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXPECTED_HASHES = {}

def nuke_process(reason):
    """Mata o processo na raiz (C-level) e oblitera o repositório."""
    print(f"\n[🚨 HAPIE SECURITY LOCKDOWN 🚨]\nAcesso Negado: {reason}")
    
    # [🔥 PROTOCOLO TERRA ARRASADA 🔥]
    # PARA ATIVAR A DESTRUIÇÃO FÍSICA: Remova o '#' das 4 linhas abaixo
    # print("[🔥 INICIANDO PROTOCOLO TERRA ARRASADA... APAGANDO ARQUIVOS 🔥]")
    # if os.path.exists(BASE_DIR):
    #     shutil.rmtree(BASE_DIR, ignore_errors=True)
    # os.system(f"rm -rf {BASE_DIR}")
    
    os._exit(1)

def obter_dna_dispositivo():
    comandos_dna = {
        "android_id": "su -c 'settings get secure android_id'",
        "serial": "getprop ro.serialno",
        "placa": "getprop ro.board.platform"
    }
    dna_coletado = []
    for chave, comando in comandos_dna.items():
        try:
            res = subprocess.check_output(comando, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
            if res and res.lower() != "unknown":
                dna_coletado.append(res)
        except: pass
    dna_bruto = "|".join(dna_coletado) if dna_coletado else "fallback_gen_id"
    return hashlib.sha256(dna_bruto.encode('utf-8')).hexdigest()

def gerar_assinatura_hmac(dna, timestamp):
    mensagem = f"{dna}:{timestamp}".encode('utf-8')
    return hmac.new(HMAC_SECRET, mensagem, hashlib.sha256).hexdigest()

def check_file_integrity():
    for relative_path, expected_hash in EXPECTED_HASHES.items():
        filepath = os.path.join(BASE_DIR, relative_path.replace("/", os.sep))
        if not os.path.exists(filepath):
            nuke_process(f"Arquivo vital ausente: {relative_path}")
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            if sha256_hash.hexdigest() != expected_hash:
                nuke_process(f"Código adulterado detectado no arquivo: {relative_path}")
        except Exception as e:
            nuke_process(f"Falha de integridade ({relative_path}): {e}")

def run_security_checks():
    main_script = os.path.abspath(sys.argv[0])
    if "Hapiephonee" not in main_script:
        nuke_process("Tentativa de importação externa não autorizada.")

    for proxy_var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
        if proxy_var in os.environ:
            nuke_process(f"Interceptação de Rede (Proxy: {proxy_var})")

    # --- DEFESAS ANTI-ENGENHARIA REVERSA ---

    # Nível 1: Debuggers Python
    if sys.gettrace() is not None:
        nuke_process("Debugger Python Ativo.")

    # Nível 2: O Autogrampo C-Level (Anti-Root / Anti-Strace)
    # Aciona a API nativa do C. O valor 0 significa PTRACE_TRACEME.
    try:
        libc = ctypes.CDLL(None)
        if libc.ptrace(0, 0, 0, 0) < 0:
            nuke_process("Interceptação Kernel Detectada (Bloqueio PTRACE).")
    except Exception:
        pass

    # Nível 3: Leitura de TracerPid (Fallback para sistemas sem restrição severa de ptrace)
    try:
        with open('/proc/self/status', 'r') as f:
            for linha in f:
                if linha.startswith('TracerPid:'):
                    tracer_pid = int(linha.split(':')[1].strip())
                    if tracer_pid != 0:
                        nuke_process(f"Interceptação Kernel Detectada (TracerPid: {tracer_pid})")
                    break
    except Exception:
        pass

    # Nível 4: Varredura de Injeção em Memória RAM (Anti-Frida / Anti-Xposed / Magisk)
    try:
        with open('/proc/self/maps', 'r') as f:
            maps_data = f.read().lower()
            # Se encontrar o nome dessas ferramentas mapeadas na memória do bot:
            for malware in ['frida', 'xposed', 'edxposed', 'lsposed', 'magisk', 'substrate']:
                if malware in maps_data:
                    nuke_process(f"Injeção Root em Memória RAM Detectada ({malware}).")
    except Exception:
        pass

    # Nível 5: Bloqueio de Mocking (Alteração de módulos na memória do Python)
    if 'unittest.mock' in sys.modules:
        nuke_process("Tentativa de manipulação de memória (Mocking).")

    if EXPECTED_HASHES:
        check_file_integrity()

    return True

run_security_checks()
