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

# 🔥 NOVA FUNÇÃO: Burlar a trava do Termux buscando o Root Real
def execute_root(comando):
    caminhos_su = ['/system/bin/su', '/system/xbin/su', '/sbin/su', '/su/bin/su']
    su_correto = 'su' # Fallback
    
    for caminho in caminhos_su:
        if os.path.exists(caminho):
            su_correto = caminho
            break
            
    return subprocess.run([su_correto, '-c', comando], capture_output=True, text=True)

def get_app_aberto():
    try:
        out = execute_root('dumpsys window windows | grep -E "mCurrentFocus|mFocusedApp"')
        return out.stdout.strip() if out.stdout else "Nenhum app focado detectado"
    except Exception as e:
        return f"Erro ao detectar app: {e}"

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
    
    app_atual = get_app_aberto()
    log_debug(f"🔍 INICIANDO VARREDURA. App em foco no Android:\n{app_atual}")

    for tentativa in range(1, max_tentativas + 1):
        log_debug(f"[*] Tentativa {tentativa}/{max_tentativas}...")

        log_debug("[-] Matando uiautomator fantasma e apagando XML velho...")
        execute_root('pkill uiautomator')
        execute_root('rm -f /data/local/tmp/ui_dump.xml')

        log_debug("[-] Executando uiautomator dump...")
        dump_proc = execute_root('uiautomator dump /data/local/tmp/ui_dump.xml')
        log_debug(f"[-] Resposta do dump: {dump_proc.stdout.strip()} | Erros: {dump_proc.stderr.strip()}")

        xml_data = execute_root('cat /data/local/tmp/ui_dump.xml').stdout
        log_debug(f"[-] Tamanho do XML lido: {len(xml_data)} caracteres.")

        if len(xml_data) < 100:
            log_debug("❌ FALHA: XML vazio ou muito pequeno. O uiautomator travou (tela em movimento ou cursor piscando).")
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
    log_debug(f"⚡ INJEÇÃO: Validando ID {id_alvo} para injetar texto...")

    if not os.path.exists(CAMPOS_FILE):
        log_debug("❌ INJEÇÃO CANCELADA: Arquivo campos_mapeados.json sumiu!")
        return

    try:
        with open(CAMPOS_FILE, "r") as f:
            dados_locais = json.load(f)
    except Exception as e:
        log_debug(f"❌ INJEÇÃO ERRO: Falha ao ler JSON local - {e}")
        return

    alvo = next((c for c in dados_locais.get("campos_disponiveis", []) if c["id"] == id_alvo), None)

    if not alvo:
        log_debug(f"❌ INJEÇÃO CANCELADA: ID {id_alvo} não achado na memória local.")
        return

    b = alvo["bounds"]
    str_bounds = f'bounds="[{b[0]},{b[1]}][{b[2]},{b[3]}]"'

    log_debug("[-] Limpando cache para re-checar a tela (segurança)...")
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
        log_debug("✅ INJEÇÃO AUTORIZADA: Campo validado no mesmo local.")
        cx, cy = (b[0] + b[2]) // 2, (b[1] + b[3]) // 2
        execute_root(f'input tap {cx} {cy}')
        time.sleep(0.5)

        texto_formatado = texto.replace(' ', '%s').replace("'", "\\'")
        execute_root(f"input text '{texto_formatado}'")
        log_debug("✅ INJEÇÃO CONCLUÍDA: Texto digitado!")
    else:
        log_debug("🚨 INJEÇÃO ABORTADA CRITICAMENTE: A tela mudou ou rolou antes de digitar!")

    try:
        os.remove(CAMPOS_FILE)
        log_debug("[-] Arquivo campos_mapeados.json deletado com sucesso.")
    except Exception as e:
        log_debug(f"⚠️ Erro ao excluir arquivo residual: {e}")

def main():
    log_debug("==================================================")
    if len(sys.argv) >= 3 and sys.argv[1] == "--file":
        payload_path = sys.argv[2]
        log_debug(f"🚀 [MODO 1 - INJEÇÃO] Iniciado via Webhook.")
        try:
            with open(payload_path, "r") as f:
                payload_http = json.load(f)

            cmd = payload_http.get("auto_input_cmd", {})
            id_alvo = cmd.get("id_alvo")
            texto_para_aplicar = cmd.get("texto")

            if id_alvo and texto_para_aplicar:
                aplicar_texto_com_seguranca(int(id_alvo), str(texto_para_aplicar))
            else:
                log_debug("❌ MODO 1 FALHA: Faltou 'id_alvo' ou 'texto' no payload.")
        except Exception as e:
            log_debug(f"❌ MODO 1 ERRO GERAL: {e}")
        sys.exit(0)

    log_debug("🚀 [MODO 2 - OLHEIRO] Acionado para mapear a tela.")
    if not check_permission():
        log_debug("❌ MODO 2 CANCELADO: Permissão 'auto_input' negada no functions.json.")
        sys.exit(0)

    campos = obter_todos_edittexts()

    if campos:
        payload = {"status_autoinput": True, "campos_disponiveis": campos}
        with open(CAMPOS_FILE, "w") as f:
            json.dump(payload, f, indent=4)
        if os.path.exists(CAMPOS_FILE):
            log_debug(f"✅ FINAL: campos_mapeados.json criado e pronto para o import.py recolher.")
    else:
        log_debug("❌ FINAL: Falha total. Nenhum campo salvo.")

if __name__ == '__main__':
    main()
