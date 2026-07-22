import sys
import subprocess
import json
import re

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
        return {"erro": "XML não encontrado."}

    filhos_setup = {}
    clones_validos = 0

    for child_pkg, parent_pkg in child_parent_pairs:
        # 🎯 LEITURA A LASER VIA REGEX: Pula o XML inteiro e pega só a linha que importa
        regex_child = r'<string name="clone_settings_' + re.escape(child_pkg) + r'">({.*?})</string>'
        regex_parent = r'<string name="clone_settings_' + re.escape(parent_pkg) + r'">({.*?})</string>'
        
        match = re.search(regex_child, xml_content, re.DOTALL)
        if not match:
            match = re.search(regex_parent, xml_content, re.DOTALL)
        
        if match:
            config_str_raw = match.group(1)
            # Decodifica as aspas do HTML (&quot;) para aspas de JSON (")
            config_str = config_str_raw.replace('&quot;', '"').replace('&amp;', '&')
            
            try:
                configs_completas = json.loads(config_str)
                configs_ativas = {}
                
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
                filhos_setup[child_pkg] = {"erro": "Estrutura JSON corrompida."}
        else:
            filhos_setup[child_pkg] = {"status": "Sem configurações registradas."}

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
