import os
import sys
import subprocess
import time
import re
import json

print("🚀 Carregando Monitor Estruturado (hapie_apps)...")

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
REPO_ROOT = os.path.dirname(BASE_DIR)

ICONS_DIR = os.path.join(REPO_ROOT, "icons")
DATA_DIR = os.path.join(REPO_ROOT, "Data")
JSON_FILE = os.path.join(DATA_DIR, "apps_install.json")
PENDING_TASKS_FILE = os.path.join(DATA_DIR, "pending_tasks.json")
CONFIG_FILE = os.path.join(REPO_ROOT, "hapie_config.json")

os.makedirs(ICONS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

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

# ========================================================
# 🔥 NOVO UPLOADER: FreeImage.host (Estável e compatível com Discord)
# ========================================================
def upload_to_nuvem(file_path):
    try:
        upload_cmd = f'curl -s -F "key=6d207e02198a847aa98d0a2a901485a5" -F "action=upload" -F "source=@{file_path}" -F "format=json" https://freeimage.host/api/1/upload'
        out = subprocess.check_output(upload_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()

        data = json.loads(out)
        if "image" in data and "url" in data["image"]:
            return data["image"]["url"]
    except Exception:
        pass
    return None

def get_app_info(pkg_name):
    info = {"name": "Desconhecido", "version": "Desconhecida", "icon_local": None, "size_mb": 0.0}
    try:
        apk_path_cmd = f"su -c 'pm path {pkg_name}'"
        apk_path_raw = subprocess.check_output(apk_path_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()

        if not apk_path_raw:
            return info

        lines = [line.replace("package:", "").strip() for line in apk_path_raw.split("\n") if line.strip()]
        if not lines:
            return info
        apk_path = lines[0]

        try:
            size_cmd = f"su -c 'stat -c %s \"{apk_path}\"'"
            size_bytes = int(subprocess.check_output(size_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip())
            info["size_mb"] = round(size_bytes / (1024 * 1024), 2)
        except Exception:
            try:
                ls_cmd = f"su -c 'ls -l \"{apk_path}\"'"
                ls_out = subprocess.check_output(ls_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
                size_bytes = int(ls_out.split()[4])
                info["size_mb"] = round(size_bytes / (1024 * 1024), 2)
            except:
                info["size_mb"] = 0.0

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
                cloud_url = upload_to_nuvem(icon_dest)

                if cloud_url:
                    info["icon_local"] = cloud_url
                else:
                    icon_filename = os.path.basename(icon_dest)
                    info["icon_local"] = f"icons/{icon_filename}"

    except Exception:
        pass

    return info

def print_app_panel(app_package, info, is_new=False):
    status_title = "📥 Novo App Detectado!" if is_new else "🔄 App Sincronizado no JSON"
    border_color = "green" if is_new else "blue"

    detalhes = f"[bold]{status_title}[/bold]\n\n"
    detalhes += f"📦 [bold]Pacote:[/bold] [yellow]{app_package}[/yellow]\n"
    detalhes += f"🏷️ [bold]Nome:[/bold] {info['name']}\n"
    detalhes += f"🔢 [bold]Versão:[/bold] {info['version']}\n"
    detalhes += f"⚖️ [bold]Tamanho:[/bold] {info.get('size_mb', 0.0)} MB\n"

    if info["icon_local"]:
        if str(info["icon_local"]).startswith("http"):
            detalhes += f"🔗 [bold]URL Nuvem:[/bold] [cyan]{info['icon_local']}[/cyan]"
        else:
            detalhes += f"🖼️ [bold]Local:[/bold] [cyan]{info['icon_local']}[/cyan]"
    else:
        detalhes += f"🖼️ [bold]Capa:[/bold] [red]Nenhuma imagem gerada[/red]"

    console.print(Panel(detalhes, border_style=border_color))

# ========================================================
# 🚀 PENDÊNCIAS: EXTRAÇÃO E UPLOAD PARA O FLASK
# ========================================================
def process_pending_uploads():
    if not os.path.exists(PENDING_TASKS_FILE):
        return

    try:
        with open(PENDING_TASKS_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    except Exception:
        return

    if not tasks:
        return

    owner_id = "unknown"
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                owner_id = config.get("owner_id", "unknown")
    except:
        pass

    # A rota do seu Flask que configuramos no connection.py
    UPLOAD_URL = "https://iodize-scrounger-auction.ngrok-free.dev/upload_apk"

    for pkg in tasks:
        console.print(f"\n[bold magenta]🚀 [FILA] Iniciando extração e upload do APK: {pkg}[/bold magenta]")
        try:
            apk_path_cmd = f"su -c 'pm path {pkg}'"
            apk_path_raw = subprocess.check_output(apk_path_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
            lines = [line.replace("package:", "").strip() for line in apk_path_raw.split("\n") if line.strip()]

            if not lines:
                console.print(f"[red]❌ APK não encontrado no sistema para: {pkg}[/red]")
                continue

            apk_path = lines[0]
            temp_apk = f"/sdcard/Download/{pkg}_temp.apk"

            # 1. Copia o APK protegido para a pasta de downloads pública do celular
            os.system(f"su -c 'cp \"{apk_path}\" \"{temp_apk}\"'")
            os.system(f"su -c 'chmod 777 \"{temp_apk}\"'")

            console.print(f"[dim]Enviando para o Drive da VPS (Isso pode demorar dependendo do tamanho)...[/dim]")
            
            # 2. Faz o envio Multipart-Form-Data para o seu connection.py
            upload_cmd = f'curl -s -X POST -F "file=@{temp_apk}" -F "pkg_name={pkg}" -F "owner_id={owner_id}" {UPLOAD_URL}'
            response = subprocess.check_output(upload_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()

            # 3. Limpa o arquivo temporário para não entupir a memória do celular
            os.system(f"su -c 'rm \"{temp_apk}\"'")

            console.print(f"[bold green]✅ Upload concluído com sucesso: {response}[/bold green]")

        except Exception as e:
            console.print(f"[bold red]❌ Erro crítico no upload de {pkg}: {e}[/bold red]")

    # 4. Apaga o arquivo de pendências após processar todos
    try:
        os.remove(PENDING_TASKS_FILE)
        console.print("[dim]🗑️ Fila de pendências concluída e resetada.[/dim]\n")
    except:
        pass

def start_monitor():
    os.system("clear" if os.name == "posix" else "cls")
    console.print(Panel.fit("[bold cyan]Hapiephone Monitor Estruturado[/bold cyan]\n[dim]Pasta: hapie_apps | Banco: Data/apps_install.json[/dim]", border_style="cyan"))

    console.print("[yellow]📂 Carregando memória...[/yellow]")
    app_db = load_data()

    current_apps = get_user_apps()
    new_or_updated = 0

    for app in current_apps:
        needs_update = False
        if app not in app_db:
            needs_update = True
        elif app_db[app].get("icon_local") and not str(app_db[app]["icon_local"]).startswith("http"):
            needs_update = True
        elif "size_mb" not in app_db[app]:
            needs_update = True

        if needs_update:
            console.print(f"[dim]⚡ Analisando/Upando: {app}...[/dim]")
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
        console.print(f"[bold green]✅ apps_install.json atualizado! ({len(app_db)} apps no total)[/bold green]")
    else:
        console.print(f"[bold green]✅ Todos os {len(app_db)} apps já estão upados e em dia.[/bold green]")

    print("\n🌟 Monitor ativo... (Pressione CTRL+C para sair)\n")

    while True:
        try:
            # INTERCEPTA AS ORDENS DE UPLOAD VINDAS DO IMPORT.PY
            process_pending_uploads()
            
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
        except Exception as e:
            time.sleep(2)

if __name__ == "__main__":
    start_monitor()
