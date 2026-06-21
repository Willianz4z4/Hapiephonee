import os
import sys
import subprocess
import time
import re
import json

print("🚀 Carregando Monitor Silencioso (Modo Local/Discord)...")

try:
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
except ImportError:
    os.system("pip install rich -q > /dev/null 2>&1")
    from rich.console import Console
    from rich.panel import Panel
    console = Console()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(BASE_DIR, "icons")
JSON_FILE = os.path.join(BASE_DIR, "apps_data.json")
os.makedirs(ICONS_DIR, exist_ok=True)

def load_data():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_data(data):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_user_apps():
    try:
        out = subprocess.check_output("su -c 'pm list packages -3'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8')
        return set([line.replace("package:", "").strip() for line in out.split("\n") if line.strip()])
    except:
        return set()

def get_app_info(pkg_name):
    info = {"name": "Desconhecido", "version": "Desconhecida", "icon_local": None}
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
        
        if icon_match:
            full_icon_path = icon_match.group(1)
            icon_name_base = os.path.splitext(os.path.basename(full_icon_path))[0]
            
            potential_icons = re.findall(r"\s+([^\s]*" + re.escape(icon_name_base) + r"\.(?:png|webp))\b", files_list)
            potential_icons.sort(key=lambda x: ("xxxhdpi" in x, "xxhdpi" in x, "xhdpi" in x), reverse=True)
            
            if potential_icons:
                icon_internal_path = potential_icons[0]
                
        if not icon_internal_path:
            all_imgs = re.findall(r"\s+([^\s]+\.(?:png|webp|jpg|jpeg))\b", files_list)
            fallback_icons = [f for f in all_imgs if "icon" in f.lower() or "logo" in f.lower() or "launcher" in f.lower()]
            fallback_icons.sort(key=lambda x: ("xxxhdpi" in x, "xxhdpi" in x, "xhdpi" in x, "mipmap" in x), reverse=True)
            
            if fallback_icons:
                icon_internal_path = fallback_icons[0]
            elif all_imgs:
                icon_internal_path = all_imgs[0]
                
        if icon_internal_path:
            icon_ext = icon_internal_path.split('.')[-1]
            icon_dest = os.path.join(ICONS_DIR, f"{pkg_name}.{icon_ext}")
            
            unzip_p_cmd = f"unzip -p \"{apk_path}\" \"{icon_internal_path}\" > \"{icon_dest}\""
            os.system(unzip_p_cmd)
            
            if os.path.exists(icon_dest) and os.path.getsize(icon_dest) > 0:
                icon_filename = os.path.basename(icon_dest)
                # 🔥 Fica exclusivamente local! Pronto para o bot usar com discord.File()
                info["icon_local"] = f"icons/{icon_filename}"

    except Exception:
        pass
        
    return info

def print_app_panel(app_package, info, is_new=False):
    status_title = "📥 Novo App Detectado!" if is_new else "🔄 App Atualizado no JSON"
    border_color = "green" if is_new else "blue"
    
    detalhes = f"[bold]{status_title}[/bold]\n\n"
    detalhes += f"📦 [bold]Pacote:[/bold] [yellow]{app_package}[/yellow]\n"
    detalhes += f"🏷️ [bold]Nome:[/bold] {info['name']}\n"
    detalhes += f"🔢 [bold]Versão:[/bold] {info['version']}\n"
    
    if info["icon_local"]:
        detalhes += f"🖼️ [bold]Capa Guardada Em:[/bold] [cyan]{info['icon_local']}[/cyan]"
    else:
        detalhes += f"🖼️ [bold]Capa:[/bold] [red]Nenhuma imagem PNG/WebP suportada[/red]"
        
    console.print(Panel(detalhes, border_style=border_color))

def start_monitor():
    os.system("clear" if os.name == "posix" else "cls")
    console.print(Panel.fit("[bold cyan]Hapiephone Monitor Local[/bold cyan]\n[dim]Banco JSON + Armazenamento Oculto para o Git[/dim]", border_style="cyan"))
    
    console.print("[yellow]📂 Carregando memória do JSON...[/yellow]")
    app_db = load_data()
    
    current_apps = get_user_apps()
    new_or_updated = 0
    
    for app in current_apps:
        if app not in app_db:
            console.print(f"[dim]⚡ Analisando: {app}...[/dim]")
            info = get_app_info(app)
            app_db[app] = info
            new_or_updated += 1
            print_app_panel(app, info, is_new=True)
            
    apps_to_remove = [app for app in app_db if app not in current_apps]
    for app in apps_to_remove:
        del app_db[app]
        new_or_updated += 1
        
    if new_or_updated > 0:
        save_data(app_db)
        console.print(f"[bold green]✅ JSON atualizado e salvo! ({len(app_db)} apps no total)[/bold green]")
    else:
        console.print(f"[bold green]✅ JSON já estava 100% atualizado com {len(app_db)} apps.[/bold green]")
        
    print("\n🌟 Monitor ativo em segundo plano... (CTRL+C para sair)\n")

    while True:
        try:
            time.sleep(2)
            new_apps = get_user_apps()
            
            if new_apps != current_apps:
                added = new_apps - current_apps
                removed = current_apps - new_apps
                
                if added:
                    for app in added:
                        console.print(f"\n[bold yellow]⚙️ Nova instalação: {app}...[/bold yellow]")
                        info = get_app_info(app)
                        app_db[app] = info
                        save_data(app_db)
                        print_app_panel(app, info, is_new=True)
                        
                if removed:
                    for app in removed:
                        if app in app_db:
                            del app_db[app]
                            save_data(app_db)
                        console.print(Panel(f"[bold red]🗑️ Aplicativo Removido:[/bold red]\n📦 [yellow]{app}[/yellow]", border_style="red"))
                        
                current_apps = new_apps
        except KeyboardInterrupt:
            break
        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    start_monitor()
