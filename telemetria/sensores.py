import subprocess
import time
import json
import os
import hashlib
import hmac

# ==========================================
# 🔒 CONFIGURAÇÃO DE SEGURANÇA
# No futuro, este segredo e estas funções de hash
# devem ir para o arquivo compilado (.so) para ninguém ler.
# ==========================================
HMAC_SECRET = b"Hapie_Super_Secret_Key_2026_!@#"

def obter_dna_dispositivo():
    """Gera um Hash único e imutável baseado no hardware real do aparelho."""
    comandos_dna = {
        "android_id": "su -c 'settings get secure android_id'",
        "serial": "getprop ro.serialno",
        "placa": "getprop ro.board.platform"
    }
    
    dna_coletado = []
    for chave, comando in comandos_dna.items():
        try:
            resultado = subprocess.check_output(comando, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
            if resultado and resultado.lower() != "unknown":
                dna_coletado.append(resultado)
        except Exception:
            pass
            
    dna_bruto = "|".join(dna_coletado) if dna_coletado else "fallback_gen_id"
    # Retorna o SHA-256 do hardware (não envia o serial real, apenas a matemática)
    return hashlib.sha256(dna_bruto.encode('utf-8')).hexdigest()

def gerar_assinatura_hmac(dna, timestamp):
    """Cria o token dinâmico impossível de ser falsificado sem a chave secreta."""
    # A mensagem a ser assinada é a união do DNA com a Hora Atual
    mensagem = f"{dna}:{timestamp}".encode('utf-8')
    assinatura = hmac.new(HMAC_SECRET, mensagem, hashlib.sha256).hexdigest()
    return assinatura

# ==========================================
# 📊 FUNÇÕES DE TELEMETRIA ORIGINAIS
# ==========================================

def obter_nome_processador():
    nome_cpu = "Desconhecido"
    try:
        out = subprocess.check_output("getprop ro.board.platform", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        if out and out.lower() != "unknown":
            nome_cpu = out.upper()
        else:
            with open('/proc/cpuinfo', 'r') as f:
                for linha in f:
                    if linha.startswith("Hardware") or linha.startswith("model name"):
                        partes = linha.split(":")
                        if len(partes) > 1:
                            nome_cpu = partes[1].strip()
                            break
        if "MSM" in nome_cpu or "SDM" in nome_cpu or "SM" in nome_cpu or "LAHAINA" in nome_cpu or "TARO" in nome_cpu or "KALI" in nome_cpu:
            nome_cpu = f"Snapdragon ({nome_cpu})"
        elif "MT" in nome_cpu:
            nome_cpu = f"MediaTek ({nome_cpu})"
        elif "EXYNOS" in nome_cpu:
            nome_cpu = f"Exynos ({nome_cpu})"
        elif "RK" in nome_cpu:
            nome_cpu = f"Rockchip ({nome_cpu})"
    except Exception:
        pass
    return nome_cpu

def obter_uso_cpu():
    try:
        with open('/proc/stat', 'r') as f:
            linha1 = f.readline().split()
        idle1 = float(linha1[4])
        total1 = sum(float(x) for x in linha1[1:])
        time.sleep(0.3)
        with open('/proc/stat', 'r') as f:
            linha2 = f.readline().split()
        idle2 = float(linha2[4])
        total2 = sum(float(x) for x in linha2[1:])
        delta_idle = idle2 - idle1
        delta_total = total2 - total1
        return round(100.0 * (1.0 - delta_idle / delta_total), 1)
    except Exception:
        return 0.0

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
                    if "cpu" in tipo or "tsens" in tipo or "core" in tipo:
                        with open(temp_file, "r") as f: temp_bruta = float(f.read().strip())
                        if temp_bruta > 1000: temp_bruta /= 1000.0
                        elif temp_bruta > 100: temp_bruta /= 10.0
                        if 10 < temp_bruta < 105: temps_cpu.append(temp_bruta)
    except Exception:
        pass
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
    except Exception:
        return 0.0

def obter_armazenamento():
    dados = {"total_gb": 0.0, "usado_gb": 0.0, "porcentagem": 0.0}
    try:
        st = os.statvfs('/data')
        total = (st.f_blocks * st.f_frsize) / (1024 ** 3)
        livre = (st.f_bavail * st.f_frsize) / (1024 ** 3)
        dados["total_gb"] = round(total, 1)
        dados["usado_gb"] = round(total - livre, 1)
        dados["porcentagem"] = round(((total - livre) / total) * 100, 1)
    except Exception:
        pass
    return dados

def obter_dados_bateria():
    dados = {
        "porcentagem": 0, "saude": "Desconhecida", "temperatura_c": 0.0,
        "voltagem_v": 0.0, "status": "Desconhecido"
    }
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
    except Exception:
        pass
    return dados

def obter_uptime():
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_segundos = float(f.readline().split()[0])
        dias = int(uptime_segundos // 86400)
        horas = int((uptime_segundos % 86400) // 3600)
        minutos = int((uptime_segundos % 3600) // 60)

        if dias > 0: return f"{dias}d {horas}h {minutos}m"
        elif horas > 0: return f"{horas}h {minutos}m"
        else: return f"{minutos}m"
    except Exception:
        return "Desconhecido"

def obter_trafego_rede():
    dados = {"download_mb": 0.0, "upload_mb": 0.0}
    try:
        with open('/proc/net/dev', 'r') as f:
            linhas = f.readlines()[2:]
        rx_bytes = tx_bytes = 0
        for linha in linhas:
            partes = linha.split(':')
            interface = partes[0].strip()
            if interface != "lo":
                valores = partes[1].split()
                rx_bytes += int(valores[0])
                tx_bytes += int(valores[8])
        dados["download_mb"] = round(rx_bytes / (1024 * 1024), 2)
        dados["upload_mb"] = round(tx_bytes / (1024 * 1024), 2)
    except Exception:
        pass
    return dados

def obter_apps_consumindo_mais():
    apps_final = {}
    total_system_cpu = 0.0
    system_processes = ["system_server", "zygote", "surfaceflinger", "kworker", "servicemanager", "logd", "audioserver", "mediaserver", "netd", "vendor", "android", "kernel"]
    try:
        out = subprocess.check_output("su -c 'dumpsys cpuinfo'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8')
        for linha in out.split('\n'):
            linha = linha.strip()
            if '%' in linha and '/' in linha and ':' in linha:
                try:
                    partes = linha.split('%', 1)
                    uso_cpu = float(partes[0].strip().replace('+', ''))
                    resto = partes[1].split(':', 1)[0]
                    nome_app = resto.split('/')[1].strip() if '/' in resto else resto
                    if any(proc in nome_app.lower() for proc in system_processes): total_system_cpu += uso_cpu
                    else:
                        apps_final[nome_app] = apps_final.get(nome_app, 0.0) + uso_cpu
                except Exception:
                    continue
    except Exception:
        pass
    lista_final = [{"nome": k, "uso_cpu_percent": round(v, 1)} for k, v in apps_final.items() if v > 0.1]
    lista_final.append({"nome": "SYSTEM (Agrupado)", "uso_cpu_percent": round(total_system_cpu, 1)})
    return sorted(lista_final, key=lambda x: x['uso_cpu_percent'], reverse=True)

def coletar_telemetria_completa():
    bateria = obter_dados_bateria()
    armazenamento = obter_armazenamento()
    rede = obter_trafego_rede()
    
    # Coleta a segurança
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
        "apps_cpu": obter_apps_consumindo_mais(),
        "timestamp": ts
    }
    
    return relatorio, dna, ts

if __name__ == "__main__":
    # Gera o relatório, pega o DNA e o Timestamp
    relatorio, dna, timestamp = coletar_telemetria_completa()
    
    # Cria a assinatura de segurança
    assinatura = gerar_assinatura_hmac(dna, timestamp)
    
    # Constrói o "Envelope" final
    envelope_seguro = {
        "signature": assinatura,
        "payload": relatorio
    }
    
    # Imprime para quem for ler (agora encapsulado com segurança)
    print(json.dumps(envelope_seguro))
