import sys
import time
import subprocess
import requests

if len(sys.argv) < 3:
    print("❌ Faltando IDs no comando!")
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]

URL_WEBHOOK_COPY = "https://hapiephoneugph.vercel.app/api/copy"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"

def get_clipboard_root():
    try:
        comando = "su -c 'cmd clipboard get-text'"
        output = subprocess.check_output(comando, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        
        if "Text: " in output:
            return output.split("Text: ", 1)[1].strip()
        return output
    except Exception as e:
        print(f"⚠️ Erro ao ler teclado: {e}")
        return ""

last_clipboard = get_clipboard_root()

print(f"📋 Monitor de Teclado (Root) Iniciado!")
print(f"📱 Device: {device_id} | 🛡️ Guilda: {guild_id}")
print(f"Última coisa copiada: '{last_clipboard}'\n")
print("⏳ Pode ir lá no chat e copiar alguma coisa...")

while True:
    try:
        current_clipboard = get_clipboard_root()

        if current_clipboard and current_clipboard != last_clipboard:
            print(f"\n📝 NOVO TEXTO DETECTADO: '{current_clipboard}'")
            print("🚀 Enviando para a Vercel...")
            
            payload = {
                "texto": current_clipboard,
                "device_id": device_id,
                "guild_id": guild_id
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": AUTH_SECRET
            }

            resp = requests.post(URL_WEBHOOK_COPY, json=payload, headers=headers, timeout=5)
            
            print(f"📡 Resposta da Vercel: STATUS {resp.status_code}")
            
            if resp.status_code == 200:
                print("✅ Sucesso! O texto foi entregue ao servidor.")
                last_clipboard = current_clipboard 
                
                try:
                    with open("last_activity.txt", "w") as f:
                        f.write(str(time.time()))
                except:
                    pass
            else:
                print(f"❌ Erro! O Servidor recusou a mensagem.")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de Internet: {e}")
    except Exception as e:
        print(f"❌ Erro Desconhecido no Loop: {e}")

    time.sleep(2)
