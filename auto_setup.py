import os
import subprocess
import json

def verificar_permissao():
    try:
        with open("Data/config.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
            # Se for True, ele instala a persistência
            return dados.get("auto_restart", True) 
    except Exception:
        return True 

def configurar_root_boot():
    if not verificar_permissao():
        print("⚠️ Permissão de auto-restart negada no config.json.")
        return

    # Diretórios padrão onde gerenciadores de Root (como Magisk) leem scripts de boot
    magisk_dir = "/data/adb/service.d"
    init_d_dir = "/system/etc/init.d"
    
    boot_dir = None
    if os.system(f"su -c '[ -d {magisk_dir} ]'") == 0:
        boot_dir = magisk_dir
    elif os.system(f"su -c '[ -d {init_d_dir} ]'") == 0:
        boot_dir = init_d_dir
        # Monta o sistema como Leitura/Escrita para conseguir injetar o arquivo
        os.system("su -c 'mount -o rw,remount /system'")
    
    if not boot_dir:
        print("❌ Pasta de boot do Root não encontrada. Verifique se o Magisk está ativo.")
        return

    script_path = os.path.join(boot_dir, "99start_hapie")
        
    # --- O SCRIPT DE BOOT ROOT ---
    # Ele espera o Android ligar 100%, carrega o ambiente do Termux e prende o bot num loop infinito.
    conteudo_sh = """#!/system/bin/sh
# Espera o sistema terminar de ligar para não dar crash sem internet
until [ $(getprop sys.boot_completed) -eq 1 ]; do
    sleep 2
done

# Cria uma rotina em segundo plano (&) para não travar o boot do Android
(
    # Ensina para o Root onde o Termux instalou o Python
    export PREFIX=/data/data/com.termux/files/usr
    export HOME=/data/data/com.termux/files/home
    export LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib
    export PATH=/data/data/com.termux/files/usr/bin:/system/bin:/system/xbin

    # Loop imortal: se fechar, reabre em 10 segundos
    while true; do
        cd $HOME/Hapiephone
        python import.py
        sleep 10
    done
) &
"""

    # Salva o arquivo temporariamente e depois move com privilégios Root
    try:
        with open("temp_boot.sh", "w", encoding="utf-8") as f:
            f.write(conteudo_sh)
        
        # Move, dá permissão de execução (755) e define o Root como dono
        os.system(f"su -c 'mv temp_boot.sh {script_path}'")
        os.system(f"su -c 'chmod 755 {script_path}'")
        os.system(f"su -c 'chown root:root {script_path}'")
        os.remove("temp_boot.sh") # Limpa o temp caso a cópia root falhe e ele fique solto
        
        print(f"✅ Sistema Imortal ativado via Root! Arquivo salvo em: {script_path}")
    except Exception as e:
        print(f"❌ Erro ao configurar boot: {e}")

if __name__ == "__main__":
    configurar_root_boot()
