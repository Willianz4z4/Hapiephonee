import os
import sys
import json
import subprocess

def run_su(cmd):
    """Executa comandos com privilégio Root (su)"""
    return subprocess.run(f"su -c '{cmd}'", shell=True, capture_output=True, text=True)

def install_apk(url, vision):
    tmp_path = "/sdcard/Download/temp_install.apk"
    print(f"📥 Downloading APK...")
    
    # Download usando gdown (Drive) ou curl (Direto)
    if "drive.google.com" in url:
        os.system(f"gdown '{url}' -O {tmp_path} --fuzzy -q")
    else:
        os.system(f"curl -sL '{url}' -o {tmp_path}")

    if os.path.exists(tmp_path):
        print(f"⚙️ Installing package...")
        run_su(f"pm install -r {tmp_path}")
        
        # Lógica de Visibilidade
        pkg_name = subprocess.getoutput(f"aapt dump badging {tmp_path} | grep package | awk '{{print $2}}' | sed s/name=//g | sed s/\\'//g")
        if vision == "oculto":
            run_su(f"pm hide {pkg_name}")
        else:
            run_su(f"pm unhide {pkg_name}")
            
        os.remove(tmp_path)
        return pkg_name
    return None

def inject_data(data_url, package_name):
    """Injeta o backup .tar.gz na pasta do app (Data Beta)"""
    if not data_url or not package_name: return
    
    tmp_data = f"/sdcard/Download/data_inject.tar.gz"
    target_path = f"/data/data/{package_name}"
    
    print(f"📁 Injecting data into {package_name}...")
    
    if "drive.google.com" in data_url:
        os.system(f"gdown '{data_url}' -O {tmp_data} --fuzzy -q")
    else:
        os.system(f"curl -sL '{data_url}' -o {tmp_data}")

    if os.path.exists(tmp_data):
        # 1. Para o app, 2. Limpa o lixo, 3. Extrai o backup, 4. Corrige permissão
        run_su(f"am force-stop {package_name}")
        run_su(f"tar -xzf {tmp_data} -C {target_path}")
        run_su(f"chown -R $(stat -c %u {target_path}):$(stat -c %g {target_path}) {target_path}")
        os.remove(tmp_data)
        print(f"✅ Data injected successfully.")

def remove_app(package_name):
    print(f"🗑️ Removing app: {package_name}")
    run_su(f"pm uninstall {package_name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    try:
        # O Client passa o JSON da resposta do Vercel como argumento
        data = json.loads(sys.argv[1])
        
        # 1. Processar Instalações (Com ou Sem Data)
        if "instalar" in data:
            for item in data["instalar"]:
                # Padrão: [link_apk, vision, false, {json_extra}]
                url_apk = item[0]
                vision = item[1]
                extra = item[3]
                
                pkg = install_apk(url_apk, vision)
                
                # Se a instalação deu certo e veio link de data no JSON
                if pkg and extra.get("data_link"):
                    inject_data(extra["data_link"], pkg)

        # 2. Processar Comandos (como o 'remove package.name')
        if "comandos" in data:
            for cmd in data["comandos"]:
                if cmd.startswith("remove "):
                    target_pkg = cmd.replace("remove ", "").strip()
                    remove_app(target_pkg)
                else:
                    run_su(cmd)

    except Exception as e:
        print(f"❌ Error during execution: {e}")
