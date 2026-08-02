import subprocess
import re
import json
import os
import sys
import time
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DATA_DIR = os.path.join(BASE_DIR, "Data")
CAMPOS_FILE = os.path.join(DATA_DIR, "campos_mapeados.json")
FUNCTIONS_FILE = os.path.join(BASE_DIR, "functions.json")
DEBUG_LOG = os.path.join(DATA_DIR, "auto_input_debug.txt")

TRIGGER_FILE = "/sdcard/Hapiephone/trigger_visao.txt"
TRIGGER_INJECT = "/sdcard/Hapiephone/trigger_inject.txt"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs("/sdcard/Hapiephone", exist_ok=True)

cache_mapa = {}

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
    return subprocess.run(f"PATH=/system/bin:/system/xbin:/sbin:$PATH su -c \"{comando}\"", shell=True, capture_output=True, text=True)

def check_permission():
    if os.path.exists(FUNCTIONS_FILE):
        try:
            with open(FUNCTIONS_FILE, "r") as f: return json.load(f).get("auto_input", False)
        except: pass
    return False

def obter_todos_edittexts_robusto(max_tentativas=3, delay=1.5):
    classes_alvo = ['android.widget.EditText', 'android.widget.AutoCompleteTextView']
    campos = []
    for tentativa in range(1, max_tentativas + 1):
        log_debug(f"[*] Raio-X Tentativa {tentativa}/{max_tentativas}...")
        execute_root('pkill uiautomator')
        time.sleep(0.5)
        execute_root('rm -f /sdcard/ui_dump_loop.xml')
        execute_root('uiautomator dump /sdcard/ui_dump_loop.xml')
        xml_data = execute_root('cat /sdcard/ui_dump_loop.xml').stdout

        log_debug(f"[*] Tamanho do XML retornado: {len(xml_data)} caracteres")

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
                        res_id = match_id.group(1) if match_id else ""
                        text_val = match_text.group(1) if match_text else ""
                        nome_base = text_val or (res_id.split('/')[-1] if res_id else "Campo Web/Google")
                        campos.append({"id": contador, "nome_identificador": f"[📝 TEXTO] {nome_base}", "bounds": bounds})
                        contador += 1
            if campos: 
                log_debug(f"[*] {len(campos)} campos mapeados com sucesso!")
                break
            else:
                log_debug("[*] XML foi lido, mas nenhum campo de texto foi encontrado na tela.")
        else:
            log_debug("[!] Erro: XML muito pequeno ou Uiautomator travado.")
        time.sleep(delay)
    return campos

# =========================================================
# MODO 1: GATILHO DIRETO
# =========================================================
if len(sys.argv) == 2 and not sys.argv[1].startswith("--"):
    session_id = sys.argv[1]
    log_debug(f"🚀 [VISÃO DIRETA] MacroDroid acionou o Raio-X! (Session: {session_id})")
    
    if check_permission():
        campos = obter_todos_edittexts_robusto()
        if campos:
            payload = {"status_autoinput": True, "campos_disponiveis": campos, "session": session_id, "session_id": session_id}
            with open(CAMPOS_FILE, "w", encoding="utf-8") as f: 
                json.dump(payload, f, indent=4)
            log_debug(f"✅ Mapa salvo com sucesso no arquivo! (Session: {session_id})")
        else:
            log_debug("⚠️ Abortando: Nenhum campo de texto válido para salvar no mapa.")
    else:
        log_debug("🔴 Abortando: Permissão auto_input desligada no painel.")
    
    sys.exit(0)

# =========================================================
# MODO 2: DAEMON
# =========================================================
def main():
    global cache_mapa
    if len(sys.argv) >= 3 and sys.argv[1] == "--file": sys.exit(0)
    print("👁️ [AUTO-INPUT DAEMON] Vigiando ordens de injeção e fallbacks...", flush=True)

    while True:
        if os.path.exists(TRIGGER_FILE):
            time.sleep(0.5)
            log_debug("🚀 [VISÃO ARQUIVO] Raio-X Iniciado...")
            session_id = ""
            try:
                with open(TRIGGER_FILE, "r", encoding="utf-8") as f:
                    conteudo = f.read().strip()
                    if "|" in conteudo: session_id = conteudo.split("|")[1].strip()
                os.remove(TRIGGER_FILE)
            except: pass

            if check_permission():
                campos = obter_todos_edittexts_robusto()
                if campos:
                    payload = {"status_autoinput": True, "campos_disponiveis": campos}
                    if session_id:
                        payload["session"] = session_id
                        payload["session_id"] = session_id
                    cache_mapa = payload
                    with open(CAMPOS_FILE, "w", encoding="utf-8") as f: json.dump(payload, f, indent=4)
                    log_debug(f"✅ Mapa salvo! (Session: {session_id})")

        if os.path.exists(TRIGGER_INJECT):
            time.sleep(0.3)
            try:
                with open(TRIGGER_INJECT, "r", encoding="utf-8") as f: conteudo_injetar = f.read().strip()
                os.remove(TRIGGER_INJECT)

                if "|" in conteudo_injetar:
                    partes = conteudo_injetar.split("|", 2)
                    id_alvo = int(partes[0].strip())
                    auto_enter_flag = (partes[1].strip() == "1")
                    texto_alvo = partes[2].strip()

                    log_debug(f"💉 [INJEÇÃO] ID: {id_alvo} | Auto-Enter: {auto_enter_flag} | Texto: {texto_alvo}")
                    mapeamento = cache_mapa
                    if not mapeamento and os.path.exists(CAMPOS_FILE):
                        with open(CAMPOS_FILE, "r", encoding="utf-8") as f: mapeamento = json.load(f)

                    if mapeamento:
                        campo_escolhido = next((c for c in mapeamento.get("campos_disponiveis", []) if c["id"] == id_alvo), None)
                        if campo_escolhido:
                            bounds = campo_escolhido["bounds"]
                            centro_x = (bounds[0] + bounds[2]) // 2
                            centro_y = (bounds[1] + bounds[3]) // 2
                            execute_root(f"input tap {centro_x} {centro_y}")
                            time.sleep(0.5)

                            texto_formatado = texto_alvo.replace(" ", "%s").replace("'", "\\'")
                            execute_root(f"input text '{texto_formatado}'")

                            if auto_enter_flag:
                                log_debug("↵ Pressionando ENTER...")
                                execute_root("input keyevent 66")

                            log_debug("✅ Injeção concluída!")
            except Exception as e:
                log_debug(f"❌ Erro na injeção: {e}")
                try: os.remove(TRIGGER_INJECT)
                except: pass

        time.sleep(1.0)

if __name__ == '__main__':
    main()
