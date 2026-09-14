<#
.SYNOPSIS
    Lanceur PowerShell pour OSBuilder-Win avec élévation UAC automatique.
.DESCRIPTION
    Vérifie les prérequis, élève les privilèges si nécessaire et lance OSBuilder-Win.
#>

[CmdletBinding()]
param(
    [switch]$CheckEnv,
    [switch]$ListProfiles,
    [string]$Profile,
    [string]$ISO,
    [string]$Output
)

# 1. Vérification des droits Administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[OSBuilder-Win] Droits Administrateur requis. Déclenchement de l'élévation UAC..." -ForegroundColor Yellow
    $scriptPath = $MyInvocation.MyCommand.Path
    
    $argArray = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $scriptPath)
    if ($CheckEnv) { $argArray += "-CheckEnv" }
    if ($ListProfiles) { $argArray += "-ListProfiles" }
    if ($Profile) { $argArray += @("-Profile", $Profile) }
    if ($ISO) { $argArray += @("-ISO", $ISO) }
    if ($Output) { $argArray += @("-Output", $Output) }

    Start-Process pwsh.exe -ArgumentList $argArray -WorkingDirectory $PSScriptRoot -Verb RunAs -ErrorAction SilentlyContinue
    if (-not $?) {
        Start-Process powershell.exe -ArgumentList $argArray -WorkingDirectory $PSScriptRoot -Verb RunAs
    }
    exit
}

# 2. Se placer dans le répertoire du script
Set-Location -Path $PSScriptRoot
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 3. Vérification de Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Host "[ERREUR] Python n'a pas été trouvé dans le PATH." -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour quitter..."
    exit 1
}

# 4. Exécution selon les arguments
if ($CheckEnv) {
    & $pythonCmd.Source cli.py --check-env
    exit $LASTEXITCODE
}

if ($ListProfiles) {
    & $pythonCmd.Source cli.py --list-profiles
    exit $LASTEXITCODE
}

if ($Profile -and $ISO -and $Output) {
    & $pythonCmd.Source cli.py --profile $Profile --iso $ISO --output $Output
    exit $LASTEXITCODE
}

# Mode interactif par défaut
& $pythonCmd.Source cli.py
