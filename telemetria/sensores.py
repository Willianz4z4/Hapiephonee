import subprocess
import json

def obter_apps_consumindo_mais():
    """Lista todos os apps, mas agrupa os processos do sistema em uma única linha"""
    apps_final = {}
    total_system_cpu = 0.0
    
    # Lista de processos que queremos agrupar como "SYSTEM"
    system_processes = [
        "system_server", "zygote", "surfaceflinger", "kworker", 
        "servicemanager", "logd", "audioserver", "mediaserver", 
        "netd", "vendor", "android", "kernel"
    ]

    try:
        out = subprocess.check_output("su -c 'dumpsys cpuinfo'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8')
        
        for linha in out.split('\n'):
            linha = linha.strip()
            # Filtra linhas que têm porcentagem e identificador de processo
            if '%' in linha and '/' in linha and ':' in linha:
                try:
                    partes = linha.split('%', 1)
                    uso_cpu = float(partes[0].strip().replace('+', ''))
                    resto = partes[1].split(':', 1)[0] 
                    nome_app = resto.split('/')[1].strip() if '/' in resto else resto
                    
                    # Lógica de Agrupamento
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

    # Converte para lista e adiciona o SYSTEM no final
    lista_final = [{"nome": k, "uso_cpu_percent": round(v, 1)} for k, v in apps_final.items() if v > 0.1]
    lista_final.append({"nome": "SYSTEM (Agrupado)", "uso_cpu_percent": round(total_system_cpu, 1)})
    
    # Ordena pelos que mais consomem
    return sorted(lista_final, key=lambda x: x['uso_cpu_percent'], reverse=True)

if __name__ == "__main__":
    print("⏳ Monitorando CPU com filtro de sistema...\n")
    dados = obter_apps_consumindo_mais()
    print(json.dumps(dados, indent=4, ensure_ascii=False))
