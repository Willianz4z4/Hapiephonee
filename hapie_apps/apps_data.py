import os
import subprocess
import re
import requests
import json

try:
    import gdown
except ImportError:
    gdown = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DATA_DIR = os.path.join(SCRIPT_DIR, "data_apps")
TIMEOUT_REDE = 15

def inicializar_ambiente():
    if not os.path.exists(BASE_DATA_DIR):
        os.makedirs(BASE_DATA_DIR, exist_ok=True)

def pacote_eh_valido(pacote):
    return bool(re.match(r'^[a-zA-Z0-9_.]+$', pacote))

def executar_root(comando):
    resultado = subprocess.run(
        ['su', '-c', comando],
        capture_output=True,
        text=True
    )
    return True, resultado.stdout.strip() + " " + resultado.stderr.strip()

def data_save(pacote):
    if not pacote_eh_valido(pacote):
        print(f"[X] Erro: Nome do pacote inválido '{pacote}'")
        return False

    inicializar_ambiente()
    print(f"=== [data_save] SALVANDO DADOS DO PACOTE '{pacote}' ===")
    safe_pkg = pacote.replace(".", "_")
    destino_final = os.path.join(BASE_DATA_DIR, f"data_{safe_pkg}.tar.gz")

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
        tamanho_kb = os.path.getsize(destino_final) // 1024
        print(f"[+] Dados salvos com sucesso: {destino_final} (Tamanho: {tamanho_kb} KB)")
        return True
    else:
        print(f"[X] Falha no processo de compactação via root: {saida}")
        return False

