import subprocess
import re
import time

# A palavra pré-definida no código! 
# (O %s substitui o espaço. Emojis foram removidos para o Android não dar erro)
TEXTO_ALVO = "Achei%sum%scampo"

def obter_todos_edittexts():
    subprocess.run(['su', '-c', 'uiautomator dump /data/local/tmp/ui_dump.xml'], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    result = subprocess.run(['su', '-c', 'cat /data/local/tmp/ui_dump.xml'], 
                            capture_output=True, text=True)
    xml_data = result.stdout

    nodes = xml_data.split('<node')
    campos = []
    
    for node in nodes:
        if 'class="android.widget.EditText"' in node:
            match = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
            if match:
                campos.append(tuple(map(int, match.groups())))
                
    return campos

def cacador_de_campos():
    texto_limpo = TEXTO_ALVO.replace('%s', ' ')
    print(f"[*] Iniciando o CAÇADOR! Texto na agulha: '{texto_limpo}'")
    print("[*] Pressione CTRL + C para parar.")
    
    campos_ignorados = set() 
    
    while True:
        campos = obter_todos_edittexts()
        
        if not campos:
            campos_ignorados.clear()
            
        # O script passa por TODOS os campos encontrados na tela
        for bounds in campos:
            if bounds not in campos_ignorados:
                x1, y1, x2, y2 = bounds
                centro_x = (x1 + x2) // 2
                centro_y = (y1 + y2) // 2
                
                print(f"\n[!] Campo detectado na coordenada: {bounds}")
                print(" -> Clicando no alvo...")
                subprocess.run(['su', '-c', f'input tap {centro_x} {centro_y}'])
                
                time.sleep(0.5) 
                
                print(" -> Escrevendo a palavra pré-definida...")
                # Digita o texto definido lá em cima direto no campo
                subprocess.run(['su', '-c', f'input text "{TEXTO_ALVO}"'])
                
                time.sleep(0.5)
                
                campos_ignorados.add(bounds)
        
        time.sleep(2)

if __name__ == '__main__':
    try:
        cacador_de_campos()
    except KeyboardInterrupt:
        print("\n[!] Caçada encerrada pelo usuário. Bom descanso!")
