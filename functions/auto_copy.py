import sys
import time
import subprocess
import requests

if len(sys.argv) < 3:
    print("⚠️ Uso: python script.py <device_id> <guild_id>")
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
headers = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}

subprocess.run("termux-wake-lock", shell=True, check=False)
print(f"🚀 Iniciando monitoramento invisível (Device: {device_id})")

def get_clipboard_invisivel():
    try:
        # subprocess.run é a forma moderna e segura no Python de rodar comandos de terminal
        result = subprocess.run(
            ['su', '-c', 'cmd clipboard get-text'], 
            capture_output=True, 
            text=True, 
            timeout=2 # Evita que o comando trave infinitamente
        )
        
        # Se o comando root falhar, ele retorna vazio, mas não trava o script
        if result.returncode != 0:
            return ""
            
        output = result.stdout.strip()
        
        if output == "null" or output == "":
            return ""
            
        return output
        
    except Exception as e:
        # Se der um erro grave, agora ele te mostra no Termux em vez de esconder
        print(f"⚠️ [Aviso] Erro ao tentar ler clipboard: {e}")
        return ""

last_clip = get_clipboard_invisivel()

while True:
    try:
        current = get_clipboard_invisivel()
        
        # Se achou texto novo e é diferente do último...
        if current and current != last_clip:
            print(f"\n📋 Novo texto detectado: '{current[:30]}...'") # Mostra os primeiros 30 caracteres
            print("🚀 Enviando para a Vercel...")
            
            try:
                resposta = requests.post(
                    URL_WEBHOOK, 
                    json={"texto": current, "device_id": device_id, "guild_id": guild_id}, 
                    headers=headers, 
                    timeout=5
                )
                
                if resposta.status_code == 200:
                    print("✅ Sucesso! Texto processado pela Vercel.")
                    last_clip = current # Só atualiza o último clip se o envio deu certo
                    
                    try:
                        with open("last_activity.txt", "w") as f:
                            f.write(str(time.time()))
                    except:
                        pass
                else:
                    print(f"❌ Vercel recusou o envio (Erro {resposta.status_code})")
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Falha de conexão com a Vercel: {e}")
                
    except Exception as e:
        print(f"⚠️ Erro no loop principal: {e}")
        
    time.sleep(2) # Pausa de 2 segundos para não fritar o processador do UgPhone
