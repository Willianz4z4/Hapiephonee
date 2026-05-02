import sys
import time
import subprocess
import requests

if len(sys.argv) < 3:
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
headers = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}

subprocess.run("termux-wake-lock", shell=True, check=False)

def force_focus_and_read():
    """Traz o Termux pra frente rápido, rouba o texto e volta pro jogo"""
    try:
        # 1. Puxa pra tela (Brought to front)
        subprocess.run('su -c "am start --activity-brought-to-front com.termux/.TermuxActivity" 2>/dev/null', shell=True)
        time.sleep(0.3) # Tempo pro Android liberar o clipboard pro Termux
        
        # 2. Lê o texto
        texto = subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        
        # 3. Minimiza (Aperta o botão Voltar do celular)
        subprocess.run('su -c "input keyevent 4" 2>/dev/null', shell=True)
        
        return texto if texto and texto != "null" else ""
    except Exception:
        return ""

# Avisa a Vercel que o robô ligou
try:
    requests.post(URL_WEBHOOK, json={"texto": "⚡ Módulo Auto-Focus Ativado!", "device_id": device_id, "guild_id": guild_id}, headers=headers, timeout=5)
except:
    pass

last_clip = force_focus_and_read()

# Limpa logs antigos para não pegar lixo e inicia o vigilante
subprocess.run('su -c "logcat -c" 2>/dev/null', shell=True)
cmd_vigia = 'su -c "logcat | grep -i clipboard"'
process = subprocess.Popen(cmd_vigia, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

while True:
    # Fica lendo as ações do sistema Android infinitamente
    line = process.stdout.readline()
    
    if line:
        # Opa! O sistema registrou que alguém copiou algo. Hora do bote:
        time.sleep(0.5) 
        current = force_focus_and_read()
        
        if current and current != last_clip:
            try:
                r = requests.post(URL_WEBHOOK, json={"texto": current, "device_id": device_id, "guild_id": guild_id}, headers=headers, timeout=5)
                if r.status_code == 200:
                    last_clip = current
                    try:
                        with open("last_activity.txt", "w") as f:
                            f.write(str(time.time()))
                    except:
                        pass
            except:
                pass
                
    # Se o logcat fechar por algum motivo, ele reinicia o processo
    if process.poll() is not None:
        process = subprocess.Popen(cmd_vigia, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
