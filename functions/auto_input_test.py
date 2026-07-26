import subprocess
import re
import time

def obter_todos_edittexts():
    print("[*] Lendo a tela do Android...")
    subprocess.run(['su', '-c', 'uiautomator dump /data/local/tmp/ui_dump.xml'], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    result = subprocess.run(['su', '-c', 'cat /data/local/tmp/ui_dump.xml'], 
                            capture_output=True, text=True)
    xml_data = result.stdout

    # Quebra o XML em partes e procura por todos os campos de texto nativos
    nodes = xml_data.split('<node')
    campos = []
    
    for node in nodes:
        if 'class="android.widget.EditText"' in node:
            # Pega as coordenadas de cada campo de texto encontrado
            match = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
            if match:
                campos.append(tuple(map(int, match.groups())))
                
    return campos

def preencher_todos():
    campos = obter_todos_edittexts()
    
    if not campos:
        print("[-] Nenhum campo de texto (EditText) encontrado nesta tela.")
        return

    print(f"[+] Uhuu! Encontramos {len(campos)} campo(s) de texto!")
    print("[*] Lembre-se de ter copiado '🔽🌟⭐Achei um campo' antes de rodar!")
    
    # Faz um loop para clicar e colar em CADA campo encontrado
    for index, bounds in enumerate(campos):
        x1, y1, x2, y2 = bounds
        centro_x = (x1 + x2) // 2
        centro_y = (y1 + y2) // 2
        
        print(f"\n -> Iniciando ataque ao campo {index + 1}...")
        print(f" -> Clicando na coordenada: X={centro_x}, Y={centro_y}")
        
        # Simula o clique no meio do campo
        subprocess.run(['su', '-c', f'input tap {centro_x} {centro_y}'])
        
        # Dá um tempinho (0.5s) para o Android focar no campo e abrir o teclado
        time.sleep(0.5) 
        
        print(" -> Colando o texto da área de transferência...")
        subprocess.run(['su', '-c', 'input keyevent 279'])
        
        # Dá um tempinho antes de ir para o próximo campo
        time.sleep(0.5)
        
    print("\n[✔] Todos os campos foram preenchidos com sucesso!")

if __name__ == '__main__':
    preencher_todos()
