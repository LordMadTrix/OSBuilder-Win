"""
Module de gestion de la virtualisation Windows, sous-systèmes IA/Linux et tuning HVCI/VBS.
Permet d'activer en un clic WSL2, Hyper-V, Windows Sandbox, ou au contraire de désactiver VBS/HVCI
pour éliminer la dégradation de FPS et les micro-stutters dans les jeux vidéo compétitifs.
"""

from pathlib import Path
from typing import List, Optional
from core.registry_manager import RegistryManager


class VirtualizationManager:
    """Gestionnaire des fonctionnalités de virtualisation et d'intégrité de code (HVCI/VBS)."""

    # Noms officiels des fonctionnalités DISM pour Windows 10 / 11
    FEATURE_WSL = "Microsoft-Windows-Subsystem-Linux"
    FEATURE_VMP = "VirtualMachinePlatform"
    FEATURE_SANDBOX = "Containers-DisposableClientVM"
    FEATURE_HYPERV = "Microsoft-Hyper-V-All"

    @classmethod
    def get_features_for_profile(
        cls,
        enable_wsl: bool = False,
        enable_sandbox: bool = False,
        enable_hyperv: bool = False
    ) -> List[str]:
        """Retourne la liste des fonctionnalités DISM nécessaires selon la configuration."""
        features = []
        if enable_wsl:
            features.extend([cls.FEATURE_VMP, cls.FEATURE_WSL])
        if enable_sandbox:
            features.append(cls.FEATURE_SANDBOX)
        if enable_hyperv:
            features.append(cls.FEATURE_HYPERV)
        
        seen = set()
        deduped = []
        for f in features:
            if f not in seen:
                seen.add(f)
                deduped.append(f)
        return deduped

    @classmethod
    def apply_gaming_vbs_tweaks(cls, reg: RegistryManager) -> bool:
        """
        Désactive VBS (Virtualization-Based Security) et HVCI (Hypervisor-Enforced Code Integrity)
        dans la ruche SYSTEM hors-ligne pour éliminer les micro-saccades et maximiser les performances GPU/CPU.
        """
        try:
            # 1. Neutraliser DeviceGuard & VBS
            dg_key = r"ControlSet001\Control\DeviceGuard"
            reg.set_value("SYSTEM", dg_key, "EnableVirtualizationBasedSecurity", "REG_DWORD", 0)
            reg.set_value("SYSTEM", dg_key, "RequirePlatformSecurityFeatures", "REG_DWORD", 0)
            reg.set_value("SYSTEM", dg_key, "RequireMicrosoftSignedBootChain", "REG_DWORD", 0)

            # 2. Neutraliser HVCI (Memory Integrity)
            hvci_key = r"ControlSet001\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity"
            reg.set_value("SYSTEM", hvci_key, "Enabled", "REG_DWORD", 0)
            reg.set_value("SYSTEM", hvci_key, "WasEnabledBy", "REG_DWORD", 0)

            return True
        except Exception:
            return False

    @classmethod
    def apply_spectre_meltdown_gaming_override(cls, reg: RegistryManager) -> bool:
        """
        Désactive les atténuations logicielles Spectre/Meltdown (pour machines de tournoi / bancs de test isolés).
        Réduit drastiquement l'overhead des commutations de contexte CPU (jusqu'à 15-20% de gain sur CPU anciens).
        """
        try:
            mm_key = r"ControlSet001\Control\Session Manager\Memory Management"
            reg.set_value("SYSTEM", mm_key, "FeatureSettings", "REG_DWORD", 1)
            reg.set_value("SYSTEM", mm_key, "FeatureSettingsOverride", "REG_DWORD", 3)
            reg.set_value("SYSTEM", mm_key, "FeatureSettingsOverrideMask", "REG_DWORD", 3)
            return True
        except Exception:
            return False
