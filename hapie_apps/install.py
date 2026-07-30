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

# Cores
C_GREEN = '\033[92m'
C_YELLOW = '\033[93m'
C_CYAN = '\033[96m'
C_RED = '\033[91m'
C_RESET = '\033[0m'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNCTIONS_JSON_FILE = os.path.join(BASE_DIR, "functions.json")
DATA_DIR = os.path.join(BASE_DIR, "Data")
HAPIE_APPS_DIR = os.path.join(BASE_DIR, "hapie_apps")
PAYLOAD_FILE = os.path.join(DATA_DIR, "payload_install.json")
REPORT_FILE = os.path.join(DATA_DIR, "install_report.json")
TEMP_EXTRACT_DIR = os.path.join(DATA_DIR, "temp_extract")
DEBUG_LOG_FILE = os.path.join(DATA_DIR, "install_debug.txt")

os.makedirs(DATA_DIR, exist_ok=True)

# Limpa o log antigo a cada nova execução
with open(DEBUG_LOG_FILE, 'w', encoding='utf-8') as f:
    f.write(f"--- LOG DE INSTALAÇÃO INICIADO EM {time.ctime()} ---\n")

def log_debug(msg):
    try:
        with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except: pass

def disable_play_protect():
    """Desativa a verificação de aplicativos do Android para evitar INSTALL_FAILED_VERIFICATION_FAILURE."""
    log_debug("Desativando Play Protect / Verificador de pacotes...")
    subprocess.run("su -c 'settings put global package_verifier_enable 0'", shell=True, capture_output=True)
    subprocess.run("su -c 'settings put global package_verifier_user_consent -1'", shell=True, capture_output=True)

def activate_global_tag(tag):
    if not tag or str(tag).strip().lower() in ["", "none", "null"]: return
    tag = str(tag).strip()
    data = {}
    if os.path.exists(FUNCTIONS_JSON_FILE):
        try:
            with open(FUNCTIONS_JSON_FILE, "r") as f: data = json.load(f)
        except: pass
    data[tag] = True
    try:
        with open(FUNCTIONS_JSON_FILE, "w") as f: json.dump(data, f, indent=4)
        log_debug(f"Tag Global '{tag}' ativada com sucesso.")
    except Exception as e:
        log_debug(f"ERRO ao ativar Tag Global: {e}")

def get_package_name_from_apk(apk_path):
    """Tenta obter o package name do APK via aapt ou aapt2 se disponíveis."""
    try:
        res = subprocess.run(f"aapt dump badging \"{apk_path}\" | grep package", shell=True, capture_output=True, text=True)
        if "name='" in res.stdout:
            pkg = res.stdout.split("name='")[1].split("'")[0]
            return pkg
    except Exception as e:
        log_debug(f"Aviso ao extrair pacote via aapt: {e}")
    return None

def hide_app(package_name):
    """Oculta o app do launcher do Android."""
    if not package_name:
        return
    log_debug(f"Ocultando app do launcher: {package_name}")
    subprocess.run(f"su -c 'pm hide \"{package_name}\"'", shell=True, capture_output=True)
    subprocess.run(f"su -c 'pm disable-user --user 0 \"{package_name}\"'", shell=True, capture_output=True)

def download_file(url, dest_folder, extras=None):
    if extras is None: extras = {}
    os.makedirs(dest_folder, exist_ok=True)
    temp_filename = f"payload_{int(time.time())}_temp"
    dest_path = os.path.join(dest_folder, temp_filename)

    try:
        print(f"{C_CYAN}📥 Baixando pacote...{C_RESET}")
        log_debug(f"Iniciando download do link: {url[:50]}...")
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
                    if "AndroidManifest.xml" not in z.namelist():
                        ext = ".zip"
        except: pass

        final_path = dest_path.replace("_temp", ext)
        os.rename(dest_path, final_path)
        log_debug(f"Download concluído! Arquivo identificado como {ext.upper()}")
        return final_path
    except Exception as e:
        log_debug(f"ERRO CRÍTICO NO DOWNLOAD: {e}")
        return None

