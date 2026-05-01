import sys
import time
import subprocess
import requests
import os

# 1. VERIFICAÇÃO DE ARGUMENTOS
if len(sys.argv) < 3:
    print("❌ Faltando IDs no comando! Use: python copy.py DEVICE_ID GUILD_ID")
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]

URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"

# 2. CONFIGURAÇÃO DE ALTA PRIORIDADE (ROOT)
def prioridade_maxima():
    try:
        # Pega o ID do processo atual (este script)
        pid = os.getpid()
        # Diz ao Android: "Não mate este processo mesmo que falte memória RAM" (-1000 é prioridade total)
        subprocess.run(f'su -c "echo -1000 > /proc/{pid}/oom_score_adj"', shell=True)
        # Libera as APIs ocultas do Android
        subprocess.run('su -c "settings put global hidden_api_policy 1"', shell=True)
        # Coloca o Termux na lista branca de bateria
        subprocess.run('su -c "dumpsys deviceidle whitelist +com.termux"', shell=True)
        subprocess.run('su -c "dumpsys deviceidle whitelist +com.termux.api"', shell=True)
        # Garante que o Termux não durma
        subprocess.run("termux-wake-lock", shell=True)
        print("🚀 Superpoderes ativados: Prioridade de Sistema -1000")
    except Exception as e:
        print(f"⚠️ Erro ao definir prioridade: {e}")

prioridade_maxima()

def get_clipboard():
    """Tenta ler o clipboard forçando o foco via Root"""
    try:
        # O pulo do gato: Enviamos um sinal de 'am' (Activity Manager) para acordar o serviço
        # Isso faz o Android liberar o texto para o Termux mesmo em segundo plano
        subprocess.run('su -c "am broadcast -a com.termux.api.clipboard.get"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Agora lemos o conteúdo
        output = subprocess.check_output("termux-clipboard-get", shell=True).decode('utf-8').strip()
        return output
    except:
        return ""

last_clipboard = get_clipboard()

print(f"\n✅ MONITOR ATIVO E BLINDADO")
print(f"📱 ID: {device_id} | 🛡️ Guild: {guild_id}")
print(f"📡 O script continuará rodando após minimizar o Termux.")
print("-" * 40)

# 3. LOOP PRINCIPAL
while True:
    try:
        current_clipboard = get_clipboard()

        if current_clipboard and current_clipboard != last_clipboard:
            print(f"📝 NOVO TEXTO: {current_clipboard[:30]}...")
            
            payload = {
                "texto": current_clipboard,
                "device_id": device_id,
                "guild_id": guild_id
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": AUTH_SECRET
            }

            # Envio para a Vercel
            resp = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                print(f"✅ Enviado com sucesso! (Status 200)")
                last_clipboard = current_clipboard
                # Atualiza arquivo de atividade para controle externo
                with open("last_activity.txt", "w") as f:
                    f.write(str(time.time()))
            else:
                print(f"❌ Erro no servidor: {resp.status_code}")

    except requests.exceptions.RequestException:
        # Se a internet cair, ele apenas espera e tenta de novo
        pass
    except Exception as e:
        # Log de erro silencioso para não parar o loop
        pass

    # Pausa de 2 segundos para economizar bateria e CPU do Ugphone
    time.sleep(2)
