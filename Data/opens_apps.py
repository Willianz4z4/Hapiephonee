import os
import subprocess
import time

# Caminho do arquivo que o MacroDroid está atualizando
MACRODROID_FILE = "/sdcard/Download/open_apps.txt"

# 🛡️ LISTA NEGRA: Pacotes que o script NUNCA deve tentar abrir
BLACKLIST = [
    "com.termux",            # O próprio terminal
    "com.og.launcher",       # Launcher do UgPhone/VPhone
    "com.android.launcher",  # Launcher padrão
    "com.android.systemui",  # Sistema
    "com.android.settings"   # Configurações
]

def run_su(cmd):
    """Executa comando de forma bruta e garantida com Root"""
    return subprocess.getoutput(f"su -c '{cmd}'")

def restore_apps():
    print(f"🔍 Lendo lista de apps em: {MACRODROID_FILE}")
    
    if not os.path.exists(MACRODROID_FILE):
        print("❌ Arquivo não encontrado!")
        return

    try:
        with open(MACRODROID_FILE, "r") as f:
            raw_text = f.read()
    except Exception as e:
        print(f"❌ Erro ao tentar ler o arquivo: {e}")
        return

    # 🧹 LIMPEZA PESADA: Remove quebras de linha que o MacroDroid deixa e separa por vírgula
    clean_text = raw_text.replace('\n', '').replace('\r', '')
    raw_apps = [app.strip() for app in clean_text.split(',') if app.strip()]

    if not raw_apps:
        print("⚠️ A lista está vazia. Nenhum app para abrir.")
        return

    # 🎯 FILTRAGEM: Remove duplicatas e aplica a Lista Negra
    apps_to_open = []
    
    # dict.fromkeys remove os duplicados mas mantém a ordem original
    for app in list(dict.fromkeys(raw_apps)):
        is_blacklisted = False
        
        # Verifica se o app faz parte dos proibidos
        for blocked in BLACKLIST:
            if blocked in app:
                is_blacklisted = True
                break
        
        if not is_blacklisted:
            apps_to_open.append(app)
        else:
            print(f"🚫 Ignorando pacote de sistema: {app}")

    if not apps_to_open:
        print("\n⚠️ Nenhum app válido para reabrir (todos eram pacotes de sistema).")
        return

    print(f"\n🚀 Iniciando restauração de {len(apps_to_open)} clones/apps...")
    
    for app in apps_to_open:
        print(f"🔄 Abrindo: {app}")
        # Comando 'monkey' para toque certeiro no app
        run_su(f"monkey -p {app} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1")
        
        # Pausa mágica de 2 segundos para não travar o celular abrindo tudo de uma vez
        time.sleep(2)
        
    print("\n✅ Todos os apps válidos foram reabertos com sucesso!")

if __name__ == "__main__":
    restore_apps()
