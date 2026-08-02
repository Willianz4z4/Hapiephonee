import os
import subprocess

def setup_termux_tasker():
    termux_tasker_dir = os.path.expanduser("~/.termux/tasker")
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
