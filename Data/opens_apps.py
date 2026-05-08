import subprocess

def run_su(cmd):
    # O método mais bruto e garantido de rodar comandos Root
    return subprocess.getoutput(f"su -c '{cmd}'")

print("\n--- 🔍 1. TESTE BRUTO (ACTIVITY) ---")
print(run_su("dumpsys activity activities | grep -iE 'resumed|focused|paused'"))

print("\n--- 🔍 2. TESTE BRUTO (WINDOW) ---")
print(run_su("dumpsys window windows | grep -iE 'mcurrentfocus|mfocusedapp'"))

print("\n--- 🔍 3. TESTE BRUTO (HISTÓRICO) ---")
print(run_su("dumpsys activity recents | grep -i 'realactivity' | head -n 5"))

print("\n✅ Fim do diagnóstico.")
