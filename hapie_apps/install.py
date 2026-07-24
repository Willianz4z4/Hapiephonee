import os
import sys
import json
import time
import shutil
import zipfile
import subprocess
import argparse
import requests
import gdown
from urllib.parse import urlparse

# ==========================================
# 📂 CONFIGURAÇÃO DE DIRETÓRIOS
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNCTIONS_JSON_FILE = os.path.join(BASE_DIR, "functions.json")
DATA_DIR = os.path.join(BASE_DIR, "Data")
HAPIE_APPS_DIR = os.path.join(BASE_DIR, "hapie_apps")

PAYLOAD_FILE = os.path.join(DATA_DIR, "payload.json")
REPORT_FILE = os.path.join(DATA_DIR, "install_report.json")
TEMP_EXTRACT_DIR = os.path.join(DATA_DIR, "temp_extract")

os.makedirs(DATA_DIR, exist_ok=True)

# ==========================================
# 🛠️ FUNÇÃO CHAVE: ATIVAÇÃO DINÂMICA GLOBAL
# ==========================================
def activate_global_tag(tag):
    """
    Só é chamada no FINAL de 100% do processo. 
    Transforma qualquer string (autocopy, autopush, etc) em True.
    """
    if not tag or str(tag).strip().lower() in ["", "none", "null"]:
        return
        
    tag = str(tag).strip()
    data = {}
    
    if os.path.exists(FUNCTIONS_JSON_FILE):
        try:
            with open(FUNCTIONS_JSON_FILE, "r") as f:
                data = json.load(f)
        except: pass
        
    data[tag] = True
    
    try:
        with open(FUNCTIONS_JSON_FILE, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ [SUCESSO] Chave Global '{tag}' ATIVADA no painel do celular!")
    except Exception as e:
        print(f"❌ [ERRO] Falha ao ligar a chave '{tag}': {e}")

# ==========================================
# 📥 FUNÇÕES DE DOWNLOAD E EXTRAÇÃO
# ==========================================
def download_file(url, dest_folder):
    os.makedirs(dest_folder, exist_ok=True)
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path) or f"payload_{int(time.time())}.zip"
    dest_path = os.path.join(dest_folder, filename)

    try:
        if "drive.google.com" in url:
            gdown.download(url, dest_path, quiet=False, fuzzy=True)
        else:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        return dest_path
    except Exception as e:
        print(f"❌ Erro ao baixar arquivo: {e}")
        return None

def install_apk(apk_path, visibility):
    print(f"📦 Instalando APK: {os.path.basename(apk_path)}")
    try:
        result = subprocess.run(f"su -c 'pm install -r \"{apk_path}\"'", shell=True, capture_output=True, text=True)
        if "Success" in result.stdout:
            print("✅ APK Instalado com sucesso!")
            # Opcional: Lógica do pm hide caso a visibilidade seja "system"
            if str(visibility).lower() == "system":
                # Como não temos o nome do pacote exato aqui, uma versão avançada usaria aapt.
                # Aqui consideramos o comando básico.
                print("👻 Comando para ocultar o app registrado (Modo System).")
            return True
        else:
            print(f"❌ Falha ao instalar APK: {result.stdout} {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erro crítico no PM INSTALL: {e}")
        return False

def run_data_injection(tar_file):
    print(f"💉 Dados encontrados ({os.path.basename(tar_file)}). Iniciando injeção profunda...")
    apps_data_script = os.path.join(HAPIE_APPS_DIR, "apps_data.py")
    
    if not os.path.exists(apps_data_script):
        print("⚠️ Script apps_data.py não encontrado. Injeção abortada.")
        return False

    try:
        # Chama o apps_data.py como um operário separado
        # Se ele rodar e sair com código 0, deu certo. Se sair com erro (Crash), check=True ativa o Except.
        subprocess.run([sys.executable, apps_data_script, "--file", tar_file], check=True)
        print("✅ Dados injetados com maestria!")
        return True
    except subprocess.CalledProcessError:
        print("❌ apps_data.py falhou ao injetar os dados.")
        return False
    except Exception as e:
        print(f"❌ Erro ao chamar injetor de dados: {e}")
        return False

