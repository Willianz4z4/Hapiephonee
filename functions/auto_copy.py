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

print("🔓 Iniciando Módulo Auto-Copy (Background)...")

# Evita que o Termux durma
subprocess.run("termux-wake-lock", shell=True, check=False)

def get_clipboard_invisivel():
    """Usa o Root puro para ler o teclado sem abrir nenhum app (Modo Limpo)"""
    try:
        # O comando original, silenciando erros para focar só no resultado
        output = subprocess.check_output('su -c "cmd clipboard get-text"', shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        
        if output == "null" or output == "":
            return ""
            
        return output
    except Exception:
        return ""

last_clip = get_clipboard_invisivel()

print("📋 Monitor 100% Invisível Iniciado!")
print("⏳ Teste de Permissão ativo: Vá no Google e copie algo para testar.")

while True:
    try:
        current = get_clipboard_invisivel()
        
        if current and current != last_clip:
            print(f"\n📝 NOVO TEXTO CAPTURADO: '{current}'")
            try:
                requests.post(URL_WEBHOOK, json={"texto": current, "device_id": device_id, "guild_id": guild_id}, headers=headers, timeout=5)
                print("✅ Enviado com sucesso para o Webhook!")
                last_clip = current
                
                # Salva o ping de vida para o seu gerenciador
                try:
                    with open("last_activity.txt", "w") as f:
                        f.write(str(time.time()))
                except:
                    pass
            except Exception as e:
                print(f"❌ Erro de internet: {e}")
                
    except Exception as e:
        pass
        
    time.sleep(2)
