import sys
import time
import subprocess
import requests

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

print("🔓 Ativando bypass nível HARD (Leitura Direta de Memória IPC)...")

# Garante o Wake Lock para o Termux não dormir
try:
    subprocess.run("termux-wake-lock", shell=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except:
    pass

def get_clipboard_binder():
    """Lê a memória bruta do Binder IPC ignorando os bloqueios do Ugphone e Android 10+"""
    try:
        # 1. Bate direto na porta do Binder (Comunicação de baixo nível do Android)
        out = subprocess.check_output('su -c "service call clipboard 2"', shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
        
        if "Result: Parcel" not in out:
            # Tenta o código 1 caso a versão da API do Android no Ugphone seja diferente
            out = subprocess.check_output('su -c "service call clipboard 1"', shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
            
        if "Result: Parcel" not in out:
            return ""

        # 2. Constrói a memória RAM byte a byte a partir do HexDump
        byte_array = bytearray()
        for line in out.split('\n'):
            if ':' in line and "'" in line:
                # Pega só os blocos de memória tipo "00740068"
                hex_part = line.split(':', 1)[1].split("'")[0].strip()
                for word in hex_part.split():
                    if len(word) == 8:
                        b = bytes.fromhex(word)
                        # Inverte para Little Endian (Padrão de organização de memória RAM)
                        byte_array.extend([b[3], b[2], b[1], b[0]])

        # 3. Traduz os bytes para texto (UTF-16 LE)
        decoded_text = byte_array.decode('utf-16-le', errors='ignore')
        
        # 4. Limpa a sujeira da memória separando as strings
        valid_strings = []
        for s in decoded_text.split('\x00'):
            s = s.strip()
            # Filtra lixos de memória e foca em textos reais e imprimíveis
            if len(s) > 0 and s.isprintable():
                # Ignora metadados padrão das classes do Android
                if s not in ['android.content.ClipData', 'text/plain', 'text/html']:
                    if not s.startswith('android.') and not s.startswith('com.android'):
                        valid_strings.append(s)

        # O texto que você copiou (o payload principal) é quase sempre a última string limpa desse bloco
        if valid_strings:
            return valid_strings[-1]
            
        return ""
    except Exception:
        return ""

last_clipboard = get_clipboard_binder()

print(f"\n📋 Monitor IPC Root Iniciado com Sucesso!")
print(f"📱 Device: {device_id} | 🛡️ Guilda: {guild_id}")
print(f"Última coisa copiada: '{last_clipboard}'\n")
print("⏳ Rodando! Dumpsys e restrições do Android ignorados. Pode minimizar o Termux e ir testar!")

while True:
    try:
        current_clipboard = get_clipboard_binder()

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

    # Pausa leve
    time.sleep(2)
