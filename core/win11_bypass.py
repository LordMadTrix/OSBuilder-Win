"""
Module de contournement des restrictions matérielles et OOBE pour Windows 11 (y compris 24H2).
Injecte les clés LabConfig dans boot.wim (WinPE Setup), MoSetup/OOBE dans install.wim,
et neutralise appraiserres.dll dans les sources de l'ISO pour les mises à jour sans blocage.
"""

from pathlib import Path
from typing import Callable, Optional
from core.registry_manager import RegistryManager
from core.config import Win11Options


class Win11Bypass:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log = log_callback or (lambda msg: None)

    def patch_extracted_sources(self, extracted_dir: Path | str) -> bool:
        """
        Neutralise le validateur matériel de l'installateur Windows 11 (sources\\appraiserres.dll).
        Permet de lancer le Setup directement depuis Windows (mise à niveau sans perte)
        ou depuis WinPE sans aucun blocage matériel (TPM, Secure Boot, CPU, RAM).
        """
        sources_dir = Path(extracted_dir).resolve() / "sources"
        if not sources_dir.exists():
            self.log(f"[BYPASS 11] Dossier sources introuvable : {sources_dir}")
            return False

        appraiser_dll = sources_dir / "appraiserres.dll"
        try:
            # Remplacement par un fichier vide (technique universelle reconnue pour neutraliser Appraiser)
            with open(appraiser_dll, "wb") as f:
                f.write(b"")
            self.log("[OK] sources\\appraiserres.dll neutralisé avec succès (Contournement matériel universel).")

            # Suppression éventuelle de la base de télémétrie de compatibilité
            appraiser_sdb = sources_dir / "appraiser.sdb"
            if appraiser_sdb.exists():
                try:
                    appraiser_sdb.unlink()
                    self.log("[INFO] sources\\appraiser.sdb supprimé pour accélérer le démarrage du setup.")
                except Exception:
                    pass

            return True
        except Exception as e:
            self.log(f"[ATTENTION] Impossible de patcher appraiserres.dll : {e}")
            return False

    def patch_boot_wim(self, boot_mount_dir: Path | str, options: Win11Options) -> bool:
        """
        Injecte les clés LabConfig dans la ruche SYSTEM de boot.wim (Index 2).
        Permet au programme d'installation de Windows 11 d'ignorer les prérequis
        TPM 2.0, SecureBoot, RAM, CPU et stockage dès le boot ISO.
        """
        self.log("Application des bypasses matériels Windows 11 dans boot.wim (WinPE)...")
        reg = RegistryManager(self.log)
        mount = Path(boot_mount_dir)
        system_hive = mount / "Windows" / "System32" / "config" / "SYSTEM"

        if not system_hive.exists():
            self.log(f"Ruche SYSTEM introuvable dans boot.wim : {system_hive}")
            return False

        # On charge uniquement la ruche SYSTEM
        res = reg._run_reg(["load", reg.MOUNT_SYSTEM, str(system_hive)])
        if res.returncode != 0:
            self.log("Impossible de charger la ruche SYSTEM de boot.wim")
            return False

        try:
            lab_config_path = r"Setup\LabConfig"
            if options.bypass_tpm:
                reg.set_value("SYSTEM", lab_config_path, "BypassTPMCheck", "REG_DWORD", 1)
            if options.bypass_secureboot:
                reg.set_value("SYSTEM", lab_config_path, "BypassSecureBootCheck", "REG_DWORD", 1)
            if options.bypass_ram:
                reg.set_value("SYSTEM", lab_config_path, "BypassRAMCheck", "REG_DWORD", 1)
            if options.bypass_cpu:
                reg.set_value("SYSTEM", lab_config_path, "BypassCPUCheck", "REG_DWORD", 1)
            if options.bypass_storage:
                reg.set_value("SYSTEM", lab_config_path, "BypassStorageCheck", "REG_DWORD", 1)

            self.log("[OK] Clés LabConfig injectées avec succès dans boot.wim.")
            return True
        finally:
            reg._run_reg(["unload", reg.MOUNT_SYSTEM], check=False)

    def patch_install_wim(self, install_mount_dir: Path | str, options: Win11Options) -> bool:
        """
        Injecte les contournements dans le système installé (install.wim) :
        MoSetup (Upgrades non supportées) et BypassNRO (Compte local sans réseau).
        """
        self.log("Application des bypasses système Windows 11 dans install.wim...")
        reg = RegistryManager(self.log)
        if not reg.load_hives(install_mount_dir):
            self.log("[ATTENTION] Certaines ruches n'ont pas pu être chargées pour install.wim")

        try:
            # MoSetup pour autoriser les mises à jour sans TPM/CPU
            reg.set_value("SYSTEM", r"Setup\MoSetup", "AllowUpgradesWithUnsupportedTPMOrCPU", "REG_DWORD", 1)

            # BypassNRO pour débloquer l'OOBE sans connexion Internet ni compte Microsoft
            reg.set_value("SOFTWARE", r"Microsoft\Windows\CurrentVersion\OOBE", "BypassNRO", "REG_DWORD", 1)

            if options.classic_context_menu:
                reg.apply_win11_classic_context_menu()

            if options.disable_copilot or options.disable_widgets or options.disable_recall:
                reg.apply_win11_debloat_tweaks()

            return True
        finally:
            reg.unload_hives()