def install_apk(apk_path, visibility, tag=None):
    try:
        log_debug(f"Executando PM INSTALL para: {os.path.basename(apk_path)}")
        
        # Pega o nome do pacote antes de instalar se possível
        pkg_name = get_package_name_from_apk(apk_path)

        # Usando -r (reinstall), -d (downgrade) e -g (grant permissions) para evitar falhas
        result = subprocess.run(f"su -c 'pm install -r -d -g \"{apk_path}\"'", shell=True, capture_output=True, text=True)
        
        if "Success" in result.stdout:
            log_debug(f"Instalação do APK {os.path.basename(apk_path)} -> SUCESSO")
            
            # Verifica se precisa ocultar o app
            vis_str = str(visibility).strip().lower() if visibility else ""
            tag_str = str(tag).strip().lower() if tag else ""
            
            is_system_app = vis_str in ["system", "hide", "hidden"] or tag_str in ["system", "hide", "hidden"]
            
            if is_system_app:
                log_debug(f"Tag/Visibility 'system' detectada para {os.path.basename(apk_path)}.")
                if pkg_name:
                    hide_app(pkg_name)
                else:
                    log_debug("Aviso: Nome do pacote não foi identificado via aapt. Tentando ocultação alternativa.")

            return True
        else:
            log_debug(f"FALHA na instalação do APK {os.path.basename(apk_path)}. Erro: {result.stdout} | {result.stderr}")
            return False
    except Exception as e:
        log_debug(f"ERRO EXCEPTION NO PM INSTALL: {e}")
        return False

