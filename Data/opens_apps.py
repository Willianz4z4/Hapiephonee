import os
import json
import subprocess
import time
import re
import argparse
import logging
import sys
from pathlib import Path

# Configuração de Logs
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Uso de caminhos modernos e seguros com pathlib
TMP_DIR = os.environ.get("TMPDIR", os.path.expanduser("~"))
SAVE_FILE = Path(TMP_DIR) / "last_opened_apps.json"

# Validação estrita de segurança para evitar Shell Injection
VALID_COMPONENT_REGEX = re.compile(r'^[a-zA-Z0-9_.\$]+/[a-zA-Z0-9_.\$]+$')

class AndroidShell:
    """Gerencia um terminal Root persistente para altíssima performance"""
    def __init__(self):
        # Tenta usar 'tsu' para preservar as variáveis de ambiente do Termux, senão usa 'su'
        su_bin = "tsu" if subprocess.call(["which", "tsu"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0 else "su"
        
        # Inicia o shell persistente via Popen
        self.process = subprocess.Popen(
            [su_bin, "-c", "sh"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
    def run(self, cmd):
        # Envia o comando e garante que o buffer seja liberado (flush)
        self.process.stdin.write(cmd + "\n")
        self.process.stdin.write("echo __EOF__\n")
        self.process.stdin.flush()
        
        output = []
        while True:
            line = self.process.stdout.readline()
            if not line or "__EOF__" in line:
                break
            output.append(line.strip())
        return "\n".join(output)
        
    def close(self):
        self.process.stdin.write("exit\n")
        self.process.stdin.flush()
        self.process.wait()

def get_currently_open_apps(shell):
    # Uso de caminhos absolutos (/system/bin/) para evitar path hijacking
    cmd = "/system/bin/dumpsys activity activities | grep -iE 'mresumedactivity|mfocusedapp|recent #0|mfocusedactivity|topresumedactivity'"
    output = shell.run(cmd)
    
    apps_to_restore = []
    
    # Regex robusto que aceita classes internas de Java (com $)
    matches = re.findall(r'([a-zA-Z0-9_]+\.[a-zA-Z0-9_.]+/[a-zA-Z0-9_$]+(?:\.[a-zA-Z0-9_$]+)*)', output)
    
    for match in matches:
        match = match.strip()
        
        # Filtro de segurança contra injeção de comandos
        if not VALID_COMPONENT_REGEX.match(match):
            continue
            
        if "com.android.systemui" not in match and "com.termux" not in match and "launcher" not in match.lower():
            apps_to_restore.append(match)
            
    # Remove duplicatas preservando a ORDEM da pilha de navegação
    return list(dict.fromkeys(apps_to_restore))

def save_state(shell):
    apps = get_currently_open_apps(shell)
    if apps:
        with open(SAVE_FILE, "w") as f:
            json.dump(apps, f)
        logging.info(f"✅ Checkpoint: {len(apps)} apps saved for restoration.")
        logging.info(f"📱 Apps: {apps}")
    else:
        logging.warning("⚠️ No foreground app detected to save.")

def restore_state(shell):
    if not SAVE_FILE.exists():
        logging.info("ℹ️ No restoration file found.")
        return

    try:
        with open(SAVE_FILE, "r") as f:
            apps = json.load(f)
        
        logging.info(f"🚀 Restoring {len(apps)} apps...")
        
        # Inverte a lista para restaurar de baixo para cima (preserva a ordem visual)
        for app in reversed(apps):
            if not VALID_COMPONENT_REGEX.match(app):
                logging.warning(f"Skipping invalid package name: {app}")
                continue
                
            logging.info(f"🔄 Opening: {app}")
            
            # Executa com -W (Espera o app abrir) e -f 0x14000000 (Limpa a UI duplicada)
            shell.run(f"/system/bin/am start -W -f 0x14000000 -n {app}")
            
        SAVE_FILE.unlink()
        logging.info("✅ Restoration complete.")
        
    except Exception as e:
        logging.error(f"❌ Restoration error: {e}")

def list_state():
    if SAVE_FILE.exists():
        try:
            with open(SAVE_FILE, "r") as f:
                apps = json.load(f)
            logging.info(f"📁 Current saved apps: {apps}")
        except json.JSONDecodeError:
            logging.error("❌ Corrupted save file.")
    else:
        logging.info("ℹ️ No apps currently saved.")

if __name__ == "__main__":
    # Interface Profissional de Linha de Comando usando argparse
    parser = argparse.ArgumentParser(description="Android App State Manager (Root)")
    parser.add_argument("--save", action="store_true", help="Capture the current state")
    parser.add_argument("--restore", action="store_true", help="Relaunch the saved apps")
    parser.add_argument("--list", action="store_true", help="View the current contents of the save file")
    parser.add_argument("--verbose", action="store_true", help="Show detailed diagnostic output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.list:
        list_state()
        sys.exit(0)

    # Se o usuário não passou argumentos válidos, exibe a ajuda
    if not (args.save or args.restore):
        parser.print_help()
        sys.exit(1)

    shell = AndroidShell()
    try:
        if args.restore:
            restore_state(shell)
        elif args.save:
            save_state(shell)
    finally:
        shell.close() # Garante que a sessão Root será fechada no final
