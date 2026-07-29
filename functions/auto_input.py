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

TRIGGER_FILE = "/sdcard/Hapiephone/trigger_visao.txt"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs("/sdcard/Hapiephone", exist_ok=True)

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

def obter_todos_edittexts_robusto(max_tentativas=3, delay=1.5):
    classes_alvo = ['android.widget.EditText', 'android.widget.AutoCompleteTextView']

    campos = []
    for tentativa in range(1, max_tentativas + 1):
        log_debug(f"[*] Tentativa {tentativa}/{max_tentativas}...")

        execute_root('pkill uiautomator')
        time.sleep(0.5)
        execute_root('rm -f /sdcard/ui_dump_loop.xml')

        execute_root('uiautomator dump /sdcard/ui_dump_loop.xml')
        xml_data = execute_root('cat /sdcard/ui_dump_loop.xml').stdout

        if len(xml_data) <= 300:
            pass
        else:
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

                        res_id = match_id.group(1) if match_id else ""
                        text_val = match_text.group(1) if match_text else ""
                        nome_base = text_val or (res_id.split('/')[-1] if res_id else "Campo Web/Google")

                        nome_final = f"[📝 TEXTO] {nome_base}"
                        campos.append({"id": contador, "nome_identificador": nome_final, "bounds": bounds})
                        contador += 1
            if campos: break
        time.sleep(delay)

    return campos

def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--file":
        sys.exit(0)

    print("👁️ [VISÃO] Bot Online. Vigiando chamados do MacroDroid...", flush=True)

    while True:
        if os.path.exists(TRIGGER_FILE):
            time.sleep(0.5) 
            log_debug("🚀 O MacroDroid pediu leitura da tela! Iniciando Raio-X...")

            session_id = ""
            try:
                with open(TRIGGER_FILE, "r", encoding="utf-8") as f:
                    conteudo = f.read().strip()
                    log_debug(f"Conteúdo lido do arquivo: '{conteudo}'")
                    if "|" in conteudo:
                        session_id = conteudo.split("|")[1].strip()
                os.remove(TRIGGER_FILE)
            except Exception as e:
                try: os.remove(TRIGGER_FILE)
                except: pass

            if check_permission():
                campos = obter_todos_edittexts_robusto()
                if campos:
                    payload = {
                        "status_autoinput": True,
                        "campos_disponiveis": campos
                    }

                    if session_id:
                        # 🔥 O SEGREDO ESTAVA AQUI: Injetando os dois nomes para o servidor não errar!
                        payload["session"] = session_id
                        payload["session_id"] = session_id

                    with open(CAMPOS_FILE, "w", encoding="utf-8") as f:
                        json.dump(payload, f, indent=4)

                    log_debug(f"✅ FINAL: campos_mapeados.json criado! (Session: {session_id})")
                else:
                    log_debug("❌ FINAL: Falha total. Nenhum campo salvo.")

        time.sleep(1.0)

if __name__ == '__main__':
    main()
