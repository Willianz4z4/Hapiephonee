import sys
import subprocess
import json
import re

def executar_root_leitura(comando):
    resultado = subprocess.run(['su', '-c', comando], capture_output=True, text=True)
    return resultado.stdout.strip()

def ler_configs_ugclone(child_parent_pairs):
    master_xml = "/data/data/com.ugcloner.xfein/shared_prefs/com.ugcloner.xfein_preferences.xml"
    xml_content = executar_root_leitura(f"cat {master_xml} 2>/dev/null")
    
    if not xml_content or "No such file" in xml_content:
        return {"erro": "XML não encontrado."}

    filhos_setup = {}
    clones_validos = 0

    for child_pkg, parent_pkg in child_parent_pairs:
        regex_child = r'<string name="clone_settings_' + re.escape(child_pkg) + r'">\s*({.*?})\s*</string>'
        regex_parent = r'<string name="clone_settings_' + re.escape(parent_pkg) + r'">\s*({.*?})\s*</string>'
        
        match_child = re.search(regex_child, xml_content, re.DOTALL)
        
        if match_child:
            # Tem chave própria (Pode ser o Pai Mestre ou um Filho com config customizada)
            config_str = match_child.group(1).replace('&quot;', '"').replace('&amp;', '&')
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
        print(json.dumps({"erro": "Parâmetros inválidos."}, ensure_ascii=False))
        sys.exit(1)
        
    pares = [(args[i], args[i+1]) for i in range(0, len(args), 2)]
    print(json.dumps(ler_configs_ugclone(pares), indent=4, ensure_ascii=False))
