import subprocess
import time
import hashlib
import hmac
import os
import sys

# ==========================================
# 🛑 CONFIGURAÇÕES CRÍTICAS C-LEVEL
# ==========================================
HMAC_SECRET = b"Hapie_Super_Secret_Key_2026_!@#"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Aqui você coloca o nome do arquivo e o HASH original dele.
# Se o hacker der um 'espaço' no arquivo telemetria/sensores.py, o Hash muda e o bot morre.
EXPECTED_HASHES = {
    # Exemplo: "telemetria/sensores.py": "aqui_vai_o_hash_sha256_do_arquivo",
    # Você vai preencher isso depois, antes de lançar o bot final.
}

def nuke_process(reason):
    """Mata o processo na raiz (C-level) sem chance de captura de erro."""
    print(f"\n[🚨 HAPIE SECURITY LOCKDOWN 🚨]\nAcesso Negado: {reason}")
    os._exit(1)

def obter_dna_dispositivo():
    """Gera o DNA imutável do hardware."""
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
    """Gera a assinatura criptográfica para o servidor."""
    mensagem = f"{dna}:{timestamp}".encode('utf-8')
    return hmac.new(HMAC_SECRET, mensagem, hashlib.sha256).hexdigest()

def check_file_integrity():
    """Verifica se algum arquivo vital foi editado pelo invasor."""
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
    """Executa a blindagem do ambiente."""
    # 1. Bloqueio de Origem (Ninguém de fora pode importar esse módulo)
    main_script = os.path.abspath(sys.argv[0])
    if "Hapiephonee" not in main_script:
        nuke_process("Tentativa de importação externa não autorizada.")

    # 2. Bloqueio de Rede/Proxies
    for proxy_var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
        if proxy_var in os.environ:
            nuke_process(f"Interceptação de Rede (Proxy: {proxy_var})")

    # 3. Bloqueio de Engenharia Reversa (Debuggers e Kernel Tracers)
    # Proteção Nível 1: Debuggers Python (PDB, IDEs)
    if sys.gettrace() is not None:
        nuke_process("Debugger Python Ativo.")

    # Proteção Nível 2: Grampos de Sistema (strace, gdb, ptrace)
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

    # 4. Bloqueio de Mocking (Alteração de módulos na memória)
    if 'unittest.mock' in sys.modules:
        nuke_process("Tentativa de manipulação de memória (Mocking).")

    # 5. Verifica se os códigos vitais foram editados
    if EXPECTED_HASHES:
        check_file_integrity()

    return True

# Inicia as defesas instantaneamente quando o arquivo é chamado
run_security_checks()
