import subprocess
import time
import re
import xml.etree.ElementTree as ET
import sys
import os
import json

# ==========================================
# FUNÇÕES DE SISTEMA E UTILIDADES
# ==========================================

def executar_root(comando):
    try:
        resultado = subprocess.check_output(f"su -c '{comando}'", shell=True, stderr=subprocess.STDOUT, text=True)
        return resultado.strip()
    except subprocess.CalledProcessError as e:
        return e.output.strip()

def obter_dpi_atual():
    saida = executar_root("wm density")
    match = re.search(r'(\d+)', saida)
    return match.group(1) if match else "380"

def desativar_teclado():
    print("🔒 Matando o Gboard e forçando modo oculto...")
    executar_root("ime disable com.google.android.inputmethod.latin/com.android.inputmethod.latin.LatinIME")
    executar_root("settings put secure show_ime_with_hard_keyboard 0")

def reativar_teclado():
    print("🔓 Reativando o Gboard...")
    executar_root("ime enable com.google.android.inputmethod.latin/com.android.inputmethod.latin.LatinIME")
    executar_root("ime set com.google.android.inputmethod.latin/com.android.inputmethod.latin.LatinIME")
    executar_root("settings put secure show_ime_with_hard_keyboard 1")

def desativar_play_protect():
    print("🛡️ Desligando o Google Play Protect (Verificador de Pacotes)...")
    executar_root("settings put global package_verifier_enable 0")
    executar_root("settings put global upload_apk_enable 0")

def reativar_play_protect():
    print("🛡️ Reativando o Google Play Protect...")
    executar_root("settings put global package_verifier_enable 1")
    executar_root("settings put global upload_apk_enable 1")

def conceder_permissoes_iniciais(pacote):
    print("🔓 Concedendo permissões do sistema silenciosamente (Root)...")
    executar_root(f"appops set {pacote} REQUEST_INSTALL_PACKAGES allow")
    executar_root(f"pm grant {pacote} android.permission.READ_EXTERNAL_STORAGE")
    executar_root(f"pm grant {pacote} android.permission.WRITE_EXTERNAL_STORAGE")
    time.sleep(1)

def obter_nome_real(pacote):
    """Lê o banco de dados local para descobrir o nome legível do aplicativo."""
    caminho_json = os.path.join(os.path.dirname(__file__), "../Data/apps_install.json")
    try:
        if os.path.exists(caminho_json):
            with open(caminho_json, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                if pacote in dados and "name" in dados[pacote]:
                    return dados[pacote]["name"]
    except Exception as e:
        print(f"⚠️ Erro ao ler apps_install.json: {e}")
        
    fallback = pacote.split('.')[-1].capitalize()
    return fallback

# ==========================================
# FUNÇÕES DE INTERAÇÃO COM A TELA
# ==========================================

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

def limpar_texto(texto):
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto).strip()

def achar_e_clicar(xml_content, atributo, valor_procurado, min_y=0):
    if not xml_content: return False
    valor_procurado_limpo = limpar_texto(valor_procurado).lower()
    try:
        root = ET.fromstring(xml_content)
        for node in root.iter('node'):
            valor_node = node.attrib.get(atributo, '')
            valor_node_limpo = limpar_texto(valor_node).lower()
            if valor_procurado_limpo == valor_node_limpo or valor_procurado_limpo in valor_node_limpo:
                bounds = node.attrib.get('bounds')
                if bounds:
                    coords = re.findall(r'\d+', bounds)
                    if len(coords) == 4:
                        _, y1, _, _ = map(int, coords)
                        if y1 < min_y: continue
                        print(f"✅ Encontrou '{valor_node}'!")
                        return clicar_no_centro(bounds)
    except Exception:
        pass
    return False

