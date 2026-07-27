import subprocess
import re
import json
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Data")
CAMPOS_FILE = os.path.join(DATA_DIR, "campos_mapeados.json")
FUNCTIONS_FILE = os.path.join(BASE_DIR, "functions.json")

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
        print(f"[*] Tentativa {tentativa}/{max_tentativas} de varredura (buscando campos)...")
        
        processo = subprocess.run(['su', '-c', 'uiautomator dump /data/local/tmp/ui_dump.xml'], capture_output=True, text=True)
        xml_data = subprocess.run(['su', '-c', 'cat /data/local/tmp/ui_dump.xml'], capture_output=True, text=True).stdout

        if len(xml_data) < 100:
            print("[-] uiautomator falhou (A tela deve estar em movimento).")
        else:
            campos = []
            contador = 1

            for node in xml_data.split('<node'):
                is_text_field = any(f'class="{classe}"' in node for classe in classes_alvo)
                is_focused_html = 'class="android.view.View"' in node and 'focused="true"' in node and 'focusable="true"' in node

                if is_text_field or is_focused_html:
                    if contador > 10:
                        break

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

                        campos.append({
                            "id": contador,
                            "nome_identificador": nome_final,
                            "bounds": bounds
                        })
                        contador += 1

            if campos:
                print(f"[*] Sucesso na tentativa {tentativa}! {len(campos)} campos encontrados.")
                return campos
            else:
                print("[-] Tela capturada, mas nenhum campo de texto visível ainda.")

        if tentativa < max_tentativas:
            print(f"[*] Aguardando {delay}s antes de tentar novamente...")
            time.sleep(delay)

    print("[-] Esgotaram-se as tentativas. Nenhum campo mapeado.")
    return []

def aplicar_texto_com_seguranca(id_alvo, texto):
    print(f"[*] Verificando segurança para aplicar no ID {id_alvo}...")

    if not os.path.exists(CAMPOS_FILE):
        print("[-] Arquivo de campos mapeados não encontrado. Nada a fazer.")
        return

    try:
        with open(CAMPOS_FILE, "r") as f:
            dados_locais = json.load(f)
    except Exception as e:
        print(f"[-] Erro ao ler JSON local: {e}")
        return

    alvo = next((c for c in dados_locais.get("campos_disponiveis", []) if c["id"] == id_alvo), None)

    if not alvo:
        print(f"[-] ID {id_alvo} não encontrado na última varredura da tela.")
        return

    b = alvo["bounds"]
    str_bounds = f'bounds="[{b[0]},{b[1]}][{b[2]},{b[3]}]"'

    subprocess.run(['su', '-c', 'uiautomator dump /data/local/tmp/ui_check.xml'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    xml_atual = subprocess.run(['su', '-c', 'cat /data/local/tmp/ui_check.xml'], capture_output=True, text=True).stdout

    node_seguro = False
    for node in xml_atual.split('<node'):
        if str_bounds in node and ('EditText' in node or 'AutoCompleteTextView' in node or 'focused="true"' in node):
            node_seguro = True
            break

    if node_seguro:
        print("[+] Tela validada de forma cirúrgica! O campo original está lá. Aplicando...")
        cx, cy = (b[0] + b[2]) // 2, (b[1] + b[3]) // 2

        subprocess.run(['su', '-c', f'input tap {cx} {cy}'])
        time.sleep(0.5)

        texto_formatado = texto.replace(' ', '%s')
        subprocess.run(['su', '-c', f"input text '{texto_formatado}'"])
        print("\n[✔] Ação HTTP concluída e segura!")
    else:
        print("\n[!] ALERTA CRÍTICO: A tela mudou radicalmente, foi rolada ou o campo desapareceu.")
        print("[!] Abortando injeção de texto por medida de segurança extrema.")

    try:
        os.remove(CAMPOS_FILE)
        print("[*] Arquivo campos_mapeados.json deletado para evitar reciclar dados antigos.")
    except Exception as e:
        print(f"[-] Erro ao tentar excluir arquivo residual: {e}")

def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--file":
        payload_path = sys.argv[2]
        print(f"[*] MODO 1 INICIADO: Lendo payload de {payload_path}")
        try:
            with open(payload_path, "r") as f:
                payload_http = json.load(f)

            cmd = payload_http.get("auto_input_cmd", {})
            id_alvo = cmd.get("id_alvo")
            texto_para_aplicar = cmd.get("texto")

            if id_alvo and texto_para_aplicar:
                aplicar_texto_com_seguranca(int(id_alvo), str(texto_para_aplicar))
            else:
                print("[-] O Payload HTTP não continha 'id_alvo' ou 'texto'.")
        except Exception as e:
            print(f"[-] Erro ao processar arquivo de payload HTTP: {e}")
        sys.exit(0)

    print("[*] MODO 2 INICIADO: Iniciando Olheiro...")
    if not check_permission():
        print("[-] Permissão 'auto_input' negada no functions.json. Abortando.")
        sys.exit(0)

    campos = obter_todos_edittexts()

    if campos:
        payload = {
            "status_autoinput": True,
            "campos_disponiveis": campos
        }
        
        os.makedirs(DATA_DIR, exist_ok=True)
        
        with open(CAMPOS_FILE, "w") as f:
            json.dump(payload, f, indent=4)
            
        if os.path.exists(CAMPOS_FILE):
            print(f"[✔] CONFIRMADO: O arquivo campos_mapeados.json foi CRIADO fisicamente!")

        print(f"[+] Tela mapeada e salva de forma cirúrgica. ID's de 1 a {len(campos)} prontos.")
    else:
        print("[-] Falha ao mapear a tela após todas as tentativas.")

if __name__ == '__main__':
    main()
