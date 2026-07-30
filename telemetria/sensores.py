import subprocess
import time
import json
import os
import sys

# ==========================================
# 🔗 CONEXÃO COM O COFRE DE SEGURANÇA (CYTHON)
# ==========================================
# Adiciona a raiz do projeto ao path para achar a pasta security_system
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Importa as funções direto do arquivo binário (.so)
# Assim que importamos, ele já roda o run_security_checks() lá de dentro!
try:
    from security_system.core import obter_dna_dispositivo, gerar_assinatura_hmac
except ImportError:
    print('{"status": "error", "reason": "SECURITY_MODULE_MISSING"}')
    sys.exit(1)

# ==========================================
# 📊 FUNÇÕES DE TELEMETRIA (SEM SEGREDOS AQUI)
# ==========================================

def obter_nome_processador():
    nome_cpu = "Desconhecido"
    try:
        out = subprocess.check_output("getprop ro.board.platform", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        if out and out.lower() != "unknown": nome_cpu = out.upper()
        else:
            with open('/proc/cpuinfo', 'r') as f:
                for linha in f:
                    if linha.startswith("Hardware") or linha.startswith("model name"):
                        partes = linha.split(":")
                        if len(partes) > 1:
                            nome_cpu = partes[1].strip()
                            break
        if any(x in nome_cpu for x in ["MSM", "SDM", "SM", "LAHAINA", "TARO", "KALI"]): nome_cpu = f"Snapdragon ({nome_cpu})"
        elif "MT" in nome_cpu: nome_cpu = f"MediaTek ({nome_cpu})"
        elif "EXYNOS" in nome_cpu: nome_cpu = f"Exynos ({nome_cpu})"
        elif "RK" in nome_cpu: nome_cpu = f"Rockchip ({nome_cpu})"
    except Exception: pass
    return nome_cpu

def obter_uso_cpu():
    try:
        with open('/proc/stat', 'r') as f: linha1 = f.readline().split()
        idle1 = float(linha1[4])
        total1 = sum(float(x) for x in linha1[1:])
        time.sleep(0.3)
        with open('/proc/stat', 'r') as f: linha2 = f.readline().split()
        idle2 = float(linha2[4])
        total2 = sum(float(x) for x in linha2[1:])
        return round(100.0 * (1.0 - (idle2 - idle1) / (total2 - total1)), 1)
    except Exception: return 0.0

def obter_temperatura_cpu():
    temps_cpu = []
    base_path = "/sys/class/thermal"
    if not os.path.exists(base_path): return 0.0
    try:
        for zone in os.listdir(base_path):
            if zone.startswith("thermal_zone"):
                zone_path = os.path.join(base_path, zone)
                type_file = os.path.join(zone_path, "type")
                temp_file = os.path.join(zone_path, "temp")
                if os.path.exists(type_file) and os.path.exists(temp_file):
                    with open(type_file, "r") as f: tipo = f.read().lower().strip()
                    if any(x in tipo for x in ["cpu", "tsens", "core"]):
                        with open(temp_file, "r") as f: temp_bruta = float(f.read().strip())
                        if temp_bruta > 1000: temp_bruta /= 1000.0
                        elif temp_bruta > 100: temp_bruta /= 10.0
                        if 10 < temp_bruta < 105: temps_cpu.append(temp_bruta)
    except Exception: pass
    return round(sum(temps_cpu) / len(temps_cpu), 1) if temps_cpu else 0.0

def obter_uso_memoria():
    try:
        with open('/proc/meminfo', 'r') as f: linhas = f.readlines()
        mem_total = mem_disponivel = 0
        for linha in linhas:
            if linha.startswith('MemTotal:'): mem_total = int(linha.split()[1])
            elif linha.startswith('MemAvailable:'): mem_disponivel = int(linha.split()[1])
        if mem_total == 0: return 0.0
        return round(((mem_total - mem_disponivel) / mem_total) * 100, 1)
    except Exception: return 0.0

def obter_armazenamento():
    dados = {"total_gb": 0.0, "usado_gb": 0.0, "porcentagem": 0.0}
    try:
        st = os.statvfs('/data')
        total = (st.f_blocks * st.f_frsize) / (1024 ** 3)
        livre = (st.f_bavail * st.f_frsize) / (1024 ** 3)
        dados["total_gb"] = round(total, 1)
        dados["usado_gb"] = round(total - livre, 1)
        dados["porcentagem"] = round(((total - livre) / total) * 100, 1)
    except Exception: pass
    return dados

def obter_dados_bateria():
    dados = {"porcentagem": 0, "saude": "Desconhecida", "temperatura_c": 0.0, "voltagem_v": 0.0, "status": "Desconhecido"}
    mapa_saude = {1: "Desconhecida", 2: "Boa", 3: "Superaquecendo", 4: "Morta", 5: "Sobretensão", 6: "Falha", 7: "Fria"}
    mapa_status = {1: "Desconhecido", 2: "Carregando", 3: "Descarregando", 4: "Nao Carregando", 5: "Cheia"}
    try:
        out = subprocess.check_output("su -c 'dumpsys battery'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8')
        for linha in out.split('\n'):
            linha = linha.strip()
            if linha.startswith("level:"): dados["porcentagem"] = int(linha.split(':')[1].strip())
            elif linha.startswith("health:"): dados["saude"] = mapa_saude.get(int(linha.split(':')[1].strip()), "Desconhecida")
            elif linha.startswith("temperature:"): dados["temperatura_c"] = int(linha.split(':')[1].strip()) / 10.0
            elif linha.startswith("voltage:"): dados["voltagem_v"] = round(int(linha.split(':')[1].strip()) / 1000.0, 2)
            elif linha.startswith("status:"): dados["status"] = mapa_status.get(int(linha.split(':')[1].strip()), "Desconhecido")
    except Exception: pass
    return dados

def obter_uptime():
    try:
        with open('/proc/uptime', 'r') as f: uptime_segundos = float(f.readline().split()[0])
        dias, horas, minutos = int(uptime_segundos // 86400), int((uptime_segundos % 86400) // 3600), int((uptime_segundos % 3600) // 60)
        if dias > 0: return f"{dias}d {horas}h {minutos}m"
        elif horas > 0: return f"{horas}h {minutos}m"
        else: return f"{minutos}m"
    except Exception: return "Desconhecido"

def obter_trafego_rede():
    dados = {"download_mb": 0.0, "upload_mb": 0.0}
    try:
        with open('/proc/net/dev', 'r') as f: linhas = f.readlines()[2:]
        rx_bytes = tx_bytes = 0
        for linha in linhas:
            partes = linha.split(':')
            if partes[0].strip() != "lo":
                valores = partes[1].split()
                rx_bytes += int(valores[0])
                tx_bytes += int(valores[8])
        dados["download_mb"], dados["upload_mb"] = round(rx_bytes / (1024**2), 2), round(tx_bytes / (1024**2), 2)
    except Exception: pass
    return dados

def coletar_telemetria_completa():
    bateria, armazenamento, rede = obter_dados_bateria(), obter_armazenamento(), obter_trafego_rede()
    
    # Busca o DNA lá dentro do C (Cofre)
    dna = obter_dna_dispositivo()
    ts = int(time.time())

    relatorio = {
        "device_dna": dna,
        "cpu_name": obter_nome_processador(),
        "cpu_percent": obter_uso_cpu(),
        "cpu_temp_c": obter_temperatura_cpu(),
        "ram_percent": obter_uso_memoria(),
        "storage_total_gb": armazenamento["total_gb"],
        "storage_used_gb": armazenamento["usado_gb"],
        "storage_percent": armazenamento["porcentagem"],
        "battery_percent": bateria["porcentagem"],
        "battery_status": bateria["status"],
        "battery_health": bateria["saude"],
        "battery_temp_c": bateria["temperatura_c"],
        "battery_voltage_v": bateria["voltagem_v"],
        "uptime": obter_uptime(),
        "network_download_mb": rede["download_mb"],
        "network_upload_mb": rede["upload_mb"],
        "timestamp": ts
    }
    return relatorio, dna, ts

if __name__ == "__main__":
    relatorio, dna, timestamp = coletar_telemetria_completa()
    
    # O arquivo Python NÃO SABE a senha. Ele pede para o Cofre gerar a assinatura
    assinatura = gerar_assinatura_hmac(dna, timestamp)
    
    envelope_seguro = {
        "signature": assinatura,
        "payload": relatorio
    }
    
    print(json.dumps(envelope_seguro))
