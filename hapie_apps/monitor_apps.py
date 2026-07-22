import os
import sys
import subprocess
import time
import re
import json
import requests

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
PENDING_APPS_FILE = os.path.join(DATA_DIR, "pending_apps.json")
CONFIG_FILE = os.path.join(REPO_ROOT, "hapie_config.json")

os.makedirs(ICONS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

os.system("pkg install zip -y -q > /dev/null 2>&1")

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

def update_relationships(app_db):
    """Mapeia os clones e atualiza o número total de filhos no respectivo App Pai."""
    for pkg, info in app_db.items():
        if info.get("is_parent", True):
            info["clone_count"] = 0

    for pkg, info in app_db.items():
        if not info.get("is_parent", True):
            # Encontra o Pai removendo os números finais do pacote do clone
            base_pkg = re.sub(r'\d+$', '', pkg)
            
            if base_pkg in app_db and app_db[base_pkg].get("is_parent"):
                app_db[base_pkg]["clone_count"] = app_db[base_pkg].get("clone_count", 0) + 1
            else:
                # Tenta localizar o Pai pelo prefixo mais longo caso o padrão seja diferente
                pais_candidatos = [p for p, i in app_db.items() if i.get("is_parent") and pkg.startswith(p)]
                if pais_candidatos:
                    pai_real = max(pais_candidatos, key=len)
                    app_db[pai_real]["clone_count"] = app_db[pai_real].get("clone_count", 0) + 1

def get_app_info(pkg_name):
    info = {"name": "Desconhecido", "version": "Desconhecida", "icon_local": None, "size_mb": 0.0, "is_parent": True}

    try:
        apk_path_cmd = f"su -c 'pm path {pkg_name}'"
        apk_path_raw = subprocess.check_output(apk_path_cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()

        if not apk_path_raw:
            return info

        lines = [line.replace("package:", "").strip() for line in apk_path_raw.split("\n") if line.strip()]
        if not lines:
            return info
        apk_path = lines[0]

        # 🧬 TESTE DE DNA
        try:
            check_cmd = f"su -c 'dumpsys package {pkg_name} | grep -i applisto.appcloner'"
            check_proc = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            if "applisto.appcloner" in check_proc.stdout.lower():
                info["is_parent"] = False 
        except Exception:
            pass

        # 🤖 INTEGRAÇÃO UGCLONE_MONITOR (Somente para Filhos)
        if not info["is_parent"]:
            try:
                monitor_script = os.path.join(BASE_DIR, "ugclone_monitor.py")
                if os.path.exists(monitor_script):
                    cmd_ug = f"python {monitor_script} {pkg_name}"
                    out_ug = subprocess.check_output(cmd_ug, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
                    if out_ug:
                        dados_ug = json.loads(out_ug)
                        if "filhos_setup" in dados_ug and pkg_name in dados_ug["filhos_setup"]:
                            info["filhos_setup"] = dados_ug["filhos_setup"][pkg_name]
            except Exception:
                info["filhos_setup"] = {}
        else:
            info["clone_count"] = 0 # Inicializa contagem no Pai

        # Metadados padrões (Tamanho, Versão, Nome e Ícone)
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

    if info.get("is_parent", True):
        tipo_app = "👑 [bold yellow]PAI (Base Original)[/bold yellow]"
        extra_info = f"👥 [bold]Clones Ativos:[/bold] {info.get('clone_count', 0)}"
    else:
        tipo_app = "🧬 [bold magenta]CLONE (Filho)[/bold magenta]"
        qtd_configs = len(info.get('filhos_setup', {}))
        extra_info = f"⚙️ [bold]Configs Injetadas:[/bold] {qtd_configs} opções"

    detalhes = f"[bold]{status_title}[/bold]\n\n"
    detalhes += f"📦 [bold]Pacote:[/bold] [yellow]{app_package}[/yellow]\n"
    detalhes += f"🏷️ [bold]Nome:[/bold] {info['name']}\n"
    detalhes += f"🧬 [bold]DNA:[/bold] {tipo_app}\n"
    detalhes += f"{extra_info}\n"
    detalhes += f"🔢 [bold]Versão:[/bold] {info['version']}\n"
    detalhes += f"⚖️ [bold]Tamanho:[/bold] {info.get('size_mb', 0.0)} MB\n"

    if info.get("icon_local"):
        if str(info["icon_local"]).startswith("http"):
            detalhes += f"🔗 [bold]URL Nuvem:[/bold] [cyan]{info['icon_local']}[/cyan]"
        else:
            detalhes += f"🖼️ [bold]Local:[/bold] [cyan]{info['icon_local']}[/cyan]"
    else:
        detalhes += f"🖼️ [bold]Capa:[/bold] [red]Nenhuma imagem gerada[/red]"

    console.print(Panel(detalhes, border_style=border_color))

def process_ugclone_action(task):
    import apps_data
    pkg_alvo = task.get("package_name", "Desconhecido")
    link = task.get("link")

    console.print(f"\n[bold magenta]🚀 [FILA] Injeção de configuração (UGClone): {pkg_alvo}[/bold magenta]")
    if not link:
        console.print("[bold red]❌ Nenhum link de JSON fornecido.[/bold red]")
        return

    console.print(f"[cyan]📥 Baixando payload JSON do bot (Discord)...[/cyan]")
    try:
        r = requests.get(link, timeout=15)
        if r.status_code in [200, 201]:
            payload_data = r.json()
            ug_tasks = payload_data.get("tasks", [])

            for ug_t in ug_tasks:
                target_pkg = ug_t.get("target_pkg")
                settings = ug_t.get("settings", {})

                if target_pkg and settings:
                    apps_data.add_ugclone_config(target_pkg, settings)

            console.print(f"[bold green]✅ UGClone atualizado com sucesso para {pkg_alvo}![/bold green]")
        else:
            console.print(f"[bold red]❌ Erro ao baixar JSON (HTTP {r.status_code})[/bold red]")
    except Exception as e:
        console.print(f"[bold red]❌ Falha de rede ou JSON inválido: {e}[/bold red]")

def process_pending_apps():
    if not os.path.exists(PENDING_APPS_FILE):
        return

    try:
        with open(PENDING_APPS_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    except Exception:
        return

    if not tasks:
        return

    for task in tasks:
        if isinstance(task, dict):
            action = task.get("action")
            if action == "update_ugclone":
                process_ugclone_action(task)

    try:
        os.remove(PENDING_APPS_FILE)
        console.print("[dim]🗑️ Fila de ações (pending_apps) processada e resetada.[/dim]\n")
    except:
        pass

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

    UPLOAD_URL = "https://pandanaceous-meghann-nonincarnate.ngrok-free.dev/upload_apk"

    for pkg in tasks:
        if isinstance(pkg, dict):
            if pkg.get("action") == "update_ugclone":
                process_ugclone_action(pkg)
            continue

        console.print(f"\n[bold magenta]🚀 [FILA] Iniciando extração e camuflagem do APK: {pkg}[/bold magenta]")
        try:
            apk_path_cmd = f"su -c 'pm path {pkg}'"
            apk_path_raw = subprocess.check_output(apk_path_cmd, shell=True).decode('utf-8').strip()
            lines = [line.replace("package:", "").strip() for line in apk_path_raw.split("\n") if line.strip()]

            if not lines:
                console.print(f"[red]❌ APK não encontrado no sistema para: {pkg}[/red]")
                continue

            apk_path = lines[0]

            temp_apk = os.path.join(DATA_DIR, f"{pkg}_temp.apk")
            temp_zip = os.path.join(DATA_DIR, f"{pkg}_temp.zip")

            os.system(f"su -c 'cp \"{apk_path}\" \"{temp_apk}\" && chmod 777 \"{temp_apk}\"'")

            console.print(f"[cyan]📦 Zipando arquivo com senha '123' para burlar o Drive...[/cyan]")

            zip_cmd = f"zip -j -P 123 \"{temp_zip}\" \"{temp_apk}\""
            zip_process = subprocess.run(zip_cmd, shell=True, capture_output=True, text=True)

            if zip_process.returncode != 0:
                console.print(f"[bold red]❌ Erro ao zipar o APK:[/bold red]\n{zip_process.stderr}")
                os.system(f"rm -f \"{temp_apk}\" \"{temp_zip}\"")
                continue

            size_check = subprocess.run(f"stat -c %s \"{temp_zip}\"", shell=True, capture_output=True, text=True)
            if size_check.returncode == 0:
                tamanho_mb = int(size_check.stdout.strip()) / (1024 * 1024)
                console.print(f"[dim]Tamanho do ZIP gerado: {tamanho_mb:.2f} MB[/dim]")
            else:
                console.print(f"[bold red]❌ Arquivo ZIP falhou em ser criado![/bold red]")
                os.system(f"rm -f \"{temp_apk}\"")
                continue

            console.print(f"[dim]Enviando arquivo ZIP seguro para a VPS (Isso pode levAlguns minutos)...[/dim]")

            upload_cmd = f'curl -s -m 600 -w "\\nHTTP_STATUS:%{{http_code}}" -X POST -F "file=@{temp_zip}" -F "pkg_name={pkg}" -F "owner_id={owner_id}" {UPLOAD_URL}'
            upload_process = subprocess.run(upload_cmd, shell=True, capture_output=True, text=True)

            os.system(f"rm -f \"{temp_apk}\" \"{temp_zip}\"")

            if upload_process.returncode != 0:
                console.print(f"[bold red]❌ Falha de Conexão com o Flask (cURL exit {upload_process.returncode}):[/bold red]\n{upload_process.stderr}")
            else:
                saida_curl = upload_process.stdout.strip()
                if "HTTP_STATUS:200" in saida_curl:
                    console.print(f"[bold green]✅ Upload ZIP concluído com sucesso![/bold green]\n[dim]{saida_curl}[/dim]")
                else:
                    console.print(f"[bold red]⚠️ A VPS negou o arquivo (Ngrok ou Flask retornou erro):[/bold red]\n{saida_curl}")

        except Exception as e:
            console.print(f"[bold red]❌ Erro crítico inesperado no upload de {pkg}: {e}[/bold red]")

    try:
        os.remove(PENDING_TASKS_FILE)
        console.print("[dim]🗑️ Fila de pendências de upload concluída e resetada.[/dim]\n")
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
        elif "is_parent" not in app_db[app] or ("is_parent" in app_db[app] and app_db[app]["is_parent"] is False and "filhos_setup" not in app_db[app]):
            needs_update = True

        if needs_update:
            console.print(f"[dim]⚡ Analisando/Atualizando: {app}...[/dim]")
            info = get_app_info(app)
            app_db[app] = info
            new_or_updated += 1
            print_app_panel(app, info, is_new=True)

    apps_to_remove = [app for app in app_db if app not in current_apps]
    for app in apps_to_remove:
        del app_db[app]
        new_or_updated += 1

    # Atualiza hierarquia e contagem de clones antes de salvar o estado inicial
    update_relationships(app_db)

    if new_or_updated > 0:
        save_data(app_db)
        console.print(f"[bold green]✅ apps_install.json atualizado! ({len(app_db)} apps no total)[/bold green]")
    else:
        console.print(f"[bold green]✅ Todos os {len(app_db)} apps já estão upados e validados no DNA.[/bold green]")

    print("\n🌟 Monitor ativo... (Pressione CTRL+C para sair)\n")

    while True:
        try:
            process_pending_apps()
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
                        
                        update_relationships(app_db)
                        save_data(app_db)
                        print_app_panel(app, info, is_new=True)

                if removed:
                    for app in removed:
                        if app in app_db:
                            del app_db[app]
                            
                            update_relationships(app_db)
                            save_data(app_db)
                        console.print(Panel(f"[bold red]🗑️ Aplicativo Removido:[/bold red]\n📦 [yellow]{app}[/yellow]", border_style="red"))

                current_apps = new_apps
        except KeyboardInterrupt:
            break
        except Exception as e:
            time.sleep(2)

if __name__ == "__main__":
    start_monitor()
