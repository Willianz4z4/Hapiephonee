import sys
import time
import subprocess
import requests
import re

if len(sys.argv) < 3:
    print("❌ IDs ausentes")
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
headers = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}

print("🚀 [FANTASMA] Robô iniciado com sucesso no nível do Sistema!")

def scan_clipboard():
    # ESTRATÉGIA 1: DUMPSYS ROOT (Ignora o Ugphone, lê direto do cérebro do Android)
    try:
        out = subprocess.check_output('dumpsys clipboard', shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
        if "Primary Clip:" in out:
            clip_block = out.split("Primary Clip:")[1]
            # Caça o texto entre aspas
            match = re.search(r'Text:\s*"(.*?)"', clip_block, re.DOTALL)
            if match: return match.group(1).strip()
            # Caça o texto sem aspas (Fallback)
            match2 = re.search(r'Text:\s*(.*?)(?=\n)', clip_block)
            if match2: return match2.group(1).strip()
    except:
        pass

    # ESTRATÉGIA 2: TERMUX API (Backup agressivo via Broadcast)
    try:
        subprocess.run('am broadcast -a com.termux.api.clipboard.get', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        out = subprocess.check_output('termux-clipboard-get', shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore').strip()
        if out: return out
    except:
        pass

    return ""

last_clipboard = scan_clipboard()
print(f"🔍 Leitura Inicial do Sistema: '{last_clipboard}'")

# Avisa a Vercel que ele assumiu o posto
try:
    requests.post(URL_WEBHOOK, json={"texto": "🚀 [SISTEMA] Robô Fantasma Vigiando a Memória!", "device_id": device_id, "guild_id": guild_id}, headers=headers, timeout=5)
except:
    pass

contador = 0
while True:
    try:
        current = scan_clipboard()
        
        if current and current != last_clipboard:
            print(f"📝 CAPTURADO: '{current}'")
            resp = requests.post(URL_WEBHOOK, json={"texto": current, "device_id": device_id, "guild_id": guild_id}, headers=headers, timeout=5)
            print(f"📡 Status Vercel: {resp.status_code}")
            
            if resp.status_code == 200:
                last_clipboard = current
                
        # Bate o ponto no log a cada 20 segundos
        contador += 1
        if contador >= 10:
            print(f"⏳ [FANTASMA] Trabalhando no escuro... (Último texto visto: '{last_clipboard[:15]}')")
            contador = 0
            
    except Exception as e:
        print(f"❌ Erro no loop: {e}")
        
    # Pausa segura para não travar o processador do Ugphone
    time.sleep(2)
