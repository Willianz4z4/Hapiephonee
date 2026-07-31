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
            pass # Temporariamente flexível

def iniciar_watchdog():
    t = threading.Thread(target=_watchdog_loop, daemon=True)
    t.start()

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
    if not os.path.exists(CACHE_FILE):
        return True 
        
    try:
        with open(CACHE_FILE, "r") as f:
            dna_oficial = json.load(f)
    except:
        nuke_process("DNA de segurança corrompido.")

    main_script = os.path.abspath(sys.argv[0])
    rel_script_path = os.path.relpath(main_script, BASE_DIR)

    if rel_script_path not in dna_oficial:
        nuke_process(f"Arquivo não autorizado na matriz: {rel_script_path}")

    sha3 = hashlib.sha3_512()
    try:
        with open(main_script, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha3.update(chunk)
        hash_atual = sha3.hexdigest()
    except Exception:
        nuke_process("Falha ao calcular hash local.")

    if hash_atual != dna_oficial[rel_script_path]:
        nuke_process(f"Adulteração detectada no arquivo: {rel_script_path}")

    return True

def run_security_checks():
    main_script = os.path.abspath(sys.argv[0])
    
    if "Hapiephonee" not in main_script:
        nuke_process("Tentativa de importação externa não autorizada.")

    validar_e_obter_status_execucao()

    for proxy_var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
        if proxy_var in os.environ:
            nuke_process(f"Interceptação de Rede (Proxy: {proxy_var})")
            
    if sys.gettrace() is not None:
        nuke_process("Debugger Python Ativo.")
        
    # 🧠 LEITURA INTELIGENTE DE TRACER (Caminho + Comando)
    try:
        with open('/proc/self/status', 'r') as f:
            for linha in f:
                if linha.startswith('TracerPid:'):
                    tracer_pid = int(linha.split(':')[1].strip())
                    if tracer_pid != 0:
                        pai_pid = os.getppid()
                        if tracer_pid == pai_pid:
                            break # O Watchdog/Pai pode rastrear, é legítimo
                        
                        try:
                            tracer_exe = os.readlink(f'/proc/{tracer_pid}/exe')
                            with open(f'/proc/{tracer_pid}/cmdline', 'rb') as cf:
                                tracer_cmd = cf.read().replace(b'\x00', b' ').decode('utf-8', errors='ignore')
                            
                            caminhos_seguros = [
                                '/system/bin/',
                                '/system/xbin/',
                                '/data/data/com.termux/files/usr/bin/',
                                '/data/adb/' # Pasta raiz do Magisk (su)
                            ]
                            
                            is_trusted_path = any(tracer_exe.startswith(caminho) for caminho in caminhos_seguros)
                            is_our_watchdog = 'Hapiephonee' in tracer_cmd
                            
                            if not (is_trusted_path or is_our_watchdog):
                                nuke_process(f"Debugger Falso (PID: {tracer_pid} | EXE: {tracer_exe} | CMD: {tracer_cmd.strip()})")
                        except Exception as e:
                            nuke_process(f"Processo Fantasma no Kernel (PID: {tracer_pid}). Acesso Negado.")
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
