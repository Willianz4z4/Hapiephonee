import subprocess
import time
import hashlib
import hmac
import os
import sys
import ctypes
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED_HASHES = {}
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
    return hashlib.sha3_512(dna_bruto.encode('utf-8')).hexdigest()

def gerar_assinatura_hmac(dna, timestamp):
    mensagem = f"{dna}:{timestamp}".encode('utf-8')
    segredo = get_hmac_secret()
    return hmac.new(segredo, mensagem, hashlib.sha3_512).hexdigest()

def check_file_integrity():
    for relative_path, expected_hash in EXPECTED_HASHES.items():
        filepath = os.path.join(BASE_DIR, relative_path.replace("/", os.sep))
        if not os.path.exists(filepath):
            nuke_process(f"Arquivo vital ausente: {relative_path}")
        sha3_hash = hashlib.sha3_512()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha3_hash.update(byte_block)
            if sha3_hash.hexdigest() != expected_hash:
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
    if sys.gettrace() is not None:
        nuke_process("Debugger Python Ativo.")
    try:
        libc = ctypes.CDLL(None)
        if libc.ptrace(0, 0, 0, 0) < 0:
            nuke_process("Interceptação Kernel Detectada (Bloqueio PTRACE).")
    except Exception:
        pass
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
    try:
        with open('/proc/self/maps', 'r') as f:
            maps_data = f.read().lower()
            for malware in ['frida', 'xposed', 'edxposed', 'lsposed', 'magisk', 'substrate']:
                if malware in maps_data:
                    nuke_process(f"Injeção Root em Memória RAM Detectada ({malware}).")
    except Exception:
        pass
    if 'unittest.mock' in sys.modules:
        nuke_process("Tentativa de manipulação de memória (Mocking).")
    if EXPECTED_HASHES:
        check_file_integrity()
        
    iniciar_watchdog()
    return True

run_security_checks()