def achar_botao_laranja_padrao(xml_content):
    if not xml_content: return False
    try:
        root = ET.fromstring(xml_content)
        candidatos = []
        for node in root.iter('node'):
            bounds = node.attrib.get('bounds')
            texto = node.attrib.get('text', '')
            desc = node.attrib.get('content-desc', '')
            classe = node.attrib.get('class', '')
            clicavel = node.attrib.get('clickable', 'false')
            if bounds and not texto and not desc and clicavel == 'true' and 'Image' in classe:
                coords = re.findall(r'\d+', bounds)
                if len(coords) == 4:
                    x1, y1, x2, y2 = map(int, coords)
                    if x1 > 400: candidatos.append({'bounds': bounds, 'y2': y2})
        if candidatos:
            candidatos.sort(key=lambda c: c['y2'], reverse=True)
            alvo = candidatos[0]['bounds']
            print(f"🎯 Botão Laranja fixo detectado! Coordenadas: {alvo}")
            return clicar_no_centro(alvo)
    except Exception:
        pass
    return False

# ==========================================
# FLUXOS DE CLONAGEM MÚLTIPLA E INTELIGENTE
# ==========================================

def limpar_apks_antigos(pacote_ug):
    """Garante que a pasta cache esteja vazia antes da nova compilação."""
    print("🧹 Limpando resíduos e APKs antigos do cache...")
    executar_root(f"rm -f /data/data/{pacote_ug}/files/*.apk")

def cacar_e_instalar_fantasma(pacote_ug):
    print("\n🕵️ Procurando todos os APKs gerados na pasta secreta...")
    time.sleep(2) # Respiro pro celular salvar tudo no disco
    
    comando_busca = f"ls /data/data/{pacote_ug}/files/*.apk 2>/dev/null"
    saida = executar_root(comando_busca)
    
    # Separa por linha e pega apenas arquivos válidos
    apks_encontrados = [linha.strip() for linha in saida.split('\n') if linha.strip().endswith('.apk')]
    
    if not apks_encontrados:
        print("❌ Nenhum APK encontrado na pasta /files/.")
        return False
        
    print(f"📦 Encontrados {len(apks_encontrados)} APK(s) prontos para injeção!")
    sucesso_total = True
    
    # Motor de instalação em cadeia
    for apk in apks_encontrados:
        nome_arquivo = apk.split('/')[-1]
        print(f"👻 Injetando no sistema: {nome_arquivo}...")
        resultado = executar_root(f"pm install -r '{apk}'")
        if "Success" in resultado:
            print(f"✅ SUCESSO: Instalação fantasma concluída.")
        else:
            print(f"⚠️ FALHA ao instalar {nome_arquivo}: {resultado}")
            sucesso_total = False
            
    return sucesso_total

def aguardar_e_instalar(pacote_ug):
    print("⏳ Monitorando a compilação do UGClone...")
    instalou = False
    
    # 60 tentativas de 3 segundos = 3 minutos de timeout (ideal para clones pesados/múltiplos)
    for _ in range(60): 
        time.sleep(3)
        tela_clonando = ler_tela()
        if not tela_clonando: continue
            
        # ==========================================
        # 🧠 EXTRAÇÃO INTELIGENTE DE PROGRESSO (REGEX)
        # ==========================================
        status_str = "Clonando aplicativo..."
        
        # Procura por padrões como: "Creating clone 1 of 2", "Criando clone 1 de 2"
        match_etapa = re.search(r'text="[^"]*?(\d+)\s*(of|de)\s*(\d+)[^"]*"', tela_clonando, re.IGNORECASE)
        # Procura por "66%"
        match_pct = re.search(r'text="(\d+)%"', tela_clonando)
        
        if match_etapa:
            atual, _, total = match_etapa.groups()
            status_str = f"Gerando clone {atual} de {total}"
        
        if match_pct:
            status_str += f" [{match_pct.group(1)}%]"
            
        sys.stdout.write(f"\r\033[K🔄 {status_str}")
        sys.stdout.flush()

        # ==========================================
        # 🎯 GATILHO DE TÉRMINO DINÂMICO
        # Aceita: "INSTALL APP", "INSTALL APPS", "INSTALL ALL", "INSTALAR TUDO", etc.
        # ==========================================
        if re.search(r'text=".*?(INSTALL|INSTALAR).*?(APP|ALL|TUDO).*?"', tela_clonando, re.IGNORECASE):
            print("\n✨ O motor de clonagem indicou término do processo!")
            instalou = cacar_e_instalar_fantasma(pacote_ug)
            break

    if not instalou:
        print("\n⚠️ O processo atingiu o limite de tempo (Timeout) ou não gerou botão de instalação.")
    return instalou

