@echo off
setlocal EnableDelayedExpansion
title OSBuilder-Win Launcher - LordMadTrix

cd /d "%~dp0"
chcp 65001 >nul

:: Verification des droits Administrateur
fltmc >nul 2>&1
if %errorLevel% equ 0 (
    set "IS_ADMIN=1"
    set "ADMIN_STATUS=[Privileges Administrateur : ACTIF]"
) else (
    set "IS_ADMIN=0"
    set "ADMIN_STATUS=[ATTENTION : Mode Standard - Droits Administrateur recommandes]"
)

:: Detection intelligente de Python
set "PYTHON_EXE="

py -3 -c "import PyQt6" >nul 2>&1
if %errorLevel% equ 0 (
    set "PYTHON_EXE=py -3"
    goto PYTHON_READY
)

python -c "import PyQt6" >nul 2>&1
if %errorLevel% equ 0 (
    set "PYTHON_EXE=python"
    goto PYTHON_READY
)

py -3 --version >nul 2>&1
if %errorLevel% equ 0 (
    set "PYTHON_EXE=py -3"
    goto PYTHON_READY
)

python --version >nul 2>&1
if %errorLevel% equ 0 (
    set "PYTHON_EXE=python"
    goto PYTHON_READY
)

echo.
echo ==============================================================================
echo  [ERREUR CRITIQUE] Python n'est pas detecte sur votre machine.
echo  Veuillez installer Python 3.10+ depuis https://www.python.org/
echo  Pensez a cocher l'option "Add Python to PATH" lors de l'installation.
echo ==============================================================================
echo.
pause
exit /b 1

:PYTHON_READY
:: Verification des modules requis
%PYTHON_EXE% -c "import rich, yaml, pydantic, PyQt6" >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo [INFO] Installation des modules requis [rich, pyyaml, pydantic, PyQt6]...
    %PYTHON_EXE% -m pip install -r requirements.txt
    if %errorLevel% neq 0 (
        echo [ERREUR] Impossible d'installer les dependances avec pip.
        pause
        exit /b 1
    )
)

:MENU
cls
echo.
echo ==============================================================================
echo    ____   _____ ____        _ _     _              __          ___       
echo   / __ \ / ____^|  _ \      (_) ^|   ^| ^|             \ \        / (_)      
echo  ^| ^|  ^| ^| (___ ^| ^|_) ^|_   _ _^| ^| __^| ^| ___ _ __ ____\ \  /\  / / _ _ __  
echo  ^| ^|  ^| ^|\___ \^|  _ ^<^| ^| ^| ^| ^| ^|/ _` ^|/ _ \ '__^|_____\ \/  \/ / ^| ^| '_ \ 
echo  ^| ^|__^| ^|____) ^| ^|_) ^| ^|_^| ^| ^| ^| (_^| ^|  __/ ^|         \  /\  /  ^| ^| ^| ^| ^|
echo   \____/^|_____/^|____/ \__,_^_^_^|\__,_^|\___^_^_^|          \/  \/   ^|_^_^_^| ^|_^|
echo.
echo      Generateur d'images Windows 7, 10, 11 - LordMadTrix
echo      %ADMIN_STATUS%
echo ==============================================================================
echo.
if "%IS_ADMIN%"=="0" echo   [0] Relancer en mode Administrateur [UAC]
echo   [1] Lancer l'Interface Graphique (PyQt6) [Recommande]
echo   [2] Lancer OSBuilder-Win en Console [Mode Interactif CLI]
echo   [3] Telecharger des ISOs Officielles Microsoft [Fido / Rufus]
echo   [4] Diagnostiquer l'environnement et les outils [--check-env]
echo   [5] Afficher la liste des profils de build disponibles
echo   [6] Executer la suite de tests unitaires
echo   [7] Quitter
echo.
echo ==============================================================================

choice /c 01234567 /n /m "Entrez votre choix [0-7] : "
set "SEL=%errorLevel%"

if "%SEL%"=="8" goto DO_EXIT
if "%SEL%"=="7" goto DO_TESTS
if "%SEL%"=="6" goto DO_PROFILES
if "%SEL%"=="5" goto DO_CHECK
if "%SEL%"=="4" goto DO_FIDO
if "%SEL%"=="3" goto DO_CLI
if "%SEL%"=="2" goto DO_GUI
if "%SEL%"=="1" goto DO_ELEVATE

goto MENU

:DO_ELEVATE
echo.
echo [UAC] Declenchement de la demande d'elevation Administrateur...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath cmd.exe -ArgumentList @('/k', 'call', '""%~f0""') -Verb RunAs"
exit /b 0

:DO_GUI
cls
echo [INFO] Demarrage de l'interface graphique PyQt6...
start "" %PYTHON_EXE% gui.py
goto DO_EXIT

:DO_CLI
cls
%PYTHON_EXE% cli.py
echo.
pause
goto MENU

:DO_FIDO
cls
echo [INFO] Lancement de l'outil officiel Microsoft Fido (Rufus)...
start powershell.exe -NoProfile -ExecutionPolicy Bypass -File "tools\Fido.ps1"
goto MENU

:DO_CHECK
cls
%PYTHON_EXE% cli.py --check-env
echo.
pause
goto MENU

:DO_PROFILES
cls
%PYTHON_EXE% cli.py --list-profiles
echo.
pause
goto MENU

:DO_TESTS
cls
echo [TESTS] Execution de la suite de tests unitaires...
%PYTHON_EXE% -m unittest tests/test_osbuilder.py
echo.
pause
goto MENU

:DO_EXIT
exit /b 0
