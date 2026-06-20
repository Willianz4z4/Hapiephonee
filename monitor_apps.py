import os
import sys
import subprocess
import time
import re

print("🚀 Carregando super caçador de logos...")

try:
    import requests
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
except ImportError:
    print("⚠️ Instalando rich e requests... aguarde.")
    os.system("pip install rich requests -q > /dev/null 2>&1")
    import requests
    from rich.console import Console
    from rich.panel import Panel
    console = Console()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(BASE_DIR, "icons")
os.makedirs(ICONS_DIR, exist_ok=True)

def upload_to_catbox(file_path):
    url = "https://catbox.moe/user/api.php"
    data = {"reqtype": "fileupload"}
    try:
        with open(file_path, "rb") as f:
            files = {"fileToUpload": f}
            response = requests.post(url, data=data, files=files, timeout=15)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    return None

def get_user_apps():
    try:
        out = subprocess.check_output("su -c 'pm list packages -3'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8')
        return set([line.replace("package:", "").strip() for line in out.split("\n") if line.strip()])
    except:
        return set()

def find_best_icon_in_apk(apk_path):
    """Varre a estrutura interna do APK atrás de qualquer imagem real de ícone/logo"""
    try:
        # Lista todos os arquivos dentro do APK sem descompactar
        cmd = f"su -c 'unzip -l \"{apk_path}\"'"
        files_list = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
        
        # Filtra apenas linhas que terminam com extensões de imagem válidas
        img_files = re.findall(r"\s+([^\s]+\.(?:png|webp|jpg|jpeg))\b", files_list)
        
        if not img_files:
            return None
            
        # 1ª Prioridade: Arquivos que têm 'logo' ou 'icon' no nome e estão em pastas de alta resolução (xxhdpi, xxxhdpi)
        for f in img_files:
            if ("icon" in f.lower() or "logo" in f.lower()) and ("xhdpi" in f or "hdpi" in f):
                return f
                
        # 2ª Prioridade: Qualquer arquivo com 'icon' ou 'logo' no nome
        for f in img_files:
            if "icon" in f.lower() or "logo" in f.lower():
                return f
                
        # 3ª Prioridade: Qualquer PNG dentro da pasta res/drawable
        for f in img_files:
            if "res/" in f and f.endswith(".png"):
                return f
                
        # Fallback: A primeira imagem que encontrar
        return img_files[0]
    except:
        return None

def get_app_info(pkg_name):
    info = {"name": "Desconhecido", "version": "Desconhecida", "icon_saved": False, "icon_url": None}
    try:
        apk_path_cmd = f"su -c 'pm path {pkg_name}'"
        apk_path_raw = subprocess.check_output(apk_path_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        
        if not apk_path_raw:
            return info
            
        lines = [line.replace("package:", "").strip() for line in apk_path_raw.split("\n") if line.strip()]
        if not lines:
            return info
        apk_path = lines[0]
        
        # Coleta Nome e Versão básicos
        badging_cmd = f"su -c 'aapt dump badging \"{apk_path}\"'"
        badging_output = subprocess.check_output(badging_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
        
        version_match = re.search(r"versionName='([^']+)'", badging_output)
        if version_match:
            info["version"] = version_match.group(1)
            
        name_match = re.search(r"application-label:'([^']+)'", badging_output)
        if name_match:
            info["name"] = name_match.group(1)
        else:
            name_fallback = re.search(r"application: label='([^']+)'", badging_output)
            if name_fallback:
                info["name"] = name_fallback.group(1)
        
        # 🚀 BUSCA PROFUNDA DA LOGO: Vasculha o arquivo do APK de cima a baixo
        icon_internal_path = find_best_icon_in_apk(apk_path)
            
        if icon_internal_path:
            icon_ext = icon_internal_path.split('.')[-1]
            icon_dest = os.path.join(ICONS_DIR, f"{pkg_name}.{icon_ext}")
            
            unzip_cmd = f"su -c 'unzip -p \"{apk_path}\" \"{icon_internal_path}\"' > \"{icon_dest}\""
            os.system(unzip_cmd)
            
            if os.path.exists(icon_dest) and os.path.getsize(icon_dest) > 0:
                info["icon_saved"] = icon_dest
                info["icon_url"] = upload_to_catbox(icon_dest)

    except Exception:
        pass
        
    return info

def print_app_panel(app_package, info, is_startup=False):
    status_title = "🔍 App Detectado" if is_startup else "📥 Novo App Instalado!"
    border_color = "cyan" if is_startup else "green"
    
    detalhes = f"[bold]{status_title}[/bold]\n\n"
    detalhes += f"📦 [bold]Pacote:[/bold] [yellow]{app_package}[/yellow]\n"
    detalhes += f"🏷️ [bold]Nome:[/bold] {info['name']}\n"
    detalhes += f"🔢 [bold]Versão:[/bold] {info['version']}\n"
    
    if info["icon_url"]:
        detalhes += f"🔗 [bold]Link da Logo:[/bold] [underline cyan]{info['icon_url']}[/underline cyan]"
    elif info["icon_saved"]:
        detalhes += f"🖼️ [bold]Logo Local:[/bold] Salvo em icons/{os.path.basename(info['icon_saved'])}\n"
        detalhes += f"[dim red](Falha ao enviar link)[/dim red]"
    else:
        detalhes += f"🖼️ [bold]Logo:[/bold] [red]Nenhuma imagem extraível encontrada no APK[/red]"
        
    console.print(Panel(detalhes, border_style=border_color))

def start_monitor():
    console.print(Panel.fit("[bold cyan]Hapiephone Monitor Ultra[/bold cyan]\n[dim]Varredura Profunda e Extrator de Logos Reais[/dim]", border_style="cyan"))
    
    console.print("[yellow]🔍 Fazendo varredura minuciosa dos APKs...[/yellow]")
    current_apps = get_user_apps()
    
    console.print(f"[bold green]📦 {len(current_apps)} apps encontrados. Buscando logos internas...[/bold green]\n")
    for app in sorted(current_apps):
        info = get_app_info(app)
        print_app_panel(app, info, is_startup=True)
        time.sleep(0.3)
        
    print("\n🌟 Varredura concluída! Monitor ativo... (CTRL+C para sair)\n")

    while True:
        try:
            time.sleep(2)
            new_apps = get_user_apps()
            if new_apps != current_apps:
                added = new_apps - current_apps
                removed = current_apps - new_apps
                
                if added:
                    for app in added:
                        info = get_app_info(app)
                        print_app_panel(app, info, is_startup=False)
                if removed:
                    print(f"🗑️ Desinstalado: {app}")
                current_apps = new_apps
        except KeyboardInterrupt:
            break
        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    start_monitor()
