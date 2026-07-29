import subprocess
import re
import json
import os
import sys
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Data")
CAMPOS_FILE = os.path.join(DATA_DIR, "campos_mapeados.json")
FUNCTIONS_FILE = os.path.join(BASE_DIR, "functions.json")
DEBUG_LOG = os.path.join(DATA_DIR, "auto_input_debug.txt")
TRIGGER_FILE = "/sdcard/Hapiephone_Data/trigger_visao.txt"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs("/sdcard/Hapiephone_Data", exist_ok=True)

def log_debug(msg):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    texto = f"[{agora}] {msg}"
    print(texto, flush=True)
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(texto + "\n")
    except: pass

def execute_root(comando):
    caminhos_su_android = ["/system/xbin/su", "/system/bin/su", "/sbin/su"]
    for path in caminhos_su_android:
        if os.path.exists(path):
            return subprocess.run([path, "-c", comando], capture_output=True, text=True)
    cmd_fallback = f"PATH=/system/bin:/system/xbin:/sbin:$PATH su -c \"{comando}\""
    return subprocess.run(cmd_fallback, shell=True, capture_output=True, text=True)

def check_permission():
    if os.path.exists(FUNCTIONS_FILE):
        try:
            with open(FUNCTIONS_FILE, "r") as f:
                return json.load(f).get("auto_input", False)
        except: pass
    return False

def toggle_macrodroid_only(ligar):
    MACRODROID_SERVICES = "com.arlosoft.macrodroid/com.arlosoft.macrodroid.triggers.services.MacroDroidAccessibilityServiceJellyBean:com.arlosoft.macrodroid/com.arlosoft.macrodroid.UIInteractionAccessibilityService:com.arlosoft.macrodroid/com.arlosoft.macrodroid.MacroDroidAccessibilityService"
    if ligar: execute_root(f'settings put secure enabled_accessibility_services {MACRODROID_SERVICES}')
    else: execute_root('settings put secure enabled_accessibility_services null')

def obter_todos_edittexts_robusto(max_tentativas=3, delay=2.0):
    classes_alvo = ['android.widget.EditText', 'android.widget.AutoCompleteTextView']
    
    log_debug("[-] Pausando APENAS o MacroDroid cirurgicamente...")
    toggle_macrodroid_only(False)
    time.sleep(2.0) 

    campos = []
    for tentativa in range(1, max_tentativas + 1):
        log_debug(f"[*] Tentativa {tentativa}/{max_tentativas}...")
        execute_root('pkill uiautomator')
        execute_root('rm -f /data/local/tmp/ui_dump.xml')
        
        execute_root('uiautomator dump --compressed /data/local/tmp/ui_dump.xml')
        xml_data = execute_root('cat /data/local/tmp/ui_dump.xml').stdout

        log_debug(f"[-] Tamanho do XML lido: {len(xml_data)} caracteres.")

        if len(xml_data) > 300:
            contador = 1
            for node in xml_data.split('<node'):
                is_text_field = any(f'class="{classe}"' in node for classe in classes_alvo)
                is_editable = 'editable="true"' in node
                is_focused = 'focused="true"' in node and 'focusable="true"' in node
                
                if is_text_field or is_editable or is_focused:
                    match_bounds = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
                    match_id = re.search(r'resource-id="([^"]*)"', node)
                    match_text = re.search(r'text="([^"]*)"', node)
                    if match_bounds:
                        bounds = tuple(map(int, match_bounds.groups()))
                        if bounds[2] - bounds[0] <= 0: continue
                        nome_base = match_text.group(1) if match_text else "Campo Web/Google"
                        campos.append({"id": contador, "nome_identificador": f"[📝 TEXTO] {nome_base}", "bounds": bounds})
                        contador += 1
            if campos: break
        time.sleep(delay)

    log_debug("[-] Relativando o MacroDroid...")
    toggle_macrodroid_only(True)
    return campos

def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--file":
        # Logica de aplicar o texto que já tínhamos fica aqui intacta (omitida para resumir visualmente)
        sys.exit(0)

    print("👁️ [VISÃO] Bot Online. Vigiando chamados do MacroDroid...", flush=True)
    
    while True:
        # Se o MacroDroid criar esse arquivo, o Termux ataca!
        if os.path.exists(TRIGGER_FILE):
            log_debug("🚀 O MacroDroid pediu leitura da tela! Iniciando Raio-X...")
            try: os.remove(TRIGGER_FILE)
            except: pass
            
            if check_permission():
                campos = obter_todos_edittexts_robusto()
                if campos:
                    payload = {"status_autoinput": True, "campos_disponiveis": campos}
                    with open(CAMPOS_FILE, "w") as f: json.dump(payload, f, indent=4)
                    log_debug("✅ FINAL: campos_mapeados.json criado.")
                else:
                    log_debug("❌ FINAL: Falha total. Nenhum campo salvo.")
            else:
                log_debug("⚠️ Sem permissão no functions.json para ler a tela.")
                
        time.sleep(1.5)

if __name__ == '__main__':
    main()