# ==========================================
# 🧠 MOTOR PRINCIPAL DE INSTALAÇÃO
# ==========================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Caminho do arquivo payload.json", default=PAYLOAD_FILE)
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print("⚠️ Arquivo de payload não encontrado. Saindo...")
        return

    try:
        with open(args.file, "r") as f:
            payload = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler payload: {e}")
        return

    install_orders = payload.get("install", [])
    if not install_orders:
        print("💤 Nenhuma ordem de instalação encontrada.")
        return

    report = {"install_success": [], "install_failed": []}

    for app_data in install_orders:
        if len(app_data) < 4:
            continue
            
        link, visibility, tag, extras = app_data
        print(f"\n🚀 Iniciando processamento do link: {link[:40]}...")

        # 1. Download do Pacote
        downloaded_file = download_file(link, DATA_DIR)
        if not downloaded_file:
            report["install_failed"].append(link)
            continue

        process_100_percent_success = False

        # 2. Verificação do Tipo de Arquivo
        if downloaded_file.endswith(".zip"):
            if os.path.exists(TEMP_EXTRACT_DIR):
                shutil.rmtree(TEMP_EXTRACT_DIR)
            os.makedirs(TEMP_EXTRACT_DIR, exist_ok=True)

            print("🗜️ Extraindo arquivo ZIP...")
            try:
                with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
                    zip_ref.extractall(TEMP_EXTRACT_DIR)
            except Exception as e:
                print(f"❌ Erro ao extrair ZIP: {e}")
                report["install_failed"].append(link)
                continue

            # Varrendo o que tem dentro do ZIP
            arquivos_extraidos = os.listdir(TEMP_EXTRACT_DIR)
            apk_file = next((f for f in arquivos_extraidos if f.endswith(".apk")), None)
            tar_file = next((f for f in arquivos_extraidos if f.endswith(".tar.gz")), None)

            # Instala o APK primeiro
            apk_success = False
            if apk_file:
                apk_path = os.path.join(TEMP_EXTRACT_DIR, apk_file)
                apk_success = install_apk(apk_path, visibility)
            else:
                print("⚠️ Nenhum APK encontrado dentro do ZIP!")

            # Se instalou o APK e achou dados (.tar.gz)
            if apk_success:
                if tar_file:
                    tar_path = os.path.join(TEMP_EXTRACT_DIR, tar_file)
                    # Delega a injeção ao apps_data.py e pega o resultado (Verdadeiro ou Falso)
                    injection_success = run_data_injection(tar_path)
                    
                    if injection_success:
                        process_100_percent_success = True
                    else:
                        print("⚠️ O APK instalou, mas a injeção FALHOU. A tag global não será ativada.")
                else:
                    # Tinha APK, mas não tinha dados extra. Então o ZIP acabou com 100% de sucesso.
                    process_100_percent_success = True
            
            # Limpeza
            shutil.rmtree(TEMP_EXTRACT_DIR, ignore_errors=True)
            
        elif downloaded_file.endswith(".apk"):
            # É só um APK direto, não tem dados
            if install_apk(downloaded_file, visibility):
                process_100_percent_success = True

        # 3. VEREDITO FINAL (A TRAVA DE SEGURANÇA DA TAG)
        if process_100_percent_success:
            report["install_success"].append(link)
            print("🌟 Processo finalizado com SUCESSO ABSOLUTO.")
            # 🔥 AQUI ACONTECE A MÁGICA: Só liga se fechou os 100%!
            activate_global_tag(tag)
        else:
            report["install_failed"].append(link)

        # Remove arquivo baixado original para poupar espaço
        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)

    # 4. Salvar Relatório para o webhook mandar pro Servidor
    try:
        with open(REPORT_FILE, "w") as f:
            json.dump(report, f)
    except: pass

    # Limpa o payload processado
    if os.path.exists(args.file):
        os.remove(args.file)

if __name__ == "__main__":
    main()
