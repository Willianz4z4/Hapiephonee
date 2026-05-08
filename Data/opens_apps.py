import os
import json
import subprocess
import time
import re
import sys

DUMPSYS = "/system/bin/dumpsys"
AM = "/system/bin/am"
SAVE_FILE = os.path.expanduser("~/last_opened_apps.json")

def run_su(cmd):
    """Executa comando com shell explícito"""
    return subprocess.getoutput(f"su -c 'sh -c \"{cmd}\"'")

def get_active_packages():
    """Obtém lista de PACOTES ATIVOS (não apenas o em foco)"""
    
    # Estratégia 1: Tenta via package manager (melhor para detectar tudo)
    raw_data = run_su(f"{DUMPSYS} package | grep -E 'Package \\[|android.intent.action.MAIN'")
    
    if raw_data.strip():
        # Extrai pacotes da forma: Package [com.google.android.apps.maps]
        pattern = r'Package \[([a-zA-Z0-9_.]+)\]'
        packages = re.findall(pattern, raw_data)
        return list(set(packages))  # Remove duplicatas
    
    return []

def get_running_apps():
    """Obtém apps ATUALMENTE EM EXECUÇÃO via activity manager"""
    
    # Método 1: dumpsys activity recents (apps recentes)
    raw_data = run_su(f"{DUMPSYS} activity recents")
    
    # Padrão: #0 com.google.android.gms/.auth.api.signin.internal.SignInActivity
    pattern = r'#\d+\s+([a-zA-Z0-9_.]+)(?:/([a-zA-Z0-9_.$]+))?'
    matches = re.findall(pattern, raw_data)
    
    apps = []
    for package, activity in matches:
        if activity:
            apps.append(f"{package}/{activity}")
        else:
            apps.append(package)
    
    return apps

def get_foreground_app():
    """Obtém APENAS o app em primeiro plano"""
    
    # Método 1: mCurrentFocus (mais direto)
    raw_data = run_su(f"{DUMPSYS} window windows | grep -A 2 mCurrentFocus")
    
    # Procura por padrão: com.example.app/com.example.Activity
    pattern = r'([a-zA-Z0-9_.]+)/([a-zA-Z0-9_.$]+)'
    match = re.search(pattern, raw_data)
    
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    
    # Fallback: tenta window manager focus
    raw_data = run_su(f"{DUMPSYS} window windows | grep -E 'Window #'")
    match = re.search(pattern, raw_data)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    
    return None

def get_currently_open_apps():
    """Combina múltiplas estratégias para máxima detecção"""
    
    print("🔍 Detectando apps em execução...")
    
    apps = []
    
    # 1. App em primeiro plano
    foreground = get_foreground_app()
    if foreground:
        print(f"✓ Foreground: {foreground}")
        apps.append(foreground)
    
    # 2. Apps recentes (que estão na pilha de tarefas)
    running = get_running_apps()
    print(f"✓ Running apps ({len(running)} encontrados)")
    apps.extend(running)
    
    # 3. Pacotes ativos do sistema
    packages = get_active_packages()
    print(f"✓ Active packages ({len(packages)} encontrados)")
    
    # Filtra apps úteis (remove sistema e Termux)
    filtered_apps = []
    blacklist = ["com.termux", "com.android.systemui", "com.android.launcher", 
                 "android", "com.android.settings", "com.android.shell"]
    
    for app in apps:
        package = app.split('/')[0] if '/' in app else app
        if not any(blocked in package for blocked in blacklist):
            if app not in filtered_apps:
                filtered_apps.append(app)
    
    return filtered_apps

def save_state():
    apps = get_currently_open_apps()
    if apps:
        with open(SAVE_FILE, "w") as f:
            json.dump(apps, f, indent=2)
        print(f"\n✅ Checkpoint: {len(apps)} apps salvos.")
        print(f"📱 Apps salvos:")
        for app in apps:
            print(f"   - {app}")
    else:
        print("\n⚠️ Nenhum app detectado.")
        print("💡 Debug: Verifique se:")
        print("   1. Root está ativo")
        print("   2. dumpsys está acessível")
        print("   3. Apps reais estão instalados")

def restore_state():
    if not os.path.exists(SAVE_FILE):
        print("ℹ️ Arquivo de restauração não encontrado.")
        return

    with open(SAVE_FILE, "r") as f:
        apps = json.load(f)
    
    print(f"🚀 Restaurando {len(apps)} apps...")
    for app in apps:
        print(f"🔄 Abrindo: {app}")
        if '/' in app:
            run_su(f"{AM} start -W -n {app}")
        else:
            run_su(f"{AM} start -W {app}")
        time.sleep(1)
    
    os.remove(SAVE_FILE)
    print("✅ Restauração concluída.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_state()
    else:
        save_state()