import os
import sys
import subprocess
import re
import requests
import json
import shutil
import argparse
from datetime import datetime

try:
    import gdown
except ImportError:
    gdown = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DATA_DIR = os.path.join(SCRIPT_DIR, "data_apps")
LOG_FILE = os.path.join(SCRIPT_DIR, "log_detetive.txt")
TIMEOUT_REDE = 15

def inicializar_ambiente():
    if not os.path.exists(BASE_DATA_DIR):
        os.makedirs(BASE_DATA_DIR, exist_ok=True)

def dprint(msg):
    # Agora exibe no terminal (print) E salva no log
    print(msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    except:
        pass

def pacote_eh_valido(pacote):
    return bool(re.match(r'^[a-zA-Z0-9_.]+$', pacote))

def executar_root(comando):
    resultado = subprocess.run(
        ['su', '-c', comando],
        capture_output=True,
        text=True
    )
    return True, resultado.stdout.strip() + "\n" + resultado.stderr.strip()

def data_save(pacote):
    dprint(f"\n--- [data_save] Iniciando processo para pacote: {pacote} ---")
    
    if not pacote_eh_valido(pacote):
        dprint(f"[data_save] ERRO: Nome do pacote ({pacote}) é inválido.")
        return False

    inicializar_ambiente()
    safe_pkg = pacote.replace(".", "_")
    destino_final = os.path.join(BASE_DATA_DIR, f"data_{safe_pkg}.tar.gz")
    dprint(f"[data_save] Destino do arquivo será: {destino_final}")

    comando = f"""
    if [ -d "/data/data/{pacote}" ]; then
        echo "Pasta do app encontrada. Iniciando compressão tar..."
        tar --exclude='cache' --exclude='code_cache' --exclude='no_backup' -czf "{destino_final}" -C "/data/data" "{pacote}" 2>&1
        TAR_STATUS=$?
        
        if [ $TAR_STATUS -eq 0 ] || [ $TAR_STATUS -eq 1 ] || [ $TAR_STATUS -eq 2 ]; then
            chmod 777 "{destino_final}"
            echo "sucesso_tar"
        else
            echo "erro_tar_codigo_$TAR_STATUS"
        fi
    else
        echo "erro_pasta_nao_encontrada"
    fi
    """
    
    dprint("[data_save] Executando comando root...")
    sucesso, saida = executar_root(comando)
    dprint(f"[data_save] Saída do terminal root:\n{saida.strip()}")

    if "erro_pasta_nao_encontrada" in saida:
        dprint(f"[data_save] FALHA: A pasta /data/data/{pacote} não existe. App pode não estar instalado ou nunca foi aberto.")
        return False
        
    if "erro_tar_codigo_" in saida:
        dprint(f"[data_save] FALHA: Ocorreu um erro no comando tar ao criar o backup.")
        return False

    if os.path.exists(destino_final):
        tamanho = os.path.getsize(destino_final)
        dprint(f"[data_save] SUCESSO: Arquivo final gerado! Tamanho: {tamanho} bytes.")
        return True
    else:
        dprint(f"[data_save] FALHA GRAVE: Root diz que foi sucesso, mas o arquivo {destino_final} não apareceu!")
        return False

def data_export(pacote, url_servidor, owner_id, device_id):
    dprint(f"\n--- [data_export] Exportando dados de {pacote} ---")
    inicializar_ambiente()
    safe_pkg = pacote.replace(".", "_")
    arquivo_bot = os.path.join(BASE_DATA_DIR, f"data_{safe_pkg}.tar.gz")

    if not os.path.exists(arquivo_bot):
        dprint(f"[data_export] ERRO: Arquivo para upload não foi encontrado ({arquivo_bot})")
        return False

    try:
        with open(arquivo_bot, 'rb') as f:
            files = {'file': (f"data_{safe_pkg}.tar.gz", f, 'application/gzip')}
            data = {
                'pkg_name': pacote,
                'owner_id': str(owner_id),
                'device_id': str(device_id)
            }
            
            dprint(f"[data_export] Enviando POST para: {url_servidor}")
            response = requests.post(url_servidor, files=files, data=data, timeout=TIMEOUT_REDE)
            dprint(f"[data_export] Código HTTP de Resposta: {response.status_code}")

            if response.status_code in [200, 201]:
                os.remove(arquivo_bot)
                dprint("[data_export] SUCESSO: Arquivo exportado e apagado localmente.")
                return True
            else:
                dprint("[data_export] FALHA: O servidor rejeitou o envio.")
                return False
    except Exception as e:
        dprint(f"[data_export] ERRO DE CONEXÃO: {str(e)}")
        return False

def baixar_data_com_cookies(url, out_path):
    dprint(f"[baixar] Preparando download da URL: {url}")
    file_id = None
    match_d = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if match_d:
        file_id = match_d.group(1)
    else:
        match_id = re.search(r'id=([a-zA-Z0-9_-]+)', url)
        if match_id:
            file_id = match_id.group(1)

    if file_id:
        if gdown:
            try:
                dprint("[baixar] Tentando gdown...")
                gdown.download(f"https://drive.google.com/uc?id={file_id}", out_path, quiet=True)
                if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                    dprint("[baixar] Download gdown completo!")
                    return True
            except Exception as e:
                dprint(f"[baixar] Falha no gdown: {e}")

        dprint("[baixar] Tentando requests manual para Google Drive...")
        session = requests.Session()
        confirm_url = "https://docs.google.com/uc?export=download"
        params = {'id': file_id}
        try:
            response = session.get(confirm_url, params=params, stream=True, timeout=TIMEOUT_REDE)
            token = None
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    token = value
                    break

            if token:
                params['confirm'] = token
                response = session.get(confirm_url, params=params, stream=True, timeout=TIMEOUT_REDE)

            if response.status_code == 200:
                with open(out_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                dprint("[baixar] Download requests manual completo!")
                return True
        except requests.exceptions.RequestException as e:
            dprint(f"[baixar] Erro na requisição Drive: {e}")
            return False
    else:
        try:
            dprint("[baixar] Tentando requisição direta (Link normal)...")
            response = requests.get(url, stream=True, timeout=TIMEOUT_REDE)
            if response.status_code == 200:
                with open(out_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                dprint("[baixar] Requisição direta completa!")
                return True
        except requests.exceptions.RequestException as e:
            dprint(f"[baixar] Erro na requisição direta: {e}")
            return False

    dprint("[baixar] Todos os métodos de download falharam.")
    return False

def data_inject(pacote, url_servidor):
    dprint(f"\n--- [data_inject] Iniciando Injeção de {pacote} ---")
    if not pacote_eh_valido(pacote):
        return False

    inicializar_ambiente()
    safe_pkg = pacote.replace(".", "_")
    arquivo_local = os.path.join(BASE_DATA_DIR, f"data_{safe_pkg}.tar.gz")

    if not os.path.exists(arquivo_local):
        if "drive.google.com" in url_servidor:
            url_download = url_servidor
        else:
            url_download = f"{url_servidor.rstrip('/')}/download/data_{safe_pkg}.tar.gz"

        dprint(f"[data_inject] Baixando pacote do servidor/nuvem...")
        try:
            sucesso_download = baixar_data_com_cookies(url_download, arquivo_local)
            if sucesso_download and os.path.exists(arquivo_local) and os.path.getsize(arquivo_local) > 1000:
                dprint("[data_inject] Arquivo baixado com sucesso.")
            else:
                if os.path.exists(arquivo_local):
                    os.remove(arquivo_local)
                dprint("[data_inject] FALHA no download do zip.")
                return False
        except Exception as e:
            if os.path.exists(arquivo_local):
                os.remove(arquivo_local)
            dprint(f"[data_inject] EXCEÇÃO no download: {e}")
            return False

    temp_extract_dir = os.path.join(BASE_DATA_DIR, f"temp_inspect_{safe_pkg}")
    if os.path.exists(temp_extract_dir):
        subprocess.run(["rm", "-rf", temp_extract_dir])
    os.makedirs(temp_extract_dir, exist_ok=True)

    try:
        import tarfile
        dprint("[data_inject] Reempacotando estrutura do TAR (Fix)...")
        try:
            with tarfile.open(arquivo_local, "r:gz") as tar:
                tar.extractall(path=temp_extract_dir)
        except EOFError:
            pass
        except Exception as e:
            dprint(f"[data_inject] Aviso no tar.extractall: {e}")

        conteudo_temp = os.listdir(temp_extract_dir)
        target_data_dir = os.path.join(temp_extract_dir, pacote)

        if pacote in conteudo_temp and os.path.isdir(target_data_dir):
            pass
        elif "data" in conteudo_temp and os.path.isdir(os.path.join(temp_extract_dir, "data")):
            subdata_dir = os.path.join(temp_extract_dir, "data")
            if os.path.exists(target_data_dir):
                subprocess.run(["rm", "-rf", target_data_dir])
            os.makedirs(target_data_dir, exist_ok=True)
            for item in os.listdir(subdata_dir):
                subprocess.run(["mv", os.path.join(subdata_dir, item), target_data_dir])
        else:
            if os.path.exists(target_data_dir):
                subprocess.run(["rm", "-rf", target_data_dir])
            os.makedirs(target_data_dir, exist_ok=True)
            for item in conteudo_temp:
                item_path = os.path.join(temp_extract_dir, item)
                if item != pacote:
                    subprocess.run(["mv", item_path, target_data_dir])

        padrao_tar_local = os.path.join(BASE_DATA_DIR, f"fixed_{safe_pkg}.tar.gz")
        subprocess.run(["tar", "-czf", padrao_tar_local, "-C", temp_extract_dir, pacote], check=True)
        os.replace(padrao_tar_local, arquivo_local)
        dprint("[data_inject] Fix do tar concluído.")
    except Exception as e:
        dprint(f"[data_inject] Erro ao fazer o FIX do tar: {e}")
    finally:
        if os.path.exists(temp_extract_dir):
            subprocess.run(["rm", "-rf", temp_extract_dir])

    comando = f"""
    if [ ! -f "{arquivo_local}" ]; then echo "erro_arquivo_sumiu_raiz"; exit 0; fi
    if [ ! -d "/data/data/{pacote}" ]; then echo "erro_pacote_nao_instalado"; exit 0; fi
    am force-stop "{pacote}"
    APP_OWNER=$(stat -c '%U:%G' /data/data/{pacote})

    echo "Extraindo arquivos no sistema..."
    tar -xzf "{arquivo_local}" -C /data/data/ 2>&1
    TAR_STATUS=$?

    echo "Ajustando permissões para $APP_OWNER..."
    chown -R $APP_OWNER /data/data/{pacote}
    restorecon -R /data/data/{pacote}

    if [ $TAR_STATUS -eq 0 ] || [ $TAR_STATUS -eq 1 ] || [ $TAR_STATUS -eq 2 ]; then
        echo "sucesso_absoluto"
    else
        echo "erro_tar_crash_$TAR_STATUS"
    fi
    """

    dprint("[data_inject] Executando injeção raiz...")
    sucesso, saida = executar_root(comando)
    dprint(f"[data_inject] Saída Root:\n{saida.strip()}")

    if os.path.exists(arquivo_local):
        try: os.remove(arquivo_local)
        except: pass

    if "erro_pacote_nao_instalado" in saida:
        dprint("[data_inject] FALHA: O aplicativo não está instalado.")
        return False
    elif "sucesso_absoluto" in saida:
        dprint("[data_inject] SUCESSO na injeção de dados!")
        try:
            report_file = os.path.join(os.path.dirname(SCRIPT_DIR), "Data", "install_report.json")
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            report_data = {"install_success": [], "install_failed": []}
            if os.path.exists(report_file):
                with open(report_file, "r") as f:
                    report_data = json.load(f)
            if pacote not in report_data["install_success"]:
                report_data["install_success"].append(pacote)
            with open(report_file, "w") as f:
                json.dump(report_data, f, indent=4)
        except Exception as e:
            pass
        return True
    else:
        dprint("[data_inject] FALHA na descompressão (Root).")
        return False

def add_ugclone_config(pacote_alvo, configs):
    dprint(f"\n--- [ugclone_config] Configurando clones para {pacote_alvo} ---")
    inicializar_ambiente()
    master_xml = "/data/data/com.ugcloner.xfein/shared_prefs/com.ugcloner.xfein_preferences.xml"
    ug_pkg = "com.ugcloner.xfein"
    tag_name = f"clone_settings_{pacote_alvo}"

    executar_root(f"am force-stop {ug_pkg}")

    sucesso, xml_content = executar_root(f"cat {master_xml} 2>/dev/null || echo 'FILE_NOT_FOUND'")
    xml_content = xml_content.strip()

    if "FILE_NOT_FOUND" in xml_content or not xml_content:
        xml_content = "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n<map>\n</map>"

    template_str = '{"accessibleDataDirectory":false,"activitiesMonitor":false,"addActivities":["com.applisto.appcloner.classes.FakeCamera$FakeCameraActivity"],"addLauncherIcons":{},"addPermissions":["android.permission.READ_LOGS","android.permission.FLASHLIGHT","net.dinglisch.android.tasker.PERMISSION_RUN_TASKS","android.permission.BLUETOOTH_ADMIN","android.permission.VIBRATE","android.permission.SYSTEM_ALERT_WINDOW","android.permission.CHANGE_WIFI_STATE","android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS","android.permission.ACCESS_NETWORK_STATE","android.permission.USE_FINGERPRINT","android.permission.ACCESS_WIFI_STATE","android.permission.CAMERA","android.permission.READ_EXTERNAL_STORAGE","android.permission.BLUETOOTH","android.permission.WRITE_SETTINGS","android.permission.READ_SETTINGS"],"addProviders":[],"addReceivers":["com.applisto.appcloner.action.FAKE_CAMERA_SELECT_CAMERA_PICTURE,com.applisto.appcloner.action.FAKE_CAMERA_ROTATE_CLOCKWISE,com.applisto.appcloner.action.FAKE_CAMERA_ROTATE_ANTI_CLOCKWISE@com.applisto.appcloner.classes.FakeCamera$FakeCameraReceiver","com.applisto.appcloner.classes.DisableClipboardAccess$ClearClipboardReceiver"],"allowBackup":"NO_CHANGE","allowDarkMode":false,"allowNotificationsWhenRunning":false,"allowScreenshots":false,"allowSharingImages":false,"allowTextSelection":false,"appDataExportImport":true,"appPasswordAskOnlyOnce":false,"appPasswordStealthMode":false,"appValidFrom":0,"appValidUntil":0,"audioPlaybackCapture":"NO_CHANGE","autoIncognitoMode":false,"autoPressButtons":[],"autoRemoveFromRecents":false,"autoStart":"NO_CHANGE","backAlwaysFinishes":false,"badge":"","batchAppendCloneNumber":true,"batchChangeIconHue":false,"batchSetBadge":false,"blockActivitiesNames":[],"blockAllNotifications":false,"blockAllToasts":false,"blockByDefault":false,"bringAppToFrontNotification":false,"bundleAppData":false,"bundleFilesDirectories":[],"bundleObb":false,"bundleOriginalApp":false,"changeAndroidId":false,"changeAndroidIdSeed":0,"changeBluetoothMacAddress":"NO_CHANGE","changeBluetoothMacAddressRandomizeClone":false,"changeDefaultFont":false,"changeImei":"NO_CHANGE","changeImeiImsi":false,"changeImeiRandomizeClone":false,"changeImsi":"NO_CHANGE","changeImsiRandomizeClone":false,"changeWifiMacAddress":"NO_CHANGE","changeWifiMacAddressRandomizeClone":false,"clearCacheOnExit":false,"clearCacheWhenNotUsed":false,"clearCacheWhenNotUsedTimeUnit":"DAYS","clearCacheWhenNotUsedValue":3,"clipboardTimeout":false,"cloneNumber":1,"cloningMode":"DEFAULT","confirmExit":false,"customPermissions":[],"debugUtils":false,"defaultNotificationLights":{"notificationLightsColor":"NO_CHANGE","notificationLightsPattern":"NO_CHANGE"},"deleteFilesDirectoriesOnExit":[],"densityDpiScale":1.0,"deviceLockDeviceIdentifiers":[],"disableAccessibilityServices":false,"disableActivityTransitions":false,"disableAllNetworking":false,"disableAllNetworkingDisableDelay":0,"disableAllNetworkingEnableDelay":0,"disableAppDefaults":false,"disableAutoFill":false,"disableAutoStart":false,"disableBackgroundNetworking":false,"disableCalendarAccess":false,"disableCallLogSmsAccess":false,"disableCameras":false,"disableChromecastButton":false,"disableClearTextNetworking":false,"disableClipboardReadAccess":false,"disableClipboardWriteAccess":false,"disableConnectivityChangeEvents":false,"disableContactsAccess":false,"disableDeviceAdmin":false,"disableHapticFeedback":false,"disableHardwareAcceleration":false,"disableInAppSearch":false,"disableLogcatLogging":false,"disableMobileData":false,"disableNestedScrolling":false,"disableNetworkingWithoutVpn":false,"disableNewPictureVideoEvents":false,"disablePermissionPrompts":false,"disablePhotoMediaAccess":false,"disableRuntimeModdingOptions":false,"disableShareActions":false,"disableSpaceManagement":false,"disableUsbAccessoryModeEvents":false,"disableUsbHostModeEvents":false,"disableWakeLocks":false,"disableWatchApp":false,"disableWidgets":false,"documentLaunchMode":false,"enableBatchCloning":true,"enableTvVersion":false,"excludeFromRecents":false,"exitAppOnScreenOff":false,"exitAppOnScreenOffDelaySeconds":0,"facebookLoginBehavior":"WEB_ONLY","fakeBatteryLevel":0,"fakeCalculator":false,"fakeCamera":false,"fakeDateDay":0,"fakeDateMonth":0,"fakeDateYear":0,"fileAccessMonitor":false,"fingerprintLongTapAction":"NONE","fingerprintTapAction":"NONE","flashlightWhileAppOpen":false,"flipIcon":false,"flipIconVertically":false,"floatingApp":false,"floatingAppLowerTargetSdk":false,"floatingAppOpacity":1.0,"floatingBackButton":false,"floatingBackButtonColor":-7829368,"floatingBackButtonDoubleBackTap":false,"floatingBackButtonLongPressAction":"NONE","floatingBackButtonOpacity":0.5,"floatingBackButtonPositionPerScreen":false,"floatingBackButtonSize":"MEDIUM","flushLogcatBufferOnExit":false,"fontScale":1.0,"forceRotationLockUsingOverlay":false,"freeFormWindow":false,"fromCloneNumber":1,"googlePlayServicesWorkaround":false,"gpsJoystick":false,"gpsJoystickColor":-7829368,"gpsJoystickHorizontalAlignment":"LEFT","gpsJoystickMaxSpeed":1.5,"gpsJoystickOpacity":1.0,"gpsJoystickSize":"MEDIUM","gpsJoystickVerticalAlignment":"BOTTOM","headphonesPluggedEventAction":"NONE","headphonesUnpluggedEventAction":"NONE","headsUpNotifications":false,"hideBluetoothMacAddress":false,"hideDeveloperMode":false,"hideFromClonedApps":false,"hideGooglePlayServices":false,"hideImei":false,"hideImsi":false,"hideNotch":false,"hideOtherApps":[],"hidePasswordCharacters":false,"hidePowerSavingMode":false,"hideRoot":false,"hideScreenMirroring":false,"hideSimOperatorInfo":false,"hideVpnConnection":false,"hideWifiInfo":false,"hideWifiMacAddress":false,"hostsBlocker":false,"hostsBlockerAllowAllOtherHosts":false,"iconEffect":"NONE","iconHue":180,"iconLightness":0.0,"iconRotation":180,"iconSaturation":0.0,"ignoreCrashes":false,"ignoreCrashesShowCrashMessages":false,"ignoreUpdates":false,"immersiveMode":false,"immersiveModeIgnoreNotch":false,"incognitoKeyboard":false,"incognitoMode":false,"installToSdCard":false,"interpretedMode":false,"joystickPointer":false,"joystickPointerColor":-7829368,"joystickPointerOpacity":1.0,"joystickPointerShowInitially":true,"joystickPointerSize":"MEDIUM","joystickPointerToggleKeyCode":23,"joystickPointerToggleLongPress":true,"keepAppLabel":false,"keepScreenOn":false,"keyboardAdjust":"NO_CHANGE","language":"","largeHeapSupport":false,"largerAspectRatios":"NO_CHANGE","launchQuickSettingsTile":false,"leanbackBannerImage":false,"leanbackLauncherSupport":false,"localActivities":false,"localBroadcastsServices":false,"localOnlyNotifications":false,"logGetPackageName":false,"logcatViewer":false,"longPressBackAction":"NONE","lowMemoryMode":false,"makeAssistApp":false,"makeCameraApp":false,"makeDebuggable":false,"makeHomeApp":false,"makeTestOnly":false,"makeWatchApp":false,"markAsGame":false,"mergeCustomClassesDex":false,"mergeOriginalClassesDex":false,"minSdkVersion":0,"multiWindow":false,"multiWindowNoPause":false,"muteMic":false,"muteOnStart":false,"navigationBarColorUseStatusBarColor":false,"noBackgroundServices":false,"noKill":false,"noOngoingNotifications":false,"noRelayoutOnRotation":false,"notificationCategories":[],"notificationColorUseStatusBarColor":false,"notificationFilter":"","notificationPriority":"NO_CHANGE","notificationQuietTime":false,"notificationQuietTimeEnd":"07:00","notificationQuietTimeStart":"21:00","notificationSnoozeTimeout":0,"notificationSound":"NO_CHANGE","notificationTextReplacements":[],"notificationTimeout":0,"notificationTintStatusBarIcon":false,"notificationVibration":"NO_CHANGE","notificationVisibility":"NO_CHANGE","overrideSharedPreferences":{},"palmRejectionWidthPercentage":0,"passwordProtectApp":false,"penButtonPressedEventAction":"NONE","penDetachedEventAction":"NONE","penInsertedEventAction":"NONE","persistentApp":false,"persistentAppAccessibilityService":false,"persistentClipboard":false,"pictureInPictureKeyCode":0,"pictureInPictureLongPress":false,"pictureInPictureNotification":false,"pictureInPictureSupport":false,"popupBlocker":false,"powerConnectedEventAction":"NONE","powerDisconnectedEventAction":"NONE","powerEventsDockUndockEvents":false,"preserveExpansionFiles":false,"pressBackAgainToExit":false,"preventImmersiveMode":false,"preventScreenshots":false,"privateAccounts":false,"privateClipboard":false,"promptKeepAppDataOnUninstall":false,"randomAndroidId":false,"randomizeBuildProps":false,"redirectExternalStorage":false,"removeLauncherIcon":false,"removeLauncherIconShortcuts":false,"removeNotificationActions":false,"removeNotificationIcon":false,"removeNotificationPeople":false,"removePermissions":[],"replaceLauncherIcon":false,"replaceNotificationIcon":false,"requestAllPermissions":false,"requestIgnoreBatteryOptimizations":false,"restoreAppDataOnEveryStart":false,"restoreAutoRotateOnExit":false,"restoreBluetoothStateOnExit":false,"restoreBrightnessOnExit":false,"restoreInterruptionFilterOnExit":false,"restoreWifiStateOnExit":false,"rotationLock":"NONE","roundIconSupport":false,"safeMode":false,"sandboxExternalStorage":false,"screenTextReplacements":[],"setClipboardDataOnStart":"","shakeAction":"NONE","shakeSensitivity":"NORMAL","showAppInfoNotification":false,"showNotificationTime":false,"showOnLockScreen":false,"showOnSecondaryDisplay":false,"showOnSecondaryDisplayActivitiesNames":[],"showTouches":false,"signAsSystemApp":false,"simpleNotifications":false,"skipNativeLibraries":false,"socksProxy":false,"socksProxyPort":1080,"splashScreen":false,"splashScreenBackgroundColor":-1,"splashScreenDuration":3,"splashScreenMargin":0.3,"spoofLocationInterval":10,"startSound":false,"stealthMode":false,"stealthModeUseFingerprint":false,"stethoSupport":false,"targetSdkVersion":0,"taskerStartTaskName":"","taskerStopTaskName":"","toCloneNumber":8,"toastDuration":"NO_CHANGE","toastFilter":"","toastHorizontalAlignment":"CENTER","toastPosition":false,"toastVerticalAlignment":"BOTTOM","toolbarColorUseStatusBarColor":false,"transparentNavigationBar":false,"trustAllCertificates":false,"twitterLoginBehavior":"WEB_ONLY","useAndHook":false,"versionCode":0,"viewModifications":[],"volumeControlIndicator":"NO_CHANGE","volumeControlIndicatorStep":1,"volumeDownKeyAction":"NONE","volumeRockerLocker":"NONE","volumeUpDownKeyAction":"NONE","volumeUpKeyAction":"NONE","waitForDebugger":false,"welcomeMessageDelay":2000,"welcomeMessageMode":"DIALOG","wideColorGamut":false}'

    template_seguro = json.loads(template_str)
    template_seguro.update(configs)
    settings_json_str = json.dumps(template_seguro, separators=(',', ':'))
    escaped_json = settings_json_str.replace('"', '&quot;')

    nova_tag = f'    <string name="{tag_name}">{escaped_json}</string>'
    regex = rf'<string name="{tag_name}">.*?</string>'

    if re.search(regex, xml_content, flags=re.DOTALL):
        xml_content = re.sub(regex, nova_tag, xml_content, flags=re.DOTALL)
    elif "</map>" in xml_content:
        xml_content = xml_content.replace("</map>", f"{nova_tag}\n</map>")
    else:
        return False

    temp_file = os.path.join(BASE_DATA_DIR, "temp_ug.xml")
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(xml_content)

    comando = f"""
    mkdir -p /data/data/{ug_pkg}/shared_prefs/
    cp "{temp_file}" "{master_xml}"
    APP_OWNER=$(stat -c '%U:%G' /data/data/{ug_pkg} 2>/dev/null || echo "10000:10000")
    chown $APP_OWNER "{master_xml}"
    chmod 660 "{master_xml}"
    restorecon "{master_xml}" 2>/dev/null || true
    rm -f "{temp_file}"
    echo "sucesso_xml"
    """

    sucesso_write, saida = executar_root(comando)

    if "sucesso_xml" in saida:
        dprint("[ugclone_config] SUCESSO: Configuração inserida no master xml.")
        return True
    else:
        dprint(f"[ugclone_config] FALHA ao gravar via root:\n{saida}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Caminho do arquivo tar.gz")
    args = parser.parse_args()

    if args.file:
        dprint(f"\n[Main CLI] Execução direta iniciada usando o arquivo: {args.file}")
        inicializar_ambiente()

        pacote_alvo = None
        nome_arquivo = os.path.basename(args.file).lower()
        if "macrodroid" in nome_arquivo:
            pacote_alvo = "com.arlosoft.macrodroid"
        else:
            match = re.search(r'data_([a-z0-9_]+)\.tar\.gz', nome_arquivo)
            if match: pacote_alvo = match.group(1).replace("_", ".")

        if pacote_alvo:
            safe_pkg = pacote_alvo.replace(".", "_")
            destino_esperado = os.path.join(BASE_DATA_DIR, f"data_{safe_pkg}.tar.gz")
            shutil.copy2(args.file, destino_esperado)

            sucesso = data_inject(pacote_alvo, "local")
            if not sucesso:
                sys.exit(1)
            else:
                sys.exit(0)
        else:
            dprint("[Main CLI] ERRO: Pacote não reconhecido pelo nome do arquivo.")
            sys.exit(1)
