import os
import sys
import subprocess
import time
import re

try:
    import requests
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
except ImportError:
    os.system("pip install rich requests -q > /dev/null 2>&1")
    import requests
    from rich.console import Console
    from rich.panel import Panel
    console = Console()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(BASE_DIR, "icons")
os.makedirs(ICONS_DIR, exist_ok=True)

def upload_to_catbox(file_path):
    """Faz o upload do arquivo para o Catbox.moe e retorna a URL direta"""
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
    """Retorna um SET com os nomes dos pacotes instalados APENAS pelo usuário"""
    try:
        out = subprocess.check_output("su -c 'pm list packages -3'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8')
        return set([line.replace("package:", "").strip() for line in out.split("\n") if line.strip()])
    except:
        return set()

def get_app_info(pkg_name):
    """Desmembra o APK para pegar Nome, Versão, extrair Ícone e gerar Link"""
    info = {"name": "Desconhecido", "version": "Desconhecida", "icon_saved": False, "icon_url": None}
    try:
        apk_path_cmd = f"su -c 'pm path {pkg_name}'"
        apk_path_raw = subprocess.check_output(apk_path_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        
        if not apk_path_raw:
            return info
            
        apk_path = apk_path_raw.replace("package:", "").strip()
        
        badging_cmd = f"aapt dump badging {apk_path}"
        badging_output = subprocess.check_output(badging_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8')
        
        version_match = re.search(r"versionName='([^']+)'", badging_output)
        if version_match:
            info["version"] = version_match.group(1)
            
        name_match = re.search(r"application-label:'([^']+)'", badging_output)
        if name_match:
            info["name"] = name_match.group(1)
            
        icon_match = re.search(r"application: label=.*? icon='([^']+)'", badging_output)
        if not icon_match:
            icon_match = re.search(r"icon='([^']+)'", badging_output)
            
        if icon_match:
            icon_internal_path = icon_match.group(1)
            icon_ext = icon_internal_path.split('.')[-1]
            icon_dest = os.path.join(ICONS_DIR, f"{pkg_name}.{icon_ext}")
            
            unzip_cmd = f"su -c 'unzip -p {apk_path} {icon_internal_path}' > {icon_dest}"
            os.system(unzip_cmd)
            
            if os.path.exists(icon_dest) and os.path.getsize(icon_dest) > 0:
                info["icon_saved"] = icon_dest
                # 🚀 INICIA O UPLOAD PARA A NUVEM
                info["icon_url"] = upload_to_catbox(icon_dest)

    except Exception as e:
        pass
        
    return info

def start_monitor():
    os.system("clear" if os.name == "posix" else "cls")
    console.print(Panel.fit("[bold cyan]Hapiephone Monitor Avançado[/bold cyan]\n[dim]Extrator & Uploader de APKs[/dim]", border_style="cyan"))
    
    console.print("[yellow]🔍 Mapeando aplicativos instalados...[/yellow]")
    current_apps = get_user_apps()
    
    console.print(f"[bold green]✅ Monitoramento iniciado! Total de apps encontrados: {len(current_apps)}[/bold green]")
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
                        console.print(f"\n[bold yellow]⚙️ Analisando e extraindo pacote: {app}...[/bold yellow]")
                        info = get_app_info(app)
                        
                        detalhes = f"[bold green]📥 Novo App Instalado![/bold green]\n\n"
                        detalhes += f"📦 [bold]Pacote:[/bold] {app}\n"
                        detalhes += f"🏷️ [bold]Nome:[/bold] {info['name']}\n"
                        detalhes += f"🔢 [bold]Versão:[/bold] {info['version']}\n"
                        
                        if info["icon_url"]:
                            detalhes += f"🔗 [bold]Link do Ícone:[/bold] [underline cyan]{info['icon_url']}[/underline cyan]\n"
                        elif info["icon_saved"]:
                            detalhes += f"🖼️ [bold]Ícone Local:[/bold] Salvo em icons/{os.path.basename(info['icon_saved'])}\n"
                            detalhes += f"[dim red](Falha ao fazer upload para a nuvem)[/dim red]"
                        else:
                            detalhes += f"🖼️ [bold]Ícone:[/bold] [red]Não foi possível extrair do APK[/red]"
                            
                        console.print(Panel(detalhes, border_style="green"))
                
                if removed:
                    for app in removed:
                        console.print(Panel(f"[bold red]🗑️ Aplicativo Desinstalado:[/bold red] {app}", border_style="red"))
                
                console.print(f"\n[bold cyan]📦 Lista Atualizada de Aplicativos Baixados ({len(new_apps)} no total):[/bold cyan]")
                for idx, app in enumerate(sorted(new_apps), 1):
                    console.print(f"  [dim]{idx}.[/dim] [cyan]{app}[/cyan]")
                console.print("-" * 45 + "\n")
                
                current_apps = new_apps
                
        except KeyboardInterrupt:
            console.print("\n[bold red]🛑 Monitoramento encerrado pelo usuário.[/bold red]")
            break
        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    os.system("pkg install aapt unzip -y -q > /dev/null 2>&1")
    start_monitor()
