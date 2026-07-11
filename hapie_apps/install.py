import os
import sys
import json
import subprocess
import re
import zipfile
import shutil
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Importação blindada do seu gerenciador especialista de data
try:
    from apps_data import data_inject
except ImportError:
    data_inject = None

try:
    import gdown
except ImportError:
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "gdown"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import gdown
    except:
        gdown = None

try:
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
except ImportError:
    class DummyConsole:
        def print(self, msg, *args, **kwargs): print(msg)
    console = DummyConsole()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(REPO_ROOT, "Data")
os.makedirs(DATA_DIR, exist_ok=True)

LOG_FILE = os.path.join(DATA_DIR, "install_log.txt")
REPORT_FILE = os.path.join(DATA_DIR, "install_report.json")

def log(msg, color="cyan", write_file=True):
    console.print(f"[{color}]{msg}[/{color}]")
    if write_file:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {msg}\n")
        except:
            pass

def run_su(cmd):
    return subprocess.run(f"su -c '{cmd}'", shell=True, capture_output=True, text=True)

def get_app_name(tmp_path, default_pkg):
    cmd = f"aapt dump badging {tmp_path} 2>/dev/null | grep 'application-label:' | head -n 1 | cut -d\' -f2"
    app_name = subprocess.getoutput(cmd).strip()
    return app_name if app_name else default_pkg

def download_file(url, out_path, index_identifier):
    if not url: return False
    if "play.google.com" in url: return False
    
    if "drive.google.com" in url:
        file_id = None
        match_d = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
        if match_d: file_id = match_d.group(1)
        else:
            match_id = re.search(r'id=([a-zA-Z0-9_-]+)', url)
            if match_id: file_id = match_id.group(1)

        if file_id:
            if gdown:
                try: gdown.download(f"https://drive.google.com/uc?id={file_id}", out_path, quiet=True)
                except: pass
            
            if not os.path.exists(out_path) or os.path.getsize(out_path) < 1000:
                cookie_path = os.path.join(BASE_DIR, f"cookies_{index_identifier}.txt")
                os.system(f"curl -sL -c '{cookie_path}' 'https://docs.google.com/uc?export=download&id={file_id}' -o '{out_path}'")
                if os.path.exists(out_path):
                    try:
                        with open(out_path, 'r', errors='ignore') as f:
                            head = f.read(15000)
                        confirm_match = re.search(r'confirm=([A-Za-z0-9_-]+)', head)
                        if confirm_match:
                            token = confirm_match.group(1)
                            os.system(f"curl -sL -b '{cookie_path}' 'https://docs.google.com/uc?export=download&confirm={token}&id={file_id}' -o '{out_path}'")
                    except: pass
                if os.path.exists(cookie_path): os.remove(cookie_path)
    else:
        os.system(f"curl -sL '{url}' -o '{out_path}'")
        
    return os.path.exists(out_path) and os.path.getsize(out_path) >= 1000

def download_worker(item, index):
    apk_url, visibility = item[0], item[1]

    extract_dir = os.path.join(BASE_DIR, f"temp_extract_{index}")
    if os.path.exists(extract_dir): shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)
    
    download_path = os.path.join(extract_dir, "payload.tmp")
    log(f"📥 [Download APK/ZIP] ID #{index} iniciado...", "yellow")
    
    if not download_file(apk_url, download_path, f"apk_{index}"):
        log(f"❌ Erro no ID #{index}: Falha no download.", "bold red")
        return []

    # Escavação recursiva de Matrioskas (Abre qualquer zip interno)
    if zipfile.is_zipfile(download_path):
        zip_path = download_path + ".zip"
        os.rename(download_path, zip_path)
        log(f"📦 Pacote ID #{index} detectado como ZIP. Executando abertura recursiva total...", "cyan")
        
        while True:
            zips_encontrados = []
            for root, dirs, files in os.walk(extract_dir):
                for f in files:
                    if f.lower().endswith('.zip'):
                        zips_encontrados.append(os.path.join(root, f))
            if not zips_encontrados:
                break
            for zip_alvo in zips_encontrados:
                try:
                    with zipfile.ZipFile(zip_alvo, 'r') as zf:
                        for pwd in [b'123', None]:
                            try:
                                zf.extractall(path=os.path.dirname(zip_alvo), pwd=pwd)
                                break
                            except: continue
                except: pass
                finally:
                    try: os.remove(zip_alvo)
                    except: pass
    else:
        os.rename(download_path, os.path.join(extract_dir, "app_puro.apk"))

    apk_files = []
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            if f.lower().endswith('.apk'):
                apk_files.append(os.path.join(root, f))
                
    resultados = []
    for apk_path in apk_files:
        cmd_get_pkg = f"aapt dump badging {apk_path} 2>/dev/null | grep package | awk '{{print $2}}' | sed s/name=//g | sed s/\\'//g"
        pkg_name = subprocess.getoutput(cmd_get_pkg).strip()
        if not pkg_name or "not found" in pkg_name or "W/zipro" in pkg_name:
            continue
            
        resultados.append({
            "apk_path": apk_path,
            "pkg_name": pkg_name,
            "visibility": visibility
        })
    return resultados