def run_data_injection(tar_file):
    apps_data_script = os.path.join(HAPIE_APPS_DIR, "apps_data.py")
    if not os.path.exists(apps_data_script):
        log_debug("Script apps_data.py não encontrado. Cancelando injeção.")
        return False
    try:
        log_debug(f"Iniciando injeção de dados ({os.path.basename(tar_file)})...")
        subprocess.run([sys.executable, apps_data_script, "--file", tar_file], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log_debug("Injeção de dados concluída com sucesso.")
        return True
    except Exception as e:
        log_debug(f"FALHA NA INJEÇÃO DE DADOS: {e}")
        return False

def recursive_extract(target_dir, senha_padrao):
    log_debug("Preparando extratores...")
    os.system("pkg install p7zip 7zip unzip -y -q > /dev/null 2>&1")

    bin_7z = None
    for cmd in ["7zz", "7z", "7za"]:
        if shutil.which(cmd):
            bin_7z = cmd
            break

    while True:
        zip_found = False
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.lower().endswith(".zip"):
                    zip_path = os.path.join(root, file)

                    if bin_7z:
                        log_debug(f"Achou ZIP para extrair: {file} (Usando {bin_7z})")
                        cmd_principal = f'{bin_7z} x "{zip_path}" -o"{root}" -y'
                        if senha_padrao:
                            cmd_principal = f'{bin_7z} x "{zip_path}" -o"{root}" -p"{senha_padrao}" -y'
                        cmd_fallback = f'{bin_7z} x "{zip_path}" -o"{root}" -p"123" -y'
                    else:
                        log_debug(f"Achou ZIP para extrair: {file} (Usando UNZIP Nativo - 7z não achado!)")
                        cmd_principal = f'unzip -o -q "{zip_path}" -d "{root}"'
                        if senha_padrao:
                            cmd_principal = f'unzip -o -q -P "{senha_padrao}" "{zip_path}" -d "{root}"'
                        cmd_fallback = f'unzip -o -q -P "123" "{zip_path}" -d "{root}"'

                    try:
                        log_debug(f"Tentativa 1...")
                        result = subprocess.run(cmd_principal, shell=True, capture_output=True, text=True, stdin=subprocess.DEVNULL)

                        if result.returncode != 0:
                            log_debug(f"Tentativa 1 falhou. Motivo: {result.stderr.strip()[:100]}... Chutando senha '123'.")
                            result_fallback = subprocess.run(cmd_fallback, shell=True, capture_output=True, text=True, stdin=subprocess.DEVNULL)

                            if result_fallback.returncode != 0:
                                log_debug(f"ERRO FATAL NA EXTRAÇÃO DE {file}: {result_fallback.stderr.strip()}")
                            else:
                                log_debug(f"Sucesso! A senha '123' abriu o {file}.")
                        else:
                            log_debug(f"Extração do {file} finalizada sem problemas.")
                    except Exception as e:
                        log_debug(f"ERRO DE SISTEMA AO CHAMAR EXTRAÇÃO: {e}")

                    try: os.remove(zip_path)
                    except: pass

                    zip_found = True
                    break
            if zip_found: break
        if not zip_found: break

def main():
    os.system("clear" if os.name == "posix" else "cls")
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=PAYLOAD_FILE)
    args = parser.parse_args()

    if not os.path.exists(args.file): return

    try:
        with open(args.file, "r") as f: payload = json.load(f)
    except: return

    install_orders = payload.get("install", [])
    if not install_orders: return
    
    # Desativa a verificação (Play Protect) para prevenir falhas de verificação
    disable_play_protect()

    report = {"install_success": [], "install_failed": []}

    for app_data in install_orders:
        if len(app_data) < 4: continue
        link, visibility, tag, extras = app_data

        print(f"\n{C_CYAN}----------------------------------------{C_RESET}")
        downloaded_file = download_file(link, DATA_DIR, extras)
        if not downloaded_file:
            print(f"{C_RED}❌ Falha no download.{C_RESET}")
            report["install_failed"].append(link)
            continue

        process_100_percent_success = False
        apps_installed_count = 0

        if downloaded_file.endswith(".zip"):
            print(f"{C_YELLOW}📦 Instalando grupo...{C_RESET}")
            log_debug(f"--- INICIANDO PROCESSAMENTO DE GRUPO ZIP ---")

            if os.path.exists(TEMP_EXTRACT_DIR): shutil.rmtree(TEMP_EXTRACT_DIR)
            os.makedirs(TEMP_EXTRACT_DIR, exist_ok=True)
            senha = extras.get("password") if isinstance(extras, dict) else None

            main_zip_temp = os.path.join(TEMP_EXTRACT_DIR, "main_payload.zip")
            shutil.copy2(downloaded_file, main_zip_temp)

            recursive_extract(TEMP_EXTRACT_DIR, senha)
            apk_files = []
            tar_file = None
            for root_dir, _, files in os.walk(TEMP_EXTRACT_DIR):
                for f in files:
                    if f.endswith(".apk"): apk_files.append(os.path.join(root_dir, f))
                    elif f.endswith(".tar.gz") and tar_file is None: tar_file = os.path.join(root_dir, f)

            log_debug(f"Total de APKs encontrados no pacote: {len(apk_files)}")
            apk_success = False
            if apk_files:
                apk_success = True
                for apk_path in apk_files:
                    if install_apk(apk_path, visibility, tag):
                        apps_installed_count += 1
                    else:
                        apk_success = False

            if apk_success:
                if tar_file:
                    if run_data_injection(tar_file): process_100_percent_success = True
                else:
                    process_100_percent_success = True

            shutil.rmtree(TEMP_EXTRACT_DIR, ignore_errors=True)

        elif downloaded_file.endswith(".apk"):
            nome_apk = os.path.basename(downloaded_file).replace(".apk", "")
            print(f"{C_YELLOW}📦 Instalando {nome_apk}...{C_RESET}")
            log_debug(f"--- INICIANDO PROCESSAMENTO DE APK ÚNICO: {nome_apk} ---")
            if install_apk(downloaded_file, visibility, tag):
                apps_installed_count += 1
                process_100_percent_success = True

        if process_100_percent_success:
            report["install_success"].append(link)
            activate_global_tag(tag)
            print(f"{C_GREEN}✅ Sucesso! {apps_installed_count} app(s) instalado(s).{C_RESET}")
            log_debug(f"STATUS FINAL: SUCESSO TOTAL.")
        else:
            print(f"{C_RED}❌ Falha na instalação.{C_RESET}")
            report["install_failed"].append(link)
            log_debug(f"STATUS FINAL: FALHA.")

        if os.path.exists(downloaded_file): os.remove(downloaded_file)

    try:
        with open(REPORT_FILE, "w") as f: json.dump(report, f)
    except: pass
    if os.path.exists(args.file): os.remove(args.file)

if __name__ == "__main__":
    main()
