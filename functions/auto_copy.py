import sys
import time
import subprocess
import requests

if len(sys.argv) < 3:
    print("❌ Faltando IDs no comando!")
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
headers = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}

print("🔓 Preparando ambiente...")
# Limpa os logs antigos para não enviar lixo acumulado
subprocess.run('su -c "logcat -c"', shell=True, stderr=subprocess.DEVNULL)
subprocess.run("termux-wake-lock", shell=True, check=False)

def force_focus_and_read():
    """Traz o Termux pra frente, lê o texto e minimiza na velocidade da luz"""
    try:
        subprocess.run('su -c "am start -n com.termux/com.termux.app.TermuxActivity"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 0.4s é o tempo perfeito pro Android piscar a tela e liberar o texto
        time.sleep(0.4) 
        
        texto = subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        
        # Aperta o botão de voltar para esconder o Termux
        subprocess.run('su -c "input keyevent 4"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return texto
    except Exception:
        return ""

print("📋 Monitor Inteligente Iniciado!")
last_clip = force_focus_and_read()

# O SEGREDO: Python lendo o logcat ao vivo (bufsize=1) sem intermediários!
cmd = ['su', '-c', 'logcat']
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

print("⏳ Aguardando você copiar algo... (Pode testar no Google!)")

while True:
    try:
        line = process.stdout.readline()
        
        # O Python fareja qualquer menção a "clipboard" rodando no celular
        if line and "clipboard" in line.lower():
            time.sleep(0.5) # Dá meio segundo pro Android salvar o texto de verdade
            
            current = force_focus_and_read()
            
            if current and current != last_clip:
                print(f"\n📝 NOVO TEXTO: '{current}'")
                try:
                    requests.post(URL_WEBHOOK, json={"texto": current, "device_id": device_id, "guild_id": guild_id}, headers=headers, timeout=5)
                    print("✅ Enviado com sucesso!")
                    last_clip = current
                    
                    # Trava de 2 segundos para ele não piscar a tela feito doido
                    time.sleep(2) 
                except:
                    print("❌ Erro de internet.")
    except Exception:
        pass
        
    # Se o logcat fechar por algum motivo, ele reinicia sozinho
    if process.poll() is not None:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
