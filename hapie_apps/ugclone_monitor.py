import sys
import subprocess
import json
import re
import html 

# O Template de Fábrica (A sua lista mestre de chaves)
TEMPLATE_JSON_STR = '{"accessibleDataDirectory":false,"activitiesMonitor":false,"addActivities":["com.applisto.appcloner.classes.FakeCamera$FakeCameraActivity"],"addLauncherIcons":{},"addPermissions":["android.permission.READ_LOGS","android.permission.FLASHLIGHT","net.dinglisch.android.tasker.PERMISSION_RUN_TASKS","android.permission.BLUETOOTH_ADMIN","android.permission.VIBRATE","android.permission.SYSTEM_ALERT_WINDOW","android.permission.CHANGE_WIFI_STATE","android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS","android.permission.ACCESS_NETWORK_STATE","android.permission.USE_FINGERPRINT","android.permission.ACCESS_WIFI_STATE","android.permission.CAMERA","android.permission.READ_EXTERNAL_STORAGE","android.permission.BLUETOOTH","android.permission.WRITE_SETTINGS","android.permission.READ_SETTINGS"],"addProviders":[],"addReceivers":["com.applisto.appcloner.action.FAKE_CAMERA_SELECT_CAMERA_PICTURE,com.applisto.appcloner.action.FAKE_CAMERA_ROTATE_CLOCKWISE,com.applisto.appcloner.action.FAKE_CAMERA_ROTATE_ANTI_CLOCKWISE@com.applisto.appcloner.classes.FakeCamera$FakeCameraReceiver","com.applisto.appcloner.classes.DisableClipboardAccess$ClearClipboardReceiver"],"allowBackup":"NO_CHANGE","allowDarkMode":false,"allowNotificationsWhenRunning":false,"allowScreenshots":false,"allowSharingImages":false,"allowTextSelection":false,"appDataExportImport":true,"appPasswordAskOnlyOnce":false,"appPasswordStealthMode":false,"appValidFrom":0,"appValidUntil":0,"audioPlaybackCapture":"NO_CHANGE","autoIncognitoMode":false,"autoPressButtons":[],"autoRemoveFromRecents":false,"autoStart":"NO_CHANGE","backAlwaysFinishes":false,"badge":"","batchAppendCloneNumber":true,"batchChangeIconHue":false,"batchSetBadge":false,"blockActivitiesNames":[],"blockAllNotifications":false,"blockAllToasts":false,"blockByDefault":false,"bringAppToFrontNotification":false,"bundleAppData":false,"bundleFilesDirectories":[],"bundleObb":false,"bundleOriginalApp":false,"changeAndroidId":false,"changeAndroidIdSeed":0,"changeBluetoothMacAddress":"NO_CHANGE","changeBluetoothMacAddressRandomizeClone":false,"changeDefaultFont":false,"changeImei":"NO_CHANGE","changeImeiImsi":false,"changeImeiRandomizeClone":false,"changeImsi":"NO_CHANGE","changeImsiRandomizeClone":false,"changeWifiMacAddress":"NO_CHANGE","changeWifiMacAddressRandomizeClone":false,"clearCacheOnExit":false,"clearCacheWhenNotUsed":false,"clearCacheWhenNotUsedTimeUnit":"DAYS","clearCacheWhenNotUsedValue":3,"clipboardTimeout":false,"cloneNumber":1,"cloningMode":"DEFAULT","confirmExit":false,"customPermissions":[],"debugUtils":false,"defaultNotificationLights":{"notificationLightsColor":"NO_CHANGE","notificationLightsPattern":"NO_CHANGE"},"deleteFilesDirectoriesOnExit":[],"densityDpiScale":1.0,"deviceLockDeviceIdentifiers":[],"disableAccessibilityServices":false,"disableActivityTransitions":false,"disableAllNetworking":false,"disableAllNetworkingDisableDelay":0,"disableAllNetworkingEnableDelay":0,"disableAppDefaults":false,"disableAutoFill":false,"disableAutoStart":false,"disableBackgroundNetworking":false,"disableCalendarAccess":false,"disableCallLogSmsAccess":false,"disableCameras":false,"disableChromecastButton":false,"disableClearTextNetworking":false,"disableClipboardReadAccess":false,"disableClipboardWriteAccess":false,"disableConnectivityChangeEvents":false,"disableContactsAccess":false,"disableDeviceAdmin":false,"disableHapticFeedback":false,"disableHardwareAcceleration":false,"disableInAppSearch":false,"disableLogcatLogging":false,"disableMobileData":false,"disableNestedScrolling":false,"disableNetworkingWithoutVpn":false,"disableNewPictureVideoEvents":false,"disablePermissionPrompts":false,"disablePhotoMediaAccess":false,"disableRuntimeModdingOptions":false,"disableShareActions":false,"disableSpaceManagement":false,"disableUsbAccessoryModeEvents":false,"disableUsbHostModeEvents":false,"disableWakeLocks":false,"disableWatchApp":false,"disableWidgets":false,"documentLaunchMode":false,"enableBatchCloning":true,"enableTvVersion":false,"excludeFromRecents":false,"exitAppOnScreenOff":false,"exitAppOnScreenOffDelaySeconds":0,"facebookLoginBehavior":"WEB_ONLY","fakeBatteryLevel":0,"fakeCalculator":false,"fakeCamera":false,"fakeDateDay":0,"fakeDateMonth":0,"fakeDateYear":0,"fileAccessMonitor":false,"fingerprintLongTapAction":"NONE","fingerprintTapAction":"NONE","flashlightWhileAppOpen":false,"flipIcon":false,"flipIconVertically":false,"floatingApp":false,"floatingAppLowerTargetSdk":false,"floatingAppOpacity":1.0,"floatingBackButton":false,"floatingBackButtonColor":-7829368,"floatingBackButtonDoubleBackTap":false,"floatingBackButtonLongPressAction":"NONE","floatingBackButtonOpacity":0.5,"floatingBackButtonPositionPerScreen":false,"floatingBackButtonSize":"MEDIUM","flushLogcatBufferOnExit":false,"fontScale":1.0,"forceRotationLockUsingOverlay":false,"freeFormWindow":false,"fromCloneNumber":1,"googlePlayServicesWorkaround":false,"gpsJoystick":false,"gpsJoystickColor":-7829368,"gpsJoystickHorizontalAlignment":"LEFT","gpsJoystickMaxSpeed":1.5,"gpsJoystickOpacity":1.0,"gpsJoystickSize":"MEDIUM","gpsJoystickVerticalAlignment":"BOTTOM","headphonesPluggedEventAction":"NONE","headphonesUnpluggedEventAction":"NONE","headsUpNotifications":false,"hideBluetoothMacAddress":false,"hideDeveloperMode":false,"hideFromClonedApps":false,"hideGooglePlayServices":false,"hideImei":false,"hideImsi":false,"hideNotch":false,"hideOtherApps":[],"hidePasswordCharacters":false,"hidePowerSavingMode":false,"hideRoot":false,"hideScreenMirroring":false,"hideSimOperatorInfo":false,"hideVpnConnection":false,"hideWifiInfo":false,"hideWifiMacAddress":false,"hostsBlocker":false,"hostsBlockerAllowAllOtherHosts":false,"iconEffect":"NONE","iconHue":180,"iconLightness":0.0,"iconRotation":180,"iconSaturation":0.0,"ignoreCrashes":false,"ignoreCrashesShowCrashMessages":false,"ignoreUpdates":false,"immersiveMode":false,"immersiveModeIgnoreNotch":false,"incognitoKeyboard":false,"incognitoMode":false,"installToSdCard":false,"interpretedMode":false,"joystickPointer":false,"joystickPointerColor":-7829368,"joystickPointerOpacity":1.0,"joystickPointerShowInitially":true,"joystickPointerSize":"MEDIUM","joystickPointerToggleKeyCode":23,"joystickPointerToggleLongPress":true,"keepAppLabel":false,"keepScreenOn":false,"keyboardAdjust":"NO_CHANGE","language":"","largeHeapSupport":false,"largerAspectRatios":"NO_CHANGE","launchQuickSettingsTile":false,"leanbackBannerImage":false,"leanbackLauncherSupport":false,"localActivities":false,"localBroadcastsServices":false,"localOnlyNotifications":false,"logGetPackageName":false,"logcatViewer":false,"longPressBackAction":"NONE","lowMemoryMode":false,"makeAssistApp":false,"makeCameraApp":false,"makeDebuggable":false,"makeHomeApp":false,"makeTestOnly":false,"makeWatchApp":false,"markAsGame":false,"mergeCustomClassesDex":false,"mergeOriginalClassesDex":false,"minSdkVersion":0,"multiWindow":false,"multiWindowNoPause":false,"muteMic":false,"muteOnStart":false,"navigationBarColorUseStatusBarColor":false,"noBackgroundServices":false,"noKill":false,"noOngoingNotifications":false,"noRelayoutOnRotation":false,"notificationCategories":[],"notificationColorUseStatusBarColor":false,"notificationFilter":"","notificationPriority":"NO_CHANGE","notificationQuietTime":false,"notificationQuietTimeEnd":"07:00","notificationQuietTimeStart":"21:00","notificationSnoozeTimeout":0,"notificationSound":"NO_CHANGE","notificationTextReplacements":[],"notificationTimeout":0,"notificationTintStatusBarIcon":false,"notificationVibration":"NO_CHANGE","notificationVisibility":"NO_CHANGE","overrideSharedPreferences":{},"palmRejectionWidthPercentage":0,"passwordProtectApp":false,"penButtonPressedEventAction":"NONE","penDetachedEventAction":"NONE","penInsertedEventAction":"NONE","persistentApp":false,"persistentAppAccessibilityService":false,"persistentClipboard":false,"pictureInPictureKeyCode":0,"pictureInPictureLongPress":false,"pictureInPictureNotification":false,"pictureInPictureSupport":false,"popupBlocker":false,"powerConnectedEventAction":"NONE","powerDisconnectedEventAction":"NONE","powerEventsDockUndockEvents":false,"preserveExpansionFiles":false,"pressBackAgainToExit":false,"preventImmersiveMode":false,"preventScreenshots":false,"privateAccounts":false,"privateClipboard":false,"promptKeepAppDataOnUninstall":false,"randomAndroidId":false,"randomizeBuildProps":false,"redirectExternalStorage":false,"removeLauncherIcon":false,"removeLauncherIconShortcuts":false,"removeNotificationActions":false,"removeNotificationIcon":false,"removeNotificationPeople":false,"removePermissions":[],"replaceLauncherIcon":false,"replaceNotificationIcon":false,"requestAllPermissions":false,"requestIgnoreBatteryOptimizations":false,"restoreAppDataOnEveryStart":false,"restoreAutoRotateOnExit":false,"restoreBluetoothStateOnExit":false,"restoreBrightnessOnExit":false,"restoreInterruptionFilterOnExit":false,"restoreWifiStateOnExit":false,"rotationLock":"NONE","roundIconSupport":false,"safeMode":false,"sandboxExternalStorage":false,"screenTextReplacements":[],"setClipboardDataOnStart":"","shakeAction":"NONE","shakeSensitivity":"NORMAL","showAppInfoNotification":false,"showNotificationTime":false,"showOnLockScreen":false,"showOnSecondaryDisplay":false,"showOnSecondaryDisplayActivitiesNames":[],"showTouches":false,"signAsSystemApp":false,"simpleNotifications":false,"skipNativeLibraries":false,"socksProxy":false,"socksProxyPort":1080,"splashScreen":false,"splashScreenBackgroundColor":-1,"splashScreenDuration":3,"splashScreenMargin":0.3,"spoofLocationInterval":10,"startSound":false,"stealthMode":false,"stealthModeUseFingerprint":false,"stethoSupport":false,"targetSdkVersion":0,"taskerStartTaskName":"","taskerStopTaskName":"","toCloneNumber":8,"toastDuration":"NO_CHANGE","toastFilter":"","toastHorizontalAlignment":"CENTER","toastPosition":false,"toastVerticalAlignment":"BOTTOM","toolbarColorUseStatusBarColor":false,"transparentNavigationBar":false,"trustAllCertificates":false,"twitterLoginBehavior":"WEB_ONLY","useAndHook":false,"versionCode":0,"viewModifications":[],"volumeControlIndicator":"NO_CHANGE","volumeControlIndicatorStep":1,"volumeDownKeyAction":"NONE","volumeRockerLocker":"NONE","volumeUpDownKeyAction":"NONE","volumeUpKeyAction":"NONE","waitForDebugger":false,"welcomeMessageDelay":2000,"welcomeMessageMode":"DIALOG","wideColorGamut":false}'

