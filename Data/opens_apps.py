import subprocess
import shutil
import re

class AndroidShell:
    def __init__(self):
        su_bin = "tsu" if shutil.which("tsu") else "su"
        self.process = subprocess.Popen(
            [su_bin, "-c", "sh"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1
        )
        
    def run(self, cmd):
        try:
            self.process.stdin.write(cmd + "\n")
            self.process.stdin.write("echo __EOF__\n")
            self.process.stdin.flush()
        except: return ""
        
        output = []
        try:
            while True:
                line = self.process.stdout.readline()
                if not line or "__EOF__" in line: break
                output.append(line.strip())
        except: pass
        return "\n".join(output)
        
    def close(self):
        try:
            self.process.kill()
        except: pass

shell = AndroidShell()

print("\n--- 🔍 1. TESTE DE ATIVIDADES (ACTIVITY) ---")
print(shell.run("/system/bin/dumpsys activity activities | grep -iE 'resumed|focused|paused'"))

print("\n--- 🔍 2. TESTE DE JANELAS (WINDOW) ---")
print(shell.run("/system/bin/dumpsys window windows | grep -iE 'mcurrentfocus|mfocusedapp'"))

print("\n--- 🔍 3. TESTE DE RECENTES (HISTÓRICO) ---")
print(shell.run("/system/bin/dumpsys activity recents | grep -i 'realactivity' | head -n 5"))

shell.close()
print("\n✅ Fim do diagnóstico.")
