import os
import sys
import json
import subprocess

def run_su(cmd):
    """Executa comandos com privilégio Root (su) e ignora a saída no terminal para ser silencioso"""
    return subprocess.run(f"su -c '{cmd}'", shell=True, capture_output=True, text=True)

def install_apk(url, vision):
    tmp_path = "/sdcard/Download/temp_install.apk"
    print("📥 Downloading APK...")
    
    # Faz o download inteligente (Google Drive via gdown ou link direto via curl)
    if "drive.google.com" in url:
        os.system(f"gdown '{url}' -O {tmp_path} --fuzzy -q")
    else:
        os.system(f"curl -sL '{url}' -o {tmp_path}")

    if os.path.exists(tmp_path):
        print("⚙️ Installing package...")
        # Instala silenciosamente via Root
        run_su(f"pm install -r {tmp_path}")
        
        # Extrai o nome do pacote (package name) diretamente do APK baixado usando aapt
        # Isso garante que a injeção de dados vá para o lugar exato
        cmd_get_pkg = f"aapt dump badging {tmp_path} | grep package | awk '{{print $2}}' | sed s/name=//g | sed s/\\'//g"
        pkg_name = subprocess.getoutput(cmd_get_pkg).strip()
        
        if pkg_name:
            # Lógica de Visibilidade
            if vision == "oculto":
                run_su(f"pm hide {pkg_name}")
            else:
                run_su(f"pm unhide {pkg_name}")
                
        # Limpa o lixo
        os.remove(tmp_path)
        return pkg_name
        
    return None

def inject_data(data_url, package_name):
    """Injeta o backup .tar.gz na pasta do app (Data Beta)"""
    if not data_url or not package_name:
        return
    
    tmp_data = "/sdcard/Download/data_inject.tar.gz"
    target_path = f"/data/data/{package_name}"
    
    print(f"📁 Injecting data into {package_name}...")
    
    if "drive.google.com" in data_url:
        os.system(f"gdown '{data_url}' -O {tmp_data} --fuzzy -q")
    else:
        os.system(f"curl -sL '{data_url}' -o {tmp_data}")

    if os.path.exists(tmp_data):
        # 1. Força a parada do app para não corromper nada
        run_su(f"am force-stop {package_name}")
        
        # 2. Extrai o arquivo .tar.gz diretamente no diretório de dados do app
        run_su(f"tar -xzf {tmp_data} -C {target_path}")
        
        # 3. Restaura as permissões do dono (crucial para o app não crashar ao abrir)
        run_su(f"chown -R $(stat -c %u {target_path}):$(stat -c %g {target_path}) {target_path}")
        
        # 4. Limpa o arquivo zipado
        os.remove(tmp_data)
        print("✅ Data injected successfully.")

def remove_app(package_name):
    print(f"🗑️ Removing app: {package_name}")
    run_su(f"pm uninstall {package_name}")

if __name__ == "__main__":
    # Proteção: O script precisa receber o JSON como argumento na linha de comando
    if len(sys.argv) < 2:
        sys.exit(1)

    try:
        # Decodifica o JSON enviado pelo client.py
        data = json.loads(sys.argv[1])
        
        # ---------------------------------------------------------
        # 1. PROCESSAR INSTALAÇÕES E DADOS (.TAR.GZ)
        # ---------------------------------------------------------
        if "instalar" in data:
            for item in data["instalar"]:
                # Padrão recebido do servidor: [link_apk, vision, false, {json_extra}]
                url_apk = item[0]
                vision = item[1]
                extra = item[3]
                
                # Instala o APK e recebe de volta o nome exato do pacote
                pkg = install_apk(url_apk, vision)
                
                # Se instalou certinho e o servidor enviou um link de dados, injeta!
                if pkg and extra.get("data_link"):
                    inject_data(extra["data_link"], pkg)

        # ---------------------------------------------------------
        # 2. PROCESSAR REMOÇÕES E OUTROS COMANDOS ROOT
        # ---------------------------------------------------------
        if "comandos" in data:
            for cmd in data["comandos"]:
                if cmd.startswith("remove "):
                    target_pkg = cmd.replace("remove ", "").strip()
                    remove_app(target_pkg)
                else:
                    # Executa qualquer outro comando genérico que você enviar no futuro
                    run_su(cmd)

    except Exception as e:
        print(f"❌ Error during execution: {e}")
