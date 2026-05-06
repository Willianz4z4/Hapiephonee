import os
import sys
import json
import subprocess
from datetime import datetime

# Define o diretório local e seguro do Termux (NÃO exige permissão de armazenamento)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "install_log.txt")

def log(msg):
    """Exibe a mensagem na tela e salva no arquivo de log local"""
    print(msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{data_hora}] {msg}\n")
    except:
        pass

def run_su(cmd):
    """Executa comandos Root e loga se houver algum erro"""
    result = subprocess.run(f"su -c '{cmd}'", shell=True, capture_output=True, text=True)
    if result.returncode != 0 and result.stderr:
        log(f"⚠️ Aviso Root: {result.stderr.strip()}")
    return result

def install_apk(url, vision):
    # Salvando direto na memória interna do Termux (Zero bloqueios)
    tmp_path = os.path.join(BASE_DIR, "temp_install.apk")
    
    log("📥 Iniciando download do APK...")
    
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    
    if "drive.google.com" in url:
        os.system(f"gdown '{url}' -O {tmp_path} --fuzzy -q")
    else:
        os.system(f"curl -sL '{url}' -o {tmp_path}")

    if os.path.exists(tmp_path):
        log("⚙️ Instalando pacote no sistema via Root...")
        run_su(f"pm install -r {tmp_path}")
        
        cmd_get_pkg = f"aapt dump badging {tmp_path} | grep package | awk '{{print $2}}' | sed s/name=//g | sed s/\\'//g"
        pkg_name = subprocess.getoutput(cmd_get_pkg).strip()
        
        if pkg_name:
            log(f"📦 Pacote identificado: {pkg_name}")
            if vision == "oculto":
                run_su(f"pm hide {pkg_name}")
                log(f"👻 Pacote {pkg_name} foi ocultado da launcher.")
            else:
                run_su(f"pm unhide {pkg_name}")
                
        os.remove(tmp_path)
        return pkg_name
    else:
        log("❌ Falha no download. O arquivo APK não foi encontrado.")
        return None

def inject_data(data_url, package_name):
    if not data_url or not package_name:
        return
    
    # Salvando os dados no Termux
    tmp_data = os.path.join(BASE_DIR, "data_inject.tar.gz")
    target_path = f"/data/data/{package_name}"
    
    log(f"📁 Baixando e injetando dados (.tar.gz) para {package_name}...")
    
    if os.path.exists(tmp_data):
        os.remove(tmp_data)
    
    if "drive.google.com" in data_url:
        os.system(f"gdown '{data_url}' -O {tmp_data} --fuzzy -q")
    else:
        os.system(f"curl -sL '{data_url}' -o {tmp_data}")

    if os.path.exists(tmp_data):
        run_su(f"am force-stop {package_name}")
        
        extracao = run_su(f"tar -xzf {tmp_data} -C {target_path}")
        if extracao.returncode == 0:
            run_su(f"chown -R $(stat -c %u {target_path}):$(stat -c %g {target_path}) {target_path}")
            log("✅ Dados injetados e permissões corrigidas com sucesso!")
        else:
            log("❌ Erro ao extrair o arquivo .tar.gz no diretório do app.")
            
        os.remove(tmp_data)
    else:
        log("❌ Falha no download do arquivo de dados.")

def remove_app(package_name):
    log(f"🗑️ Removendo aplicativo: {package_name}")
    run_su(f"pm uninstall {package_name}")
    log(f"✅ {package_name} desinstalado.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        log("❌ Erro crítico: Nenhum dado JSON recebido pelo script.")
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
        log(f"🚀 --- NOVO TRABALHO RECEBIDO ---")
        
        if "instalar" in data:
            for item in data["instalar"]:
                url_apk = item[0]
                vision = item[1]
                extra = item[3]
                
                pkg = install_apk(url_apk, vision)
                
                if pkg and extra.get("data_link"):
                    inject_data(extra["data_link"], pkg)

        if "comandos" in data:
            for cmd in data["comandos"]:
                if cmd.startswith("remove "):
                    target_pkg = cmd.replace("remove ", "").strip()
                    remove_app(target_pkg)
                else:
                    run_su(cmd)
                    log(f"⚙️ Comando root genérico executado: {cmd}")

        log("🏁 Processamento finalizado com sucesso.")

    except Exception as e:
        log(f"❌ Erro fatal durante a execução: {e}")
