import sys
import time
import subprocess
import requests
import re

# Verifica se o script principal passou as IDs corretamente
if len(sys.argv) < 3:
    print("❌ Faltando IDs no comando!")
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]

# ==========================================
# CONFIGURAÇÃO DE WEBHOOK DA VERCEL
# ==========================================
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"

print("🔓 Preparando o ambiente e ativando superpoderes absolutos...")

# Garante o Wake Lock para o Termux não dormir
try:
    subprocess.run("termux-wake-lock", shell=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except:
    pass

# 👉 A MÁGICA ACONTECE AQUI: IGNORA O TERMUX-API E LÊ A MEMÓRIA DO SISTEMA
def get_clipboard_root():
    try:
        # Puxa o estado atual do clipboard diretamente do serviço central do Android com ROOT puro
        out = subprocess.check_output('su -c "dumpsys clipboard"', shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
        
        if "Primary Clip:" not in out:
            return ""
            
        # Pega a parte de texto do serviço de transferência
        clip_block = out.split("Primary Clip:")[1]
        
        # Expressão regular para achar o texto exato com suporte a quebras de linha
        match = re.search(r'Text:\s*"(.*?)"(?=\n\s*Item|\n\s*Local State:|\n$)', clip_block, re.DOTALL)
        if match:
            return match.group(1)
            
        # Fallback caso a versão do Android não coloque aspas
        match_no_quotes = re.search(r'Text:\s*(.*?)(?=\n\s*Item|\n\s*Local State:|\n$)', clip_block, re.DOTALL)
        if match_no_quotes:
            return match_no_quotes.group(1).strip()
            
    except Exception:
        return ""
    
    return ""

last_clipboard = get_clipboard_root()

print(f"\n📋 Monitor de Teclado Global (100% ROOT DUMPSYS) Iniciado!")
print(f"📱 Device: {device_id} | 🛡️ Guilda: {guild_id}")
print(f"Última coisa copiada: '{last_clipboard}'\n")
print("⏳ Rodando! Agora o Android foi completamente bypassado. Pode minimizar!")

while True:
    try:
        # Puxa diretamente da raiz do sistema
        current_clipboard = get_clipboard_root()

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

            resp = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=5)
            
            print(f"📡 Resposta da Vercel: STATUS {resp.status_code}")
            
            if resp.status_code == 200:
                print("✅ Sucesso! O texto foi entregue ao servidor.")
                last_clipboard = current_clipboard 
                
                # Mantém o import.py sabendo que estamos vivos
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

    # Pausa de 2 segundos para manter leve
    time.sleep(2)
