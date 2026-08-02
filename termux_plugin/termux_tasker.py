import os
import subprocess

def setup_termux_tasker():
    # 1. Libera a permissão de segurança do Termux para o MacroDroid
    termux_dir = os.path.expanduser("~/.termux")
    os.makedirs(termux_dir, exist_ok=True)
    properties_file = os.path.join(termux_dir, "termux.properties")
    
    try:
        with open(properties_file, "a+", encoding="utf-8") as f:
            f.seek(0)
            content = f.read()
            if "allow-external-apps = true" not in content:
                f.write("\nallow-external-apps = true\n")
    except:
        pass

    # 2. Cria a pasta do Tasker e o script de gatilho
    termux_tasker_dir = os.path.join(termux_dir, "tasker")
    trigger_script_path = os.path.join(termux_tasker_dir, "trigger_copy.sh")

    sh_content = """#!/data/data/com.termux/files/usr/bin/sh
/data/data/com.termux/files/usr/bin/python /data/data/com.termux/files/home/Hapiephonee/functions/auto_copy.py "$1" "$2"
"""

    os.makedirs(termux_tasker_dir, exist_ok=True)

    with open(trigger_script_path, "w", encoding="utf-8") as f:
        f.write(sh_content)

    try:
        subprocess.run(["chmod", "+x", trigger_script_path], check=True)
    except:
        pass

if __name__ == "__main__":
    setup_termux_tasker()
