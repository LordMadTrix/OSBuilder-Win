@echo off
setlocal EnableDelayedExpansion
title OSBuilder-Win Studio - Script d'Installation Rapide

echo ==============================================================================
echo   OSBuilder-Win Studio v2.5 PRO - Assistant d'Installation Rapide
echo   Developpe pour LordMadTrix
echo ==============================================================================
echo.

set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"

echo [1/3] Verification des dependances Python...
python -c "import PyQt6, PIL, yaml, pydantic; print('OK: Dependances detectees avec succes.')" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Installation des modules Python requis...
    python -m pip install -r "%APP_DIR%\requirements.txt" --quiet
)

echo [2/3] Verification des binaires natifs...
if not exist "%APP_DIR%\OSBuilder-Win.exe" (
    echo [COMPILATION] Compilation de OSBuilder-Win.exe...
    C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /target:winexe /win32icon:"%APP_DIR%\app.ico" /out:"%APP_DIR%\OSBuilder-Win.exe" "%APP_DIR%\launcher.cs" >nul 2>&1
)

echo [3/3] Creation des raccourcis Bureau et Menu Demarrer...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\OSBuilder-Win.lnk'); $Shortcut.TargetPath = '%APP_DIR%\OSBuilder-Win.exe'; $Shortcut.WorkingDirectory = '%APP_DIR%'; $Shortcut.IconLocation = '%APP_DIR%\app.ico'; $Shortcut.Save();"

echo.
echo ==============================================================================
echo   [SUCCES] OSBuilder-Win Studio est pret a l'emploi !
echo   Un raccourci a ete place sur votre Bureau Windows.
echo ==============================================================================
echo.
pause