def data_export(pacote, url_servidor, owner_id, device_id):
    inicializar_ambiente()
    safe_pkg = pacote.replace(".", "_")
    arquivo_bot = os.path.join(BASE_DATA_DIR, f"data_{safe_pkg}.tar.gz")

    if not os.path.exists(arquivo_bot):
        print(f"[X] Erro de Exportação: Arquivo {arquivo_bot} não encontrado.")
        return False

    print(f"=== [data_export] ENVIANDO DATA DE '{pacote}' PARA O SERVIDOR ===")
    try:
        with open(arquivo_bot, 'rb') as f:
            files = {'file': (f"data_{safe_pkg}.tar.gz", f, 'application/gzip')}
            data = {
                'pkg_name': pacote,
                'owner_id': str(owner_id),
                'device_id': str(device_id)
            }
            response = requests.post(url_servidor, files=files, data=data, timeout=TIMEOUT_REDE)

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
    if match_d:
        file_id = match_d.group(1)
    else:
        match_id = re.search(r'id=([a-zA-Z0-9_-]+)', url)
        if match_id:
            file_id = match_id.group(1)

    if file_id:
        if gdown:
            try:
                gdown.download(f"https://drive.google.com/uc?id={file_id}", out_path, quiet=True)
                if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                    return True
            except Exception as e:
                print(f"[!] Aviso gdown falhou, tentando método nativo. Erro: {e}")

        session = requests.Session()
        confirm_url = "https://docs.google.com/uc?export=download"
        params = {'id': file_id}
        try:
            response = session.get(confirm_url, params=params, stream=True, timeout=TIMEOUT_REDE)

            token = None
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    token = value
                    break

            if token:
                params['confirm'] = token
                response = session.get(confirm_url, params=params, stream=True, timeout=TIMEOUT_REDE)

            if response.status_code == 200:
                with open(out_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
        except requests.exceptions.RequestException as e:
            print(f"[X] Erro de rede ao baixar do Drive: {e}")
            return False
    else:
        try:
            response = requests.get(url, stream=True, timeout=TIMEOUT_REDE)
            if response.status_code == 200:
                with open(out_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
        except requests.exceptions.RequestException as e:
            print(f"[X] Erro de rede ao baixar dados genéricos: {e}")
            return False

    return False

def data_inject(pacote, url_servidor):
    if not pacote_eh_valido(pacote):
        print(f"[X] Erro: Nome do pacote inválido '{pacote}'")
        return False

    inicializar_ambiente()
    print(f"=== [data_inject] INJETANDO DADOS NO PACOTE '{pacote}' ===")
    safe_pkg = pacote.replace(".", "_")
    arquivo_local = os.path.join(BASE_DATA_DIR, f"data_{safe_pkg}.tar.gz")

    if not os.path.exists(arquivo_local):
        if "drive.google.com" in url_servidor:
            url_download = url_servidor
        else:
            url_download = f"{url_servidor.rstrip('/')}/download/data_{safe_pkg}.tar.gz"

        print(f"[!] Requisitando dados da nuvem: {url_download}")
        try:
            sucesso_download = baixar_data_com_cookies(url_download, arquivo_local)
            if sucesso_download and os.path.exists(arquivo_local) and os.path.getsize(arquivo_local) > 1000:
                print(f"[+] Download da nuvem concluído com sucesso.")
            else:
                print(f"[X] Falha ao baixar os dados da nuvem ou arquivo muito pequeno.")
                if os.path.exists(arquivo_local):
                    os.remove(arquivo_local)
                return False
        except Exception as e:
            print(f"[X] Falha crítica ao fazer o download: {e}")
            if os.path.exists(arquivo_local):
                os.remove(arquivo_local)
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
        try:
            os.remove(arquivo_local)
        except OSError as e:
            print(f"[!] Aviso: Não foi possível remover o arquivo temporário. Erro: {e}")

    if "erro_pacote_nao_instalado" in saida:
        print(f"[X] Erro: O pacote alvo '{pacote}' não está instalado neste dispositivo.")
        return False
    elif "sucesso" in saida:
        print(f"[+] Dados injetados com sucesso no pacote '{pacote}'!")

        try:
            report_file = os.path.join(os.path.dirname(SCRIPT_DIR), "Data", "install_report.json")
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            report_data = {"install_success": [], "install_failed": []}

            if os.path.exists(report_file):
                with open(report_file, "r") as f:
                    report_data = json.load(f)

            if pacote not in report_data["install_success"]:
                report_data["install_success"].append(pacote)

            with open(report_file, "w") as f:
                json.dump(report_data, f, indent=4)

        except Exception as e:
            print(f"[!] Erro ao atualizar install_report.json: {e}")

        return True
    else:
        print(f"[X] Falha crítica na injeção dos dados via root: {saida}")
        return False

def add_ugclone_config(pacote_alvo, configs):
    print(f"\n=== [add_ugclone_config] INJETANDO CONFIGS PARA '{pacote_alvo}' ===")

    inicializar_ambiente()
    master_xml = "/data/data/com.ugcloner.xfein/shared_prefs/com.ugcloner.xfein_preferences.xml"
    ug_pkg = "com.ugcloner.xfein"
    tag_name = f"clone_settings_{pacote_alvo}"

    # 🛑 TRUQUE DE MESTRE: Parar o app ANTES de ler/escrever!
    # Se editarmos com ele em cache, o Android apaga nossa edição.
    executar_root(f"am force-stop {ug_pkg}")

    # Agora sim, lemos o arquivo real salvo no disco
    sucesso, xml_content = executar_root(f"cat {master_xml} 2>/dev/null || echo 'FILE_NOT_FOUND'")
    xml_content = xml_content.strip()

    if "FILE_NOT_FOUND" in xml_content or not xml_content:
        xml_content = "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n<map>\n</map>"

    # Gera a string JSON compacta e escapa as aspas
    settings_json_str = json.dumps(configs, separators=(',', ':'))
    escaped_json = settings_json_str.replace('"', '&quot;')
    
    nova_tag = f'    <string name="{tag_name}">{escaped_json}</string>'
    regex = rf'<string name="{tag_name}">.*?</string>'

    # Injeção à prova de balas
    if re.search(regex, xml_content, flags=re.DOTALL):
        xml_content = re.sub(regex, nova_tag, xml_content, flags=re.DOTALL)
        print(f"[!] Substituindo configuração existente para: {tag_name}")
    elif "</map>" in xml_content:
        xml_content = xml_content.replace("</map>", f"{nova_tag}\n</map>")
        print(f"[+] Criando nova configuração e injetando antes do </map>")
    else:
        print("[X] ERRO CRÍTICO: Não encontrei a tag <map>!")
        return False

    # Salvando temporário
    temp_file = os.path.join(BASE_DATA_DIR, "temp_ug.xml")
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(xml_content)

    # Copiando via Root e ajustando permissões
    comando = f"""
    mkdir -p /data/data/{ug_pkg}/shared_prefs/
    cp "{temp_file}" "{master_xml}"
    
    APP_OWNER=$(stat -c '%U:%G' /data/data/{ug_pkg} 2>/dev/null || echo "10000:10000")
    
    chown $APP_OWNER "{master_xml}"
    chmod 660 "{master_xml}"
    restorecon "{master_xml}" 2>/dev/null || true
    echo "sucesso"
    """

    sucesso_write, saida = executar_root(comando)

    if os.path.exists(temp_file):
        os.remove(temp_file)

    if "sucesso" in saida:
        print(f"[+] XML gravado e protegido com sucesso!")
        return True
    else:
        print(f"[X] Falha na gravação via ROOT: {saida}")
        return False
