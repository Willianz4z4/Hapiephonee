import json
import os
import sys
import time
import subprocess

# Garante que ele consiga importar o arquivo irmão na mesma pasta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ugclone_setup

# O import.py envia o caminho do payload via argumento (ex: --file ../Data/payload.json)
PAYLOAD_FILE = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "../Data/payload.json")
REPORT_ORDERS_FILE = os.path.join(os.path.dirname(PAYLOAD_FILE), "report_orders.json")

def garantir_limpeza_absoluta():
    """Mata os processos completamente antes e depois de qualquer ação."""
    print("💀 [ORQUESTRADOR] Forçando parada total do motor UGClone...")
    subprocess.run("su -c 'am force-stop com.ugcloner.xfein'", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

def processar_ordens():
    if not os.path.exists(PAYLOAD_FILE):
        print("❌ Payload não encontrado.")
        return

    try:
        with open(PAYLOAD_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("❌ Erro ao ler o Payload.")
        return

    ordens = data.get("ordens", [])
    if not ordens:
        print("💤 Nenhuma ordem tática na fila.")
        return

    # 📊 REGRA DE PRIORIDADE: Ordena do menor pro maior. Type 0 (Instalação) > Type 1 (Update)
    ordens_ordenadas = sorted(ordens, key=lambda x: x.get("type", 99))

    success_list = []
    failed_list = []

    print(f"\n🧠 [ORQUESTRADOR] Analisando fila... {len(ordens_ordenadas)} tarefas detectadas.")

    for ordem in ordens_ordenadas:
        pacote_alvo = ordem.get("package")
        tipo = ordem.get("type") # 0 = install, 1 = update

        # Traduz o código numérico para ação legível
        modo_str = "clone_install" if tipo == 0 else "update"
        
        print(f"\n" + "="*50)
        print(f"🚀 INICIANDO ORDEM: {modo_str.upper()} | PRIORIDADE: {tipo} | ALVO: {pacote_alvo}")
        print("="*50)

        # 1. Regra de Ouro: Limpa a área antes de começar
        garantir_limpeza_absoluta()

        # 2. Delega para a função especializada
        try:
            # Passa o pacote exato para o script de automação de tela
            sucesso = ugclone_setup.executar_ordem(modo=modo_str, pacote_alvo=pacote_alvo)
        except Exception as e:
            print(f"❌ Erro crítico durante a execução do setup: {e}")
            sucesso = False

        # 3. Regra de Ouro: Limpa a área após terminar
        garantir_limpeza_absoluta()

        # 4. Registra o resultado
        if sucesso:
            success_list.append(ordem)
            print(f"✅ Ordem para '{pacote_alvo}' CONCLUÍDA com sucesso.")
        else:
            failed_list.append(ordem)
            print(f"⚠️ Ordem para '{pacote_alvo}' FALHOU.")

        # Respiro do sistema para o Android assentar a memória RAM
        time.sleep(3)

    # ==========================================
    # SALVA O RELATÓRIO PARA A API COLETAR
    # ==========================================
    report = {"success": [], "failed": []}
    if os.path.exists(REPORT_ORDERS_FILE):
        try:
            with open(REPORT_ORDERS_FILE, 'r', encoding='utf-8') as f:
                report = json.load(f)
        except:
            pass

    report["success"].extend(success_list)
    report["failed"].extend(failed_list)

    with open(REPORT_ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4)

    print("\n✅ [ORQUESTRADOR] Fila encerrada. Aguardando servidor recolher o relatório.")

if __name__ == "__main__":
    processar_ordens()
