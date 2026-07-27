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

def obter_todos_edittexts():
    subprocess.run(['su', '-c', 'uiautomator dump /data/local/tmp/ui_dump.xml'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    xml_data = subprocess.run(['su', '-c', 'cat /data/local/tmp/ui_dump.xml'], capture_output=True, text=True).stdout
    
    campos = []
    contador = 1
    
    for node in xml_data.split('<node'):
        if 'class="android.widget.EditText"' in node:
            if contador > 5:
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

                nome_base = desc or (res_id.split('/')[-1] if res_id else (text_val or "Campo Oculto"))
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
                
    return campos

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

    # Tira um novo raio-x para garantir a precisão
    subprocess.run(['su', '-c', 'uiautomator dump /data/local/tmp/ui_check.xml'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    xml_atual = subprocess.run(['su', '-c', 'cat /data/local/tmp/ui_check.xml'], capture_output=True, text=True).stdout

    # VALIDAÇÃO CIRÚRGICA: Procura o nó exato com as coordenadas E garante que ainda é um EditText
    node_seguro = False
    for node in xml_atual.split('<node'):
        if str_bounds in node and 'class="android.widget.EditText"' in node:
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

    # LIMPEZA DE RASTRO: Destrói o JSON após o uso (sucesso ou falha)
    try:
        os.remove(CAMPOS_FILE)
        print("[*] Arquivo campos_mapeados.json deletado para evitar reciclar dados antigos.")
    except Exception as e:
        print(f"[-] Erro ao tentar excluir arquivo residual: {e}")

def main():
    # MODO 1: RECEBEU ORDEM VIA HTTP (Chamado pelo import.py)
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
            else:
                print("[-] O Payload HTTP não continha 'id_alvo' ou 'texto'.")
        except Exception as e:
            print(f"[-] Erro ao processar arquivo de payload HTTP: {e}")
        sys.exit(0)

    # MODO 2: OLHEIRO DA TELA (Chamado pelo MacroDroid ao copiar/clicar)
    if not check_permission():
        sys.exit(0)

    campos = obter_todos_edittexts()
    
    if campos:
        payload = {
            "status_autoinput": True,
            "campos_disponiveis": campos
        }
        with open(CAMPOS_FILE, "w") as f:
            json.dump(payload, f, indent=4)
        print(f"[+] Tela mapeada e salva de forma cirúrgica. ID's de 1 a {len(campos)} prontos.")

if __name__ == '__main__':
    main()
