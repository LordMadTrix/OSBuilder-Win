"""
Module de gestion avancée des Fonctionnalités Windows (OptionalFeatures)
et Capacités à la Demande (Features On Demand - FOD) via DISM.
Fournit des profils prédéfinis : Gaming, Développeur, Durcissement Sécurité, Ultra-Lite.
"""

from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional
from core.dism_manager import DismManager


class FeaturePreset(str, Enum):
    NONE = "none"
    GAMING = "gaming"
    DEVELOPER = "developer"
    HARDENED = "hardened"
    SUPERLITE = "superlite"


# Capacités obsolètes ou superflues à supprimer pour un système léger
BLOAT_CAPABILITIES = [
    "MathRecognizer~~~~0.0.1.0",
    "App.StepsRecorder~~~~0.0.1.0",
    "Microsoft.Windows.WordPad~~~~0.0.1.0",
    "Media.WindowsMediaPlayer~~~~0.0.12.0",
    "Browser.InternetExplorer~~~~0.0.11.0",
    "App.Support.QuickAssist~~~~0.0.1.0",
    "Print.Fax.Scan~~~~0.0.1.0",
    "XPS.Viewer~~~~0.0.1.0",
]

# Fonctionnalités par profil prédéfini
PRESET_CONFIGS: Dict[str, Dict[str, List[str]]] = {
    FeaturePreset.GAMING.value: {
        "enable_features": [
            "DirectPlay",
            "NetFx3",
        ],
        "disable_features": [
            "SMB1Protocol",
            "TelnetClient",
            "TFTP",
            "Windows-Defender-Default-Definitions",
        ],
        "remove_capabilities": [
            "MathRecognizer~~~~0.0.1.0",
            "App.StepsRecorder~~~~0.0.1.0",
            "Microsoft.Windows.WordPad~~~~0.0.1.0",
            "Print.Fax.Scan~~~~0.0.1.0",
            "XPS.Viewer~~~~0.0.1.0",
        ],
        "add_capabilities": []
    },
    FeaturePreset.DEVELOPER.value: {
        "enable_features": [
            "Microsoft-Windows-Subsystem-Linux",
            "VirtualMachinePlatform",
            "HypervisorPlatform",
            "Microsoft-Hyper-V-All",
            "Containers-DisposableClientVM",  # Windows Sandbox
            "NetFx3",
            "NetFx4-AdvSrvs",
        ],
        "disable_features": [
            "SMB1Protocol",
            "TelnetClient",
        ],
        "remove_capabilities": [
            "MathRecognizer~~~~0.0.1.0",
            "App.StepsRecorder~~~~0.0.1.0",
        ],
        "add_capabilities": [
            "OpenSSH.Client~~~~0.0.1.0",
            "OpenSSH.Server~~~~0.0.1.0",
            "Tools.Graphics.DirectX~~~~0.0.1.0",
        ]
    },
    FeaturePreset.HARDENED.value: {
        "enable_features": [
            "Containers-DisposableClientVM",  # Windows Sandbox pour isoler les fichiers suspects
        ],
        "disable_features": [
            "SMB1Protocol",
            "TelnetClient",
            "TFTP",
            "SimpleTCP",
            "WindowsMediaPlayer",
            "WorkFolders-Client",
        ],
        "remove_capabilities": [
            "Browser.InternetExplorer~~~~0.0.11.0",
            "App.Support.QuickAssist~~~~0.0.1.0",
            "Media.WindowsMediaPlayer~~~~0.0.12.0",
        ],
        "add_capabilities": []
    },
    FeaturePreset.SUPERLITE.value: {
        "enable_features": [
            "DirectPlay",
        ],
        "disable_features": [
            "SMB1Protocol",
            "TelnetClient",
            "TFTP",
            "SimpleTCP",
            "WorkFolders-Client",
            "Printing-Foundation-Features",
            "Windows-Defender-Default-Definitions",
        ],
        "remove_capabilities": BLOAT_CAPABILITIES,
        "add_capabilities": []
    }
}


class FeaturesManager:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log = log_callback or (lambda msg: None)

    def apply_preset(
        self,
        mount_dir: Path | str,
        dism: DismManager,
        preset: str | FeaturePreset
    ) -> bool:
        """
        Applique un profil complet de fonctionnalités et capacités sur l'image montée.
        """
        key = preset.value if isinstance(preset, FeaturePreset) else str(preset).lower()
        cfg = PRESET_CONFIGS.get(key)
        if not cfg:
            self.log(f"[FONCTIONNALITÉS] Aucun profil correspondant à '{preset}'.")
            return False

        self.log(f"[FONCTIONNALITÉS] Application du profil de fonctionnalités '{key.upper()}'...")

        # 1. Activation des fonctionnalités
        for feat in cfg.get("enable_features", []):
            dism.enable_feature(mount_dir, feat)

        # 2. Désactivation des fonctionnalités
        for feat in cfg.get("disable_features", []):
            dism.disable_feature(mount_dir, feat)

        # 3. Suppression des capacités (FOD)
        for cap in cfg.get("remove_capabilities", []):
            dism.remove_capability(mount_dir, cap)

        # 4. Ajout des capacités
        for cap in cfg.get("add_capabilities", []):
            dism.add_capability(mount_dir, cap)

        self.log(f"[OK] Profil de fonctionnalités '{key.upper()}' appliqué avec succès.")
        return True

    @staticmethod
    def get_available_presets() -> List[str]:
        return list(PRESET_CONFIGS.keys())
