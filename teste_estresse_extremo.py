import subprocess
import time
import re
import xml.etree.ElementTree as ET
import random
import sys

def executar_root(comando):
    try:
        resultado = subprocess.check_output(f"su -c '{comando}'", shell=True, stderr=subprocess.STDOUT, text=True)
        return resultado.strip()
    except subprocess.CalledProcessError as e:
        return e.output.strip()

def clicar_no_centro(bounds):
    coords = re.findall(r'\d+', bounds)
    if len(coords) == 4:
        x1, y1, x2, y2 = map(int, coords)
        centro_x = (x1 + x2) // 2
        centro_y = (y1 + y2) // 2
        print(f"👉 Clicando no CENTRO exato: X:{centro_x} Y:{centro_y}")
        executar_root(f"input tap {centro_x} {centro_y}")
        return True
    return False

def ler_tela():
    arquivo_xml = "/data/local/tmp/tela_dump.xml"
    executar_root(f"uiautomator dump {arquivo_xml}")
    xml_content = executar_root(f"cat {arquivo_xml}")
    match = re.search(r'<\?xml.*</hierarchy>', xml_content, re.DOTALL)
    return match.group(0) if match else None

def achar_e_clicar(xml_content, atributo, valor_procurado, min_y=0):
    try:
        root = ET.fromstring(xml_content)
        for node in root.iter('node'):
            valor_node = node.attrib.get(atributo, '')
            if valor_procurado.lower() == valor_node.lower() or valor_procurado.lower() in valor_node.lower():
                bounds = node.attrib.get('bounds')
                if bounds:
                    coords = re.findall(r'\d+', bounds)
                    if len(coords) == 4:
                        _, y1, _, _ = map(int, coords)
                        if y1 < min_y:
                            continue
                        print(f"✅ Encontrou '{valor_node}'!")
                        return clicar_no_centro(bounds)
    except Exception:
        pass
    return False

def achar_botao_laranja(xml_content):
    # Nova lógica: Caça o botão mais no Canto Inferior Direito!
    try:
        root = ET.fromstring(xml_content)
        candidatos = []
        for node in root.iter('node'):
            bounds = node.attrib.get('bounds')
            texto = node.attrib.get('text', '')
            desc = node.attrib.get('content-desc', '')
            
            if bounds and not texto and not desc:
                coords = re.findall(r'\d+', bounds)
                if len(coords) == 4:
                    x1, y1, x2, y2 = map(int, coords)
                    largura = x2 - x1
                    altura = y2 - y1
                    
                    # Verifica se é um quadrado (com tolerância) e se não é um pixel perdido
                    if largura > 20 and altura > 20 and abs(largura - altura) < (largura * 0.4):
                        candidatos.append({
                            'bounds': bounds,
                            'y2': y2, # Borda inferior
                            'x2': x2  # Borda direita
                        })
        
        if candidatos:
            # Ordena para pegar o que estiver mais para baixo (y2) e mais para direita (x2)
            candidatos.sort(key=lambda c: (c['y2'], c['x2']), reverse=True)
            alvo = candidatos[0]['bounds']
            print(f"🎯 Botão Laranja (FAB) detectado no canto! Coordenadas: {alvo}")
            return clicar_no_centro(alvo)
            
    except Exception:
        pass
    return False

def raspar_meus_apps(xml_content):
    meus_apps = []
    try:
        root = ET.fromstring(xml_content)
        for node in root.iter('node'):
            texto = node.attrib.get('text', '')
            rid = node.attrib.get('resource-id', '')
            if texto and rid == 'com.ugcloner.xfein:id/r' and texto not in ["Search apps", "Clear query", "App Bundle", "Settings", "APPS", "CLONED APPS"]:
                meus_apps.append(texto)
    except Exception:
        pass
    return list(set(meus_apps))

