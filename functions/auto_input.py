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

os.makedirs(DATA_DIR, exist_ok=True)

def log_debug(msg):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    texto = f"[{agora}] {msg}"
    print(texto)
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(texto + "\n")
    except: pass

_SU_BIN = None

def find_su():
    global _SU_BIN
    if _SU_BIN:
        return _SU_BIN
    
    # Destrói o stub falso do Termux se ele tentar atrapalhar
    fake_su = "/data/data/com.termux/files/usr/bin/su"
    if os.path.exists(fake_su):
        try: os.remove(fake_su)
        except: pass

    # Caminhos comuns de root em celulares em nuvem (UGPhone / Redfinger / Emuladores)
    caminhos_possiveis = [
        "/system/xbin/su",
        "/system/bin/su",
        "/sbin/su",
        "/vendor/bin/su",
        "/data/adb/ksu/bin/su",
        "/data/adb/magisk/su"
    ]
    
    for caminho in caminhos_possiveis:
        if os.path.exists(caminho):
            _SU_BIN = caminho
            return caminho
            
    return "su" # Fallback final

def execute_root(comando):
    su_path = find_su()
    # Força o PATH original do Android para o UGPhone não bloquear o comando
    cmd_completo = f"PATH=/sbin:/system/xbin:/system/bin:/vendor/bin:$PATH {su_path} -c '{comando}'"
    return subprocess.run(cmd_completo, shell=True, capture_output=True, text=True)

def check_permission():
    if os.path.exists(FUNCTIONS_FILE):
        try:
            with open(FUNCTIONS_FILE, "r") as f:
                return json.load(f).get("auto_input", False)
        except: pass
    return False

def obter_todos_edittexts(max_tentativas=10, delay=1.0):
    classes_alvo = [
        'android.widget.EditText',
        'android.widget.AutoCompleteTextView',
        'android.widget.MultiAutoCompleteTextView'
    ]
    
    for tentativa in range(1, max_tentativas + 1):
        log_debug(f"[*] Tentativa {tentativa}/{max_tentativas}...")

        execute_root('pkill uiautomator')
        execute_root('rm -f /data/local/tmp/ui_dump.xml')

        log_debug("[-] Executando uiautomator dump no UGPhone...")
        dump_proc = execute_root('uiautomator dump /data/local/tmp/ui_dump.xml')
        log_debug(f"[-] Resposta do dump: {dump_proc.stdout.strip()} | Erros: {dump_proc.stderr.strip()}")

        xml_data = execute_root('cat /data/local/tmp/ui_dump.xml').stdout
        log_debug(f"[-] Tamanho do XML lido: {len(xml_data)} caracteres.")

        if len(xml_data) < 100:
            log_debug("❌ FALHA: XML vazio ou root desativado no painel do UGPhone.")
        else:
            campos = []
            contador = 1

            for node in xml_data.split('<node'):
                is_text_field = any(f'class="{classe}"' in node for classe in classes_alvo)
                is_focused_html = 'class="android.view.View"' in node and 'focused="true"' in node and 'focusable="true"' in node

                if is_text_field or is_focused_html:
                    if contador > 10: break

                    match_bounds = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
                    match_id = re.search(r'resource-id="([^"]*)"', node)
                    match_desc = re.search(r'content-desc="([^"]*)"', node)
                    match_text = re.search(r'text="([^"]*)"', node)
                    match_pwd = re.search(r'password="(true)"', node)

                    if match_bounds:
                        bounds = tuple(map(int, match_bounds.groups()))
                        res_id = match_id.group(1) if match_id else ""
                        desc = match_desc.group(1) if match_desc else ""
                        text_val = match_text.group(1) if match_text else ""
                        
                        nome_base = desc or (res_id.split('/')[-1] if res_id else (text_val or "Campo HTML/Nativo"))
                        nome_lower, texto_lower = nome_base.lower(), text_val.lower()

                        is_url = any(p in nome_lower for p in ['url','link','site']) or texto_lower.startswith(('http','www.'))
                        is_pwd = match_pwd or 'senha' in nome_lower or 'password' in nome_lower

                        if is_url: nome_final = f"[🔗 URL] {nome_base}"
                        elif is_pwd: nome_final = f"[🔑 SENHA] {nome_base}"
                        else: nome_final = f"[📝 TEXTO] {nome_base}"

                        campos.append({"id": contador, "nome_identificador": nome_final, "bounds": bounds})
                        log_debug(f"    -> Encontrado ID {contador}: {nome_final}")
                        contador += 1

            if campos:
                log_debug(f"✅ SUCESSO! {len(campos)} campos mapeados na tentativa {tentativa}.")
                return campos
            else:
                log_debug("⚠️ XML capturado, mas a regex não encontrou nenhum campo de texto.")

        if tentativa < max_tentativas:
            log_debug(f"[*] Aguardando {delay}s...")
            time.sleep(delay)

    log_debug("❌ ESGOTADO: Todas as tentativas falharam.")
    return []

def aplicar_texto_com_seguranca(id_alvo, texto):
    if not os.path.exists(CAMPOS_FILE): return

    try:
        with open(CAMPOS_FILE, "r") as f:
            dados_locais = json.load(f)
    except: return

    alvo = next((c for c in dados_locais.get("campos_disponiveis", []) if c["id"] == id_alvo), None)
    if not alvo: return

    b = alvo["bounds"]
    str_bounds = f'bounds="[{b[0]},{b[1]}][{b[2]},{b[3]}]"'

    execute_root('pkill uiautomator')
    execute_root('rm -f /data/local/tmp/ui_check.xml')
    execute_root('uiautomator dump /data/local/tmp/ui_check.xml')
    
    xml_atual = execute_root('cat /data/local/tmp/ui_check.xml').stdout

    node_seguro = False
    for node in xml_atual.split('<node'):
        if str_bounds in node and ('EditText' in node or 'AutoCompleteTextView' in node or 'focused="true"' in node):
            node_seguro = True
            break

    if node_seguro:
        cx, cy = (b[0] + b[2]) // 2, (b[1] + b[3]) // 2
        execute_root(f'input tap {cx} {cy}')
        time.sleep(0.5)

        texto_formatado = texto.replace(' ', '%s').replace("'", "\\'")
        execute_root(f"input text '{texto_formatado}'")

    try: os.remove(CAMPOS_FILE)
    except: pass

def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--file":
        payload_path = sys.argv[2]
        try:
            with open(payload_path, "r") as f:
                payload_http = json.load(f)
            cmd = payload_http.get("auto_input_cmd", {})
            id_alvo = cmd.get("id_alvo")
            texto_para_aplicar = cmd.get("texto")
            if id_alvo and texto_para_aplicar:
                aplicar_texto_com_seguranca(int(id_alvo), str(texto_para_aplicar))
        except: pass
        sys.exit(0)

    if not check_permission(): sys.exit(0)

    campos = obter_todos_edittexts()

    if campos:
        payload = {"status_autoinput": True, "campos_disponiveis": campos}
        with open(CAMPOS_FILE, "w") as f:
            json.dump(payload, f, indent=4)
        log_debug("✅ FINAL: campos_mapeados.json criado.")
    else:
        log_debug("❌ FINAL: Falha total. Nenhum campo salvo.")

if __name__ == '__main__':
    main()