def install_clone(pacote_ug):
    print("\n📦 Iniciando modo: INSTALL CLONE")
    time.sleep(2)
    tela_popup = ler_tela()
    
    # Antes de apertar OK e começar o show, ele limpa a pasta de saída!
    if achar_e_clicar(tela_popup, 'text', 'OK'):
        limpar_apks_antigos(pacote_ug)
        return aguardar_e_instalar(pacote_ug)
    else:
        print("⚠️ Pop-up 'OK' não encontrado. Limpando cache e seguindo...")
        limpar_apks_antigos(pacote_ug)
        return aguardar_e_instalar(pacote_ug)

def update_clone(pacote_ug):
    print("\n🔄 Iniciando modo: UPDATE CLONE")
    time.sleep(2)
    tela_popup = ler_tela()
    print("✅ Marcando 'Safe update'...")
    achar_e_clicar(tela_popup, 'text', 'Safe update')
    time.sleep(1)
    
    print("✅ Confirmando no botão 'UPDATE'...")
    tela_popup2 = ler_tela()
    if achar_e_clicar(tela_popup2, 'text', 'UPDATE'):
        limpar_apks_antigos(pacote_ug)
        return aguardar_e_instalar(pacote_ug)
    else:
        print("⚠️ Botão 'UPDATE' não encontrado. Fluxo pode falhar.")
        return False

# ==========================================
# MOTOR PRINCIPAL (CONTROLADO PELO ORQUESTRADOR)
# ==========================================

def executar_ordem(modo, pacote_alvo):
    """
    Função principal acionada pelo Orchestrator.
    :param modo: "clone_install" ou "update"
    :param pacote_alvo: string do package (ex: "com.termux")
    :return: Booleano (True para sucesso, False para falha)
    """
    pacote_ug = "com.ugcloner.xfein"
    dpi_original = obter_dpi_atual()
    DPI_BOT = "380"
    
    sucesso_final = False

    try:
        desativar_play_protect()
        conceder_permissoes_iniciais(pacote_ug)
        desativar_teclado()
        time.sleep(1.5)

        print(f"📐 Aplicando DPI padrão do bot ({DPI_BOT})...")
        executar_root(f"wm density {DPI_BOT}")
        time.sleep(2)

        executar_root(f"monkey -p {pacote_ug} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1")
        time.sleep(4)

        tela_inicial = ler_tela()
        nome_real = obter_nome_real(pacote_alvo)

        print(f"🔍 Procurando pela lupa de pesquisa para injetar: '{nome_real}'")
        if achar_e_clicar(tela_inicial, 'content-desc', 'Search apps'):
            time.sleep(1.5)
            
            nome_formatado = nome_real.replace(" ", "%s")
            executar_root(f"input text {nome_formatado}")
            time.sleep(1)
            executar_root("input keyevent 66") 
            time.sleep(2)

            tela_pesquisa = ler_tela()
            
            if achar_e_clicar(tela_pesquisa, 'text', nome_real, min_y=100) or clicar_no_centro("20 200 1000 350"):
                time.sleep(3)
                clicou_laranja = False
                
                for _ in range(3):
                    if achar_botao_laranja_padrao(ler_tela()):
                        clicou_laranja = True
                        break
                    time.sleep(1.5)

                if clicou_laranja:
                    if modo == "clone_install":
                        sucesso_final = install_clone(pacote_ug)
                    elif modo == "update":
                        sucesso_final = update_clone(pacote_ug)
                else:
                    print("❌ Não achei o botão laranja após tentativas.")
            else:
                print(f"❌ Não foi possível clicar no resultado da busca para '{nome_real}'.")
        else:
            print("❌ Lupa de pesquisa não encontrada na interface.")

    except Exception as e:
        print(f"❌ Erro crítico no fluxo de automação: {e}")
        sucesso_final = False

    finally:
        print("\n" + "-"*40)
        print("🛑 INICIANDO RESTAURAÇÃO DO SISTEMA...")
        print("-"*40)
        reativar_play_protect()
        reativar_teclado()
        executar_root(f"wm density {dpi_original}")
        print("✅ Restauração concluída.")
        
    return sucesso_final