def remove_app(package_name):
    run_su(f"pm uninstall {package_name}")
    log(f"🗑️ {package_name} - Removido com sucesso", "bold red")

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
        success_list = []
        failed_list = []

        if "remove" in data:
            for pkg in data["remove"]:
                remove_app(pkg)

        lista_instalar = data.get("install", []) + data.get("instalar", [])
        
        # Coleta e mapeia globalmente o dicionário de links de data do payload recebido
        mapa_global_datas = {}
        for item in lista_instalar:
            extra = item[3] if len(item) > 3 else {}
            if extra and "data_links" in extra:
                mapa_global_datas.update(extra["data_links"])

        if lista_instalar:
            all_extracted_apps = []
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(download_worker, item, idx) for idx, item in enumerate(lista_instalar)]
                for future in futures:
                    res = future.result()
                    if res: all_extracted_apps.extend(res)

            print("\n")
            console.print(Panel(f"Instalando {len(all_extracted_apps)} APK(s) puros extraídos...", style="bold yellow", title="⚙️ PM INSTALADOR"))

            run_su("pm disable-user --user 0 com.android.vending > /dev/null 2>&1")
            run_su("settings put global package_verifier_enable 0")

            # FASE 1: INSTALA TODOS OS APLICATIVOS DO LOTE PRIMEIRO
            for app_data in all_extracted_apps:
                tmp_path = app_data["apk_path"]
                pkg_name = app_data["pkg_name"]
                visibility = app_data["visibility"]

                app_name = get_app_name(tmp_path, pkg_name)
                log(f"📦 Instalando Aplicativo: {app_name} ({pkg_name})...", "yellow")

                install_result = run_su(f"pm install -r -g -d '{tmp_path}'")

                if "Success" in install_result.stdout:
                    success_list.append(pkg_name)
                    if visibility == "oculto":
                        run_su(f"pm hide {pkg_name}")
                    else:
                        run_su(f"pm unhide {pkg_name}")
                    log(f"✅ {app_name} ({pkg_name}) - Sucesso", "bold green")
                else:
                    log(f"❌ Falha ao instalar {app_name}: {install_result.stderr}", "bold red")
                    failed_list.append(pkg_name)

            run_su("settings put global package_verifier_enable 1")
            run_su("pm enable com.android.vending > /dev/null 2>&1")

            # FASE 2: APÓS INSTALAR TUDO, CHAMA O APPS_DATA.PY APENAS PARA OS QUE TIVERAM SUCESSO COBRINDO SÓ OS QUE EXISTEM!
            if success_list and mapa_global_datas and data_inject:
                print("\n")
                console.print(Panel("Iniciando injeção de dados isolados para os aplicativos instalados...", style="bold magenta", title="⚡ FASE DE CONEXÃO: APPS_DATA"))
                
                for pkg_verificado in set(success_list):
                    link_da_data = mapa_global_datas.get(pkg_verificado)
                    if link_da_data:
                        log(f"🔋 Acionando 'apps_data.py' para injetar backup de: {pkg_verificado}...", "cyan")
                        try:
                            # Chama o seu script especialista passando o pacote real e o link da nuvem
                            data_inject(pkg_verificado, link_da_data)
                        except Exception as e_data:
                            log(f"❌ Erro ao processar apps_data para {pkg_verificado}: {e_data}", "bold red")

            # Limpeza dos diretórios temporários de extração
            for idx in range(len(lista_instalar)):
                shutil.rmtree(os.path.join(BASE_DIR, f"temp_extract_{idx}"), ignore_errors=True)

        if "commands" in data or "comandos" in data:
            cmd_list = data.get("commands", []) + data.get("comandos", [])
            for cmd in cmd_list:
                if cmd.startswith("remove "): remove_app(cmd.replace("remove ", "").strip())
                else: run_su(cmd)

        if success_list or failed_list:
            with open(REPORT_FILE, "w", encoding="utf-8") as f:
                json.dump({"install_success": list(set(success_list)), "install_failed": list(set(failed_list))}, f)

    except Exception as e:
        log(f"❌ Erro fatal no instalador: {e}", "bold red")
