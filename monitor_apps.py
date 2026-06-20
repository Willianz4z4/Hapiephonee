import os
import sys
import subprocess
import time
import re

print("🚀 Carregando bibliotecas do sistema...")

try:
    import requests
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
except ImportError:
    print("⚠️ Instalando pacotes necessários (rich, requests)... aguarde.")
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
        badging_output = subprocess.check_output(badging_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8')
        
        # Extrai Versão
        version_match = re.search(r"versionName='([^']+)'", badging_output)
        if version_match:
            info["version"] = version_match.group(1)
            
        # Extrai Nome
        name_match = re.search(r"application-label:'([^']+)'", badging_output)
        if name_match:
            info["name"] = name_match.group(1)
        else:
            name_fallback = re.search(r"application: label='([^']+)'", badging_output)
            if name_fallback:
                info["name"] = name_fallback.group(1)
        
        # 🚀 CÃO FAREJADOR DE IMAGENS: Procura estritamente por imagens reais (PNG, WEBP, JPG)
        icon_internal_path = None
        valid_icons = re.findall(r"application-icon-\d+='([^']+\.(?:png|webp|jpg|jpeg))'", badging_output)
        
        if valid_icons:
            icon_internal_path = valid_icons[-1] # Pega a última da lista (geralmente a de maior resolução)
        else:
            # Fallback: Se não achar as de densidade, procura a padrão, desde que seja imagem real
            fallback_icon = re.search(r"icon='([^']+\.(?:png|webp|jpg|jpeg))'", badging_output)
            if fallback_icon:
                icon_internal_path = fallback_icon.group(1)
            
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
        detalhes += f"🔗 [bold]Link do Ícone:[/bold] [underline cyan]{info['icon_url']}[/underline cyan]"
    elif info["icon_saved"]:
        detalhes += f"🖼️ [bold]Ícone Local:[/bold] Salvo em icons/{os.path.basename(info['icon_saved'])}\n"
        detalhes += f"[dim red](Falha ao fazer upload para a nuvem)[/dim red]"
    else:
        detalhes += f"🖼️ [bold]Ícone:[/bold] [red]Nenhuma imagem em formato real encontrada no APK[/red]"
        
    console.print(Panel(detalhes, border_style=border_color))

def start_monitor():
    console.print(Panel.fit("[bold cyan]Hapiephone Monitor Completo[/bold cyan]\n[dim]Extrator de Pacotes + Caçador de Imagens Reais[/dim]", border_style="cyan"))
    
    console.print("[yellow]🔍 Fazendo varredura dos aplicativos instalados...[/yellow]")
    current_apps = get_user_apps()
    
    console.print(f"[bold green]📦 {len(current_apps)} apps encontrados. Lendo metadados e caçando imagens...[/bold green]\n")
    for app in sorted(current_apps):
        info = get_app_info(app)
        print_app_panel(app, info, is_startup=True)
        time.sleep(0.5) # Pausa leve para o upload funcionar bem
        
    console.print("\n[bold green]🌟 Varredura concluída![/bold green]")
    console.print("[dim]Aguardando instalacoes ou desinstalacoes no celular... (Pressione CTRL+C para sair)[/dim]\n")

    while True:
        try:
            time.sleep(2)
            new_apps = get_user_apps()
            
            if new_apps != current_apps:
                added = new_apps - current_apps
                removed = current_apps - new_apps
                
                if added:
                    for app in added:
                        console.print(f"\n[bold yellow]⚙️ Analisando e extraindo: {app}...[/bold yellow]")
                        info = get_app_info(app)
                        print_app_panel(app, info, is_startup=False)
                
                if removed:
                    for app in removed:
                        console.print(Panel(f"[bold red]🗑️ Aplicativo Desinstalado:[/bold red]\n📦 [yellow]{app}[/yellow]", border_style="red"))
                
                console.print(f"\n[bold cyan]📦 Lista Atualizada de Aplicativos Baixados ({len(new_apps)} no total):[/bold cyan]")
                for idx, app in enumerate(sorted(new_apps), 1):
                    console.print(f"  [dim]{idx}.[/dim] [yellow]{app}[/yellow]")
                console.print("-" * 45 + "\n")
                
                current_apps = new_apps
                
        except KeyboardInterrupt:
            console.print("\n[bold red]🛑 Monitoramento encerrado.[/bold red]")
            break
        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    start_monitor()
