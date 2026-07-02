import os
import subprocess
import urllib.request
import urllib.error
import requests

BASE_DATA_DIR = os.path.join(os.getcwd(), "data_apps")

def inicializar_ambiente():
    if not os.path.exists(BASE_DATA_DIR):
        os.makedirs(BASE_DATA_DIR, exist_ok=True)

def executar_root(comando):
    try:
        resultado = subprocess.run(
            ['su', '-c', comando],
            check=True,
            capture_output=True,
            text=True
        )
        return True, resultado.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()

def data_save(pacote):
    inicializar_ambiente()
    print(f"=== [data_save] SALVANDO DADOS DO PACOTE '{pacote}' ===")

    # 🚀 Agora o destino final é passado direto pro Root! Sem intermediários.
    destino_final = os.path.join(BASE_DATA_DIR, f"{pacote}.tar.gz")

    comando = f"""
    if [ -d "/data/data/{pacote}" ]; then
        # Compacta direto na pasta do bot
        tar -czf "{destino_final}" -C "/data/data" "{pacote}"
        
        # Libera acesso total para o Python conseguir ler e apagar depois
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

    if sucesso and os.path.exists(destino_final):
        print(f"[+] Dados salvos com sucesso no Bot: {destino_final}")
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
                # Deleta o arquivo local já que subiu com sucesso
                os.remove(arquivo_bot)
                return True
            else:
                print(f"[X] Servidor rejeitou o arquivo. Código: {response.status_code} | Resposta: {response.text}")
                return False
    except Exception as e:
        print(f"[X] Falha ao exportar dados para o servidor: {e}")
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
            # Baixa direto usando a biblioteca requests
            response = requests.get(url_download, stream=True)
            if response.status_code == 200:
                with open(arquivo_local, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"[+] Download da nuvem concluído com sucesso.")
            else:
                print(f"[X] Falha ao baixar da nuvem. Código: {response.status_code}")
                return False
        except Exception as e:
            print(f"[X] Falha ao fazer o download: {e}")
            return False

    # Root faz a extração lendo direto da pasta do bot
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

    tar -xzf "{arquivo_local}" -C /data/data/

    chown -R $APP_OWNER /data/data/{pacote}
    restorecon -R /data/data/{pacote}

    echo "sucesso"
    """

    sucesso, saida = executar_root(comando)

    # Limpa o backup baixado para não ocupar espaço
    if os.path.exists(arquivo_local):
        os.remove(arquivo_local)

    if "erro_pacote_nao_instalado" in saida:
        print(f"[X] Erro: O pacote alvo '{pacote}' não está instalado neste dispositivo.")
        return False
    elif sucesso and "sucesso" in saida:
        print(f"[+] Dados injetados com sucesso no pacote '{pacote}'!")
        return True
    else:
        print(f"[X] Falha crítica na injeção dos dados via root: {saida}")
        return False
