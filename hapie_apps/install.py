import os
import sys
import json
import subprocess
import re
import zipfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Tenta importar o gdown. Se não existir, tenta instalar automaticamente
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

# ==========================================
# 📍 ROTAS ATUALIZADAS E ORGANIZADAS
# ==========================================
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

def download_worker(item, index):
    """Trabalhador focado em baixar arquivos em paralelo e tratar ZIPs automaticamente com a senha 123"""
    apk_url, visibility, _, extra = item[0], item[1], item[2], item[3]
    
    # Arquivo temporário inicial de download
    download_path = os.path.join(BASE_DIR, f"temp_download_{index}")
    final_apk_path = os.path.join(BASE_DIR, f"temp_install_{index}.apk")
    tmp_data = os.path.join(BASE_DIR, f"data_inject_{index}.tar.gz")

    if os.path.exists(download_path): os.remove(download_path)
    if os.path.exists(final_apk_path): os.remove(final_apk_path)
    if os.path.exists(tmp_data): os.remove(tmp_data)

    log(f"📥 [Download Iniciado] ID #{index} - {apk_url[:60]}...", "yellow")

    if "play.google.com" in apk_url:
        log(f"❌ ID #{index} - A URL fornecida é uma página da loja.", "bold red")
        return {"index": index, "success": False, "item": item}

    # Baixando do Google Drive usando GDown ou Curl
    if "drive.google.com" in apk_url:
        file_id = None
        match_d = re.search(r'/d/([a-zA-Z0-9_-]+)', apk_url)
        if match_d: file_id = match_d.group(1)
        else:
            match_id = re.search(r'id=([a-zA-Z0-9_-]+)', apk_url)
            if match_id: file_id = match_id.group(1)

        if file_id:
            if gdown:
                try: gdown.download(f"https://drive.google.com/uc?id={file_id}", download_path, quiet=True)
                except: pass
            
            if not os.path.exists(download_path) or os.path.getsize(download_path) < 1000:
                cookie_path = os.path.join(BASE_DIR, f"gdrive_cookies_{index}.txt")
                os.system(f"curl -sL -c '{cookie_path}' 'https://docs.google.com/uc?export=download&id={file_id}' -o '{download_path}'")
                if os.path.exists(download_path):
                    try:
                        with open(download_path, 'r', errors='ignore') as f:
                            head = f.read(15000)
                        confirm_match = re.search(r'confirm=([A-Za-z0-9_-]+)', head)
                        if confirm_match:
                            token = confirm_match.group(1)
                            os.system(f"curl -sL -b '{cookie_path}' 'https://docs.google.com/uc?export=download&confirm={token}&id={file_id}' -o '{download_path}'")
                    except: pass
                if os.path.exists(cookie_path): os.remove(cookie_path)
        else:
            os.system(f"curl -sL '{apk_url}' -o '{download_path}'")
    else:
        os.system(f"curl -sL '{apk_url}' -o '{download_path}'")

    if not os.path.exists(download_path) or os.path.getsize(download_path) < 1000:
        log(f"❌ Erro no ID #{index}: Download falhou.", "bold red")
        return {"index": index, "success": False, "item": item}

    # ========================================================
    # 🧠 DECRIPTAÇÃO E EXTRAÇÃO AUTOMÁTICA COM A SENHA 123
    # ========================================================
    if zipfile.is_zipfile(download_path):
        log(f"📦 ID #{index} detectado como ZIP. Aplicando a senha '123' automaticamente...", "cyan")
        try:
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                # b'123' vem primeiro para descriptografar de imediato os APKs protegidos
                for senha in [b'123', None]:
                    try:
                        apk_dentro_do_zip = next((f for f in zip_ref.namelist() if f.endswith('.apk')), None)
                        if apk_dentro_do_zip:
                            zip_ref.extract(apk_dentro_do_zip, BASE_DIR, pwd=senha)
                            os.rename(os.path.join(BASE_DIR, apk_dentro_do_zip), final_apk_path)
                            break
                    except:
                        continue
        except Exception as e:
            log(f"❌ Falha ao extrair ZIP do ID #{index}: {e}", "bold red")

        if os.path.exists(download_path): os.remove(download_path)
    else:
        # Se for um APK antigo direto sem estar em ZIP, apenas move para o instalador
        os.rename(download_path, final_apk_path)

    # Validação Final do APK extraído
    if not os.path.exists(final_apk_path) or os.path.getsize(final_apk_path) < 500000:
        log(f"❌ Erro no ID #{index}: Arquivo APK inválido ou falha na senha do ZIP.", "bold red")
        if os.path.exists(final_apk_path): os.remove(final_apk_path)
        return {"index": index, "success": False, "item": item}

    # Download de Dados Extras se houver
    data_url = extra.get("data_link") if extra else None
    has_data = False
    if data_url:
        log(f"📁 [Dados Extras] Baixando arquivos de injeção para ID #{index}...", "magenta")
        if "drive.google.com" in data_url:
            file_id = None
            match_d = re.search(r'/d/([a-zA-Z0-9_-]+)', data_url)
            if match_d: file_id = match_d.group(1)
            else:
                match_id = re.search(r'id=([a-zA-Z0-9_-]+)', data_url)
                if match_id: file_id = match_id.group(1)

            if file_id:
                if gdown:
                    try: gdown.download(f"https://drive.google.com/uc?id={file_id}", tmp_data, quiet=True)
                    except: pass
                if not os.path.exists(tmp_data) or os.path.getsize(tmp_data) < 10000:
                    cookie_path = os.path.join(BASE_DIR, f"gdrive_cookies_data_{index}.txt")
                    os.system(f"curl -sL -c '{cookie_path}' 'https://docs.google.com/uc?export=download&id={file_id}' -o '{tmp_data}'")
                    if os.path.exists(tmp_data):
                        try:
                            with open(tmp_data, 'r', errors='ignore') as f:
                                head = f.read(15000)
                            confirm_match = re.search(r'confirm=([A-Za-z0-9_-]+)', head)
                            if confirm_match:
                                token = confirm_match.group(1)
                                os.system(f"curl -sL -b '{cookie_path}' 'https://docs.google.com/uc?export=download&confirm={token}&id={file_id}' -o '{tmp_data}'")
                        except: pass
                    if os.path.exists(cookie_path): os.remove(cookie_path)
        else:
            os.system(f"curl -sL '{data_url}' -o '{tmp_data}'")

        if os.path.exists(tmp_data) and os.path.getsize(tmp_data) >= 10000:
            has_data = True

    log(f"✨ [Processado] ID #{index} pronto para instalação.", "green")
    return {
        "index": index,
        "success": True,
        "item": item,
        "tmp_path": final_apk_path,
        "tmp_data": tmp_data if has_data else None
    }

