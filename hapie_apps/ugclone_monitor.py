import sys
import subprocess
import json
import xml.etree.ElementTree as ET

def executar_root_leitura(comando):
    """Executa um comando root silencioso apenas para leitura e retorna a saída."""
    resultado = subprocess.run(
        ['su', '-c', comando],
        capture_output=True,
        text=True
    )
    return resultado.stdout.strip()

def ler_configs_ugclone(pacotes_filhos):
    """Lê o XML do UGClone e extrai as configurações ativas dos filhos informados."""
    master_xml = "/data/data/com.ugcloner.xfein/shared_prefs/com.ugcloner.xfein_preferences.xml"
    
    # Leitura pura, sem modificação
    xml_content = executar_root_leitura(f"cat {master_xml} 2>/dev/null")
    
    if not xml_content or "No such file" in xml_content:
        return {"erro": "Arquivo de preferências do motor UGClone não encontrado no sistema."}

    try:
        root = ET.fromstring(xml_content)
    except Exception as e:
        return {"erro": f"Falha ao processar a estrutura XML: {e}"}

    filhos_setup = {}
    clones_validos = 0

    for filho in pacotes_filhos:
        tag_name = f"clone_settings_{filho}"
        config_str = None
        
        # Busca a tag exata do pacote filho no XML
        for string_tag in root.findall('string'):
            if string_tag.get('name') == tag_name:
                config_str = string_tag.text
                break
        
        if config_str:
            try:
                configs_completas = json.loads(config_str)
                configs_ativas = {}
                
                # Filtragem inteligente: Pega apenas o que foi ativado (True) ou customizado
                for chave, valor in configs_completas.items():
                    if valor is True:
                        configs_ativas[chave] = valor
                    elif isinstance(valor, int) and valor > 0 and chave != "iconHue":
                        configs_ativas[chave] = valor
                    elif isinstance(valor, str) and valor and valor not in ["NO_CHANGE", "NONE", "DEFAULT", "WEB_ONLY"]:
                        configs_ativas[chave] = valor
                    elif isinstance(valor, list) and len(valor) > 0:
                        configs_ativas[chave] = valor

                filhos_setup[filho] = configs_ativas
                clones_validos += 1
            except json.JSONDecodeError:
                filhos_setup[filho] = {"erro": "Estrutura JSON corrompida dentro do XML."}
        else:
            filhos_setup[filho] = {"status": "Sem configurações registradas no motor."}

    # Retorna o pacote completo e mastigado para o bot processar e atualizar o banco
    return {
        "status": "sucesso",
        "quantidade_clones_pai": clones_validos,
        "filhos_setup": filhos_setup
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"erro": "Nenhum pacote filho foi passado como argumento."}, ensure_ascii=False))
        sys.exit(1)
        
    # Pega todos os argumentos passados após o nome do script
    filhos_solicitados = sys.argv[1:]
    
    # Processa e imprime o resultado como um JSON puro para o bot capturar
    resultado_json = ler_configs_ugclone(filhos_solicitados)
    print(json.dumps(resultado_json, indent=4, ensure_ascii=False))
