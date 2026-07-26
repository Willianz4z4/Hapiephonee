import subprocess
import re
import time

def obter_coordenadas_focadas():
    print("[*] Lendo a tela do Android...")
    # Tira o raio-x da tela usando root
    subprocess.run(['su', '-c', 'uiautomator dump /data/local/tmp/ui_dump.xml'], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Lê o arquivo XML gerado (usando cat com root para evitar erro de permissão)
    result = subprocess.run(['su', '-c', 'cat /data/local/tmp/ui_dump.xml'], 
                            capture_output=True, text=True)
    xml_data = result.stdout

    # Separa os elementos e procura quem está com focused="true"
    nodes = xml_data.split('<node')
    for node in nodes:
        if 'focused="true"' in node:
            # Extrai os números do bounds="[x1,y1][x2,y2]"
            match = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
            if match:
                return tuple(map(int, match.groups()))
    return None

def colar_texto():
    bounds = obter_coordenadas_focadas()
    
    if bounds:
        x1, y1, x2, y2 = bounds
        # Calcula o meio exato do campo
        centro_x = (x1 + x2) // 2
        centro_y = (y1 + y2) // 2
        
        print(f"[+] Alvo focado encontrado nas coordenadas: {bounds}")
        print(f"[+] Clicando no centro: X={centro_x}, Y={centro_y}")
        
        # Simula um toque no centro para garantir que o cursor está lá
        subprocess.run(['su', '-c', f'input tap {centro_x} {centro_y}'])
        time.sleep(0.2)
        
        print("[+] Colando texto da área de transferência...")
        # O keyevent 279 é o comando nativo do Android para "Colar" (Paste)
        subprocess.run(['su', '-c', 'input keyevent 279'])
        print("[✔] Feito!")
    else:
        print("[-] Nenhum campo de texto focado foi encontrado na tela.")

if __name__ == '__main__':
    colar_texto()
