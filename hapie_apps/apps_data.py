import os
import subprocess
import shutil
import urllib.request
import urllib.error

# Pasta local usada apenas pelo Bot (não sincronizada no GitHub)
BASE_DATA_DIR = os.path.join(os.getcwd(), "data_apps")

def inicializar_ambiente():
    """Garante que a pasta interna do Bot exista localmente."""
    if not os.path.exists(BASE_DATA_DIR):
        os.makedirs(BASE_DATA_DIR, exist_ok=True)

def executar_root(comando):
    """Executa comandos no shell do Android com permissão root."""
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
    """
    Cria um backup do pacote do app e guarda na pasta interna do Bot.
    O nome do arquivo será baseado no próprio nome do pacote (ex: com.ugcloner.xfein.tar.gz).
    """
    inicializar_ambiente()
    print(f"=== [data_save] SALVANDO DADOS DO PACOTE '{pacote}' ===")
    
    tmp_android_backup = f"/data/local/tmp/{pacote}_tmp.tar.gz"
    destino_final = os.path.join(BASE_DATA_DIR, f"{pacote}.tar.gz")
    
    comando = f"""
    if [ -d "/data/data/{pacote}" ]; then
        tar -czf "{tmp_android_backup}" -C "/data/data" "{pacote}"
        chmod 666 "{tmp_android_backup}"
        echo "sucesso"
    else
        echo "erro_pasta_nao_encontrada"
    fi
    """
    
    sucesso, saida = executar_root(comando)
    
    if "erro_pasta_nao_encontrada" in saida:
        print(f"[X] Erro: Pasta do aplicativo /data/data/{pacote} não existe.")
        return False
        
    if sucesso and os.path.exists(tmp_android_backup):
        try:
            shutil.move(tmp_android_backup, destino_final)
            print(f"[+] Dados salvos com sucesso no Bot: {destino_final}")
            return True
        except Exception as e:
            print(f"[X] Erro ao mover o arquivo para a pasta do Bot: {e}")
            return False
    else:
        print(f"[X] Falha no processo de compactação via root: {saida}")
        return False

def data_export(pacote, url_servidor):
    """
    Envia o arquivo de dados de um pacote local (data_apps/pacote.tar.gz) para o servidor central.
    """
    inicializar_ambiente()
    arquivo_bot = os.path.join(BASE_DATA_DIR, f"{pacote}.tar.gz")
    
    if not os.path.exists(arquivo_bot):
        print(f"[X] Erro de Exportação: Arquivo {arquivo_bot} não encontrado.")
        return False
        
    print(f"=== [data_export] ENVIANDO DATA DE '{pacote}' PARA O SERVIDOR ===")
    try:
        with open(arquivo_bot, 'rb') as f:
            dados_binarios = f.read()
            
        req = urllib.request.Request(
            url_servidor, 
            data=dados_binarios, 
            headers={
                'Content-Type': 'application/octet-stream',
                'X-Backup-Package': f"{pacote}.tar.gz"
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            if status in [200, 201]:
                print(f"[+] Exportado com sucesso! Código: {status}")
                return True
            else:
                print(f"[X] Servidor rejeitou o arquivo. Código: {status}")
                return False
    except Exception as e:
        print(f"[X] Falha ao exportar dados para o servidor: {e}")
        return False

def data_inject(pacote, url_servidor):
    """
    Injeta os dados no pacote do app de forma inteligente:
    1. Olha se o arquivo local 'data_apps/pacote.tar.gz' existe.
    2. Se NÃO existe, faz uma requisição HTTP para o servidor para baixar o arquivo.
    3. Injeta os dados via Root corrigindo permissões e SELinux.
    """
    inicializar_ambiente()
    print(f"=== [data_inject] INJETANDO DADOS NO PACOTE '{pacote}' ===")
    
    arquivo_local = os.path.join(BASE_DATA_DIR, f"{pacote}.tar.gz")
    tmp_android_backup = f"/data/local/tmp/inject_{pacote}_tmp.tar.gz"
    
    # INTELIGÊNCIA: Verifica se o arquivo já existe localmente na pasta do Bot
    if os.path.exists(arquivo_local):
        print(f"[-] Arquivo local localizado em data_apps/{pacote}.tar.gz. Usando local...")
        try:
            shutil.copy2(arquivo_local, tmp_android_backup)
        except Exception as e:
            print(f"[X] Erro ao preparar arquivo local para injeção: {e}")
            return False
    else:
        # Se NÃO existe na pasta, faz a requisição para o servidor externo
        url_download = f"{url_servidor.rstrip('/')}/download/{pacote}.tar.gz"
        print(f"[!] Arquivo local não encontrado. Requisitando ao servidor: {url_download}")
        try:
            with urllib.request.urlopen(url_download) as response, open(tmp_android_backup, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            print(f"[+] Download do servidor concluído com sucesso.")
            
            # Opcional: Salva uma cópia na pasta local para as próximas vezes ser mais rápido
            shutil.copy2(tmp_android_backup, arquivo_local)
        except urllib.error.HTTPError as e:
            print(f"[X] Erro no servidor (HTTP {e.code}): O servidor não possui esse data.")
            return False
        except Exception as e:
            print(f"[X] Falha ao requisitar/baixar o arquivo do servidor: {e}")
            return False

    # Executa a injeção via Root no sistema Android
    comando = f"""
    if [ ! -f "{tmp_android_backup}" ]; then
        echo "erro_arquivo_sumiu"
        exit 0
    fi
    
    if [ ! -d "/data/data/{pacote}" ]; then
        echo "erro_pacote_nao_instalado"
        exit 0
    fi
    
    # Fecha o app para evitar quebras
    am force-stop "{pacote}"
    
    # Captura quem é o dono original (UID:GID) do app no aparelho
    APP_OWNER=$(stat -c '%U:%G' /data/data/{pacote})
    
    # Extrai substituindo os dados antigos
    tar -xzf "{tmp_android_backup}" -C /data/data/
    
    # Ajusta permissões e o contexto SELinux
    chown -R $APP_OWNER /data/data/{pacote}
    restorecon -R /data/data/{pacote}
    
    rm -f "{tmp_android_backup}"
    echo "sucesso"
    """
    
    sucesso, saida = executar_root(comando)
    
    # Limpeza preventiva do arquivo temporário
    if os.path.exists(tmp_android_backup):
        os.remove(tmp_android_backup)
        
    if "erro_pacote_nao_instalado" in saida:
        print(f"[X] Erro: O pacote alvo '{pacote}' não está instalado neste dispositivo.")
        return False
    elif sucesso and "sucesso" in saida:
        print(f"[+] Dados injetados com sucesso no pacote '{pacote}'!")
        return True
    else:
        print(f"[X] Falha crítica na injeção dos dados via root: {saida}")
        return False

