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

    # 2. Cria a pasta do Tasker
    termux_tasker_dir = os.path.join(termux_dir, "tasker")
    os.makedirs(termux_tasker_dir, exist_ok=True)

    # 3. Cria o script de gatilho do Auto Copy
    trigger_copy_path = os.path.join(termux_tasker_dir, "trigger_copy.sh")
    copy_sh_content = """#!/data/data/com.termux/files/usr/bin/sh
/data/data/com.termux/files/usr/bin/python /data/data/com.termux/files/home/Hapiephonee/functions/auto_copy.py "$1" "$2"
"""
    with open(trigger_copy_path, "w", encoding="utf-8") as f:
        f.write(copy_sh_content)

    # 4. Cria o script de gatilho do Auto Input (Raio-X / Visão Direta)
    trigger_input_path = os.path.join(termux_tasker_dir, "trigger_input.sh")
    input_sh_content = """#!/data/data/com.termux/files/usr/bin/sh
/data/data/com.termux/files/usr/bin/python /data/data/com.termux/files/home/Hapiephonee/functions/auto_input.py "$1"
"""
    with open(trigger_input_path, "w", encoding="utf-8") as f:
        f.write(input_sh_content)

    # 5. Dá permissão de execução para os dois gatilhos
    try:
        subprocess.run(["chmod", "+x", trigger_copy_path, trigger_input_path], check=True)
        print("✅ Gatilhos do Termux Tasker criados com sucesso!")
    except:
        pass

if __name__ == "__main__":
    setup_termux_tasker()
