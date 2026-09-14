"""
Module de gestion et de déploiement d'applications (WinGet & Logiciels Hors-ligne).
Fournit un catalogue préconfiguré de logiciels indispensables (Gaming, Dev, Runtimes, Utilitaires)
et génère les scripts d'installation silencieuse pour le premier démarrage.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AppItem:
    id: str
    name: str
    category: str
    description: str
    winget_id: str
    choco_id: Optional[str] = None
    default_selected: bool = False
    icon_name: str = "app"


# Catalogue préconfiguré de logiciels haute qualité
APP_CATALOG: List[AppItem] = [
    # Runtimes & Essentiels
    AppItem(
        id="vcredist_aio",
        name="Visual C++ All-In-One",
        category="runtimes",
        description="Packs de bibliothèques runtime VC++ 2005 à 2022 x86/x64 indispensables aux jeux et applications.",
        winget_id="Microsoft.VCRedist.2015+.x64",
        default_selected=True,
    ),
    AppItem(
        id="directx_runtime",
        name="DirectX End-User Runtimes",
        category="runtimes",
        description="Composants et DLLs DirectX 9.0c / 10 / 11 pour une compatibilité parfaite avec tous les jeux.",
        winget_id="Microsoft.DirectX",
        default_selected=True,
    ),
    AppItem(
        id="dotnet_runtime_8",
        name=".NET Desktop Runtime 8.0",
        category="runtimes",
        description="Environnement d'exécution .NET 8 moderne pour les outils Windows récents.",
        winget_id="Microsoft.DotNet.DesktopRuntime.8",
        default_selected=False,
    ),
    AppItem(
        id="sevenzip",
        name="7-Zip (64-bit)",
        category="runtimes",
        description="Gestionnaire d'archives ultra-rapide et gratuit avec compression maximale LZMA2.",
        winget_id="7zip.7zip",
        default_selected=True,
    ),

    # Gaming & Esport
    AppItem(
        id="steam",
        name="Steam",
        category="gaming",
        description="Plateforme de distribution de jeux vidéo de Valve Corporation.",
        winget_id="Valve.Steam",
        default_selected=True,
    ),
    AppItem(
        id="discord",
        name="Discord",
        category="gaming",
        description="Messagerie vocale et textuelle optimisée pour les gamers et créateurs.",
        winget_id="Discord.Discord",
        default_selected=True,
    ),
    AppItem(
        id="obs_studio",
        name="OBS Studio",
        category="gaming",
        description="Logiciel open source d'enregistrement et de streaming vidéo haute performance.",
        winget_id="OBSProject.OBSStudio",
        default_selected=False,
    ),
    AppItem(
        id="msi_afterburner",
        name="MSI Afterburner",
        category="gaming",
        description="Utilitaire référence d'overclocking GPU, surveillance des températures et frametime.",
        winget_id="Guru3D.Afterburner",
        default_selected=False,
    ),
    AppItem(
        id="heroic_launcher",
        name="Heroic Games Launcher",
        category="gaming",
        description="Lanceur alternatif léger et open source pour Epic Games, GOG et Amazon Games.",
        winget_id="HeroicGamesLauncher.HeroicGamesLauncher",
        default_selected=False,
    ),
    AppItem(
        id="prismlauncher",
        name="Prism Launcher",
        category="gaming",
        description="Lanceur Minecraft haute performance prenant en charge Fabric, Forge, et modpacks multiples.",
        winget_id="PrismLauncher.PrismLauncher",
        default_selected=False,
    ),

    # Navigateurs Web
    AppItem(
        id="brave_browser",
        name="Brave Browser",
        category="browsers",
        description="Navigateur Web ultra-rapide basé sur Chromium avec bloqueur publicitaire et anti-trackers natif.",
        winget_id="Brave.Brave",
        default_selected=False,
    ),
    AppItem(
        id="firefox",
        name="Mozilla Firefox",
        category="browsers",
        description="Navigateur Web respectueux de la vie privée propulsé par le moteur Gecko indépendant.",
        winget_id="Mozilla.Firefox",
        default_selected=True,
    ),
    AppItem(
        id="google_chrome",
        name="Google Chrome",
        category="browsers",
        description="Navigateur Web standard de Google avec synchronisation de compte intégrée.",
        winget_id="Google.Chrome",
        default_selected=False,
    ),
    AppItem(
        id="librewolf",
        name="LibreWolf",
        category="browsers",
        description="Version durcie et ultra-sécurisée de Firefox axée à 100% sur la confidentialité.",
        winget_id="LibreWolf.LibreWolf",
        default_selected=False,
    ),

    # Outils Développeur & Système
    AppItem(
        id="vscode",
        name="Visual Studio Code",
        category="dev_tools",
        description="Éditeur de code extensible et puissant conçu par Microsoft.",
        winget_id="Microsoft.VisualStudioCode",
        default_selected=False,
    ),
    AppItem(
        id="git",
        name="Git pour Windows",
        category="dev_tools",
        description="Système de contrôle de version distribué rapide et standardisé.",
        winget_id="Git.Git",
        default_selected=False,
    ),
    AppItem(
        id="python3",
        name="Python 3.12",
        category="dev_tools",
        description="Langage de programmation moderne polyvalent et moteur de scripts d'automatisation.",
        winget_id="Python.Python.3.12",
        default_selected=False,
    ),
    AppItem(
        id="nodejs_lts",
        name="Node.js (LTS)",
        category="dev_tools",
        description="Environnement d'exécution JavaScript côté serveur asynchrone et événementiel.",
        winget_id="OpenJS.NodeJS.LTS",
        default_selected=False,
    ),
    AppItem(
        id="windows_terminal",
        name="Windows Terminal",
        category="dev_tools",
        description="Terminal moderne à onglets pour PowerShell, CMD et distributions WSL Linux.",
        winget_id="Microsoft.WindowsTerminal",
        default_selected=True,
    ),
    AppItem(
        id="powertoys",
        name="Microsoft PowerToys",
        category="dev_tools",
        description="Suite d'utilitaires avancés (FancyZones, PowerToys Run, Color Picker, Text Extractor).",
        winget_id="Microsoft.PowerToys",
        default_selected=False,
    ),
    AppItem(
        id="notepad_plus_plus",
        name="Notepad++",
        category="dev_tools",
        description="Éditeur de texte brut et de code source ultra-léger avec coloration syntaxique.",
        winget_id="Notepad++.Notepad++",
        default_selected=False,
    ),

    # Utilitaires & Diagnostics Système
    AppItem(
        id="hwinfo64",
        name="HWiNFO64",
        category="utilities",
        description="Outil de diagnostic matériel en temps réel et monitoring thermique précis des composants.",
        winget_id="REALiX.HWiNFO",
        default_selected=True,
    ),
    AppItem(
        id="crystaldiskinfo",
        name="CrystalDiskInfo",
        category="utilities",
        description="Surveillance de l'état de santé SMART des disques durs et SSDs NVMe/SATA.",
        winget_id="CrystalDewWorld.CrystalDiskInfo",
        default_selected=False,
    ),
    AppItem(
        id="system_informer",
        name="System Informer (Process Hacker)",
        category="utilities",
        description="Gestionnaire de tâches et moniteur de processus avancé avec analyse mémoire et réseau en direct.",
        winget_id="SystemInformer.SystemInformer",
        default_selected=False,
    ),
    AppItem(
        id="voidtools_everything",
        name="Everything (Voidtools)",
        category="utilities",
        description="Moteur de recherche instantané de fichiers sur volumes NTFS indexant des millions de fichiers en ms.",
        winget_id="voidtools.Everything",
        default_selected=True,
    ),
    AppItem(
        id="geek_uninstaller",
        name="Geek Uninstaller",
        category="utilities",
        description="Désinstallateur propre éliminant toutes les traces et résidus de registre des logiciels.",
        winget_id="GeekUninstaller.GeekUninstaller",
        default_selected=False,
    ),
    AppItem(
        id="bleachbit",
        name="BleachBit",
        category="utilities",
        description="Nettoyeur open source de fichiers temporaires, caches et traces de vie privée.",
        winget_id="BleachBit.BleachBit",
        default_selected=False,
    ),

    # Multimédia & Audio
    AppItem(
        id="vlc",
        name="VLC Media Player",
        category="multimedia",
        description="Lecteur multimédia universel prenant en charge quasiment tous les codecs vidéo et audio.",
        winget_id="VideoLAN.VLC",
        default_selected=True,
    ),
    AppItem(
        id="mpc_hc",
        name="MPC-HC (K-Lite Codec Pack Standard)",
        category="multimedia",
        description="Media Player Classic Home Cinema ultra-léger avec rendu madVR et filtres LAV.",
        winget_id="CodecGuide.K-LiteCodecPack.Standard",
        default_selected=False,
    ),
    AppItem(
        id="spotify",
        name="Spotify",
        category="multimedia",
        description="Application de streaming musical et podcasts.",
        winget_id="Spotify.Spotify",
        default_selected=False,
    ),
]


CATEGORY_LABELS: Dict[str, str] = {
    "runtimes": "🧱 Runtimes & Essentiels",
    "gaming": "🎮 Gaming & Streaming",
    "browsers": "🌐 Navigateurs Web",
    "dev_tools": "💻 Outils Développeur & Shell",
    "utilities": "🔧 Utilitaires & Diagnostics",
    "multimedia": "🎬 Multimédia & Audio",
}


class AppBundler:
    """Gestionnaire de catalogue et générateur de scripts d'installation silencieuse."""

    @staticmethod
    def get_catalog() -> List[AppItem]:
        """Retourne l'ensemble du catalogue d'applications."""
        return APP_CATALOG

    @staticmethod
    def get_categories() -> List[str]:
        """Retourne la liste des identifiants de catégories disponibles."""
        return list(CATEGORY_LABELS.keys())

    @staticmethod
    def get_category_label(category: str) -> str:
        """Retourne le libellé formaté d'une catégorie."""
        return CATEGORY_LABELS.get(category, category.capitalize())

    @staticmethod
    def get_apps_by_category(category: str) -> List[AppItem]:
        """Filtre les applications par catégorie."""
        return [app for app in APP_CATALOG if app.category == category]

    @staticmethod
    def get_app_by_id(app_id: str) -> Optional[AppItem]:
        """Recherche une application par son identifiant unique."""
        for app in APP_CATALOG:
            if app.id == app_id:
                return app
        return None

    @staticmethod
    def get_app_by_winget_id(winget_id: str) -> Optional[AppItem]:
        """Recherche une application par son identifiant WinGet."""
        for app in APP_CATALOG:
            if app.winget_id.lower() == winget_id.lower():
                return app
        return None

    @staticmethod
    def generate_winget_powershell_script(
        winget_ids: List[str],
        log_path: str = r"C:\Windows\Temp\winget_install.log"
    ) -> str:
        """
        Génère un script PowerShell résilient qui installe les paquets WinGet sélectionnés
        au premier démarrage de la machine avec gestion d'erreurs et log détaillé.
        """
        if not winget_ids:
            return ""

        apps_array_str = ", ".join(f'"{wid}"' for wid in winget_ids)

        script = f"""# Script d'installation automatique d'applications WinGet
# Généré par OSBuilder-Win Studio PRO
$ErrorActionPreference = "Continue"
$LogPath = "{log_path}"

Function LogWrite {{
    Param([string]$Text)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Line = "[$Timestamp] $Text"
    Write-Output $Line
    Add-Content -Path $LogPath -Value $Line -ErrorAction SilentlyContinue
}}

LogWrite "=== DÉMARRAGE INSTALLATION DES APPLICATIONS WINGET ==="
$Apps = @({apps_array_str})

# Vérifier si winget est disponible dans le PATH
$WingetExe = (Get-Command winget -ErrorAction SilentlyContinue).Source
if (-not $WingetExe) {{
    $PossiblePath = "$env:LOCALAPPDATA\\Microsoft\\WindowsApps\\winget.exe"
    if (Test-Path $PossiblePath) {{
        $WingetExe = $PossiblePath
    }}
}}

if (-not $WingetExe) {{
    LogWrite "[AVERTISSEMENT] WinGet n'est pas encore disponible dans l'environnement courant."
    LogWrite "[INFO] Les applications seront installées dès la mise à jour du Store / App Installer."
    exit 0
}}

LogWrite "WinGet binaire détecté : $WingetExe"

foreach ($AppId in $Apps) {{
    LogWrite "Installation de : $AppId ..."
    try {{
        & $WingetExe install --id $AppId --exact --silent --accept-source-agreements --accept-package-agreements --disable-interactivity
        if ($LASTEXITCODE -eq 0) {{
            LogWrite "[SUCCÈS] $AppId installé avec succès."
        }} else {{
            LogWrite "[ATTENTION] Code retour pour $AppId : $LASTEXITCODE"
        }}
    }} catch {{
        LogWrite "[ERREUR] Échec de l'installation de $AppId : $_"
    }}
}}

LogWrite "=== INSTALLATION DES APPLICATIONS WINGET TERMINÉE ==="
"""
        return script

    @staticmethod
    def generate_offline_apps_installer_script(
        apps_folder: str = r"C:\Windows\Setup\Apps",
        log_path: str = r"C:\Windows\Temp\offline_apps_install.log"
    ) -> str:
        """
        Génère un script PowerShell pour installer automatiquement tous les installeurs
        .exe, .msi ou scripts .ps1 présents dans le dossier hors-ligne Windows\\Setup\\Apps\\.
        """
        script = f"""# Script d'installation silencieuse des exécutables hors-ligne
# Généré par OSBuilder-Win Studio PRO
$ErrorActionPreference = "Continue"
$AppsDir = "{apps_folder}"
$LogPath = "{log_path}"

Function LogWrite {{
    Param([string]$Text)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Line = "[$Timestamp] $Text"
    Write-Output $Line
    Add-Content -Path $LogPath -Value $Line -ErrorAction SilentlyContinue
}}

if (-not (Test-Path $AppsDir)) {{
    LogWrite "Aucun dossier $AppsDir trouvé. Fin du script."
    exit 0
}}

LogWrite "=== DÉMARRAGE INSTALLATION DES LOGICIELS HORS-LIGNE ==="

# 1. Traitement des installateurs MSI
Get-ChildItem -Path $AppsDir -Filter "*.msi" -Recurse | ForEach-Object {{
    LogWrite "Installation MSI : $($_.Name) ..."
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$($_.FullName)`" /qn /norestart" -Wait
    LogWrite "[OK] Terminé pour $($_.Name)"
}}

# 2. Traitement des installateurs EXE (InnoSetup, NSIS, InstallShield flags)
Get-ChildItem -Path $AppsDir -Filter "*.exe" -Recurse | ForEach-Object {{
    LogWrite "Installation EXE : $($_.Name) ..."
    # Tente les paramètres silencieux universels
    $proc = Start-Process -FilePath $_.FullName -ArgumentList "/silent /quiet /qn /s /VERYSILENT /NORESTART" -Wait -PassThru
    LogWrite "[OK] Terminé pour $($_.Name) (Code: $($proc.ExitCode))"
}}

# 3. Traitement des scripts PowerShell personnalisés
Get-ChildItem -Path $AppsDir -Filter "*.ps1" -Recurse | ForEach-Object {{
    LogWrite "Exécution Script PS1 : $($_.Name) ..."
    & powershell.exe -ExecutionPolicy Bypass -File $_.FullName
    LogWrite "[OK] Terminé pour $($_.Name)"
}}

LogWrite "=== TOUTES LES APPLICATIONS HORS-LIGNE ONT ÉTÉ TRAITÉES ==="
"""
        return script
