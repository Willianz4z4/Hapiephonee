import subprocess
import re
import time

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
    print("[*] Iniciando o modo CAÇADOR! (Pressione CTRL + C para parar)")
    print("[*] O script vai ler a tela a cada 2 segundos procurando alvos...")
    
    # Memória para não floodar o mesmo campo repetidas vezes
    campos_ignorados = set() 
    
    while True:
        campos = obter_todos_edittexts()
        
        # Se você mudou para uma tela sem campos (ex: Tela Inicial), 
        # nós limpamos a memória. Assim, se você voltar no app de antes, ele cola de novo!
        if not campos:
            campos_ignorados.clear()
            
        for bounds in campos:
            # Só ataca se for um campo novo que ainda não preenchemos nesta tela
            if bounds not in campos_ignorados:
                x1, y1, x2, y2 = bounds
                centro_x = (x1 + x2) // 2
                centro_y = (y1 + y2) // 2
                
                print(f"\n[!] NOVO ALVO ENCONTRADO: {bounds}")
                print(" -> Clicando e colando...")
                
                subprocess.run(['su', '-c', f'input tap {centro_x} {centro_y}'])
                time.sleep(0.5) 
                subprocess.run(['su', '-c', 'input keyevent 279'])
                time.sleep(0.5)
                
                # Registra na memória que esse já foi
                campos_ignorados.add(bounds)
        
        # Pausa de 2 segundos antes de tirar o próximo raio-x
        time.sleep(2)

if __name__ == '__main__':
    try:
        cacador_de_campos()
    except KeyboardInterrupt:
        # Se você apertar CTRL + C, ele encerra de forma limpa
        print("\n[!] Caçada encerrada pelo usuário. Bom descanso!")
