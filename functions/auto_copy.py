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

print("🔓 Preparando o ambiente e ativando superpoderes...")

# 👉 1. LOOP PERSISTENTE PARA GARANTIR O ROOT
# Se a permissão for negada, ele tenta de novo a cada 3 segundos até dar certo!
while True:
    print("🛡️ Solicitando ROOT para liberar leitura de teclado global...")
    try:
        # check=True faz o código acusar erro se o Root for negado
        subprocess.run('su -c "appops set com.termux READ_CLIPBOARD allow"', shell=True, check=True)
        print("✅ ROOT concedido! Bloqueio do Android desativado com sucesso.")
        break  # Sai da repetição infinita porque deu certo!
    except subprocess.CalledProcessError:
        print("❌ Permissão Root NEGADA ou falhou!")
        print("🔄 Tentando novamente em 3 segundos... (Se você recusou sem querer, aceite agora!)")
        print("⚠️ DICA: Se a janela não aparecer mais, vá no app Magisk/SuperSU e permita o Termux manualmente.")
        time.sleep(3)
    except Exception as e:
        print(f"⚠️ Erro inesperado ao pedir root: {e}")
        time.sleep(3)

# 👉 2. ATIVA O WAKE LOCK AUTOMATICAMENTE PARA O TERMUX NÃO DORMIR
try:
    subprocess.run("termux-wake-lock", shell=True, check=False)
    print("🔋 Wake Lock ativado! Processador segurando o Termux acordado.")
except Exception as e:
    print(f"⚠️ Aviso: Não foi possível ativar o wake lock automaticamente: {e}")

def get_clipboard_termux():
    """Lê o clipboard usando a API oficial do Termux (Cópia Universal)"""
    try:
        output = subprocess.check_output("termux-clipboard-get", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        return output
    except Exception:
        # Retorna vazio silenciosamente se der erro, para não poluir o terminal
        return ""

last_clipboard = get_clipboard_termux()

print(f"\n📋 Monitor de Teclado Global (Root API) Iniciado!")
print(f"📱 Device: {device_id} | 🛡️ Guilda: {guild_id}")
print(f"Última coisa copiada: '{last_clipboard}'\n")
print("⏳ Rodando em segundo plano. Pode minimizar o Termux e ir copiar suas coisas!")

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
