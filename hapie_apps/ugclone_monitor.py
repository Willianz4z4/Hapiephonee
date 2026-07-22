import sys
import subprocess
import json
import xml.etree.ElementTree as ET

def executar_root_leitura(comando):
    resultado = subprocess.run(
        ['su', '-c', comando],
        capture_output=True,
        text=True
    )
    return resultado.stdout.strip()

def ler_configs_ugclone(child_parent_pairs):
    master_xml = "/data/data/com.ugcloner.xfein/shared_prefs/com.ugcloner.xfein_preferences.xml"
    xml_content = executar_root_leitura(f"cat {master_xml} 2>/dev/null")
    
    if not xml_content or "No such file" in xml_content:
        return {"erro": "XML de preferências não encontrado."}

    try:
        root = ET.fromstring(xml_content)
    except Exception as e:
        return {"erro": f"Falha ao processar XML: {e}"}

    filhos_setup = {}
    clones_validos = 0

    for child_pkg, parent_pkg in child_parent_pairs:
        # 👑 A MÁGICA AQUI: Busca pelo filho primeiro, se falhar, busca pelo pai.
        tag_name_child = f"clone_settings_{child_pkg}"
        tag_name_parent = f"clone_settings_{parent_pkg}"
        
        config_str = None
        
        for string_tag in root.findall('string'):
            nome_tag = string_tag.get('name')
            # Prioridade 1: Nome exato do clone (com.roblox.cliena)
            if nome_tag == tag_name_child:
                config_str = string_tag.text
                break 
            # Prioridade 2: Nome do pai como backup (com.roblox.client)
            elif nome_tag == tag_name_parent and not config_str:
                config_str = string_tag.text
        
        if config_str:
            try:
                configs_completas = json.loads(config_str)
                configs_ativas = {}
                
                # Filtragem para pegar só o que o usuário alterou/ativou
                for chave, valor in configs_completas.items():
                    if valor is True:
                        configs_ativas[chave] = valor
                    elif isinstance(valor, int) and valor > 0 and chave != "iconHue":
                        configs_ativas[chave] = valor
                    elif isinstance(valor, str) and valor and valor not in ["NO_CHANGE", "NONE", "DEFAULT", "WEB_ONLY"]:
                        configs_ativas[chave] = valor
                    elif isinstance(valor, list) and len(valor) > 0:
                        configs_ativas[chave] = valor

                filhos_setup[child_pkg] = configs_ativas
                clones_validos += 1
            except json.JSONDecodeError:
                filhos_setup[child_pkg] = {"erro": "Estrutura JSON corrompida dentro do XML."}
        else:
            filhos_setup[child_pkg] = {"status": "Sem configurações registradas no motor."}

    return {
        "status": "sucesso",
        "quantidade_clones_pai": clones_validos,
        "filhos_setup": filhos_setup
    }

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) % 2 != 0:
        print(json.dumps({"erro": "Parâmetros inválidos."}, ensure_ascii=False))
        sys.exit(1)
        
    args = sys.argv[1:]
    pares = [(args[i], args[i+1]) for i in range(0, len(args), 2)]
    
    resultado_json = ler_configs_ugclone(pares)
    print(json.dumps(resultado_json, indent=4, ensure_ascii=False))
