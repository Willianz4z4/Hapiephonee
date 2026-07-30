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

PAYLOAD_FILE = os.path.join(DATA_DIR, "payload_install.json")
REPORT_FILE = os.path.join(DATA_DIR, "install_report.json")
TEMP_EXTRACT_DIR = os.path.join(DATA_DIR, "temp_extract")

os.makedirs(DATA_DIR, exist_ok=True)

# ==========================================
# 🛠️ FUNÇÃO CHAVE: ATIVAÇÃO DINÂMICA GLOBAL
# ==========================================
def activate_global_tag(tag):
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
# 📥 FUNÇÕES DE DOWNLOAD E INSTALAÇÃO
# ==========================================
def download_file(url, dest_folder, extras=None):
    if extras is None: extras = {}
    os.makedirs(dest_folder, exist_ok=True)

    temp_filename = f"payload_{int(time.time())}_temp"
    dest_path = os.path.join(dest_folder, temp_filename)

    try:
        if "drive.google.com" in url:
            gdown.download(url, dest_path, quiet=False)
        else:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        ext = ".apk"
        try:
            if zipfile.is_zipfile(dest_path):
                with zipfile.ZipFile(dest_path, 'r') as z:
                    if "AndroidManifest.xml" in z.namelist():
                        ext = ".apk"
                    else:
                        ext = ".zip"
        except Exception:
            pass 

        final_path = dest_path.replace("_temp", ext)
        os.rename(dest_path, final_path)
        print(f"🔍 Detetive de arquivo detectou: pacote {ext.upper()}")

        return final_path
    except Exception as e:
        print(f"❌ Erro ao baixar arquivo: {e}")
        return None

def install_apk(apk_path, visibility):
    print(f"📦 Instalando APK: {os.path.basename(apk_path)}")
    try:
        result = subprocess.run(f"su -c 'pm install -r \"{apk_path}\"'", shell=True, capture_output=True, text=True)
        if "Success" in result.stdout:
            print("✅ APK Instalado com sucesso!")
            if str(visibility).lower() == "system":
                print("👻 Comando para ocultar o app registrado (Modo System).")
            return True
        else:
            print(f"❌ Falha ao instalar APK: {result.stdout} {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erro crítico no PM INSTALL: {e}")
        return False

def run_data_injection(tar_file):
    print(f"💉 Dados encontrados ({os.path.basename(tar_file)}). Enviando para o apps_data.py...")
    apps_data_script = os.path.join(HAPIE_APPS_DIR, "apps_data.py")

    if not os.path.exists(apps_data_script):
        print("⚠️ Script apps_data.py não encontrado. Injeção abortada.")
        return False

    try:
        subprocess.run([sys.executable, apps_data_script, "--file", tar_file], check=True)
        print("✅ Dados injetados com maestria no data user!")
        return True
    except subprocess.CalledProcessError:
        print("❌ apps_data.py falhou ao injetar os dados.")
        return False
    except Exception as e:
        print(f"❌ Erro ao chamar injetor de dados: {e}")
        return False

# ==========================================
# 🗜️ MOTOR DE EXTRAÇÃO BLINDADO (7-ZIP)
# ==========================================
def recursive_extract(target_dir, senha_padrao):
    # Instala o mestre das extrações e garante que não vai travar
    os.system("pkg install p7zip -y -q > /dev/null 2>&1")

    while True:
        zip_found = False
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.lower().endswith(".zip"):
                    zip_path = os.path.join(root, file)
                    print(f"🗜️ Extraindo: {file} (Força Bruta com 7z)...")
                    
                    try:
                        # O 7z lida com AES e o stdin=subprocess.DEVNULL impede que ele congele esperando você digitar algo
                        if senha_padrao:
                            cmd = f'7z x "{zip_path}" -o"{root}" -p"{senha_padrao}" -y'
                        else:
                            cmd = f'7z x "{zip_path}" -o"{root}" -y'
                            
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, stdin=subprocess.DEVNULL)
                        
                        if result.returncode != 0:
                            print(f"🔒 {file} recusou a extração! Chutando a porta com a senha '123'...")
                            cmd_fallback = f'7z x "{zip_path}" -o"{root}" -p"123" -y'
                            result_fallback = subprocess.run(cmd_fallback, shell=True, capture_output=True, text=True, stdin=subprocess.DEVNULL)
                            
                            if result_fallback.returncode != 0:
                                print(f"❌ Erro fatal ao extrair {file}. (Pode estar corrompido ou a senha não é 123)")
                            else:
                                print(f"🔓 Sucesso! A senha '123' abriu o cofre.")
                    except Exception as e:
                        print(f"❌ Erro no terminal ao chamar 7z para {file}: {e}")
                    
                    # Deleta o ZIP que acabou de ser processado para não criar loop infinito
                    try: os.remove(zip_path)
                    except: pass
                    
                    zip_found = True
                    break # Quebra para recomeçar a varredura com os novos arquivos extraídos
            if zip_found:
                break
                
        # Se varreu tudo e não achou nenhum .zip, sai do loop
        if not zip_found:
            break

