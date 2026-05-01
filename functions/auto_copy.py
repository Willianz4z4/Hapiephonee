import sys
import time
import subprocess
import requests

# Verifica se os IDs foram passados
if len(sys.argv) < 3:
    print("❌ Faltando IDs no comando!")
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
headers = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}

print("🔓 Preparando ambiente e limpando cache...")

# Limpa o Logcat para não pegar eventos de cópias antigas
subprocess.run('su -c "logcat -c"', shell=True, stderr=subprocess.DEVNULL)
# Garante que o Termux não durma
subprocess.run("termux-wake-lock", shell=True, check=False)

def force_focus_and_read():
    """Traz o Termux pra frente num piscar de olhos, lê o texto e fecha"""
    try:
        # Comando oficial e à prova de falhas para chamar a janela do Termux:
        subprocess.run('su -c "am start -n com.termux/com.termux.app.TermuxActivity"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Pausa cirúrgica de 0.3s (0.1 é muito rápido, o Android pode não dar o foco a tempo)
        time.sleep(0.3)
        
        # Puxa o texto da área de transferência
        texto = subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        
        # Aperta a tecla "Voltar" (keyevent 4) para esconder o Termux imediatamente
        subprocess.run('su -c "input keyevent 4"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return texto
    except Exception as e:
        return ""

print("📋 Monitor Inteligente de Logcat Iniciado!")
last_clip = force_focus_and_read()

# Fica escutando as entranhas do Android aguardando alguém copiar algo
cmd = 'su -c "logcat -b events | grep -i CLIPBOARD_CHANGED"'
process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

print("⏳ Rodando invisível. Só vou piscar a tela quando você copiar alguma coisa!")

while True:
    # Fica travado nesta linha até o Logcat avisar: "Opa, copiaram algo!"
    line = process.stdout.readline()
    
    if line:
        # Dá um tempinho extra de 0.5s pro Android salvar o texto de vez na memória do celular
        time.sleep(0.5) 
        
        # Dispara o flash-open
        current = force_focus_and_read()
        
        # Se capturou algo novo, envia!
        if current and current != last_clip:
            print(f"\n📝 NOVO TEXTO DETECTADO: '{current}'")
            print("🚀 Enviando para a Vercel...")
            
            try:
                resp = requests.post(URL_WEBHOOK, json={"texto": current, "device_id": device_id, "guild_id": guild_id}, headers=headers, timeout=5)
                
                if resp.status_code == 200:
                    print("✅ Sucesso! O texto foi entregue.")
                    last_clip = current
                    
                    # Salva que o script está vivo (ping)
                    try:
                        with open("last_activity.txt", "w") as f:
                            f.write(str(time.time()))
                    except:
                        pass
                else:
                    print(f"❌ Erro do Servidor: {resp.status_code}")
            except Exception as e:
                print(f"❌ Falha de Internet: {e}")
    
    # Sistema de proteção: Se o comando do logcat morrer do nada, ele reinicia automaticamente
    if process.poll() is not None:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
