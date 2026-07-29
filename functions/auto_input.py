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

def toggle_accessibility(estado):
    # 0 = Desliga (Libera a tela) | 1 = Liga (Volta o MacroDroid)
    execute_root(f'settings put secure accessibility_enabled {estado}')

def obter_todos_edittexts(max_tentativas=5, delay=1.5):
    classes_alvo = [
        'android.widget.EditText',
        'android.widget.AutoCompleteTextView',
        'android.widget.MultiAutoCompleteTextView'
    ]

    # 1. DESLIGA A ACESSIBILIDADE TEMPORARIAMENTE PARA O DUMP FUNCIONAR (Evita XML de 161 bytes)
    log_debug("[-] Desativando acessibilidade para liberar a tela pro UIAutomator...")
    toggle_accessibility(0)
    time.sleep(0.5)

    campos = []

    for tentativa in range(1, max_tentativas + 1):
        log_debug(f"[*] Tentativa {tentativa}/{max_tentativas}...")

        execute_root('pkill uiautomator')
        execute_root('rm -f /data/local/tmp/ui_dump.xml')

        log_debug("[-] Executando uiautomator dump no UGPhone...")
        dump_proc = execute_root('uiautomator dump /data/local/tmp/ui_dump.xml')
        
        xml_proc = execute_root('cat /data/local/tmp/ui_dump.xml')
        xml_data = xml_proc.stdout

        log_debug(f"[-] Tamanho do XML lido: {len(xml_data)} caracteres.")

        # Se for maior que 300 caracteres, pegou a tela real (e não só a hierarquia vazia de 161)
        if len(xml_data) > 300:
            contador = 1
            for node in xml_data.split('<node'):
                # 2. MELHORIA AQUI: Captura Google (WebView/Chrome) e sites
                is_text_field = any(f'class="{classe}"' in node for classe in classes_alvo)
                is_editable = 'editable="true"' in node
                is_focused = 'focused="true"' in node and 'focusable="true"' in node
                
                if is_text_field or is_editable or is_focused:
                    match_bounds = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
                    match_id = re.search(r'resource-id="([^"]*)"', node)
                    match_desc = re.search(r'content-desc="([^"]*)"', node)
                    match_text = re.search(r'text="([^"]*)"', node)
                    match_pwd = re.search(r'password="(true)"', node)

                    if match_bounds:
                        bounds = tuple(map(int, match_bounds.groups()))
                        # Ignora elementos fantasmas invisíveis na tela
                        if bounds[2] - bounds[0] <= 0 or bounds[3] - bounds[1] <= 0:
                            continue

                        res_id = match_id.group(1) if match_id else ""
                        desc = match_desc.group(1) if match_desc else ""
                        text_val = match_text.group(1) if match_text else ""

                        nome_base = desc or text_val or (res_id.split('/')[-1] if res_id else "Campo Web/Google")
                        nome_lower, texto_lower = nome_base.lower(), text_val.lower()

                        is_url = any(p in nome_lower for p in ['url','link','site','pesquisar','search']) or texto_lower.startswith(('http','www.'))
                        is_pwd = match_pwd or 'senha' in nome_lower or 'password' in nome_lower

                        if is_url: nome_final = f"[🔗 BUSCA/URL] {nome_base}"
                        elif is_pwd: nome_final = f"[🔑 SENHA] {nome_base}"
                        else: nome_final = f"[📝 TEXTO] {nome_base}"

                        campos.append({"id": contador, "nome_identificador": nome_final, "bounds": bounds})
                        log_debug(f"    -> Encontrado ID {contador}: {nome_final}")
                        contador += 1
            
            if campos:
                log_debug(f"✅ SUCESSO! {len(campos)} campos mapeados na tentativa {tentativa}.")
                break
            else:
                log_debug("⚠️ XML capturado, mas não encontrou campos HTML ou Nativos digitáveis.")
        else:
            log_debug("⚠️ XML vazio (O Android bloqueou a leitura da tela).")

        if tentativa < max_tentativas:
            log_debug(f"[*] Aguardando {delay}s...")
            time.sleep(delay)

    # 3. LIGA O MACRODROID DE VOLTA
    log_debug("[-] Reativando acessibilidade para o MacroDroid voltar a funcionar...")
    toggle_accessibility(1)

    if not campos:
        log_debug("❌ ESGOTADO: Todas as tentativas de leitura falharam.")
    return campos

def aplicar_texto_com_seguranca(id_alvo, texto):
    if not os.path.exists(CAMPOS_FILE): return

    try:
        with open(CAMPOS_FILE, "r") as f:
            dados_locais = json.load(f)
    except: return

    alvo = next((c for c in dados_locais.get("campos_disponiveis", []) if c["id"] == id_alvo), None)
    if not alvo: return

    b = alvo["bounds"]
    
    # Desliga a acessibilidade rapidamente para não bugar o clique
    toggle_accessibility(0)
    time.sleep(0.3)

    cx, cy = (b[0] + b[2]) // 2, (b[1] + b[3]) // 2
    execute_root(f'input tap {cx} {cy}')
    time.sleep(0.5)

    # Trata aspas simples do texto para não quebrar o terminal do Android
    texto_formatado = str(texto).replace("'", "'\\''")
    execute_root(f"input text '{texto_formatado}'")
    
    # Liga de volta
    toggle_accessibility(1)

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
                aplicar_texto_com_seguranca(int(id_alvo), texto_para_aplicar)
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
