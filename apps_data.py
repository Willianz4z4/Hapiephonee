import os
import re
import json
import subprocess
import tarfile

# ==========================================
# FUNÇÃO ANTIGA: Injeção de Data (tar.gz)
# Usada para outros apps (jogos normais)
# ==========================================
def deploy_tar_payload(tar_path, dest_dir="/data/data/"):
    """
    Extrai um arquivo .tar.gz diretamente no diretório especificado.
    Ideal para injetar pastas inteiras de outros aplicativos.
    """
    print(f"[+] Iniciando extração padrão do payload: {tar_path}")
    if not os.path.exists(tar_path):
        print(f"[-] Erro: Arquivo {tar_path} não encontrado.")
        return False
        
    try:
        # Extrai o arquivo preservando a estrutura
        subprocess.run(f"tar -xzf {tar_path} -C {dest_dir}", shell=True, check=True)
        print(f"[+] Payload extraído com sucesso em {dest_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] Erro ao extrair tar.gz: {e}")
        return False


# ==========================================
# FUNÇÃO NOVA: Injeção Inteligente UGClone
# Usada apenas para gerenciar os Clones
# ==========================================
def add_ugclone_config(target_pkg, settings_dict):
    """
    Injeta ou atualiza a configuração de um app específico dentro do XML do UGClone,
    preservando todos os outros apps que já estão configurados.
    """
    print(f"[+] Processando configuração inteligente para: {target_pkg}")
    ugcloner_pkg = "com.ugcloner.xfein"
    xml_path = f"/data/data/{ugcloner_pkg}/shared_prefs/{ugcloner_pkg}_preferences.xml"
    
    # 1. Converte o dicionário Python para o formato JSON compacto exigido pelo UGClone
    settings_json = json.dumps(settings_dict, separators=(',', ':'))
    settings_json_escaped = settings_json.replace('"', '&quot;')
    
    # 2. Verifica se o arquivo mestre do UGClone existe
    if not os.path.exists(xml_path):
        print(f"[-] Erro: Arquivo {xml_path} não encontrado. O UGClone foi instalado e aberto?")
        return False
        
    # 3. Lê o arquivo atual inteiro
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"[-] Erro ao ler XML do UGClone: {e}")
        return False
        
    # 4. Prepara as tags (Regex para buscar se o app já existe)
    tag_name = f"clone_settings_{target_pkg}"
    tag_pattern = f'<string name="{tag_name}">.*?</string>'
    new_tag = f'<string name="{tag_name}">{settings_json_escaped}</string>'
    
    if re.search(tag_pattern, content):
        # ATUALIZA: Se o pacote já existe, sobrescreve só a linha dele
        content = re.sub(tag_pattern, new_tag, content)
        print(f"[+] Configuração de {target_pkg} ATUALIZADA no XML.")
    else:
        # ADICIONA: Se não existe, coloca a nova tag no final antes do </map>
        content = content.replace('</map>', f'    {new_tag}\n</map>')
        print(f"[+] Nova configuração de {target_pkg} ADICIONADA no XML.")
        
    # 5. Salva o arquivo modificado
    try:
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"[-] Erro ao salvar XML modificado: {e}")
        return False
        
    # 6. Restaura permissões dinâmicas do Android para evitar Crash (Root)
    try:
        # Pega o UID atual do UGClone
        uid_cmd = subprocess.check_output(f"stat -c '%u' {xml_path}", shell=True)
        uid = int(uid_cmd.decode().strip())
        
        # Aplica o dono e o contexto de segurança correto
        os.chown(xml_path, uid, uid)
        subprocess.run(f"restorecon {xml_path}", shell=True, check=False)
        print("[+] Permissões restauradas.")
    except Exception as e:
        print(f"[-] Aviso ao arrumar permissões: {e}")
        
    # 7. Força a parada do UGClone para ele carregar as mudanças no próximo inicio
    subprocess.run(f"am force-stop {ugcloner_pkg}", shell=True, check=False)
    print(f"[+] {ugcloner_pkg} reiniciado. Injeção concluída!")
    
    return True


# ==========================================
# TESTE (Remova ou adapte quando for plugar no seu Bot)
# ==========================================
if __name__ == "__main__":
    # Exemplo de como você vai chamar a nova função quando o bot mandar o comando:
    configs = {
        "hideRoot": True,
        "hideImei": True,
        "hideWifiInfo": True,
        "changeAndroidId": True,
        "randomAndroidId": True
    }
    
    # Adicionando o Roblox no UGClone
    add_ugclone_config("com.roblox.client", configs)
    
    # Se fosse extrair um arquivo de data normal para outro app, você usaria:
    # deploy_tar_payload("/sdcard/data_do_jogo.tar.gz")
