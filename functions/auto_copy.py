import sys
import time
import subprocess
import requests
import os

# --- CONFIGURAÇÕES ---
if len(sys.argv) < 3:
    print("Uso: python script.py DEVICE_ID GUILD_ID")
    sys.exit(1)

device_id = sys.argv[1]
guild_id = sys.argv[2]
URL_WEBHOOK = "https://hapiephoneugph.vercel.app/api/webhook"
AUTH_SECRET = "ugphoneoficialbrasil13willianz4z4oof$$$pitucho13"
headers = {"Content-Type": "application/json", "Authorization": AUTH_SECRET}

# --- FUNÇÕES DE BYPASS (ROOT) ---

def apply_system_bypass():
    """Força a abertura das travas de segurança do Android e do UgPhone"""
    print("🔓 Aplicando Bypass de Sistema...")
    cmds = [
        # Permite leitura em background (Android 10+)
        "device_config put device_config_inf_dest_clipboard_allow_background_read true",
        # Dá permissão total ao Termux no sistema
        "appops set com.termux SYSTEM_ALERT_WINDOW allow",
        "appops set com.termux READ_CLIPBOARD allow",
        # Evita que o Android 'congele' o processo no fundo
        "dumpsys deviceidle whitelist +com.termux",
        # Tenta desativar restrições do SELinux (Modo Permissivo)
        "setenforce 0"
    ]
    for c in cmds:
        subprocess.run(f"su -c '{c}'", shell=True, stderr=subprocess.DEVNULL)

def get_clip_low_level():
    """Lê o clipboard direto do Service Manager (Bypassa o bloqueio de foco)"""
    try:
        # Tenta a chamada direta ao Binder (mais poderosa que a API comum)
        # O awk limpa a saída hex para pegar apenas o texto entre aspas
        cmd = "su -c 'service call clipboard 2 s16 com.android.shell | awk -F \"\\\"\" \"{print $2}\" | tr -d \"\\n\"'"
        res = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        
        # Se o service call falhar ou vir vazio, tenta o comando de sistema secundário
        if not res or "Result: Parcel" in res or res == "null":
            res = subprocess.check_output("su -c 'cmd clipboard get-text'", shell=True).decode('utf-8').strip()
        
        return res
    except:
        return ""

# --- LOOP PRINCIPAL (POLLING AGRESSIVO) ---

def main():
    apply_system_bypass()
    
    last_clip = get_clip_low_level()
    print(f"🚀 Monitoramento ativo no Dispositivo: {device_id}")
    print("👀 Aguardando cópia no Google ou qualquer App...")

    while True:
        try:
            # No UgPhone, não esperamos o sistema avisar (Logcat). 
            # Nós perguntamos diretamente o que tem no clipboard.
            current = get_clip_low_level()

            if current and current != last_clip:
                # Se o texto mudou, enviamos imediatamente
                print(f"✨ Novo texto detectado: {current[:30]}...")
                
                payload = {
                    "texto": current, 
                    "device_id": device_id, 
                    "guild_id": guild_id
                }
                
                response = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    print("✅ Enviado com sucesso para o painel.")
                else:
                    print(f"❌ Erro no envio: {response.status_code}")
                
                last_clip = current

            # Intervalo de 0.7s é o 'sweet spot' para não pesar o CPU e não perder o timing da cópia
            time.sleep(0.7)

        except KeyboardInterrupt:
            print("\n🛑 Encerrando...")
            sys.exit(0)
        except Exception as e:
            # Silencia erros de rede ou sistema para o script não parar
            time.sleep(2)
            continue

if __name__ == "__main__":
    main()
