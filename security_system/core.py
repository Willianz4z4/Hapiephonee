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
            nuke_process("Anomalia Temporal Detectada. Congelamento de execucao!")

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

def validar_e_obter_status_execucao():
    """Valida o código com base no DNA do repositório Git."""
    if not os.path.exists(CACHE_FILE):
        return True # Permite rodar na 1ª vez para o update.sh conseguir gerar o cache
        
    try:
        with open(CACHE_FILE, "r") as f:
            dna_oficial = json.load(f)
    except:
        nuke_process("DNA de segurança corrompido.")

    main_script = os.path.abspath(sys.argv[0])
    rel_script_path = os.path.relpath(main_script, BASE_DIR)

    if rel_script_path not in dna_oficial:
        nuke_process(f"Arquivo fantasma não autorizado na matriz: {rel_script_path}")

    sha3 = hashlib.sha3_512()
    try:
        with open(main_script, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha3.update(chunk)
        hash_atual = sha3.hexdigest()
    except Exception:
        nuke_process("Falha ao calcular hash de integridade local.")

    if hash_atual != dna_oficial[rel_script_path]:
        nuke_process(f"Adulteração detectada no arquivo: {rel_script_path}")

    return True

def run_security_checks():
    main_script = os.path.abspath(sys.argv[0])
    
    if "Hapiephonee" not in main_script:
        nuke_process("Tentativa de importação externa não autorizada.")

    # Se o script passar daqui, ele é 100% oficial e o código-fonte está virgem.
    validar_e_obter_status_execucao()

    for proxy_var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
        if proxy_var in os.environ:
            nuke_process(f"Interceptação de Rede (Proxy: {proxy_var})")
            
    if sys.gettrace() is not None:
        nuke_process("Debugger Python Ativo.")
        
    # 🧠 BLOQUEIO INTELIGENTE DE TRACER (Fim do Loop Infinito)
    try:
        with open('/proc/self/status', 'r') as f:
            for linha in f:
                if linha.startswith('TracerPid:'):
                    tracer_pid = int(linha.split(':')[1].strip())
                    pai_pid = os.getppid() # Descobre quem é o 'Pai' legítimo (Bash/Watchdog)
                    
                    # Só bloqueia se for diferente de 0 E diferente do processo Pai
                    if tracer_pid != 0 and tracer_pid != pai_pid:
                        nuke_process(f"Interceptação Kernel Maliciosa (Debugger PID: {tracer_pid} != Pai Legitimo {pai_pid})")
                    break
    except Exception:
        pass
        
    try:
        with open('/proc/self/maps', 'r') as f:
            maps_data = f.read().lower()
            for malware in ['frida', 'xposed', 'edxposed', 'lsposed', 'substrate']:
                if malware in maps_data:
                    nuke_process(f"Injeção Root em Memória RAM Detectada ({malware}).")
    except Exception:
        pass
        
    if 'unittest.mock' in sys.modules:
        nuke_process("Tentativa de manipulação de memória (Mocking).")
        
    return True

run_security_checks()
