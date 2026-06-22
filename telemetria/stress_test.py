import multiprocessing
import time
import os
import sys

def fritar_cpu():
    """Loop infinito de ponto flutuante para cravam o uso do núcleo em 100%"""
    while True:
        # Matemática inútil, mas extremamente pesada para o processador
        _ = 3.14159265358979323846 ** 2.71828182845904523536

def devorar_ram():
    """Aloca blocos gigantes de strings para forçar o swap e uso extremo de RAM"""
    vazamento = []
    try:
        while True:
            # Adiciona blocos de 50MB na memória repetidamente
            vazamento.append(' ' * (50 * 1024 * 1024)) 
            time.sleep(0.5) # Pausa leve para não ser morto pelo Android instantaneamente
    except MemoryError:
        # Se encher tudo, fica segurando a memória até o script ser cancelado
        while True:
            time.sleep(1)

if __name__ == '__main__':
    os.system("clear" if os.name == "posix" else "cls")
    print("🔥 INICIANDO TESTE DE ESTRESSE MÁXIMO (DOOMSDAY) 🔥")
    print("⚠️ O sistema vai ficar EXTREMAMENTE lento. Para cancelar, pressione CTRL+C!\n")
    
    # Identifica o poder da máquina
    nucleos = multiprocessing.cpu_count()
    print(f"🚀 Detectados {nucleos} núcleos de CPU. Preparando {nucleos} ogivas...")
    
    processos = []
    
    # 1. Ataca o Processador
    for i in range(nucleos):
        p = multiprocessing.Process(target=fritar_cpu)
        p.start()
        processos.append(p)
        print(f"   [+] Núcleo {i+1} fritando a 100%...")
        
    # 2. Ataca a Memória RAM
    print("\n🧠 Lançando devorador de Memória RAM...")
    p_ram = multiprocessing.Process(target=devorar_ram)
    p_ram.start()
    processos.append(p_ram)
    
    print("\n⏳ CAOS INSTAURADO! Vá para outro terminal e rode: python telemetria/sensores.py")
    
    try:
        # Mantém o script vivo e a vigiar
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 SINAL DE ABORTO RECEBIDO! Desligando os motores...")
        for p in processos:
            p.terminate()
        print("✅ Sistema salvo. Pode respirar novamente.")
        sys.exit(0)
