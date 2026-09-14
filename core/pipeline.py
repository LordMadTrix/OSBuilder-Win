"""
Pipeline d'orchestration principal de build d'image Windows pour OSBuilder-Win.
Coordonne l'extraction, le servicing DISM, les ruches de registre, l'automatisation et l'ISO.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Optional

from core.config import BuildProfile, TargetOS, AppxPreset
from core.dism_manager import DismManager
from core.iso_extractor import IsoExtractor
from core.iso_builder import IsoBuilder
from core.registry_manager import RegistryManager
from core.unattended_generator import UnattendedGenerator
from core.win11_bypass import Win11Bypass
from core.win7_compat import Win7Compat
from core.driver_manager import DriverManager
from core.iso_validator import IsoValidator
from core.appx_catalog import get_patterns_for_preset
from core.oem_manager import OemManager
from core.update_manager import UpdateManager


class BuildPipeline:
    def __init__(self, profile: BuildProfile, work_dir: Optional[Path | str] = None, log_callback: Optional[Callable[[str], None]] = None):
        self.profile = profile
        self.log = log_callback or (lambda msg: None)
        self._is_cancelled = False
        
        # Répertoire de travail
        if work_dir:
            self.work_dir = Path(work_dir).resolve()
        else:
            self.work_dir = Path(os.getcwd()) / "workspace_build"
            
        self.extracted_dir = self.work_dir / "extracted"
        self.mount_dir = self.work_dir / "mount"
        
        # Modules
        self.extractor = IsoExtractor(self.log)
        self.dism = DismManager(self.log)
        self.reg = RegistryManager(self.log)
        self.iso_builder = IsoBuilder(self.log)
        self.win11 = Win11Bypass(self.log)
        self.win7 = Win7Compat(self.log)

    def cancel(self) -> None:
        """Demande l'annulation coopérative et sécurisée du build en cours."""
        self._is_cancelled = True
        self.log("[ANNULATION] Signal d'arrêt reçu. Démontage propre et interruption...")

    def _check_cancellation(self) -> None:
        if self._is_cancelled:
            raise RuntimeError("Construction annulée par l'utilisateur.")

    def run(self, source_iso: Path | str, output_iso: Path | str) -> bool:
        """Exécute l'intégralité du pipeline de build."""
        self._is_cancelled = False
        self.log("=" * 60)
        self.log(f"LANCEMENT DU PIPELINE OSBUILDER-WIN : {self.profile.name}")
        self.log(f"OS Cible : {self.profile.target_os.value.upper()} ({self.profile.architecture})")
        self.log(f"Source ISO : {source_iso}")
        self.log(f"Sortie ISO : {output_iso}")
        self.log("=" * 60)

        # 0. Vérifications initiales
        if not self.dism.is_admin():
            err = "OSBuilder-Win requiert impérativement les droits Administrateur pour manipuler DISM et le registre hors-ligne."
            self.log(f"[ERREUR CRITIQUE] {err}")
            raise PermissionError(err)

        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.mount_dir.mkdir(parents=True, exist_ok=True)
        
        # Nettoyage préventif
        self.dism.cleanup_mountpoints()
        self._check_cancellation()

        try:
            # 1. Extraction de l'ISO
            self.log("[ÉTAPE 1/6] Extraction de l'ISO source...")
            if not self.extractor.extract(source_iso, self.extracted_dir):
                raise RuntimeError("Échec de l'extraction de l'ISO source.")
            self._check_cancellation()

            # Inspection et validation d'intégrité des sources
            val_res = IsoValidator.validate_extracted_tree(self.extracted_dir)
            if not val_res.is_valid:
                self.log(f"[ATTENTION ISO] Anomalies détectées : {', '.join(val_res.missing_files)}")
            else:
                self.log(f"[VALIDATION ISO] Arborescence conforme ({val_res.install_image_format}, {val_res.total_size_mb} Mo).")

            sources_info = self.extractor.inspect_extracted_sources(self.extracted_dir)
            install_img = Path(sources_info["install_image"])
            boot_wim = Path(sources_info["boot_wim"])

            if not install_img.exists() or not boot_wim.exists():
                raise FileNotFoundError("Image install (wim/esd) ou boot.wim introuvable dans l'ISO extraite.")

            # Capture automatique des pilotes réseau (Wi-Fi/LAN) hôte si demandée
            if self.profile.auto_inject_host_network_drivers:
                self.log("[PILOTES] Capture automatique des pilotes réseau de la machine hôte...")
                drv_mgr = DriverManager(self.log)
                host_net_dir = self.work_dir / "host_network_drivers"
                retained = drv_mgr.export_host_drivers(host_net_dir, filter_network_storage_only=True)
                if retained and str(host_net_dir) not in self.profile.driver_dirs:
                    self.profile.driver_dirs.append(str(host_net_dir))
                    self.log(f"[PILOTES] {len(retained)} pilotes réseau hôte prêts pour injection.")

            # 2. Conversion ESD en WIM si nécessaire
            if sources_info["image_type"] == "ESD":
                self.log("L'image d'installation est au format compressé ESD. Conversion vers WIM...")
                target_wim = install_img.parent / "install.wim"
                self.dism.convert_esd_to_wim(install_img, target_wim, index=self.profile.image_index)
                install_img.unlink()  # Supprimer le .esd
                install_img = target_wim
                # Après extraction d'un index ESD unique vers WIM, l'index devient 1
                self.profile.image_index = 1

            self._check_cancellation()

            # 2b. Mode Mono-Édition (Single-Edition Export) pour alléger considérablement l'ISO
            if self.profile.single_edition_only and install_img.exists():
                self.log(f"[OPTIMISATION] Export mono-édition de l'index {self.profile.image_index} pour alléger l'image...")
                mono_wim = install_img.parent / "install_mono.wim"
                comp_type = getattr(self.profile.compression_type, "value", "maximum")
                if self.dism.export_single_image(install_img, mono_wim, index=self.profile.image_index, compression=comp_type):
                    install_img.unlink()
                    mono_wim.rename(install_img)
                    self.profile.image_index = 1
                    self.log("[OK] Image réduite à une seule édition avec succès.")

            self._check_cancellation()

            # 3. Patch du boot.wim (WinPE Setup)
            self._process_boot_wim(boot_wim)
            self._check_cancellation()

            # 4. Patch du install.wim (Système d'exploitation cible)
            self._process_install_wim(install_img)
            self._check_cancellation()

            # 5. Automatisation (autounattend.xml)
            if self.profile.unattended.enabled:
                self.log("[ÉTAPE 5/6] Génération et placement de autounattend.xml...")
                
                # Assemblage des commandes FirstLogon (Post-Installation)
                first_logon_cmds = []
                if self.profile.post_install.install_vcredist:
                    first_logon_cmds.append(
                        'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "'
                        'irm https://aka.ms/vs/17/release/vc_redist.x64.exe -OutFile $env:TEMP\\vc_redist.x64.exe; '
                        'Start-Process $env:TEMP\\vc_redist.x64.exe -ArgumentList \'/quiet /norestart\' -Wait"'
                    )
                for app_id in self.profile.post_install.winget_apps:
                    first_logon_cmds.append(
                        f'cmd.exe /c start /wait winget install --id {app_id} --exact --silent --accept-package-agreements --accept-source-agreements'
                    )
                if self.profile.post_install.enable_hwid_activation:
                    first_logon_cmds.append(
                        'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& ([ScriptBlock]::Create((irm https://get.activated.win))) /HWID"'
                    )

                unattend_gen = UnattendedGenerator(
                    config=self.profile.unattended,
                    target_os=self.profile.target_os,
                    architecture=self.profile.architecture,
                    post_install_commands=first_logon_cmds
                )
                unattend_gen.write_to_file(self.extracted_dir / "autounattend.xml")

            # Déblocage de toutes les éditions Windows 7 (suppression de ei.cfg)
            if self.profile.target_os == TargetOS.WIN7:
                ei_cfg = self.extracted_dir / "sources" / "ei.cfg"
                if ei_cfg.exists():
                    ei_cfg.unlink()
                    self.log("[WIN7] Suppression de sources/ei.cfg (toutes les éditions débloquées dans le setup).")

            # Découpage WIM pour compatibilité FAT32 (< 4 Go) si demandé
            if self.profile.split_wim_fat32 and install_img.exists():
                self._split_wim_fat32(install_img)

            self._check_cancellation()

            # 6. Reconstruction de l'ISO
            self.log("[ÉTAPE 6/6] Reconstruction de l'ISO bootable...")
            vol_label = f"OSB_{self.profile.target_os.value.upper()}_{self.profile.architecture.upper()}"
            if not self.iso_builder.build_iso(self.extracted_dir, output_iso, volume_label=vol_label):
                raise RuntimeError("Échec lors de la création de l'ISO finale.")

            # 7. Génération du rapport de compilation
            try:
                from core.build_reporter import BuildReporter
                reporter = BuildReporter(self.profile, source_iso, output_iso)
                report_file = reporter.generate_markdown_report()
                self.log(f"[RAPPORT] Rapport d'audit généré : {report_file}")
            except Exception as e:
                self.log(f"[ATTENTION] Impossible de générer le rapport : {e}")

            self.log("=" * 60)
            self.log(f"[SUCCÈS] Le build s'est terminé avec succès ! Fichier : {output_iso}")
            self.log("=" * 60)
            return True

        finally:
            self._cleanup()

    def _process_boot_wim(self, boot_wim: Path) -> None:
        """Personnalise l'environnement de préinstallation et d'installation (boot.wim)."""
        self.log("[ÉTAPE 3/6] Personnalisation de boot.wim (Index 2 - Setup)...")
        # L'index 2 de boot.wim contient l'installateur Microsoft Windows Setup
        self.dism.mount_image(boot_wim, self.mount_dir, index=2)
        try:
            # Si Windows 11 : injecter LabConfig (Bypass TPM / SecureBoot)
            if self.profile.target_os == TargetOS.WIN11:
                self.win11.patch_boot_wim(self.mount_dir, self.profile.win11)

            # Si Windows 7 : injecter USB3 et NVMe pour que le setup détecte souris/clavier et SSD
            if self.profile.target_os == TargetOS.WIN7:
                self.win7.inject_hardware_drivers(self.mount_dir, self.profile.win7, context_name="boot.wim (Index 2)")

            # Injection des pilotes Intel RST / VMD dans boot.wim si spécifiés (pour PC modernes 11e-14e gén)
            if self.profile.intel_vmd_drivers_dir:
                vmd_path = Path(self.profile.intel_vmd_drivers_dir)
                if vmd_path.exists():
                    self.log(f"[PILOTES] Injection des pilotes Intel VMD / RST dans boot.wim ({vmd_path})...")
                    self.dism.add_drivers(self.mount_dir, vmd_path, recurse=True, force_unsigned=True)

            # Injection des pilotes réseau hôte dans boot.wim pour accès réseau durant l'installation
            if self.profile.auto_inject_host_network_drivers:
                host_net_dir = self.work_dir / "host_network_drivers"
                if host_net_dir.exists():
                    self.log(f"[PILOTES] Injection des pilotes réseau hôte dans boot.wim...")
                    self.dism.add_drivers(self.mount_dir, host_net_dir, recurse=True, force_unsigned=True)

            self.dism.unmount_image(self.mount_dir, commit=True)
        except Exception:
            self.dism.unmount_image(self.mount_dir, commit=False)
            raise

    def _process_install_wim(self, install_wim: Path) -> None:
        """Applique tous les tweaks, pilotes et debloat sur install.wim."""
        self.log(f"[ÉTAPE 4/6] Personnalisation de install.wim (Index {self.profile.image_index})...")
        self.dism.mount_image(install_wim, self.mount_dir, index=self.profile.image_index)
        
        try:
            # 1. Injection des pilotes
            for drv_path in self.profile.driver_dirs:
                self.dism.add_drivers(self.mount_dir, drv_path)

            if self.profile.intel_vmd_drivers_dir:
                vmd_path = Path(self.profile.intel_vmd_drivers_dir)
                if vmd_path.exists():
                    self.dism.add_drivers(self.mount_dir, vmd_path, recurse=True, force_unsigned=True)

            if self.profile.target_os == TargetOS.WIN7:
                self.win7.inject_hardware_drivers(self.mount_dir, self.profile.win7, context_name="install.wim")

            # 1b. Injection des pilotes critiques dans WinRE (Environnement de Récupération)
            if getattr(self.profile, "inject_drivers_to_winre", True):
                all_crit_drvs = list(self.profile.driver_dirs)
                if self.profile.intel_vmd_drivers_dir:
                    all_crit_drvs.append(self.profile.intel_vmd_drivers_dir)
                if self.profile.auto_inject_host_network_drivers:
                    host_net = self.work_dir / "host_network_drivers"
                    if host_net.exists() and str(host_net) not in all_crit_drvs:
                        all_crit_drvs.append(str(host_net))
                if all_crit_drvs:
                    self.log("[WINRE] Préparation de l'injection des pilotes critiques dans Winre.wim...")
                    self.dism.inject_drivers_to_winre(self.mount_dir, all_crit_drvs, scratch_dir=self.work_dir)

            # 2. Injection des mises à jour / paquets
            for pkg_path in self.profile.update_files:
                self.dism.add_packages(self.mount_dir, pkg_path)

            if getattr(self.profile, "updates_dir", None):
                upd_mgr = UpdateManager(self.log)
                ordered_pkgs = upd_mgr.scan_updates(self.profile.updates_dir, self.profile.architecture)
                for opkg in ordered_pkgs:
                    self.log(f"[UPDATE] Injection ordonnancée : {opkg.name}")
                    self.dism.add_packages(self.mount_dir, opkg)

            # 3. Suppression AppX (Debloat) pour Win 10 et 11 avec résolution des profils prédéfinis
            appx_patterns = list(self.profile.remove_appx_patterns)
            if hasattr(self.profile, "appx_preset") and self.profile.appx_preset != AppxPreset.NONE:
                preset_patterns = get_patterns_for_preset(self.profile.appx_preset)
                appx_patterns = sorted(list(set(appx_patterns + preset_patterns)))
                self.log(f"[DEBLOAT] Application du profil AppX '{self.profile.appx_preset.value}' ({len(appx_patterns)} motifs actifs)...")

            if appx_patterns and self.profile.target_os in (TargetOS.WIN10, TargetOS.WIN11):
                self.dism.remove_appx_by_patterns(self.mount_dir, appx_patterns)

            # 4. Activation / Désactivation de fonctionnalités
            for feat in self.profile.enable_features:
                self.dism.enable_feature(self.mount_dir, feat)
            for feat in self.profile.disable_features:
                self.dism.disable_feature(self.mount_dir, feat)

            # 4b. Fonctionnalités système avancées (.NET 3.5 & DirectPlay)
            if self.profile.system_features.enable_net35:
                sxs_dir = self.extracted_dir / "sources" / "sxs"
                self.dism.enable_net35_offline(self.mount_dir, sxs_dir)
            if self.profile.system_features.enable_directplay:
                self.dism.enable_directplay(self.mount_dir)

            # 4c. Désactivation de l'espace de stockage réservé Windows Update (~7 Go)
            if self.profile.system_features.disable_reserved_storage and self.profile.target_os in (TargetOS.WIN10, TargetOS.WIN11):
                self.dism.set_reserved_storage(self.mount_dir, state=False)

            # 4d. Ajout / Suppression de capacités Windows modulaires (DISM /Add-Capability /Remove-Capability)
            for cap in getattr(self.profile, "add_capabilities", []):
                self.dism.add_capability(self.mount_dir, cap)
            for cap in getattr(self.profile, "remove_capabilities", []):
                self.dism.remove_capability(self.mount_dir, cap)

            # 5. Injection de registre hors-ligne
            self.log("Application des modifications de registre hors-ligne...")
            if self.reg.load_hives(self.mount_dir):
                try:
                    if self.profile.disable_telemetry:
                        self.reg.apply_telemetry_removal()
                        self.reg.apply_extended_telemetry_and_privacy()

                    if self.profile.enable_gaming_tweaks:
                        self.reg.apply_gaming_optimizations()
                        self.reg.apply_advanced_gaming_tweaks(self.profile.system_features)

                    if self.profile.system_features.disable_nagle_algorithm:
                        self.reg.apply_network_gaming_tweaks()

                    # Optimisations de stockage SSD / TRIM
                    self.reg.apply_storage_optimizations(self.profile.system_features)

                    # Optimisations de mémoire vive et pagination du noyau
                    self.reg.apply_memory_and_paging_optimizations(self.profile.system_features)

                    # Réactivité système, MMCSS et quantum processeur
                    self.reg.apply_system_responsiveness_and_latency(self.profile.system_features)

                    # Réglages de l'Explorateur et de l'apparence
                    self.reg.apply_explorer_tweaks(self.profile.explorer)

                    # Optimisations des services système
                    self.reg.apply_services_tweaks(self.profile.services)

                    if self.profile.target_os == TargetOS.WIN11:
                        if self.profile.win11.classic_context_menu:
                            self.reg.apply_win11_classic_context_menu()
                        if self.profile.win11.disable_copilot or self.profile.win11.disable_widgets:
                            self.reg.apply_win11_debloat_tweaks()
                        # Windows 11 24H2 anti-chiffrement forcé & OneDrive
                        self.reg.apply_win11_24h2_and_onedrive_tweaks(self.profile.win11)
                        # Ergonomie barre des tâches & suppression des prompts OOBE
                        self.reg.apply_win11_taskbar_and_oobe_tweaks(self.profile.win11)
                        # BypassNRO et MoSetup
                        self.reg.set_value("SYSTEM", r"Setup\MoSetup", "AllowUpgradesWithUnsupportedTPMOrCPU", "REG_DWORD", 1)
                        self.reg.set_value("SOFTWARE", r"Microsoft\Windows\CurrentVersion\OOBE", "BypassNRO", "REG_DWORD", 1)

                    if self.profile.target_os == TargetOS.WIN7:
                        self.win7.apply_win7_optimizations(self.mount_dir)

                    # Branding OEM constructeur et fond d'écran
                    if getattr(self.profile, "oem", None) and self.profile.oem.enabled:
                        oem_mgr = OemManager(self.log)
                        oem_mgr.apply_oem_branding(self.mount_dir, self.reg.set_value, self.profile.oem)

                    # Tweaks personnalisés du profil
                    if self.profile.custom_registry_tweaks:
                        self.reg.apply_tweak_rules(self.profile.custom_registry_tweaks)
                finally:
                    self.reg.unload_hives()

            # 6. Injection et génération dynamique de SetupComplete.cmd
            scripts_dir = self.mount_dir / "Windows" / "Setup" / "Scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            
            setup_complete_path = scripts_dir / "SetupComplete.cmd"
            base_script = Path(__file__).resolve().parent.parent / "scripts" / "setup_complete.cmd"
            content = ""
            if base_script.exists():
                with open(base_script, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            else:
                content = "@echo off\r\n"
            
            custom_cmds = getattr(self.profile, "setup_complete_commands", [])
            if custom_cmds:
                content += "\r\n:: ==============================================================================\r\n"
                content += ":: Commandes personnalisées injectées par OSBuilder-Win (NT AUTHORITY\\SYSTEM)\r\n"
                content += ":: ==============================================================================\r\n"
                for cmd_line in custom_cmds:
                    if cmd_line.strip():
                        content += f"{cmd_line.strip()}\r\n"

            # 6b. Intégration des scripts personnalisés déposés dans custom_scripts/
            custom_scripts_dir = Path(__file__).resolve().parent.parent / "custom_scripts"
            injected_scripts_count = 0
            if custom_scripts_dir.exists():
                for script_item in custom_scripts_dir.iterdir():
                    if script_item.is_file() and script_item.suffix.lower() in (".cmd", ".bat", ".ps1") and not script_item.name.startswith("."):
                        target_file = scripts_dir / script_item.name
                        shutil.copy2(script_item, target_file)
                        injected_scripts_count += 1
                        # Ajouter l'appel dans SetupComplete.cmd
                        if script_item.suffix.lower() in (".cmd", ".bat"):
                            content += f'\r\ncall "%~dp0{script_item.name}"\r\n'
                        elif script_item.suffix.lower() == ".ps1":
                            content += f'\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0{script_item.name}"\r\n'
                if injected_scripts_count > 0:
                    self.log(f"[SCRIPTS] {injected_scripts_count} script(s) personnalisé(s) injecté(s) depuis custom_scripts/")

            with open(setup_complete_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.log(f"Script SetupComplete.cmd généré et injecté dans Windows\\Setup\\Scripts\\ ({len(custom_cmds)} commandes personnalisées).")

            # 7. Nettoyage du magasin de composants WinSxS (/StartComponentCleanup /ResetBase)
            if getattr(self.profile, "cleanup_component_store", False) and self.profile.target_os in (TargetOS.WIN10, TargetOS.WIN11):
                self.dism.cleanup_image_component_store(self.mount_dir, reset_base=True)

            # 8. Optimisation finale des composants (/Optimize-Image)
            if self.profile.target_os in (TargetOS.WIN10, TargetOS.WIN11):
                self.dism.optimize_image(self.mount_dir)

            self.dism.unmount_image(self.mount_dir, commit=True)
        except Exception:
            self.dism.unmount_image(self.mount_dir, commit=False)
            raise

    def _split_wim_fat32(self, wim_path: Path) -> bool:
        """Découpe install.wim en fichiers install.swm (< 3800 Mo) pour compatibilité clé USB FAT32."""
        swm_target = wim_path.parent / "install.swm"
        self.log("Découpage de install.wim en fichiers install.swm (< 3800 Mo) pour FAT32/UEFI...")

        # 1. Essai avec wimlib-imagex (très rapide)
        wimlib = Path(__file__).resolve().parent.parent / "bin" / "wimlib-imagex.exe"
        if wimlib.exists():
            import subprocess
            cmd = [str(wimlib), "split", str(wim_path), str(swm_target), "3800"]
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if res.returncode == 0:
                wim_path.unlink()  # Supprimer le .wim original
                self.log("[OK] Image découpée avec succès en fichiers .swm via wimlib.")
                return True
            else:
                self.log(f"[ATTENTION] wimlib split a échoué ({res.stderr.strip()}), basculement vers DISM...")

        # 2. Repli avec DISM /Split-Image
        if self.dism.split_image(wim_path, swm_target, file_size_mb=3800):
            wim_path.unlink()
            self.log("[OK] Image découpée avec succès en fichiers .swm via DISM.")
            return True

        self.log("[ATTENTION] Échec du découpage SWM (wimlib et DISM). L'image WIM originale est conservée.")
        return False

    def _cleanup(self) -> None:
        """Nettoie les dossiers temporaires après la fin du build."""
        self.log("Nettoyage des dossiers de travail temporaires...")
        try:
            self.reg.unload_hives()
            self.dism.force_cleanup_and_unmount(self.mount_dir)
            if self.mount_dir.exists():
                shutil.rmtree(self.mount_dir, ignore_errors=True)
            if self.extracted_dir.exists():
                shutil.rmtree(self.extracted_dir, ignore_errors=True)
        except Exception as e:
            self.log(f"[ATTENTION] Nettoyage partiel : {e}")
