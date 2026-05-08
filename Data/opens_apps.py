import os
import subprocess
import time

# O backup que o MacroDroid não apaga no shutdown
SESSION_FILE = "/sdcard/Download/session_restore.txt"

BLACKLIST = [
    "com.termux", 
    "com.og.launcher", 
    "com.android.launcher",
    "com.android.systemui"
]

def run_su(cmd):
    return subprocess.getoutput(f"su -c '{cmd}'")

def restore_session():
    if not os.path.exists(SESSION_FILE):
        print("ℹ️ Nenhuma sessão pendente para restaurar.")
        return

    try:
        with open(SESSION_FILE, "r") as f:
            raw_text = f.read()
    except Exception as e:
        print(f"❌ Erro ao ler sessão: {e}")
        return

    clean_text = raw_text.replace('\n', '').replace('\r', '').strip()
    if not clean_text:
        return

    apps = [app.strip() for app in clean_text.split(',') if app.strip()]
    
    # Remove duplicatas preservando a ordem
    apps_to_open = []
    for app in list(dict.fromkeys(apps)):
        if not any(blocked in app for blocked in BLACKLIST):
            apps_to_open.append(app)

    if not apps_to_open:
        return

    print(f"🚀 Restaurando {len(apps_to_open)} apps da última sessão...")

    for app in apps_to_open:
        print(f"🔄 Abrindo: {app}")
        run_su(f"monkey -p {app} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1")
        time.sleep(3) # Tempo para o Android carregar a janela flutuante

    # 🔥 A MÁGICA DA AUTOLIMPEZA:
    # Apaga o arquivo após o uso. O MacroDroid criará um novo conforme os apps abrirem.
    try:
        os.remove(SESSION_FILE)
        print("\n✅ Sessão restaurada e arquivo de backup limpo.")
    except:
        pass

if __name__ == "__main__":
    # Aguarda o sistema carregar o Root após o boot
    print("⏳ Aguardando estabilização do sistema...")
    time.sleep(12) 
    restore_session()
