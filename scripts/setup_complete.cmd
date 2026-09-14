@echo off
:: ==============================================================================
:: OSBuilder-Win - SetupComplete.cmd
:: Script exécuté automatiquement avec les privilèges NT AUTHORITY\SYSTEM
:: à la fin du processus d'installation de Windows, avant l'ouverture de session.
:: ==============================================================================

echo [OSBuilder-Win] Initialisation des finitions post-installation... >> %WINDIR%\Temp\osbuilder_postinstall.log

:: 1. Suppression de l'installateur résiduel de OneDrive
if exist "%SystemRoot%\System32\OneDriveSetup.exe" (
    "%SystemRoot%\System32\OneDriveSetup.exe" /uninstall >nul 2>&1
)
if exist "%SystemRoot%\SysWOW64\OneDriveSetup.exe" (
    "%SystemRoot%\SysWOW64\OneDriveSetup.exe" /uninstall >nul 2>&1
)

:: 2. Désactivation des tâches planifiées de télémétrie résiduelles
schtasks /change /tn "\Microsoft\Windows\Customer Experience Improvement Program\Consolidator" /disable >nul 2>&1
schtasks /change /tn "\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip" /disable >nul 2>&1
schtasks /change /tn "\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser" /disable >nul 2>&1
schtasks /change /tn "\Microsoft\Windows\Application Experience\ProgramDataUpdater" /disable >nul 2>&1
schtasks /change /tn "\Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector" /disable >nul 2>&1

:: 3. Activation du plan d'alimentation Haute Performance (GUID standard)
powercfg -duplicatescheme 8c5e7fda-e83c-4450-b1a4-53c93843f2e0 >nul 2>&1
powercfg -setactive 8c5e7fda-e83c-4450-b1a4-53c93843f2e0 >nul 2>&1

:: 4. Désactivation de l'hibernation (Suppression de hiberfil.sys pour libérer 8 à 32 Go sur SSD)
powercfg /hibernate off >nul 2>&1

:: 5. Nettoyage des caches d'installation temporaires
del /q /f "%WINDIR%\Logs\CBS\*.log" >nul 2>&1

echo [OSBuilder-Win] Finitions post-installation terminées avec succès. >> %WINDIR%\Temp\osbuilder_postinstall.log
exit /b 0
