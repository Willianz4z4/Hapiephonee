import os
import subprocess
import time
import sys

# Caminho do arquivo que o MacroDroid está atualizando
# /sdcard/Download é a pasta padrão de Downloads do Android
MACRODROID_FILE = "/sdcard/Download/open_apps.txt"

def run_su(cmd):
    """Executa comando de forma bruta e garantida com Root"""
    return subprocess.getoutput(f"su -c '{cmd}'")

def restore_apps():
    print(f"🔍 Procurando lista de apps em: {MACRODROID_FILE}")
    
    if not os.path.exists(MACRODROID_FILE):
        print("❌ Arquivo não encontrado!")
        print("💡 Verifique se o MacroDroid está realmente salvando na pasta 'Downloads'.")
        return

    try:
        with open(MACRODROID_FILE, "r") as f:
            raw_text = f.read()
    except Exception as e:
        print(f"❌ Erro ao tentar ler o arquivo: {e}")
        return

    # O MacroDroid salva com vírgulas: com.roblox.clienb,com.roblox.clienc,
    # Isso divide o texto pelas vírgulas e remove espaços vazios
    apps = [app.strip() for app in raw_text.split(',') if app.strip()]

    if not apps:
        print("⚠️ A lista está vazia. Você fechou todos os apps no MacroDroid.")
        return

    # Remove duplicatas (caso o arquivo tenha salvado duas vezes) preservando a ordem
    apps_to_open = list(dict.fromkeys(apps))

    print(f"🚀 Iniciando restauração de {len(apps_to_open)} clones/apps...")
    
    for app in apps_to_open:
        print(f"🔄 Abrindo: {app}")
        # O comando 'monkey' simula um toque no ícone do app. É infalível para clones.
        run_su(f"monkey -p {app} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1")
        
        # Pausa mágica de 2 segundos.
        # Isso dá tempo do Android renderizar a Janela Flutuante antes de abrir o próximo!
        time.sleep(2) 
        
    print("\n✅ Todos os clones foram reabertos com sucesso!")

if __name__ == "__main__":
    # Como o MacroDroid já cuida de salvar, o script agora foca 100% em RESTAURAR.
    # Assim que você rodar "python opens_apps.py", ele já lê e abre direto.
    restore_apps()
