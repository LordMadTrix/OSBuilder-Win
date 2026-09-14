"""
Module de compatibilité matérielle moderne pour Windows 7.
Gère l'injection des pilotes xHCI (USB 3.0/3.1) et NVMe dans boot.wim (WinPE) et install.wim.
"""

from pathlib import Path
from typing import Callable, Optional
from core.dism_manager import DismManager
from core.registry_manager import RegistryManager
from core.config import Win7Options


class Win7Compat:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log = log_callback or (lambda msg: None)
        self.dism = DismManager(self.log)

    def inject_hardware_drivers(self, mount_dir: Path | str, options: Win7Options, context_name: str = "image") -> bool:
        """
        Injecte les pilotes NVMe et USB 3.0/3.1 dans l'image spécifiée (boot.wim ou install.wim).
        """
        self.log(f"Vérification de l'injection des pilotes pour {context_name}...")
        success = True

        # 1. Pilotes NVMe
        if options.inject_nvme and options.nvme_drivers_dir:
            nvme_path = Path(options.nvme_drivers_dir)
            if nvme_path.exists():
                self.log(f"Injection des pilotes NVMe pour {context_name} ({nvme_path})...")
                res = self.dism.add_drivers(mount_dir, nvme_path, recurse=True, force_unsigned=True)
                if not res:
                    self.log("[ATTENTION] Échec d'injection de certains pilotes NVMe")
                    success = False
            else:
                self.log(f"[INFO] Répertoire NVMe spécifié non trouvé : {nvme_path}")

        # 2. Pilotes USB 3.0 / 3.1 (xHCI)
        if options.inject_usb3 and options.usb3_drivers_dir:
            usb3_path = Path(options.usb3_drivers_dir)
            if usb3_path.exists():
                self.log(f"Injection des pilotes USB 3.0/3.1 pour {context_name} ({usb3_path})...")
                res = self.dism.add_drivers(mount_dir, usb3_path, recurse=True, force_unsigned=True)
                if not res:
                    self.log("[ATTENTION] Échec d'injection de certains pilotes USB 3.0")
                    success = False
            else:
                self.log(f"[INFO] Répertoire USB3 spécifié non trouvé : {usb3_path}")

        return success

    def apply_win7_optimizations(self, install_mount_dir: Path | str) -> bool:
        """
        Applique les tweaks d'optimisation spécifiques à Windows 7
        (Désactivation CEIP, télémétrie rétro-portée, amélioration du cache disque).
        """
        self.log("Application des optimisations système pour Windows 7...")
        reg = RegistryManager(self.log)
        if not reg.load_hives(install_mount_dir):
            self.log("[ATTENTION] Ruches non complètement chargées pour Windows 7")

        try:
            # Désactiver le CEIP (Customer Experience Improvement Program)
            reg.set_value("SOFTWARE", r"Policies\Microsoft\SQMClient\Windows", "CEIPEnable", "REG_DWORD", 0)
            reg.set_value("SOFTWARE", r"Policies\Microsoft\SQMClient", "CorporateSQMURL", "REG_SZ", "127.0.0.1")

            # Désactiver Application Impact Telemetry
            reg.set_value("SOFTWARE", r"Policies\Microsoft\Windows\AppCompat", "AITEnable", "REG_DWORD", 0)
            reg.set_value("SOFTWARE", r"Policies\Microsoft\Windows\AppCompat", "DisableInventory", "REG_DWORD", 1)

            # Optimisation I/O et Système
            reg.set_value("SYSTEM", r"ControlSet001\Control\Session Manager\Memory Management", "LargeSystemCache", "REG_DWORD", 0)
            reg.set_value("SYSTEM", r"ControlSet001\Control\FileSystem", "NtfsDisableLastAccessUpdate", "REG_DWORD", 1)

            return True
        finally:
            reg.unload_hives()
