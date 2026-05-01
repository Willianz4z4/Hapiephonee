import sys
import time
import subprocess
import requests

# Verifica se o script principal passou as IDs corretamente
if len(sys.argv) < 3:
    print("❌ Faltando IDs no comando!")
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]

# ==========================================
# USANDO EXATAMENTE A MESMA URL DO IMPORT.PY
# ==========================================
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"

def get_clipboard_termux():
    """Lê o clipboard usando a API oficial do Termux (Cópia Universal)"""
    try:
        output = subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        return output
    except Exception:
        # Retorna vazio silenciosamente se der erro, para não poluir o terminal
        return ""

last_clipboard = get_clipboard_termux()

print(f"📋 Monitor de Teclado (Termux API) Iniciado!")
print(f"📱 Device: {device_id} | 🛡️ Guilda: {guild_id}")
print(f"Última coisa copiada: '{last_clipboard}'\n")
print("⏳ Rodando em segundo plano. Pode ir copiar suas coisas!")

while True:
    try:
        current_clipboard = get_clipboard_termux()

        # Se detectou texto novo e não for vazio
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

            # Manda a bala pro Servidor na MESMA rota
            resp = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=5)
            
            print(f"📡 Resposta da Vercel: STATUS {resp.status_code}")
            
            if resp.status_code == 200:
                print("✅ Sucesso! O texto foi entregue ao servidor.")
                last_clipboard = current_clipboard 
                
                # Atualiza o ping de vida pro import.py saber que o script não travou
                try:
                    with open("last_activity.txt", "w") as f:
                        f.write(str(time.time()))
                except:
                    pass
            else:
                print(f"❌ Erro! O Servidor recusou a mensagem. (Status: {resp.status_code})")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de Internet: {e}")
    except Exception as e:
        print(f"❌ Erro Desconhecido no Loop: {e}")

    # Pausa de 2 segundos para não fritar o processador do emulador
    time.sleep(2)
