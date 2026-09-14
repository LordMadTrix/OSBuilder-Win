"""
Gestion de la configuration et des profils de build pour OSBuilder-Win.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import yaml


class TargetOS(str, Enum):
    WIN7 = "win7"
    WIN10 = "win10"
    WIN11 = "win11"


class CompressionType(str, Enum):
    FAST = "fast"          # LZX rapide
    MAXIMUM = "maximum"    # LZX compression max (standard WIM)
    RECOVERY = "recovery"  # LZMS compression ultra (ESD compact)


class UnattendedConfig(BaseModel):
    enabled: bool = True
    admin_username: str = "Admin"
    admin_password: Optional[str] = ""
    computer_name: str = "WORK-PC"
    time_zone: str = "Romance Standard Time"
    locale: str = "fr-FR"
    keyboard_layout: str = "040c:0000040c"
    bypass_nro: bool = True  # Bypass compte Microsoft sous Windows 11
    auto_logon: bool = False
    skip_eula: bool = True
    skip_oobe: bool = True
    product_key: Optional[str] = None  # Clé générique d'installation (KMS / Setup Key)
    auto_disk_partition: bool = False  # Installation 100% zéro-clic : formater et partitionner le disque en GPT/UEFI
    disk_id: int = 0  # Index du disque cible pour le partitionnement automatique
    use_builtin_admin: bool = False  # Activer directement le compte Administrateur natif
    display_resolution: str = "1920x1080"  # Résolution d'affichage native pour WinPE Setup et OOBE
    first_logon_commands: List[str] = Field(default_factory=list)  # Commandes exécutées à la première ouverture de session utilisateur


class AppxPreset(str, Enum):
    NONE = "none"
    LIGHT = "light"
    RECOMMENDED = "recommended"
    AGGRESSIVE = "aggressive"


class Win7Options(BaseModel):
    inject_nvme: bool = True
    inject_usb3: bool = True
    nvme_drivers_dir: Optional[str] = None
    usb3_drivers_dir: Optional[str] = None


class Win11Options(BaseModel):
    bypass_tpm: bool = True
    bypass_secureboot: bool = True
    bypass_ram: bool = True
    bypass_cpu: bool = True
    bypass_storage: bool = True
    classic_context_menu: bool = True
    disable_copilot: bool = True
    disable_recall: bool = True
    disable_widgets: bool = True
    disable_advertising_id: bool = True
    disable_smartscreen_telemetry: bool = False
    prevent_automatic_bitlocker: bool = True  # Désactive le chiffrement BitLocker automatique imposé par Windows 11 24H2
    disable_onedrive_autoinstall: bool = True  # Bloque l'auto-installation de OneDrive et son icône explorateur
    taskbar_align_left: bool = True  # Aligner la barre des tâches à gauche (style Windows 10/7 classique)
    disable_taskbar_chat: bool = True  # Masquer l'icône Chat / Teams de la barre des tâches
    disable_device_setup_suggestions: bool = True  # Désactiver les écrans de harcèlement OOBE post-boot
    disable_lockscreen_tips: bool = True  # Désactiver les astuces et pubs Bing sur l'écran de verrouillage


class OemOptions(BaseModel):
    enabled: bool = False
    manufacturer: str = "LordMadTrix Custom Rig"
    model: str = "OSBuilder-Win Gaming Edition"
    support_hours: str = "24/7"
    support_phone: str = ""
    support_url: str = "https://github.com/LordMadTrix"
    logo_path: Optional[str] = None       # Chemin vers oemlogo.bmp (120x120 pixels)
    wallpaper_path: Optional[str] = None  # Chemin vers img0.jpg personnalisé


class ExplorerOptions(BaseModel):
    show_file_extensions: bool = True
    show_hidden_files: bool = False
    open_to_this_pc: bool = True
    dark_mode: bool = True
    hide_3d_objects: bool = True
    add_take_ownership: bool = True  # Ajoute 'Prendre possession' au menu contextuel
    disable_start_web_search: bool = True  # Désactive la recherche Bing web dans le menu Démarrer
    add_restart_explorer_context_menu: bool = False  # Ajoute 'Redémarrer l'Explorateur' au menu contextuel
    add_open_with_notepad: bool = False  # Ajoute 'Ouvrir avec le Bloc-notes'
    add_cmd_admin_here: bool = False  # Ajoute 'Invite de commandes Administrateur ici'
    apply_mados_theme: bool = False  # Applique le style d'environnement MadOS à Windows (Dark mode, accent cyan #00f0ff, DWM réactif)
    mados_accent_color: str = "#00f0ff"  # Couleur d'accentuation DWM pour le thème MadOS


class ServicesOptions(BaseModel):
    disable_sysmain: bool = False  # Utile pour les SSDs
    disable_indexing: bool = False  # Windows Search
    disable_spooler: bool = False  # Spouleur d'impression si sans imprimante
    disable_error_reporting: bool = True  # WerSvc
    disable_remote_registry: bool = True  # Sécurité
    disable_fast_startup: bool = True  # Évite les corruptions et libère hiberfil.sys
    disable_telemetry_tasks: bool = True  # Désactive les tâches planifiées de télémétrie (Compat Tel Runner...)
    disable_windows_update_auto_reboot: bool = True  # Empêche les redémarrages inopinés lors des MàJ
    disable_delivery_optimization: bool = True  # Désactive DoSvc (partage P2P de bande passante)


class FeaturesOptions(BaseModel):
    enable_net35: bool = True  # .NET Framework 3.5 hors-ligne depuis sources\sxs
    enable_directplay: bool = True  # DirectPlay pour le gaming rétro
    disable_nagle_algorithm: bool = True  # TcpAckFrequency=1 / TCPNoDelay=1 (latence réseau minimale)
    disable_reserved_storage: bool = True  # Désactive les ~7 Go d'espace réservé de Windows Update
    enable_ultimate_performance: bool = True  # Débloque le plan d'alimentation Performances Ultimes
    enable_hags: bool = True  # Active l'accélération matérielle du GPU (HAGS)
    optimize_ntfs_trim: bool = True  # Force l'activation du TRIM SSD et désactive l'horodatage superflu
    disable_hpet_synthetic: bool = True  # Optimise la réactivité des timers multimédia gaming
    optimize_mmcss_latency: bool = True  # Priorise à 100% les jeux et le multimédia (SystemResponsiveness=0)
    optimize_processor_scheduling: bool = True  # Priorité maximale aux processus de premier plan (Win32PrioritySeparation)
    disable_edge_prelaunch: bool = True  # Empêche Microsoft Edge de s'exécuter en tâche de fond au démarrage
    disable_edge_telemetry: bool = True  # Désactive la télémétrie, suggestions et pubs Edge
    disable_smartscreen: bool = False  # Désactive SmartScreen pour les applications téléchargées
    optimize_memory_paging: bool = True  # Maintient le noyau et drivers en RAM physique (DisablePagingExecutive)


class PostInstallOptions(BaseModel):
    install_vcredist: bool = True  # Visual C++ Redistributable All-In-One
    winget_apps: List[str] = Field(default_factory=list)  # Identifiants WinGet (ex: 7zip.7zip)
    enable_hwid_activation: bool = False  # Activation permanente HWID (Massgrave) au 1er boot


class RegistryTweakRule(BaseModel):
    hive: str  # 'SOFTWARE', 'SYSTEM', 'NTUSER'
    path: str
    name: str
    type: str = "REG_DWORD"  # 'REG_DWORD', 'REG_SZ', 'REG_EXPAND_SZ', etc.
    value: Any


class BuildProfile(BaseModel):
    name: str
    description: str = ""
    target_os: TargetOS
    architecture: str = "x64"
    image_index: int = 1
    
    # Pilotes et Mises à jour
    driver_dirs: List[str] = Field(default_factory=list)
    update_files: List[str] = Field(default_factory=list)
    updates_dir: Optional[str] = None  # Dossier contenant des paquets .msu/.cab ordonnancés automatiquement
    intel_vmd_drivers_dir: Optional[str] = None  # Pilotes Intel VMD / RST pour détection NVMe moderne
    auto_inject_host_network_drivers: bool = False  # Capture et injection automatique des pilotes Wi-Fi/LAN de la machine hôte
    inject_drivers_to_winre: bool = True  # Injecte automatiquement les pilotes de stockage/réseau dans Winre.wim (Environnement de Récupération)
    setup_complete_commands: List[str] = Field(default_factory=list)  # Commandes exécutées par NT AUTHORITY\SYSTEM avant le premier login OOBE
    
    # Paquets & Fonctionnalités
    remove_appx_patterns: List[str] = Field(default_factory=list)
    appx_preset: AppxPreset = AppxPreset.NONE  # Profil de debloat préconfiguré
    enable_features: List[str] = Field(default_factory=list)
    disable_features: List[str] = Field(default_factory=list)
    add_capabilities: List[str] = Field(default_factory=list)
    remove_capabilities: List[str] = Field(default_factory=list)
    
    # Optimisations et Tweaks
    disable_telemetry: bool = True
    optimize_services: bool = True
    enable_gaming_tweaks: bool = False
    custom_registry_tweaks: List[RegistryTweakRule] = Field(default_factory=list)
    
    # Nouvelles options granulaires
    explorer: ExplorerOptions = Field(default_factory=ExplorerOptions)
    services: ServicesOptions = Field(default_factory=ServicesOptions)
    system_features: FeaturesOptions = Field(default_factory=FeaturesOptions)
    post_install: PostInstallOptions = Field(default_factory=PostInstallOptions)
    oem: OemOptions = Field(default_factory=OemOptions)

    # Spécificités OS
    win7: Win7Options = Field(default_factory=Win7Options)
    win11: Win11Options = Field(default_factory=Win11Options)
    
    # Automatisation
    unattended: UnattendedConfig = Field(default_factory=UnattendedConfig)
    
    # Optimisation de taille & Découpage WIM
    single_edition_only: bool = False  # N'exporter que l'édition cible choisie pour alléger l'ISO de 40%
    compression_type: CompressionType = CompressionType.MAXIMUM  # Type de compression wim/esd
    split_wim_fat32: bool = False  # Découpage WIM pour compatibilité FAT32 / Clé USB UEFI
    cleanup_component_store: bool = False  # Nettoyage WinSxS /StartComponentCleanup /ResetBase pour alléger install.wim de 1 à 3 Go

    # Scripts post-installation
    post_install_scripts: List[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        """Exporte le profil sous forme de dictionnaire compatible JSON."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "BuildProfile":
        """Reconstruit une instance de BuildProfile à partir d'un dictionnaire."""
        return cls(**data)


def load_profile_from_yaml(file_path: Path | str) -> BuildProfile:
    """Charge et valide un profil YAML avec Pydantic."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Le fichier de profil n'existe pas : {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    
    return BuildProfile(**data)


def save_profile_to_yaml(profile: BuildProfile, file_path: Path | str) -> None:
    """Sauvegarde un profil au format YAML."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    data = profile.model_dump(mode="json")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
