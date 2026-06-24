import re
from bson.objectid import ObjectId
from Data.mongodb import db

async def check_device_update(device_id: str, reported_version: str):
    """
    Compara a versão reportada pelo celular com a versão que o banco diz que ele deveria ter.
    Retorna um dicionário indicando se ele deve atualizar (True/False) e a ação do Git.
    """
    
    # 1. Tenta buscar o dispositivo no banco
    try: busca_id = ObjectId(device_id)
    except: busca_id = device_id
    
    device = await db.devices.find_one({"_id": busca_id})
    
    if not device:
        return {"update": False}

    cfg = await db.get_bot_config()
    history = cfg.get("history", [])
    global_current = cfg.get("version", "0.18.9")

    # 2. Descobre qual é a última versão oficial (Tirando as Early Access)
    stable_versions = [v for v in history if "Early Access" not in v]
    latest_stable_entry = stable_versions[-1] if stable_versions else "0.18.9"
    
    # Extrai o número limpo e o SHA da última versão estável
    latest_stable_ver = latest_stable_entry
    latest_sha = ""
    match_latest = re.search(r"(.*?) \[(.*?)\]", latest_stable_entry)
    if match_latest:
        latest_stable_ver = match_latest.group(1).strip()
        latest_sha = match_latest.group(2).strip()

    # 3. Avalia qual versão esse celular DEVERIA ter
    is_auto = device.get("version_auto", True)
    saved_system_version = device.get("system_version", latest_stable_ver)

    if is_auto:
        # Se Auto está LIGADO, o alvo é sempre a última versão lançada
        target_version = latest_stable_ver
        target_sha = latest_sha
        
        # Garante que o banco saiba que ele foi atualizado para a última no auto
        if saved_system_version != latest_stable_ver:
            await db.devices.update_one({"_id": busca_id}, {"$set": {"system_version": latest_stable_ver}})
    else:
        # Se Auto está DESLIGADO, ele obedece a versão travada no banco (Pode ser Antiga ou Early)
        target_version = saved_system_version
        target_sha = ""
        
        # Procura o commit exato dessa versão travada no histórico
        for entry in history:
            if entry.startswith(target_version):
                match = re.search(r"\[(.*?)\]", entry)
                if match:
                    target_sha = match.group(1)
                break
        
        # Se for a versão Early Access atual rodando globalmente, pega o SHA do monitor do Git
        if "Early Access" in target_version and "Early Access" in global_current:
            target_sha = cfg.get("last_sha", "")

    # 4. A HORA DA VERDADE (MUDO? MUDO?)
    if reported_version != target_version:
        
        # Determina a ação baseada no tipo de versão
        if "Early Access" in target_version:
            # É versão de desenvolvimento! Apenas dá um git pull normal para puxar novidades
            action = "pull"
            comando_git = "git pull"
        else:
            # É uma versão estável ou um Rollback! 
            action = "reset"
            if target_sha:
                comando_git = f"git fetch --all && git reset --hard {target_sha}"
            else:
                comando_git = "git fetch --all && git reset --hard origin/main"

        return {
            "update": True,
            "action": action,
            "target_version": target_version,
            "git_command": comando_git
        }

    # Se as versões batem, ele não faz nada
    return {"update": False}
