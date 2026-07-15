import os
import subprocess
import re
import requests
import json

try:
    import gdown
except ImportError:
    gdown = None

BASE_DATA_DIR = os.path.join(os.getcwd(), "data_apps")

def inicializar_ambiente():
    if not os.path.exists(BASE_DATA_DIR):
        os.makedirs(BASE_DATA_DIR, exist_ok=True)

def executar_root(comando):
    resultado = subprocess.run(
        ['su', '-c', comando],
        capture_output=True,
        text=True
    )
    # Agora aceitamos qualquer retorno, pois tratamos as travas direto no shell
    return True, resultado.stdout.strip() + " " + resultado.stderr.strip()

def data_save(pacote):
    inicializar_ambiente()
    print(f"=== [data_save] SALVANDO DADOS DO PACOTE '{pacote}' ===")
    destino_final = os.path.join(BASE_DATA_DIR, f"{pacote}.tar.gz")

    # 🚀 OTIMIZAÇÃO: Excluindo pastas de cache e forçando o sucesso ignorando avisos de sockets
    comando = f"""
    if [ -d "/data/data/{pacote}" ]; then
        tar --exclude='cache' --exclude='code_cache' --exclude='no_backup' -czf "{destino_final}" -C "/data/data" "{pacote}" 2>/dev/null || true
        chmod 777 "{destino_final}"
        echo "sucesso"
    else
        echo "erro_pasta_nao_encontrada"
    fi
    """
    sucesso, saida = executar_root(comando)
    
    if "erro_pasta_nao_encontrada" in saida:
        print(f"[X] Erro: Pasta do aplicativo /data/data/{pacote} não existe.")
        return False
    if os.path.exists(destino_final):
        print(f"[+] Dados salvos com sucesso no Bot: {destino_final} (Tamanho: {os.path.getsize(destino_final) // 1024} KB)")
        return True
    else:
        print(f"[X] Falha no processo de compactação via root: {saida}")
        return False

def data_export(pacote, url_servidor, owner_id, device_id):
    inicializar_ambiente()
    arquivo_bot = os.path.join(BASE_DATA_DIR, f"{pacote}.tar.gz")

    if not os.path.exists(arquivo_bot):
        print(f"[X] Erro de Exportação: Arquivo {arquivo_bot} não encontrado.")
        return False

    print(f"=== [data_export] ENVIANDO DATA DE '{pacote}' PARA O SERVIDOR ===")
    try:
        with open(arquivo_bot, 'rb') as f:
            files = {'file': (f"{pacote}_data.tar.gz", f, 'application/gzip')}
            data = {
                'pkg_name': pacote,
                'owner_id': str(owner_id),
                'device_id': str(device_id)
            }
            response = requests.post(url_servidor, files=files, data=data)
            if response.status_code in [200, 201]:
                print(f"[+] Exportado com sucesso! Servidor respondeu: {response.json()}")
                os.remove(arquivo_bot)
                return True
            else:
                print(f"[X] Servidor rejeitou o arquivo. Código: {response.status_code} | Resposta: {response.text}")
                return False
    except Exception as e:
        print(f"[X] Falha ao exportar dados para o servidor: {e}")
        return False

def baixar_data_com_cookies(url, out_path):
    file_id = None
    match_d = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if match_d: file_id = match_d.group(1)
    else:
        match_id = re.search(r'id=([a-zA-Z0-9_-]+)', url)
        if match_id: file_id = match_id.group(1)

    if file_id:
        if gdown:
            try:
                gdown.download(f"https://drive.google.com/uc?id={file_id}", out_path, quiet=True)
                if os.path.exists(out_path) and os.path.getsize(out_path) > 1000: return True
            except: pass

        session = requests.Session()
        confirm_url = "https://docs.google.com/uc?export=download"
        params = {'id': file_id}
        response = session.get(confirm_url, params=params, stream=True)

        token = None
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                token = value
                break
        if token:
            params['confirm'] = token
            response = session.get(confirm_url, params=params, stream=True)

        if response.status_code == 200:
            with open(out_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    else:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(out_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    return False

def data_inject(pacote, url_servidor):
    inicializar_ambiente()
    print(f"=== [data_inject] INJETANDO DADOS NO PACOTE '{pacote}' ===")
    arquivo_local = os.path.join(BASE_DATA_DIR, f"{pacote}.tar.gz")

    if not os.path.exists(arquivo_local):
        if "drive.google.com" in url_servidor:
            url_download = url_servidor
        else:
            url_download = f"{url_servidor.rstrip('/')}/download/{pacote}.tar.gz"

        print(f"[!] Requisitando dados da nuvem: {url_download}")
        try:
            sucesso_download = baixar_data_com_cookies(url_download, arquivo_local)
            if sucesso_download and os.path.exists(arquivo_local) and os.path.getsize(arquivo_local) > 1000:
                print(f"[+] Download da nuvem concluído com sucesso.")
            else:
                print(f"[X] Falha ao baixar os dados da nuvem.")
                if os.path.exists(arquivo_local): os.remove(arquivo_local)
                return False
        except Exception as e:
            print(f"[X] Falha ao fazer o download: {e}")
            if os.path.exists(arquivo_local): os.remove(arquivo_local)
            return False

    comando = f"""
    if [ ! -f "{arquivo_local}" ]; then
        echo "erro_arquivo_sumiu"
        exit 0
    fi
    if [ ! -d "/data/data/{pacote}" ]; then
        echo "erro_pacote_nao_instalado"
        exit 0
    fi

    am force-stop "{pacote}"
    APP_OWNER=$(stat -c '%U:%G' /data/data/{pacote})
    tar -xzf "{arquivo_local}" -C /data/data/ 2>/dev/null || true
    chown -R $APP_OWNER /data/data/{pacote}
    restorecon -R /data/data/{pacote}
    echo "sucesso"
    """
    sucesso, saida = executar_root(comando)

    if os.path.exists(arquivo_local):
        try: os.remove(arquivo_local)
        except: pass

    if "erro_pacote_nao_instalado" in saida:
        print(f"[X] Erro: O pacote alvo '{pacote}' não está instalado neste dispositivo.")
        return False
    elif "sucesso" in saida:
        print(f"[+] Dados injetados com sucesso no pacote '{pacote}'!")
        
        # 🟢 O SINAL DE FUMAÇA PARA O DISCORD:
        # Escrevemos silenciosamente no install_report para o import.py jogar pro servidor!
        try:
            report_file = os.path.join(os.path.dirname(os.getcwd()), "Data", "install_report.json")
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            report_data = {"install_success": [], "install_failed": []}
            if os.path.exists(report_file):
                with open(report_file, "r") as f:
                    report_data = json.load(f)
                    
            if pacote not in report_data["install_success"]:
                report_data["install_success"].append(pacote)
                
            with open(report_file, "w") as f:
                json.dump(report_data, f)
        except Exception as e:
            pass # Falha silenciosa no aviso não deve travar o bot
            
        return True
    else:
        print(f"[X] Falha crítica na injeção dos dados via root: {saida}")
        return False
