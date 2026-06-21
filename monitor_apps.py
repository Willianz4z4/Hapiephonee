import os
import sys
import subprocess
import time
import re

print("🚀 Carregando Super Caçador de Capas Reais...")

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
    """Tenta subir a imagem para o Telegraph ou Uguu.se, que aceitam VPS"""
    # Tentativa 1: Uguu.se (Geralmente mais rápido que Telegraph em VPS)
    try:
        url = "https://uguu.se/upload.php"
        with open(file_path, "rb") as f:
            # Força o nome do arquivo para .png para garantir aceitação
            resp = requests.post(url, files={"files[]": ("icon.png", f, "image/png")}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success") and "files" in data:
                return data["files"][0]["url"]
    except:
        pass

    # Tentativa 2: Servidor do Telegram (Telegraph)
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
        
        # 1. Coleta Nome, Versão e define qual é o ícone oficial
        badging_cmd = f"aapt dump badging \"{apk_path}\""
        badging_output = subprocess.check_output(badging_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
        
        version_match = re.search(r"versionName='([^']+)'", badging_output)
        if version_match:
            info["version"] = version_match.group(1)
            
        name_match = re.search(r"application-label:'([^']+)'", badging_output)
        if name_match:
            info["name"] = name_match.group(1)
        
        # 🎯 A MÁGICA: Descobre o nome do arquivo de ícone definido no Manifesto
        # Ex: Pega 'ic_launcher' de 'res/mipmap-anydpi-v26/ic_launcher.xml'
        icon_path_in_manifest = None
        # Procura a densidade padrão primeiro
        icon_match = re.search(r"application: label=.*? icon='([^']+)'", badging_output)
        if not icon_match:
            # Fallback para qualquer ícone definido
            icon_match = re.search(r"icon='([^']+)'", badging_output)
            
        if icon_match:
            full_icon_path = icon_match.group(1)
            # Pega só o nome do arquivo sem extensão (ex: ic_launcher)
            icon_name_base = os.path.splitext(os.path.basename(full_icon_path))[0]
            
            # 2. Faz uma busca reversa inteligente dentro do APK por esse nome exato
            # procurando formatos PNG ou WebP de alta resolução
            unzip_list_cmd = f"unzip -l \"{apk_path}\""
            files_list = subprocess.check_output(unzip_list_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
            
            # Procura linhas que tenham o nome base do ícone E terminem em .png/.webp
            # Priorizando pastas xxxhdpi, xxhdpi, etc.
            potential_icons = re.findall(r"\s+([^\s]*" + re.escape(icon_name_base) + r"\.(?:png|webp))\b", files_list)
            
            # Ordena para pegar as maiores resoluções primeiro (xxxhdpi > xxhdpi > hdpi)
            potential_icons.sort(key=lambda x: ("xxxhdpi" in x, "xxhdpi" in x, "xhdpi" in x), reverse=True)
            
            if potential_icons:
                icon_internal_path = potential_icons[0] # Pega a melhor imagem real encontrada
                icon_ext = icon_internal_path.split('.')[-1]
                icon_dest = os.path.join(ICONS_DIR, f"{pkg_name}.{icon_ext}")
                
                # Extrai a imagem real
                unzip_p_cmd = f"unzip -p \"{apk_path}\" \"{icon_internal_path}\" > \"{icon_dest}\""
                os.system(unzip_p_cmd)
                
                if os.path.exists(icon_dest) and os.path.getsize(icon_dest) > 0:
                    info["icon_saved"] = icon_dest
                    # Sobe para a nuvem
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
        detalhes += f"🔗 [bold]Link da Capa Real:[/bold] [underline cyan]{info['icon_url']}[/underline cyan]"
    elif info["icon_saved"]:
        detalhes += f"🖼️ [bold]Capa Local:[/bold] icons/{os.path.basename(info['icon_saved'])}\n"
        detalhes += f"[dim red]❌ (Falha de rede ao enviar link)[/dim red]"
    else:
        detalhes += f"🖼️ [bold]Capa:[/bold] [red]Não foi possível extrair a imagem real (.png/.webp) do APK[/red]"
        
    console.print(Panel(detalhes, border_style=border_color))

def start_monitor():
    os.system("clear" if os.name == "posix" else "cls")
    console.print(Panel.fit("[bold cyan]Hapiephone Monitor Ultra[/bold cyan]\n[dim]Extrator Cirúrgico de Capas Reais (.png/.webp)[/dim]", border_style="cyan"))
    
    console.print("[yellow]🔍 Fazendo varredura cirúrgica dos APKs...[/yellow]")
    current_apps = get_user_apps()
    
    console.print(f"[bold green]📦 {len(current_apps)} apps encontrados. Buscando capas reais...[/bold green]\n")
    for app in sorted(current_apps):
        info = get_app_info(app)
        print_app_panel(app, info, is_startup=True)
        time.sleep(0.3) # Pausa leve para uploads
        
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
