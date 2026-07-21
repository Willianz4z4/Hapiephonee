import subprocess
import time
import re
import xml.etree.ElementTree as ET
import random
import sys
import json
import os

ARQUIVO_STATUS = "../Data/status_ugclone.json"

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

def raspar_meus_apps(xml_content):
    meus_apps = []
    if not xml_content: return meus_apps
    titulos_proibidos = ["search apps", "clear query", "app bundle", "settings", "apps", "cloned apps", "recently cloned apps", "recently installed apps", "all apps", "app cloner"]
    try:
        root = ET.fromstring(xml_content)
        for node in root.iter('node'):
            texto = node.attrib.get('text', '')
            texto_limpo = limpar_texto(texto)
            rid = node.attrib.get('resource-id', '')
            if texto_limpo and rid == 'com.ugcloner.xfein:id/r':
                if texto_limpo.lower() not in titulos_proibidos:
                    meus_apps.append(texto_limpo)
    except Exception:
        pass
    return list(set(meus_apps))

def cacar_e_instalar_fantasma(pacote_ug):
    print("\n🕵️ O APK FOI GERADO! Entrando na pasta secreta do UGClone...")
    comando_busca = f"ls -t /data/data/{pacote_ug}/files/*.apk 2>/dev/null | head -n 1"
    apk_alvo = executar_root(comando_busca)
    
    if apk_alvo and apk_alvo.endswith('.apk'):
        print(f"🎯 ÚLTIMO APK GERADO ENCONTRADO: {apk_alvo}")
        print("👻 Executando instalação invisível via Root...")
        resultado = executar_root(f"pm install -r '{apk_alvo}'")
        if "Success" in resultado:
            print("✅ SUCESSO! O aplicativo foi instalado direto no sistema.")
            return True
        else:
            print(f"⚠️ Falha na instalação silenciosa: {resultado}")
            return False
    else:
        print("❌ Nenhum APK encontrado na pasta /files/.")
        return False

# ==========================================
# FLUXOS DE CLONAGEM (INSTALL & UPDATE)
# ==========================================

def aguardar_e_instalar(pacote_ug):
    print("⏳ Aguardando a clonagem terminar (Procurando INSTALL APP)...")
    instalou = False
    for _ in range(20):
        time.sleep(2)
        tela_clonando = ler_tela()
        if tela_clonando and 'text="INSTALL APP"' in tela_clonando:
            cacar_e_instalar_fantasma(pacote_ug)
            instalou = True
            break
        sys.stdout.write(".")
        sys.stdout.flush()
    if not instalou:
        print("\n⚠️ O processo de clonagem demorou demais ou falhou.")

def install_clone(pacote_ug):
    print("\n📦 Iniciando modo: INSTALL CLONE")
    time.sleep(2)
    tela_popup = ler_tela()
    if achar_e_clicar(tela_popup, 'text', 'OK'):
        aguardar_e_instalar(pacote_ug)
    else:
        print("⚠️ Pop-up 'OK' não encontrado. Tentando seguir mesmo assim...")
        aguardar_e_instalar(pacote_ug)

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
        aguardar_e_instalar(pacote_ug)
    else:
        print("⚠️ Botão 'UPDATE' não encontrado. Fluxo pode falhar.")

# ==========================================
# MOTOR PRINCIPAL (CONTROLADO)
# ==========================================

def atualizar_status(status_atual):
    caminho = os.path.join(os.path.dirname(__file__), ARQUIVO_STATUS)
    with open(caminho, 'w') as f:
        json.dump({"status": status_atual}, f)
    print(f"📡 Status do sistema atualizado para: [{status_atual}]")

def executar_ordem(modo="update"):
    pacote_ug = "com.ugcloner.xfein"
    dpi_original = obter_dpi_atual()
    DPI_BOT = "380"

    print(f"\n🔥 INICIANDO AUTOMAÇÃO UGCLONE (Modo: {modo.upper()}) 🔥")
    atualizar_status("RODANDO_IMPORTANTE_MAX")

    try:
        desativar_play_protect()
        conceder_permissoes_iniciais(pacote_ug)
        desativar_teclado()
        time.sleep(1.5)

        print(f"📐 Aplicando DPI padrão do bot ({DPI_BOT})...")
        executar_root(f"wm density {DPI_BOT}")
        time.sleep(2)

        executar_root(f"am force-stop {pacote_ug}")
        executar_root(f"monkey -p {pacote_ug} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1")
        time.sleep(4)

        tela_inicial = ler_tela()
        apps_reais = raspar_meus_apps(tela_inicial)
        if not apps_reais:
            apps_reais = ["Drive", "Chrome", "YouTube", "Gmail", "Calendar"]

        nome_app = random.choice(apps_reais)
        print(f"📱 Alvo SEGURO da sua lista: {nome_app}")

        if achar_e_clicar(tela_inicial, 'content-desc', 'Search apps'):
            time.sleep(1)
            nome_formatado = nome_app.replace(" ", "%s")
            executar_root(f"input text {nome_formatado}")
            time.sleep(1)
            executar_root("input keyevent 66") 
            time.sleep(1.5)

            tela_pesquisa = ler_tela()
            if achar_e_clicar(tela_pesquisa, 'text', nome_app, min_y=100):
                time.sleep(3)
                clicou_laranja = False
                for _ in range(3):
                    if achar_botao_laranja_padrao(ler_tela()):
                        clicou_laranja = True
                        break
                    time.sleep(1.5)

                if clicou_laranja:
                    if modo == "clone_install":
                        install_clone(pacote_ug)
                    elif modo == "update":
                        update_clone(pacote_ug)
                else:
                    print("❌ Não achei o botão laranja após tentativas.")
            else:
                print(f"❌ Não achei o app '{nome_app}' na lista.")
        else:
            print("❌ Lupa não encontrada.")

        executar_root(f"am force-stop {pacote_ug}")
        time.sleep(1)
        return True

    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        return False

    finally:
        print("\n" + "="*60)
        print("🛑 RESTAURAÇÃO DO SISTEMA INICIADA...")
        print("="*60)
        reativar_play_protect()
        reativar_teclado()
        executar_root(f"wm density {dpi_original}")
        atualizar_status("LIVRE")
        print("✅ Tudo de volta ao padrão. Sistema liberado para novas ordens!")
