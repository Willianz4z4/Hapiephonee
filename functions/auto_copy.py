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

# Evita que o Android mate o processo
subprocess.run("termux-wake-lock", shell=True, check=False)
print(f"🚀 Iniciando monitoramento invisível (Device: {device_id})")

def get_clipboard_invisivel():
    try:
        # PLANO A: Tenta ler com caminho absoluto do sistema (Garante que o root ache o comando)
        result = subprocess.run(
            ['su', '-c', '/system/bin/cmd clipboard get-text'], 
            capture_output=True, text=True, timeout=3
        )
        output = result.stdout.strip()
        
        # PLANO B: Se o plano A voltar vazio ou der erro, tenta usar a API do Termux
        if not output or output == "null" or "Error" in output:
            try:
                res_termux = subprocess.run(['termux-clipboard-get'], capture_output=True, text=True, timeout=2)
                output = res_termux.stdout.strip()
            except:
                pass

        if output == "null" or output == "":
            return ""
            
        return output
    except Exception as e:
        return ""

last_clip = get_clipboard_invisivel()
print(f"🔍 [DEBUG] Leitura inicial do clipboard: '{last_clip[:20]}'")

while True:
    try:
        current = get_clipboard_invisivel()
        
        if current and current != last_clip:
            print(f"\n📋 Novo texto detectado: '{current[:30]}...'")
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
                    last_clip = current 
                    try:
                        with open("last_activity.txt", "w") as f:
                            f.write(str(time.time()))
                    except:
                        pass
                else:
                    print(f"❌ Vercel recusou o envio (Erro {resposta.status_code})")
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Falha de conexão com a Vercel: {e}")
                
    except KeyboardInterrupt:
        # Se for fechado, sai de fininho sem cuspir erro na tela
        print("\n🛑 Monitoramento encerrado pelo sistema.")
        break
    except Exception as e:
        pass
        
    time.sleep(2)