def robo_teste_estresse():
    pacote_ug = "com.ugcloner.xfein"
    teclado_pkg = None
    
    print("\n🔥 INICIANDO O SUPER TESTE DE ESTRESSE EM ESCALA (10 RODADAS) 🔥")
    
    try:
        # 1. DESATIVAÇÃO TEMPORÁRIA DO TECLADO
        print("🔕 Identificando o teclado do sistema...")
        teclado_full = executar_root("settings get secure default_input_method")
        if teclado_full and '/' in teclado_full:
            teclado_pkg = teclado_full.split('/')[0]
            print(f"⌨️ Desativando {teclado_pkg} temporariamente para limpar a tela!")
            executar_root(f"pm disable {teclado_pkg}")
            executar_root(f"am force-stop {teclado_pkg}")
        
        for rodada in range(1, 11):
            nova_escala = random.choice([240, 300, 380, 440, 520])
            print(f"\n" + "="*60)
            print(f"🔄 RODADA {rodada}/10 | ESCALA: {nova_escala} dpi")
            print("="*60)
            executar_root(f"wm density {nova_escala}")
            time.sleep(3)
            
            executar_root(f"am force-stop {pacote_ug}")
            executar_root(f"monkey -p {pacote_ug} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1")
            time.sleep(4)
            
            print("🕵️ Lendo os seus apps instalados...")
            tela_inicial = ler_tela()
            apps_reais = raspar_meus_apps(tela_inicial) if tela_inicial else []
            
            if not apps_reais:
                apps_reais = ["Drive", "Chrome", "YouTube"]
                
            nome_app = random.choice(apps_reais)
            print(f"📱 Alvo da SUA lista: {nome_app}")
            
            print("🔍 Procurando a lupa...")
            if achar_e_clicar(tela_inicial, 'content-desc', 'Search apps'):
                time.sleep(1)
                
                print(f"⌨️ Digitando: {nome_app}")
                nome_formatado = nome_app.replace(" ", "%s")
                executar_root(f"input text {nome_formatado}")
                time.sleep(2)
                
                print("🎯 Selecionando na lista...")
                tela_pesquisa = ler_tela()
                if tela_pesquisa and achar_e_clicar(tela_pesquisa, 'text', nome_app, min_y=100):
                    print("⏳ Carregando painel de clonagem...")
                    time.sleep(3)
                    
                    print("📥 Acionando o botão laranja...")
                    tela_config = ler_tela()
                    if tela_config and achar_botao_laranja(tela_config):
                        
                        print("⏳ Confirmando pop-up (OK)...")
                        time.sleep(2)
                        tela_popup = ler_tela()
                        achar_e_clicar(tela_popup, 'text', 'OK')
                        
                        print("⏳ Aguardando botão INSTALL APP...")
                        instalou = False
                        for _ in range(15):
                            time.sleep(3)
                            tela_clonando = ler_tela()
                            if tela_clonando and achar_e_clicar(tela_clonando, 'text', 'INSTALL APP'):
                                print(f"🚀 SUCESSO NA RODADA {rodada}! App instalado!")
                                instalou = True
                                time.sleep(2)
                                break
                            sys.stdout.write(".")
                            sys.stdout.flush()
                            
                        if not instalou:
                            print("\n⚠️ O botão 'INSTALL APP' não apareceu a tempo.")
                    else:
                        print("❌ Não achei o botão laranja.")
                else:
                    print(f"❌ Não achei o app '{nome_app}' na lista.")
            else:
                print("❌ Lupa não encontrada.")
                
            executar_root(f"am force-stop {pacote_ug}")
            time.sleep(2)

    finally:
        print("\n" + "="*60)
        print("🛑 RESTAURAÇÃO DO SISTEMA INICIADA...")
        print("="*60)
        
        # 2. ATIVAÇÃO DO TECLADO DE VOLTA
        if teclado_pkg:
            print(f"⌨️ Reativando o teclado ({teclado_pkg})...")
            executar_root(f"pm enable {teclado_pkg}")
            
        print("📺 Restaurando a escala da tela...")
        executar_root("wm density reset")
        print("✅ Tudo de volta ao normal com segurança!")

if __name__ == "__main__":
    robo_teste_estresse()
