import json
import os
import time
import ugclone_setup

ARQUIVO_ORDENS = "../Data/ordens.json"
ARQUIVO_STATUS = "../Data/status_ugclone.json"

def carregar_ordens_maximas():
    caminho = os.path.join(os.path.dirname(__file__), ARQUIVO_ORDENS)
    if not os.path.exists(caminho):
        return []
    
    try:
        with open(caminho, 'r') as f:
            dados = json.load(f)
            todas_ordens = dados.get("ordens_pendentes", [])
            return [o for o in todas_ordens if o.get("nivel") == "importante_max"]
    except json.JSONDecodeError:
        return []

def remover_ordem_concluida(id_ordem):
    caminho = os.path.join(os.path.dirname(__file__), ARQUIVO_ORDENS)
    try:
        with open(caminho, 'r') as f:
            dados = json.load(f)
        
        dados["ordens_pendentes"] = [o for o in dados.get("ordens_pendentes", []) if o.get("id") != id_ordem]
        
        with open(caminho, 'w') as f:
            json.dump(dados, f, indent=4)
    except Exception as e:
        print(f"⚠️ Erro ao remover ordem concluída: {e}")

def iniciar_vigilancia():
    print("🧠 Gerenciador Passivo iniciado. Aguardando ordens 'importante_max'...")
    
    while True:
        ordens_maximas = carregar_ordens_maximas()
        
        for ordem in ordens_maximas:
            id_ordem = ordem.get("id")
            tarefa = ordem.get("tarefa")
            
            print(f"\n🚨 ALERTA: Recebida ordem máxima [{id_ordem}] -> Tarefa: {tarefa}")
            print("🚀 Assumindo controle da tela imediatamente!")
            
            sucesso = False
            if tarefa in ["clone_install", "update"]:
                sucesso = ugclone_setup.executar_ordem(modo=tarefa)
            else:
                print(f"❓ Tarefa desconhecida para o nível máximo: {tarefa}")
                sucesso = True 
            
            if sucesso:
                print(f"🧹 Removendo ordem [{id_ordem}] da fila...")
                remover_ordem_concluida(id_ordem)
            else:
                print(f"❌ A ordem [{id_ordem}] falhou. Tentando novamente mais tarde.")
                time.sleep(10)

        time.sleep(5)

if __name__ == "__main__":
    iniciar_vigilancia()
