import sys
import subprocess
import json
import re
import html 

def executar_root_comando(comando):
    """Função genérica para rodar comandos via su sem esperar leitura de textos gigantes"""
    subprocess.run(['su', '-c', comando], capture_output=True)

def ler_configs_ugclone(child_parent_pairs):
    master_xml = "/data/data/com.ugcloner.xfein/shared_prefs/com.ugcloner.xfein_preferences.xml"
    temp_xml = "/data/local/tmp/ugclone_leitura_temp.xml"

    # 1. ESTRATÉGIA DE FUGA: Copia o arquivo gigante para uma pasta temporária 
    # e dá permissão. Assim o Python lê nativamente e não engasga o subprocess!
    executar_root_comando(f"cat {master_xml} > {temp_xml} && chmod 666 {temp_xml}")
    
    # 2. Leitura nativa e robusta do arquivo
    try:
        with open(temp_xml, 'r', encoding='utf-8') as f:
            xml_content = f.read()
    except Exception as e:
        return {"erro": f"Falha ao ler o arquivo: {str(e)}"}
    finally:
        # Apaga o arquivo temporário para não deixar lixo no sistema
        executar_root_comando(f"rm {temp_xml}")
    
    if not xml_content:
        return {"erro": "XML não encontrado ou vazio."}

    filhos_setup = {}
    clones_validos = 0

    for child_pkg, parent_pkg in child_parent_pairs:
        regex_child = r'<string name="clone_settings_' + re.escape(child_pkg) + r'">\s*({.*?})\s*</string>'
        regex_parent = r'<string name="clone_settings_' + re.escape(parent_pkg) + r'">\s*({.*?})\s*</string>'
        
        match_child = re.search(regex_child, xml_content, re.DOTALL)
        
        if match_child:
            # Tem chave própria
            # 3. MÁGICA: Limpa o JSON com html.unescape (converte &quot; e &amp; perfeitamente)
            config_str = html.unescape(match_child.group(1))
            
            try:
                configs_completas = json.loads(config_str)
                
                # Filtro anti-lixo
                configs_ativas = {k: v for k, v in configs_completas.items() if v is True or (isinstance(v, int) and v > 0 and k != "iconHue") or (isinstance(v, str) and v and v not in ["NO_CHANGE", "NONE", "DEFAULT", "WEB_ONLY"]) or (isinstance(v, list) and len(v) > 0)}
                
                # Remove o 'cloneNumber' individual, mantendo o 'toCloneNumber' da rede
                configs_ativas.pop("cloneNumber", None)
                
                filhos_setup[child_pkg] = configs_ativas
                clones_validos += 1
            except json.JSONDecodeError:
                filhos_setup[child_pkg] = {"erro": "JSON corrompido."}
        else:
            # Não tem chave própria. Vamos ver se o Pai tem.
            match_parent = re.search(regex_parent, xml_content, re.DOTALL)
            if match_parent:
                # O Filho herda: retorna apenas uma referência profissional e enxuta
                filhos_setup[child_pkg] = {
                    "is_inherited": True,
                    "parent_reference": parent_pkg
                }
                clones_validos += 1
            else:
                filhos_setup[child_pkg] = {"status": "Sem configurações registradas."}

    return {
        "status": "sucesso",
        "quantidade_clones_pai": clones_validos,
        "filhos_setup": filhos_setup
    }

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2 or len(args) % 2 != 0:
        print(json.dumps({"erro": "Parâmetros inválidos. Passe sempre Filho Pai Filho Pai."}, ensure_ascii=False))
        sys.exit(1)
        
    pares = [(args[i], args[i+1]) for i in range(0, len(args), 2)]
    print(json.dumps(ler_configs_ugclone(pares), indent=4, ensure_ascii=False))
