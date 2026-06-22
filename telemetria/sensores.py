import subprocess
import time
import json
import os

def obter_uso_cpu():
    """Calcula o uso real do processador lendo os ciclos do sistema em tempo real"""
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

        uso_porcentagem = 100.0 * (1.0 - delta_idle / delta_total)
        return round(uso_porcentagem, 1)
    except Exception:
        return 0.0

def obter_uso_memoria():
    """Lê a RAM total e livre direto do kernel do Android"""
    try:
        with open('/proc/meminfo', 'r') as f:
            linhas = f.readlines()
        
        mem_total = 0
        mem_disponivel = 0
        
        for linha in linhas:
            if linha.startswith('MemTotal:'):
                mem_total = int(linha.split()[1])
            elif linha.startswith('MemAvailable:'):
                mem_disponivel = int(linha.split()[1])
                
        if mem_total == 0:
            return 0.0
            
        mem_usada = mem_total - mem_disponivel
        porcentagem = (mem_usada / mem_total) * 100
        return round(porcentagem, 1)
    except Exception:
        return 0.0

def obter_armazenamento():
    """Calcula o espaço total e livre do armazenamento interno (/data) em Gigabytes"""
    dados = {"total_gb": 0.0, "usado_gb": 0.0, "porcentagem": 0.0}
    try:
        # os.statvfs lê as propriedades do disco diretamente pelo kernel do Linux
        st = os.statvfs('/data')
        total = (st.f_blocks * st.f_frsize) / (1024 ** 3) # Converte bytes para Gigabytes
        livre = (st.f_bavail * st.f_frsize) / (1024 ** 3)
        usado = total - livre
        porcentagem = (usado / total) * 100
        
        dados["total_gb"] = round(total, 1)
        dados["usado_gb"] = round(usado, 1)
        dados["porcentagem"] = round(porcentagem, 1)
    except Exception:
        pass
    return dados

def obter_dados_bateria():
    """Extrai os dados vitais da bateria via dumpsys"""
    dados = {
        "porcentagem": 0,
        "saude": "Desconhecida",
        "temperatura_c": 0.0,
        "voltagem_v": 0.0
    }
    
    mapa_saude = {
        1: "Desconhecida", 2: "Boa", 3: "Superaquecendo", 
        4: "Morta (Viciada)", 5: "Sobretensão", 6: "Falha Geral", 7: "Muito Fria"
    }

    try:
        out = subprocess.check_output("su -c 'dumpsys battery'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8')
        
        for linha in out.split('\n'):
            linha = linha.strip()
            if linha.startswith("level:"):
                dados["porcentagem"] = int(linha.split(':')[1].strip())
            elif linha.startswith("health:"):
                codigo_saude = int(linha.split(':')[1].strip())
                dados["saude"] = mapa_saude.get(codigo_saude, "Desconhecida")
            elif linha.startswith("temperature:"):
                temp_bruta = int(linha.split(':')[1].strip())
                dados["temperatura_c"] = temp_bruta / 10.0
            elif linha.startswith("voltage:"):
                mv = int(linha.split(':')[1].strip())
                dados["voltagem_v"] = round(mv / 1000.0, 2)
    except Exception:
        pass

    return dados

def obter_apps_consumindo_mais():
    """Lista todos os apps, filtrando e agrupando os processos do sistema"""
    apps_final = {}
    total_system_cpu = 0.0
    
    system_processes = [
        "system_server", "zygote", "surfaceflinger", "kworker", 
        "servicemanager", "logd", "audioserver", "mediaserver", 
        "netd", "vendor", "android", "kernel"
    ]

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
                    
                    is_system = any(proc in nome_app.lower() for proc in system_processes)
                    
                    if is_system:
                        total_system_cpu += uso_cpu
                    else:
                        if nome_app not in apps_final:
                            apps_final[nome_app] = 0.0
                        apps_final[nome_app] += uso_cpu
                        
                except Exception:
                    continue
    except Exception:
        pass

    lista_final = [{"nome": k, "uso_cpu_percent": round(v, 1)} for k, v in apps_final.items() if v > 0.1]
    lista_final.append({"nome": "SYSTEM (Agrupado)", "uso_cpu_percent": round(total_system_cpu, 1)})
    
    return sorted(lista_final, key=lambda x: x['uso_cpu_percent'], reverse=True)

def coletar_telemetria_completa():
    """Gera o dicionário mestre com hardware, armazenamento e consumo de apps"""
    bateria = obter_dados_bateria()
    armazenamento = obter_armazenamento()
    
    relatorio = {
        "cpu_percent": obter_uso_cpu(),
        "ram_percent": obter_uso_memoria(),
        "storage_total_gb": armazenamento["total_gb"],
        "storage_used_gb": armazenamento["usado_gb"],
        "storage_percent": armazenamento["porcentagem"],
        "battery_percent": bateria["porcentagem"],
        "battery_health": bateria["saude"],
        "battery_temp_c": bateria["temperatura_c"],
        "battery_voltage_v": bateria["voltagem_v"],
        "apps_cpu": obter_apps_consumindo_mais(),
        "timestamp": int(time.time())
    }
    return relatorio

if __name__ == "__main__":
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        console = Console()
    except ImportError:
        os.system("pip install rich -q > /dev/null 2>&1")
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        console = Console()

    os.system("clear" if os.name == "posix" else "cls")
    console.print("[bold yellow]⏳ Lendo todos os sensores e partições de memória...[/bold yellow]\n")
    
    dados = coletar_telemetria_completa()

    hw_text = (
        f"💻 [bold cyan]CPU Total Em Uso:[/bold cyan] {dados['cpu_percent']}%\n"
        f"🧠 [bold cyan]Memória RAM Em Uso:[/bold cyan] {dados['ram_percent']}%\n"
        f"💾 [bold cyan]Espaço Interno Total:[/bold cyan] {dados['storage_total_gb']} GB [dim]({dados['storage_used_gb']} GB Usados | {dados['storage_percent']}%%)[/dim]\n"
        f"🔋 [bold green]Carga da Bateria:[/bold green] {dados['battery_percent']}% "
        f"[dim](Saúde: {dados['battery_health']} | {dados['battery_temp_c']}°C | {dados['battery_voltage_v']}V)[/dim]"
    )
    console.print(Panel(hw_text, title="⚙️ Diagnóstico Completo do Dispositivo", border_style="cyan", expand=False))

    table = Table(title="📊 Distribuição de CPU por App", header_style="bold magenta")
    table.add_column("App / Processo", style="cyan", no_wrap=True)
    table.add_column("Uso (%)", justify="right", style="green")

    for app in dados["apps_cpu"]:
        if "SYSTEM" in app["nome"]:
            nome_formatado = f"[dim]{app['nome']}[/dim]"
            uso_formatado = f"[dim]{app['uso_cpu_percent']}[/dim]"
        else:
            nome_formatado = f"[bold yellow]{app['nome']}[/bold yellow]"
            uso_formatado = f"{app['uso_cpu_percent']}"
            
        table.add_row(nome_formatado, uso_formatado)

    console.print(table)
    print("\n")
