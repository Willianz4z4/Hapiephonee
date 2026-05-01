import sys
import time
import subprocess
import requests

# Verifica as IDs obrigatórias
if len(sys.argv) < 3:
    print("❌ ERRO: IDs não encontrados. Use: python nome_do_script.py DEVICE_ID GUILD_ID")
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
headers = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}

print("🛡️ Iniciando sistema com Superpoderes (Root)...")

# Configuração inicial de permissões
def setup():
    try:
        # Força a permissão de leitura de clipboard em segundo plano
        subprocess.run('su -c "appops set com.termux READ_CLIPBOARD allow"', shell=True, check=True)
        # Impede o Termux de dormir
        subprocess.run("termux-wake-lock", shell=True, check=False)
        # Limpa logs antigos
        subprocess.run('su -c "logcat -c"', shell=True, check=False)
        print("✅ Ambiente configurado com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro no setup (Root): {e}")

setup()

def force_focus_and_read():
    """Técnica Flash-Open: Abre o Termux, lê e minimiza"""
    try:
        # Tenta abrir o Termux de forma universal pelo nome do pacote
        # Se não abrir, o problema pode ser o binário 'su'
        subprocess.run('su -c "monkey -p com.termux -c android.intent.category.LAUNCHER 1"', 
                       shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Espera o app aparecer na frente (0.5s é mais seguro)
        time.sleep(0.5) 
        
        # Puxa o texto copiado
        texto = subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        
        # Manda o comando de 'Home' para minimizar tudo rapidamente
        subprocess.run('su -c "input keyevent 3"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return texto
    except Exception as e:
        print(f"⚠️ Erro ao forçar foco: {e}")
        return ""

print("📋 Aguardando detecção de cópia (Logcat Ativo)...")
last_clip = ""

# Inicia o monitoramento dos logs do sistema Android
cmd = ['su', '-c', 'logcat']
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

while True:
    try:
        line = process.stdout.readline()
        
        # Monitora palavras-chave que indicam que algo foi copiado
        if line and ("clipboard" in line.lower() or "selection" in line.lower()):
            # Pequeno delay para o Android processar a cópia
            time.sleep(0.4)
            
            print("🔔 Evento detectado! Abrindo Termux para capturar...")
            current = force_focus_and_read()
            
            if current and current != last_clip:
                print(f"📝 TEXTO CAPTURADO: {current}")
                try:
                    payload = {"texto": current, "device_id": device_id, "guild_id": guild_id}
                    resp = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=5)
                    if resp.status_code == 200:
                        print("✅ Enviado para a Vercel!")
                        last_clip = current
                except Exception as e:
                    print(f"❌ Erro de conexão: {e}")
            else:
                print("ℹ️ Texto repetido ou vazio, ignorando.")
                
    except Exception as e:
        print(f"❌ Erro no loop: {e}")
        
    # Se o processo do logcat morrer, reinicia
    if process.poll() is not None:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
