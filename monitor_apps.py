import os
import sys
import subprocess
import time
import re

print("🚀 Carregando Motor Híbrido: Cirúrgico + Farejador...")

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

def upload_to_cloud(file_path):
    try:
        url = "https://uguu.se/upload.php"
        with open(file_path, "rb") as f:
            resp = requests.post(url, files={"files[]": ("icon.png", f, "image/png")}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success") and "files" in data:
                return data["files"][0]["url"]
    except:
        pass

    try:
        url = "https://telegra.ph/upload"
        with open(file_path, "rb") as f:
            resp = requests.post(url, files={"file": ("icon.png", f, "image/png")}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and "src" in data[0]:
                return "https://telegra.ph" + data[0]["src"]
    except:
        pass
        
    return None

def get_user_apps():
    try:
        out = subprocess.check_output("su -c 'pm list packages -3'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8')
        return set([line.replace("package:", "").strip() for line in out.split("\n") if line.strip()])
    except:
        return set()

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
        
        badging_cmd = f"aapt dump badging \"{apk_path}\""
        badging_output = subprocess.check_output(badging_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
        
        version_match = re.search(r"versionName='([^']+)'", badging_output)
        if version_match:
            info["version"] = version_match.group(1)
            
        name_match = re.search(r"application-label:'([^']+)'", badging_output)
        if name_match:
            info["name"] = name_match.group(1)
        
        icon_match = re.search(r"application: label=.*? icon='([^']+)'", badging_output)
        if not icon_match:
            icon_match = re.search(r"icon='([^']+)'", badging_output)
            
        unzip_list_cmd = f"unzip -l \"{apk_path}\""
        files_list = subprocess.check_output(unzip_list_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
        
        icon_internal_path = None
        
        # TENTATIVA 1: Método Cirúrgico (Nome exato do manifesto)
        if icon_match:
            full_icon_path = icon_match.group(1)
            icon_name_base = os.path.splitext(os.path.basename(full_icon_path))[0]
            
            potential_icons = re.findall(r"\s+([^\s]*" + re.escape(icon_name_base) + r"\.(?:png|webp))\b", files_list)
            potential_icons.sort(key=lambda x: ("xxxhdpi" in x, "xxhdpi" in x, "xhdpi" in x), reverse=True)
            
            if potential_icons:
                icon_internal_path = potential_icons[0]
                
        # TENTATIVA 2: Falhou o cirúrgico? Solta o Cão Farejador Genérico!
        if not icon_internal_path:
            all_imgs = re.findall(r"\s+([^\s]+\.(?:png|webp|jpg|jpeg))\b", files_list)
            fallback_icons = [f for f in all_imgs if "icon" in f.lower() or "logo" in f.lower() or "launcher" in f.lower()]
            fallback_icons.sort(key=lambda x: ("xxxhdpi" in x, "xxhdpi" in x, "xhdpi" in x, "mipmap" in x), reverse=True)
            
            if fallback_icons:
                icon_internal_path = fallback_icons[0]
            elif all_imgs:
                icon_internal_path = all_imgs[0] # Pega qualquer imagem como último recurso
                
        if icon_internal_path:
            icon_ext = icon_internal_path.split('.')[-1]
            icon_dest = os.path.join(ICONS_DIR, f"{pkg_name}.{icon_ext}")
            
            unzip_p_cmd = f"unzip -p \"{apk_path}\" \"{icon_internal_path}\" > \"{icon_dest}\""
            os.system(unzip_p_cmd)
            
            if os.path.exists(icon_dest) and os.path.getsize(icon_dest) > 0:
                info["icon_saved"] = icon_dest
                info["icon_url"] = upload_to_cloud(icon_dest)

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
        detalhes += f"🔗 [bold]Link da Capa:[/bold] [underline cyan]{info['icon_url']}[/underline cyan]"
    elif info["icon_saved"]:
        detalhes += f"🖼️ [bold]Capa Local:[/bold] icons/{os.path.basename(info['icon_saved'])}\n"
        detalhes += f"[dim red]❌ (Falha de rede ao enviar link)[/dim red]"
    else:
        detalhes += f"🖼️ [bold]Capa:[/bold] [red]Nenhuma imagem suportada encontrada[/red]"
        
    console.print(Panel(detalhes, border_style=border_color))

def start_monitor():
    os.system("clear" if os.name == "posix" else "cls")
    console.print(Panel.fit("[bold cyan]Hapiephone Monitor Híbrido[/bold cyan]\n[dim]Busca Cirúrgica + Motor Farejador Anti-Falha[/dim]", border_style="cyan"))
    
    console.print("[yellow]🔍 Fazendo varredura dos APKs...[/yellow]")
    current_apps = get_user_apps()
    
    console.print(f"[bold green]📦 {len(current_apps)} apps encontrados. Buscando capas...[/bold green]\n")
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
                    for app in removed:
                        console.print(Panel(f"[bold red]🗑️ Aplicativo Desinstalado:[/bold red]\n📦 [yellow]{app}[/yellow]", border_style="red"))
                current_apps = new_apps
        except KeyboardInterrupt:
            break
        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    start_monitor()
