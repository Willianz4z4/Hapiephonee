import subprocess
import time
import hashlib
import hmac
import os
import sys
import ctypes
import threading
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(BASE_DIR, "security_system", ".hash_cache.json")
ULTIMO_BATIMENTO = time.time()

def get_hmac_secret():
    chave_xor = 42
    fragmentos = [114, 123, 86, 83, 79, 117, 121, 95, 86, 79, 88, 117, 121, 79, 73, 88, 79, 94, 117, 97, 79, 83, 117, 24, 26, 24, 28, 117, 11, 106, 9]
    return bytes([byte ^ chave_xor for byte in fragmentos])

def nuke_process(reason):
    print(f"\n[🚨 HAPIE SECURITY LOCKDOWN 🚨]\nAcesso Negado: {reason}")
    os._exit(1)

def _watchdog_loop():
    global ULTIMO_BATIMENTO
    while True:
        time.sleep(1)
        agora = time.time()
        if agora - ULTIMO_BATIMENTO > 3.0:
            nuke_process(f"Anomalia Temporal Detectada ({(agora - ULTIMO_BATIMENTO):.1f}s). Congelamento de execucao!")

def iniciar_watchdog():
    t = threading.Thread(target=_watchdog_loop, daemon=True)
    t.start()

def bater_ponto():
    global ULTIMO_BATIMENTO
    ULTIMO_BATIMENTO = time.time()

def validar_e_obter_status_execucao():
    """Valida a integridade do script atual contra o cache oficial do Git e identifica se é o auto_copy oficial."""
    if not os.path.exists(CACHE_FILE):
        nuke_process("DNA de segurança ausente. Execute o update.sh primeiro!")
        
    try:
        with open(CACHE_FILE, "r") as f:
            dna_oficial = json.load(f)
    except:
        nuke_process("DNA de segurança corrompido.")

    main_script = os.path.abspath(sys.argv[0])
    rel_script_path = os.path.relpath(main_script, BASE_DIR)

    if rel_script_path not in dna_oficial:
        nuke_process(f"Arquivo não autorizado na matriz: {rel_script_path}")

    # Calcula o hash do arquivo executado no momento
    sha3 = hashlib.sha3_512()
    try:
        with open(main_script, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha3.update(chunk)
        hash_atual = sha3.hexdigest()
    except Exception:
        nuke_process("Falha ao calcular hash de integridade local.")

    # Compara o hash atual com o hash oficial guardado no cache do Git
    if hash_atual != dna_oficial[rel_script_path]:
        nuke_process(f"Adulteração detectada no arquivo: {rel_script_path}")

    # Descobre se este arquivo específico é exatamente o auto_copy.py oficial
    is_official_auto_copy = False
    for path, oficial_hash in dna_oficial.items():
        if "auto_copy.py" in path and hash_atual == oficial_hash:
            is_official_auto_copy = True
            break

    return is_official_auto_copy

def run_security_checks():
    main_script = os.path.abspath(sys.argv[0])
    
    if "Hapiephonee" not in main_script:
        nuke_process("Tentativa de importação externa não autorizada.")

    # 🛡️ Validação Criptográfica Total + Identificação Segura do Auto Copy
    is_official_auto_copy = validar_e_obter_status_execucao()

    for proxy_var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
        if proxy_var in os.environ:
            nuke_process(f"Interceptação de Rede (Proxy: {proxy_var})")
            
    if sys.gettrace() is not None:
        nuke_process("Debugger Python Ativo.")
        
    try:
        libc = ctypes.CDLL(None)
        if libc.ptrace(0, 0, 0, 0) < 0:
            if not is_official_auto_copy:
                nuke_process("Interceptação Kernel Detectada (Bloqueio PTRACE).")
    except Exception:
        pass
        
    try:
        with open('/proc/self/status', 'r') as f:
            for linha in f:
                if linha.startswith('TracerPid:'):
                    tracer_pid = int(linha.split(':')[1].strip())
                    if tracer_pid != 0:
                        if is_official_auto_copy:
                            pass # Exceção segura concedida apenas ao auto_copy oficial verificado por hash
                        else:
                            nuke_process(f"Interceptação Kernel Detectada (TracerPid: {tracer_pid})")
                    break
    except Exception:
        pass
        
    try:
        with open('/proc/self/maps', 'r') as f:
            maps_data = f.read().lower()
            for malware in ['frida', 'xposed', 'edxposed', 'lsposed', 'magisk', 'substrate']:
                if malware in maps_data:
                    if not (is_official_auto_copy and malware == 'magisk'):
                        nuke_process(f"Injeção Root em Memória RAM Detectada ({malware}).")
    except Exception:
        pass
        
    if 'unittest.mock' in sys.modules:
        nuke_process("Tentativa de manipulação de memória (Mocking).")

    # Watchdog apenas para scripts de longa execução (o auto_copy dispensa)
    if not is_official_auto_copy:
        iniciar_watchdog()
        
    return True

run_security_checks()