def executar_root_comando(comando):
    subprocess.run(['su', '-c', comando], capture_output=True)

def ler_configs_ugclone(child_parent_pairs):
    master_xml = "/data/data/com.ugcloner.xfein/shared_prefs/com.ugcloner.xfein_preferences.xml"
    temp_xml = "/data/local/tmp/ugclone_leitura_temp.xml"

    executar_root_comando(f"cat {master_xml} > {temp_xml} && chmod 666 {temp_xml}")
    
    try:
        with open(temp_xml, 'r', encoding='utf-8') as f:
            xml_content = f.read()
    except Exception as e:
        return {"erro": f"Falha ao ler o arquivo: {str(e)}"}
    finally:
        executar_root_comando(f"rm {temp_xml}")
    
    if not xml_content:
        return {"erro": "XML não encontrado ou vazio."}

    # Carrega o padrão de fábrica
    padroes_de_fabrica = json.loads(TEMPLATE_JSON_STR)
    
    # Chaves que SEMPRE queremos salvar para manter a sincronia e as permissões
    CHAVES_VITAIS = ["toCloneNumber", "fromCloneNumber", "batchAppendCloneNumber", "addPermissions", "removePermissions"]

    filhos_setup = {}
    clones_validos = 0

    for child_pkg, parent_pkg in child_parent_pairs:
        regex_child = r'<string name="clone_settings_' + re.escape(child_pkg) + r'">\s*({.*?})\s*</string>'
        regex_parent = r'<string name="clone_settings_' + re.escape(parent_pkg) + r'">\s*({.*?})\s*</string>'
        
        match_child = re.search(regex_child, xml_content, re.DOTALL)
        
        if match_child:
            config_str = html.unescape(match_child.group(1))
            try:
                configs_completas = json.loads(config_str)
                configs_ativas = {}
                
                for chave, valor in configs_completas.items():
                    # Ignorar o identificador único para focar na configuração global da rede
                    if chave == "cloneNumber":
                        continue
                    
                    if chave in padroes_de_fabrica:
                        # Se o usuário alterou algo (Deep ou Básico), ele ficará diferente do padrão!
                        # Ou se for uma chave vital (como as permissões e números), salvamos de qualquer jeito.
                        if valor != padroes_de_fabrica[chave] or chave in CHAVES_VITAIS:
                            
                            # Filtro extra: Não salvar listas vazias para economizar espaço no MongoDB
                            if isinstance(valor, list) and len(valor) == 0:
                                continue
                                
                            configs_ativas[chave] = valor
                
                filhos_setup[child_pkg] = configs_ativas
                clones_validos += 1
            except json.JSONDecodeError:
                filhos_setup[child_pkg] = {"erro": "JSON corrompido."}
        else:
            match_parent = re.search(regex_parent, xml_content, re.DOTALL)
            if match_parent:
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