# ==========================================
# 🧠 MOTOR PRINCIPAL DE INSTALAÇÃO
# ==========================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Caminho do arquivo payload.json", default=PAYLOAD_FILE)
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print("💤 Nenhum arquivo de payload encontrado. Saindo...")
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

        downloaded_file = download_file(link, DATA_DIR, extras)
        if not downloaded_file:
            report["install_failed"].append(link)
            continue

        process_100_percent_success = False

        if downloaded_file.endswith(".zip"):
            if os.path.exists(TEMP_EXTRACT_DIR):
                shutil.rmtree(TEMP_EXTRACT_DIR)
            os.makedirs(TEMP_EXTRACT_DIR, exist_ok=True)

            print("🗜️ Iniciando varredura e extração recursiva...")
            senha = extras.get("password") if isinstance(extras, dict) else None
            
            # Copia o zip principal para o temp_extract
            main_zip_temp = os.path.join(TEMP_EXTRACT_DIR, "main_payload.zip")
            shutil.copy2(downloaded_file, main_zip_temp)

            # Extração veloz com 7z
            recursive_extract(TEMP_EXTRACT_DIR, senha)
            
            # Caça TODOS os APKs e o arquivo tar.gz em todas as subpastas criadas
            apk_files = []
            tar_file = None
            for root_dir, _, files in os.walk(TEMP_EXTRACT_DIR):
                for f in files:
                    if f.endswith(".apk"):
                        apk_files.append(os.path.join(root_dir, f))
                    elif f.endswith(".tar.gz") and tar_file is None:
                        tar_file = os.path.join(root_dir, f)

            apk_success = False

            if apk_files:
                apk_success = True 
                print(f"📦 Foram encontrados {len(apk_files)} APK(s) no total. Iniciando instalações...")
                for apk_path in apk_files:
                    if not install_apk(apk_path, visibility):
                        apk_success = False
                        print(f"❌ Falha ao instalar o APK: {os.path.basename(apk_path)}")
            else:
                print("⚠️ Nenhum APK encontrado dentro de toda a estrutura do ZIP!")

            if apk_success:
                if tar_file:
                    injection_success = run_data_injection(tar_file)
                    if injection_success:
                        process_100_percent_success = True
                    else:
                        print("⚠️ Os APKs instalaram, mas a injeção FALHOU. A tag global não será ativada.")
                else:
                    process_100_percent_success = True

            shutil.rmtree(TEMP_EXTRACT_DIR, ignore_errors=True)

        elif downloaded_file.endswith(".apk"):
            if install_apk(downloaded_file, visibility):
                process_100_percent_success = True

        if process_100_percent_success:
            report["install_success"].append(link)
            print("🌟 Processo finalizado com SUCESSO ABSOLUTO.")
            activate_global_tag(tag)
        else:
            report["install_failed"].append(link)

        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)

    try:
        with open(REPORT_FILE, "w") as f:
            json.dump(report, f)
    except: pass

    if os.path.exists(args.file):
        os.remove(args.file)

if __name__ == "__main__":
    main()