def remove_app(package_name):
    run_su(f"pm uninstall {package_name}")
    log(f"🗑️ {package_name} - Removido com sucesso", "bold red")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
        success_list = []
        failed_list = []

        if "remove" in data:
            for pkg in data["remove"]:
                print("\n")
                console.print(Panel(f"Processando remoção...\n[dim]{pkg}[/dim]", style="red", title="🗑️ DESINSTALAÇÃO ACIONADA"))
                remove_app(pkg)

        lista_instalar = data.get("install", []) + data.get("instalar", [])
        if lista_instalar:
            console.print(Panel(f"Iniciando download e descompactação de {len(lista_instalar)} aplicativos...", style="bold cyan", title="🚀 ENGINE MULTI-THREAD + AUTO ZIP KEY"))
            
            download_results = []
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(download_worker, item, idx) for idx, item in enumerate(lista_instalar)]
                for future in futures:
                    try: download_results.append(future.result())
                    except Exception as e: log(f"❌ Erro na thread de download: {e}", "bold red")

            print("\n")
            console.print(Panel("Instalando pacotes extraídos em lote...", style="bold yellow", title="⚙️ INSTALAÇÃO EM MASSA"))
            
            run_su("pm disable-user --user 0 com.android.vending > /dev/null 2>&1")
            run_su("settings put global package_verifier_enable 0")

            for res in download_results:
                if not res or not res.get("success"): continue

                item = res["item"]
                tmp_path = res["tmp_path"]
                tmp_data = res["tmp_data"]
                visibility = item[1]

                cmd_get_pkg = f"aapt dump badging {tmp_path} 2>/dev/null | grep package | awk '{{print $2}}' | sed s/name=//g | sed s/\\'//g"
                pkg_name = subprocess.getoutput(cmd_get_pkg).strip()

                if not pkg_name or "not found" in pkg_name or "W/zipro" in pkg_name:
                    log(f"❌ ERRO: Pacote corrompido pós-extração no ID #{res['index']}.", "bold red")
                    if os.path.exists(tmp_path): os.remove(tmp_path)
                    if tmp_data and os.path.exists(tmp_data): os.remove(tmp_data)
                    continue

                app_name = get_app_name(tmp_path, pkg_name)
                log(f"📦 Instalando: {app_name} ({pkg_name})...", "yellow")

                install_result = run_su(f"pm install -r -g -d {tmp_path}")

                if "Success" in install_result.stdout:
                    success_list.append(pkg_name)
                    if visibility == "oculto":
                        run_su(f"pm hide {pkg_name}")
                        log(f"✅ {app_name} ({pkg_name}) - Instalado & Oculto", "bold green")
                    else:
                        run_su(f"pm unhide {pkg_name}")
                        log(f"✅ {app_name} ({pkg_name}) - Instalado com Sucesso", "bold green")

                    if tmp_data and os.path.exists(tmp_data):
                        target_path = f"/data/data/{pkg_name}"
                        run_su(f"am force-stop {pkg_name}")
                        extraction = run_su(f"tar -xzf {tmp_data} -C {target_path}")
                        if extraction.returncode == 0:
                            run_su(f"chown -R $(stat -c %u {target_path}):$(stat -c %g {target_path}) {target_path}")
                            log(f"✅ Dados injetados com perfeição em {target_path}", "bold green")
                        else:
                            log(f"❌ Erro ao extrair dados extras: {extraction.stderr}", "bold red")
                else:
                    log(f"❌ Falha ao instalar {app_name}: {install_result.stderr}", "bold red")
                    failed_list.append(pkg_name)

                if os.path.exists(tmp_path): os.remove(tmp_path)
                if tmp_data and os.path.exists(tmp_data): os.remove(tmp_data)

            run_su("settings put global package_verifier_enable 1")
            run_su("pm enable com.android.vending > /dev/null 2>&1")

        if "comandos" in data:
            for cmd in data["commands"]:
                if cmd.startswith("remove "): remove_app(cmd.replace("remove ", "").strip())
                else: run_su(cmd)

        if success_list or failed_list:
            with open(REPORT_FILE, "w", encoding="utf-8") as f:
                json.dump({"install_success": success_list, "install_failed": failed_list}, f)

    except Exception as e:
        log(f"❌ Erro fatal no script de instalacao: {e}", "bold red")
