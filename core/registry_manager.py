"""
Gestionnaire d'injection et de modification des ruches de registre hors-ligne.
Monte et manipule SOFTWARE, SYSTEM et NTUSER.DAT d'une image Windows montée.
"""

import gc
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from core.config import RegistryTweakRule, ExplorerOptions, ServicesOptions


class RegistryManager:
    MOUNT_SOFTWARE = r"HKLM\OSB_SOFTWARE"
    MOUNT_SYSTEM = r"HKLM\OSB_SYSTEM"
    MOUNT_DEFAULT_USER = r"HKLM\OSB_NTUSER"

    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log = log_callback or (lambda msg: None)
        self._mounted_hives = []

    def _run_reg(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        cmd = ["reg.exe"] + args
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if check and res.returncode != 0:
            self.log(f"[REG ERREUR] Commande {' '.join(cmd)} échouée : {res.stderr}")
        return res

    def load_hives(self, mount_dir: Path | str) -> bool:
        """Charge les ruches SOFTWARE, SYSTEM et NTUSER.DAT de l'image montée."""
        mount = Path(mount_dir)
        software_path = mount / "Windows" / "System32" / "config" / "SOFTWARE"
        system_path = mount / "Windows" / "System32" / "config" / "SYSTEM"
        ntuser_path = mount / "Users" / "Default" / "NTUSER.DAT"

        success = True

        if software_path.exists():
            self.log(f"Chargement de la ruche SOFTWARE...")
            res = self._run_reg(["load", self.MOUNT_SOFTWARE, str(software_path)])
            if res.returncode == 0:
                self._mounted_hives.append(self.MOUNT_SOFTWARE)
            else:
                success = False

        if system_path.exists():
            self.log(f"Chargement de la ruche SYSTEM...")
            res = self._run_reg(["load", self.MOUNT_SYSTEM, str(system_path)])
            if res.returncode == 0:
                self._mounted_hives.append(self.MOUNT_SYSTEM)
            else:
                success = False

        if ntuser_path.exists():
            self.log(f"Chargement de la ruche Default User (NTUSER.DAT)...")
            res = self._run_reg(["load", self.MOUNT_DEFAULT_USER, str(ntuser_path)])
            if res.returncode == 0:
                self._mounted_hives.append(self.MOUNT_DEFAULT_USER)
            else:
                success = False

        return success

    def unload_hives(self) -> bool:
        """Décharge toutes les ruches précédemment montées."""
        all_unloaded = True
        # Forcer la libération d'éventuels handles résiduels
        gc.collect()

        for hive in reversed(self._mounted_hives):
            self.log(f"Déchargement de la ruche {hive}...")
            unloaded = False
            for attempt in range(3):
                res = self._run_reg(["unload", hive], check=False)
                if res.returncode == 0:
                    unloaded = True
                    break
                time.sleep(1)
            if not unloaded:
                self.log(f"[ATTENTION] Impossible de décharger proprement {hive}")
                all_unloaded = False

        self._mounted_hives.clear()
        return all_unloaded

    def set_value(self, hive: str, subkey: str, name: str, value_type: str, value: Any) -> bool:
        """Écrit une valeur dans le registre hors-ligne."""
        hive_upper = hive.upper()
        if hive_upper == "SOFTWARE":
            base_key = f"{self.MOUNT_SOFTWARE}\\{subkey}"
        elif hive_upper == "SYSTEM":
            base_key = f"{self.MOUNT_SYSTEM}\\{subkey}"
        elif hive_upper in ("NTUSER", "DEFAULT"):
            base_key = f"{self.MOUNT_DEFAULT_USER}\\{subkey}"
        else:
            base_key = f"{hive}\\{subkey}"

        val_str = str(value)
        args = ["add", base_key, "/v", name, "/t", value_type, "/d", val_str, "/f"]
        res = self._run_reg(args, check=False)
        return res.returncode == 0

    def apply_tweak_rules(self, rules: List[RegistryTweakRule]) -> int:
        """Applique une liste d'objets RegistryTweakRule."""
        applied = 0
        for rule in rules:
            if self.set_value(rule.hive, rule.path, rule.name, rule.type, rule.value):
                applied += 1
        return applied

    # --- Tweaks Standardisés ---

    def apply_telemetry_removal(self) -> None:
        """Désactive la télémétrie et les diagnostics Windows."""
        self.log("Application des tweaks anti-télémétrie...")
        # SOFTWARE
        self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", "REG_DWORD", 0)
        self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\DataCollection", "MaxTelemetryAllowed", "REG_DWORD", 0)
        self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\Windows Search", "AllowCortana", "REG_DWORD", 0)
        self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\Windows Search", "DisableWebSearch", "REG_DWORD", 1)
        self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\Windows Search", "ConnectedSearchUseWeb", "REG_DWORD", 0)
        self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\CloudContent", "DisableWindowsConsumerFeatures", "REG_DWORD", 1)
        
        # SYSTEM - Désactiver le service de diagnostic DiagTrack
        self.set_value("SYSTEM", r"ControlSet001\Services\DiagTrack", "Start", "REG_DWORD", 4)
        self.set_value("SYSTEM", r"ControlSet001\Services\dmwappushservice", "Start", "REG_DWORD", 4)

    def apply_gaming_optimizations(self) -> None:
        """Optimise le planificateur multimédia et désactive GameDVR."""
        self.log("Application des optimisations Gaming / Latence...")
        # Network & Multimedia Scheduler
        self.set_value("SOFTWARE", r"Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "NetworkThrottlingIndex", "REG_DWORD", 4294967295) # 0xFFFFFFFF
        self.set_value("SOFTWARE", r"Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "SystemResponsiveness", "REG_DWORD", 0)
        self.set_value("SOFTWARE", r"Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "GPU Priority", "REG_DWORD", 8)
        self.set_value("SOFTWARE", r"Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "Priority", "REG_DWORD", 6)
        self.set_value("SOFTWARE", r"Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "Scheduling Category", "REG_SZ", "High")
        
        # GameDVR
        self.set_value("NTUSER", r"Software\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", "REG_DWORD", 0)
        self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\GameDVR", "AllowGameDVR", "REG_DWORD", 0)

    def apply_win11_classic_context_menu(self) -> None:
        """Restaure le menu contextuel classique (style Windows 10/7) sur Windows 11."""
        self.log("Restauration du menu contextuel classique sur Windows 11...")
        clsid_path = r"Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32"
        # Valeur par défaut vide pour forcer l'ancien handler
        self.set_value("NTUSER", clsid_path, "", "REG_SZ", "")

    def apply_win11_debloat_tweaks(self) -> None:
        """Désactive Copilot, Widgets et Recall."""
        self.log("Désactivation de Windows Copilot, Widgets et Recall...")
        # Copilot
        self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\WindowsCopilot", "TurnOffWindowsCopilot", "REG_DWORD", 1)
        self.set_value("NTUSER", r"Software\Policies\Microsoft\Windows\WindowsCopilot", "TurnOffWindowsCopilot", "REG_DWORD", 1)
        
        # Widgets / News & Interests
        self.set_value("SOFTWARE", r"Policies\Microsoft\Dsh", "AllowNewsAndInterests", "REG_DWORD", 0)
        
        # Recall / Windows AI User Activity Tracking
        self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\WindowsAI", "DisableAIDataAnalysis", "REG_DWORD", 1)

    def apply_win11_24h2_and_onedrive_tweaks(self, opts: Any) -> None:
        """
        Applique les protections spécifiques Windows 11 24H2 (anti-chiffrement BitLocker automatique)
        et neutralise l'auto-installation intempestive de OneDrive.
        """
        self.log("Application des protections Windows 11 24H2 et neutralisation de OneDrive...")

        # 1. Empêcher le chiffrement automatique BitLocker systématique sur 24H2
        if getattr(opts, "prevent_automatic_bitlocker", True):
            self.set_value("SYSTEM", r"ControlSet001\Control\BitLocker", "PreventDeviceEncryption", "REG_DWORD", 1)
            self.log("[SÉCURITÉ 24H2] Chiffrement automatique BitLocker désactivé.")

        # 2. Neutraliser l'auto-installation de OneDrive et son icône
        if getattr(opts, "disable_onedrive_autoinstall", True):
            self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\OneDrive", "DisableFileSyncNGSC", "REG_DWORD", 1)
            self.set_value("NTUSER", r"Software\Microsoft\Windows\CurrentVersion\Run", "OneDriveSetup", "REG_SZ", "")
            self.set_value("SOFTWARE", r"Classes\CLSID\{018D5C66-4533-4307-9B53-224DE2ED1FE6}", "System.IsPinnedToNameSpaceTree", "REG_DWORD", 0)
            self.log("[DEBLOAT] Auto-installation de OneDrive désactivée.")

    def apply_explorer_tweaks(self, opts: ExplorerOptions) -> None:
        """Applique les personnalisations de l'Explorateur Windows et de l'apparence."""
        self.log("Application des réglages de l'Explorateur et de l'apparence...")
        adv_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"

        # Extensions de fichiers
        if opts.show_file_extensions:
            self.set_value("NTUSER", adv_path, "HideFileExt", "REG_DWORD", 0)

        # Fichiers cachés
        if opts.show_hidden_files:
            self.set_value("NTUSER", adv_path, "Hidden", "REG_DWORD", 1)

        # Ouvrir l'Explorateur sur 'Ce PC' (1) plutôt que Accès Rapide (2)
        if opts.open_to_this_pc:
            self.set_value("NTUSER", adv_path, "LaunchTo", "REG_DWORD", 1)

        # Mode Sombre par défaut (Dark Theme pour le système et les applications)
        if opts.dark_mode:
            theme_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            self.set_value("NTUSER", theme_path, "AppsUseLightTheme", "REG_DWORD", 0)
            self.set_value("NTUSER", theme_path, "SystemUsesLightTheme", "REG_DWORD", 0)
            self.set_value("SOFTWARE", r"Microsoft\Windows\CurrentVersion\Themes\Personalize", "AppsUseLightTheme", "REG_DWORD", 0)
            self.set_value("SOFTWARE", r"Microsoft\Windows\CurrentVersion\Themes\Personalize", "SystemUsesLightTheme", "REG_DWORD", 0)

        # Masquer le dossier "Objets 3D" dans Ce PC
        if opts.hide_3d_objects:
            obj3d_path = r"Microsoft\Windows\CurrentVersion\Explorer\FolderDescriptions\{31C33740-3E14-4988-83B4-EB78AC0433E2}\PropertyBag"
            self.set_value("SOFTWARE", obj3d_path, "ThisPCPolicy", "REG_SZ", "Hide")

        # Ajouter 'Prendre possession' (Take Ownership) au menu contextuel
        if opts.add_take_ownership:
            file_cmd = r'cmd.exe /c takeown /f "%1" && icacls "%1" /grant administrators:F'
            self.set_value("SOFTWARE", r"Classes\*\shell\runas", "", "REG_SZ", "Prendre possession")
            self.set_value("SOFTWARE", r"Classes\*\shell\runas", "NoWorkingDirectory", "REG_SZ", "")
            self.set_value("SOFTWARE", r"Classes\*\shell\runas\command", "", "REG_SZ", file_cmd)
            self.set_value("SOFTWARE", r"Classes\*\shell\runas\command", "IsolatedCommand", "REG_SZ", file_cmd)

            dir_cmd = r'cmd.exe /c takeown /f "%1" /r /d y && icacls "%1" /grant administrators:F /t'
            self.set_value("SOFTWARE", r"Classes\Directory\shell\runas", "", "REG_SZ", "Prendre possession")
            self.set_value("SOFTWARE", r"Classes\Directory\shell\runas", "NoWorkingDirectory", "REG_SZ", "")
            self.set_value("SOFTWARE", r"Classes\Directory\shell\runas\command", "", "REG_SZ", dir_cmd)
            self.set_value("SOFTWARE", r"Classes\Directory\shell\runas\command", "IsolatedCommand", "REG_SZ", dir_cmd)

        # Désactiver la recherche web Bing dans le menu Démarrer (Recherche locale instantanée à 0ms)
        if getattr(opts, "disable_start_web_search", False):
            self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\Windows Search", "DisableWebSearch", "REG_DWORD", 1)
            self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\Windows Search", "ConnectedSearchUseWeb", "REG_DWORD", 0)
            self.set_value("NTUSER", r"Software\Microsoft\Windows\CurrentVersion\Search", "BingSearchEnabled", "REG_DWORD", 0)
            self.log("[EXPLORER] Recherche web Bing désactivée (Recherche locale pure à 0ms).")

        # Ajouter 'Redémarrer l'Explorateur' au menu contextuel du Bureau
        if getattr(opts, "add_restart_explorer_context_menu", False):
            restart_cmd = r'powershell.exe -NoProfile -Command "Stop-Process -Name explorer -Force"'
            self.set_value("SOFTWARE", r"Classes\DesktopBackground\Shell\RestartExplorer", "", "REG_SZ", "Redémarrer l'Explorateur")
            self.set_value("SOFTWARE", r"Classes\DesktopBackground\Shell\RestartExplorer", "Icon", "REG_SZ", "explorer.exe,0")
            self.set_value("SOFTWARE", r"Classes\DesktopBackground\Shell\RestartExplorer\command", "", "REG_SZ", restart_cmd)

        # Ajouter 'Ouvrir avec le Bloc-notes'
        if getattr(opts, "add_open_with_notepad", False):
            self.set_value("SOFTWARE", r"Classes\*\shell\OpenWithNotepad", "", "REG_SZ", "Ouvrir avec le Bloc-notes")
            self.set_value("SOFTWARE", r"Classes\*\shell\OpenWithNotepad", "Icon", "REG_SZ", "notepad.exe,0")
            self.set_value("SOFTWARE", r"Classes\*\shell\OpenWithNotepad\command", "", "REG_SZ", r'notepad.exe "%1"')

        # Ajouter 'Invite de commandes Administrateur ici'
        if getattr(opts, "add_cmd_admin_here", False):
            self.set_value("SOFTWARE", r"Classes\Directory\Background\shell\cmdadmin", "", "REG_SZ", "Invite de commandes (Admin) ici")
            self.set_value("SOFTWARE", r"Classes\Directory\Background\shell\cmdadmin", "Icon", "REG_SZ", "cmd.exe,0")
            self.set_value("SOFTWARE", r"Classes\Directory\Background\shell\cmdadmin\command", "", "REG_SZ", r'cmd.exe /s /k pushd "%V"')

        # Thème Signature MadOS (Dark mode intégral, accent cyan/ultraviolet, réactivité 0ms)
        if getattr(opts, "apply_mados_theme", False):
            color = getattr(opts, "mados_accent_color", "#00f0ff") or "#00f0ff"
            self.apply_mados_theme(color)

    def apply_mados_theme(self, accent_hex: str = "#00f0ff") -> None:
        """
        Applique le style d'environnement Windows exclusif MadOS (LordMadTrix Signature) :
        - Dark Mode intégral forcé pour l'OS, l'Explorateur et les applications
        - Couleur d'accentuation DWM MadOS (Cyan Cyber électrique #00f0ff ou personnalisé)
        - ColorPrevalence activé pour appliquer l'accent sur les barres de titre et bordures
        - Réactivité instantanée du bureau à 0ms (MenuShowDelay=0, animations allégées)
        """
        self.log(f"[MAD-OS] Application du Thème Windows Signature MadOS (Accent: {accent_hex})...")
        
        # 1. Dark Mode intégral dans NTUSER et SOFTWARE
        theme_personalize = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        self.set_value("NTUSER", theme_personalize, "AppsUseLightTheme", "REG_DWORD", 0)
        self.set_value("NTUSER", theme_personalize, "SystemUsesLightTheme", "REG_DWORD", 0)
        self.set_value("NTUSER", theme_personalize, "ColorPrevalence", "REG_DWORD", 1)
        self.set_value("NTUSER", theme_personalize, "EnableTransparency", "REG_DWORD", 1)

        self.set_value("SOFTWARE", r"Microsoft\Windows\CurrentVersion\Themes\Personalize", "AppsUseLightTheme", "REG_DWORD", 0)
        self.set_value("SOFTWARE", r"Microsoft\Windows\CurrentVersion\Themes\Personalize", "SystemUsesLightTheme", "REG_DWORD", 0)
        self.set_value("SOFTWARE", r"Microsoft\Windows\CurrentVersion\Themes\Personalize", "ColorPrevalence", "REG_DWORD", 1)

        # 2. Conversion hex -> DWORD DWM
        hex_clean = accent_hex.lstrip("#")
        if len(hex_clean) == 6:
            r = int(hex_clean[0:2], 16)
            g = int(hex_clean[2:4], 16)
            b = int(hex_clean[4:6], 16)
        else:
            r, g, b = 0, 240, 255  # Défaut MadOS cyan

        # Format ABGR pour DWM AccentColor : 0xffBBGGRR
        abgr_dword = 0xff000000 | (b << 16) | (g << 8) | r
        # Format ARGB pour ColorizationColor : 0xffRRGGBB
        argb_dword = 0xff000000 | (r << 16) | (g << 8) | b

        dwm_path = r"Software\Microsoft\Windows\DWM"
        self.set_value("NTUSER", dwm_path, "AccentColor", "REG_DWORD", abgr_dword)
        self.set_value("NTUSER", dwm_path, "ColorizationColor", "REG_DWORD", argb_dword)
        self.set_value("NTUSER", dwm_path, "ColorPrevalence", "REG_DWORD", 1)
        self.set_value("NTUSER", dwm_path, "Composition", "REG_DWORD", 1)

        # 3. Réactivité ultra-rapide du bureau MadOS (0ms)
        desktop_path = r"Control Panel\Desktop"
        self.set_value("NTUSER", desktop_path, "MenuShowDelay", "REG_SZ", "0")
        
        # 4. Accentuation de l'Explorateur Windows
        explorer_accent = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent"
        self.set_value("NTUSER", explorer_accent, "AccentColorMenu", "REG_DWORD", abgr_dword)

        self.log("[MAD-OS OK] Thème Windows Signature MadOS configuré avec succès.")

    def apply_services_tweaks(self, opts: ServicesOptions) -> None:
        """Désactive les services Windows superflus dans la ruche SYSTEM (hors-ligne)."""
        self.log("Application des optimisations de services système...")

        # SysMain / Superfetch (inutile voire contre-productif sur SSD NVMe)
        if opts.disable_sysmain:
            self.set_value("SYSTEM", r"ControlSet001\Services\SysMain", "Start", "REG_DWORD", 4)
            self.log("[SERVICE] SysMain (Superfetch) désactivé.")

        # Windows Search (Indexation en arrière-plan)
        if opts.disable_indexing:
            self.set_value("SYSTEM", r"ControlSet001\Services\WSearch", "Start", "REG_DWORD", 4)
            self.log("[SERVICE] Windows Search (Indexation) désactivé.")

        # Spouleur d'impression (si aucun périphérique d'impression n'est utilisé)
        if opts.disable_spooler:
            self.set_value("SYSTEM", r"ControlSet001\Services\Spooler", "Start", "REG_DWORD", 4)
            self.log("[SERVICE] Spouleur d'impression désactivé.")

        # Rapport d'erreurs Windows (WerSvc)
        if opts.disable_error_reporting:
            self.set_value("SYSTEM", r"ControlSet001\Services\WerSvc", "Start", "REG_DWORD", 4)
            self.set_value("SOFTWARE", r"Microsoft\Windows\Windows Error Reporting", "Disabled", "REG_DWORD", 1)

        # Registre à distance (RemoteRegistry - Sécurité)
        if opts.disable_remote_registry:
            self.set_value("SYSTEM", r"ControlSet001\Services\RemoteRegistry", "Start", "REG_DWORD", 4)

        # Désactiver Fast Startup (évite les corruptions de partitions en dual-boot et soulage le SSD)
        if opts.disable_fast_startup:
            self.set_value("SYSTEM", r"ControlSet001\Control\Session Manager\Power", "HiberbootEnabled", "REG_DWORD", 0)

        # Désactiver Delivery Optimization (DoSvc - P2P de bande passante en arrière-plan)
        if opts.disable_delivery_optimization:
            self.set_value("SYSTEM", r"ControlSet001\Services\DoSvc", "Start", "REG_DWORD", 4)
            self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\DeliveryOptimization", "DODownloadMode", "REG_DWORD", 0)
            self.log("[SERVICE] Delivery Optimization (DoSvc) désactivé.")

        # Empêcher le redémarrage automatique intempestif de Windows Update
        if opts.disable_windows_update_auto_reboot:
            self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\WindowsUpdate\AU", "NoAutoRebootWithLoggedOnUsers", "REG_DWORD", 1)
            self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\WindowsUpdate\AU", "AUOptions", "REG_DWORD", 2)  # Notifier uniquement

        # Désactiver les tâches planifiées de télémétrie dans le registre
        if opts.disable_telemetry_tasks:
            self.log("Neutralisation des tâches planifiées de télémétrie dans TaskCache...")
            base_task = r"Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\Tree\Microsoft\Windows"
            # Microsoft Compatibility Appraiser
            self.set_value("SOFTWARE", f"{base_task}\\Application Experience\\Microsoft Compatibility Appraiser", "Id", "REG_SZ", "")
            self.set_value("SOFTWARE", f"{base_task}\\Application Experience\\ProgramDataUpdater", "Id", "REG_SZ", "")
            # Customer Experience Improvement Program
            self.set_value("SOFTWARE", f"{base_task}\\Customer Experience Improvement Program\\Consolidator", "Id", "REG_SZ", "")
            self.set_value("SOFTWARE", f"{base_task}\\Customer Experience Improvement Program\\UsbCeip", "Id", "REG_SZ", "")
            # Autochk Proxy
            self.set_value("SOFTWARE", f"{base_task}\\Autochk\\Proxy", "Id", "REG_SZ", "")

    def apply_storage_optimizations(self, opts: Any) -> None:
        """Optimise le sous-système de stockage (TRIM SSD forcé et suppression d'horodatage)."""
        self.log("Application des optimisations de stockage SSD / NVMe...")
        if getattr(opts, "optimize_ntfs_trim", True):
            # 0 = TRIM activé (DisableDeleteNotify = 0)
            self.set_value("SYSTEM", r"ControlSet001\Control\FileSystem", "DisableDeleteNotify", "REG_DWORD", 0)
            # Désactiver la mise à jour de la date de dernier accès NTFS (réduit l'usure d'écriture SSD)
            self.set_value("SYSTEM", r"ControlSet001\Control\FileSystem", "NtfsDisableLastAccessUpdate", "REG_DWORD", 1)

    def apply_advanced_gaming_tweaks(self, opts: Any) -> None:
        """Applique les optimisations gaming avancées (HAGS, timers, réactivité DWM)."""
        self.log("Application des optimisations Gaming avancées (HAGS, timers, DWM)...")
        # Hardware Accelerated GPU Scheduling (HAGS) - 2 = Activé
        if getattr(opts, "enable_hags", True):
            self.set_value("SYSTEM", r"ControlSet001\Control\GraphicsDrivers", "HwSchMode", "REG_DWORD", 2)

        # Optimisation réactivité timers et réduction de la latence d'ordonnancement
        if getattr(opts, "disable_hpet_synthetic", True):
            self.set_value("SYSTEM", r"ControlSet001\Control\Session Manager\kernel", "GlobalTimerResolutionRequests", "REG_DWORD", 1)

        # Game Bar / Fullscreen Optimization
        self.set_value("SOFTWARE", r"Microsoft\GameBar", "AutoGameModeEnabled", "REG_DWORD", 1)
        self.set_value("SOFTWARE", r"Microsoft\GameBar", "AllowAutoGameMode", "REG_DWORD", 1)
        self.set_value("NTUSER", r"Software\Microsoft\GameBar", "AutoGameModeEnabled", "REG_DWORD", 1)

        # Réactivité DWM (Desktop Window Manager)
        self.set_value("SOFTWARE", r"Microsoft\Windows\DWM", "OverlayTestMode", "REG_DWORD", 5)

    def apply_extended_telemetry_and_privacy(self) -> None:
        """Désactive l'identifiant publicitaire, les expériences personnalisées et la télémétrie étendue."""
        self.log("Application de la protection étendue de la vie privée...")
        # Advertising ID
        self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\AdvertisingInfo", "DisabledByGroupPolicy", "REG_DWORD", 1)
        self.set_value("NTUSER", r"Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo", "Enabled", "REG_DWORD", 0)

        # Expériences personnalisées / Suivi des applications
        self.set_value("NTUSER", r"Software\Microsoft\Windows\CurrentVersion\Privacy", "TailoredExperiencesWithDiagnosticDataEnabled", "REG_DWORD", 0)
        self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\CloudContent", "DisableTailoredExperiencesWithDiagnosticData", "REG_DWORD", 1)
        self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\CloudContent", "DisableThirdPartySuggestions", "REG_DWORD", 1)
        self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\CloudContent", "DisableWindowsSpotlightFeatures", "REG_DWORD", 1)

    def apply_network_gaming_tweaks(self) -> None:
        """Optimise les paramètres TCP/IP pour réduire la latence réseau (Gaming & Ping)."""
        self.log("Application des optimisations réseau (Désactivation de l'algorithme de Nagle)...")
        # Global TCP parameters
        self.set_value("SYSTEM", r"ControlSet001\Services\Tcpip\Parameters", "DefaultTTL", "REG_DWORD", 64)
        self.set_value("SYSTEM", r"ControlSet001\Services\Tcpip\Parameters", "Tcp1323Opts", "REG_DWORD", 1)
        self.set_value("SYSTEM", r"ControlSet001\Services\Tcpip\Parameters", "TcpTimedWaitDelay", "REG_DWORD", 30)
        self.set_value("SYSTEM", r"ControlSet001\Services\Tcpip\Parameters", "MaxUserPort", "REG_DWORD", 65534)

        # Interfaces réseau - Nagle off
        self.set_value("SYSTEM", r"ControlSet001\Services\Tcpip\Parameters\Interfaces", "TcpAckFrequency", "REG_DWORD", 1)
        self.set_value("SYSTEM", r"ControlSet001\Services\Tcpip\Parameters\Interfaces", "TCPNoDelay", "REG_DWORD", 1)

    def apply_system_responsiveness_and_latency(self, opts: Any) -> None:
        """
        Applique les optimisations d'ordonnancement multimédia (MMCSS), de priorité processeur
        (Win32PrioritySeparation), et de désactivation du pré-lancement de Edge / SmartScreen.
        """
        self.log("Application des optimisations de réactivité système (MMCSS / Quantum CPU / Edge)...")

        # 1. MMCSS & SystemResponsiveness (priorité 100% aux jeux/multimédia au lieu de réserver 20% aux services)
        if getattr(opts, "optimize_mmcss_latency", True):
            mmcss_base = r"Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
            self.set_value("SOFTWARE", mmcss_base, "SystemResponsiveness", "REG_DWORD", 0)
            self.set_value("SOFTWARE", mmcss_base, "NetworkThrottlingIndex", "REG_DWORD", 0xFFFFFFFF)
            
            games_task = f"{mmcss_base}\\Tasks\\Games"
            self.set_value("SOFTWARE", games_task, "GPU Priority", "REG_DWORD", 8)
            self.set_value("SOFTWARE", games_task, "Priority", "REG_DWORD", 6)
            self.set_value("SOFTWARE", games_task, "Scheduling Category", "REG_SZ", "High")
            self.set_value("SOFTWARE", games_task, "SFIO Priority", "REG_SZ", "High")
            self.log("[LATENCE] Planificateur MMCSS configuré à 100% pour les applications de premier plan.")

        # 2. Quantum processeur : Win32PrioritySeparation = 0x26 (38 décimal)
        # Priorité maximale et quantums courts/variables adaptés aux applications interactives et jeux
        if getattr(opts, "optimize_processor_scheduling", True):
            self.set_value("SYSTEM", r"ControlSet001\Control\PriorityControl", "Win32PrioritySeparation", "REG_DWORD", 38)
            self.log("[LATENCE] Win32PrioritySeparation configuré à 38 (Priorité forte au processus actif).")

        # 3. Microsoft Edge : Désactivation du pré-lancement et de la télémétrie de fond
        if getattr(opts, "disable_edge_prelaunch", True):
            self.set_value("SOFTWARE", r"Policies\Microsoft\MicrosoftEdge\Main", "AllowPrelaunch", "REG_DWORD", 0)
            self.set_value("SOFTWARE", r"Policies\Microsoft\MicrosoftEdge\TabPreloader", "AllowTabPreloading", "REG_DWORD", 0)
            self.log("[PERF] Pré-lancement de Microsoft Edge désactivé en arrière-plan.")

        if getattr(opts, "disable_edge_telemetry", True):
            self.set_value("SOFTWARE", r"Policies\Microsoft\Edge", "MetricsReportingEnabled", "REG_DWORD", 0)
            self.set_value("SOFTWARE", r"Policies\Microsoft\Edge", "PersonalizationReportingEnabled", "REG_DWORD", 0)

        # 4. SmartScreen (si explicitement demandé)
        if getattr(opts, "disable_smartscreen", False):
            self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\System", "EnableSmartScreen", "REG_DWORD", 0)
            self.set_value("SOFTWARE", r"Microsoft\Windows\CurrentVersion\Explorer", "SmartScreenEnabled", "REG_SZ", "Off")
            self.log("[SÉCURITÉ] SmartScreen désactivé sur les fichiers téléchargés.")

    def apply_win11_24h2_and_onedrive_tweaks(
        self,
        opts: Any = None,
        prevent_device_encryption: Optional[bool] = None,
        disable_onedrive: Optional[bool] = None
    ) -> None:
        """
        Désactive l'auto-chiffrement BitLocker agressif introduit dans Windows 11 24H2
        et neutralise l'installation/intégration forcée de OneDrive.
        """
        # Résolution des drapeaux soit depuis l'objet opts (Win11Options), soit par paramètre direct
        if prevent_device_encryption is not None:
            prevent = prevent_device_encryption
        elif opts is not None:
            prevent = getattr(opts, "prevent_automatic_bitlocker", True)
        else:
            prevent = True

        if disable_onedrive is not None:
            onedrive = disable_onedrive
        elif opts is not None:
            onedrive = getattr(opts, "disable_onedrive_autoinstall", True)
        else:
            onedrive = True

        if prevent:
            self.log("[TWEAK 24H2] Neutralisation du chiffrement automatique BitLocker Device Encryption...")
            # Clé sous la ruche SYSTEM (ControlSet001)
            self.set_value("SYSTEM", r"ControlSet001\Control\BitLocker", "PreventDeviceEncryption", "REG_DWORD", 1)

        if onedrive:
            self.log("[TWEAK ONEDRIVE] Désactivation de la synchronisation et de l'intégration explorateur OneDrive...")
            # Politique système globale bloquant la synchronisation de fichiers
            self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\OneDrive", "DisableFileSyncNGSC", "REG_DWORD", 1)
            
            # Masquer OneDrive du volet de navigation de l'Explorateur Windows
            clsid_onedrive = r"Classes\CLSID\{018D5C66-4533-4307-9B53-224DE2ED1FE6}"
            self.set_value("SOFTWARE", clsid_onedrive, "System.IsPinnedToNameSpaceTree", "REG_DWORD", 0)
            self.set_value("SOFTWARE", f"Classes\\Wow6432Node\\CLSID\\{{018D5C66-4533-4307-9B53-224DE2ED1FE6}}", "System.IsPinnedToNameSpaceTree", "REG_DWORD", 0)
            self.set_value("NTUSER", r"Software\Classes\CLSID\{018D5C66-4533-4307-9B53-224DE2ED1FE6}", "System.IsPinnedToNameSpaceTree", "REG_DWORD", 0)

    def apply_win11_taskbar_and_oobe_tweaks(self, opts: Any) -> None:
        """
        Applique les optimisations d'ergonomie pour Windows 11 :
        - Alignement de la barre des tâches à gauche (style Windows 10/7)
        - Masquage de l'icône Chat / Teams
        - Désactivation des écrans de suggestions post-installation (OOBE / Scoobe)
        - Désactivation des astuces et annonces sur l'écran de verrouillage
        """
        self.log("Application des réglages d'ergonomie et de la barre des tâches Windows 11...")
        adv_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"

        # 1. Alignement de la barre des tâches (0 = Gauche, 1 = Centre)
        if getattr(opts, "taskbar_align_left", True):
            self.set_value("NTUSER", adv_path, "TaskbarAl", "REG_DWORD", 0)
            self.log("[ERGONOMIE] Barre des tâches Windows 11 alignée à gauche.")

        # 2. Masquage de l'icône Chat / Teams
        if getattr(opts, "disable_taskbar_chat", True):
            self.set_value("NTUSER", adv_path, "TaskbarMn", "REG_DWORD", 0)
            self.set_value("SOFTWARE", r"Policies\Microsoft\Windows\Windows Chat", "ChatIcon", "REG_DWORD", 3)
            self.log("[ERGONOMIE] Icône Chat / Teams masquée de la barre des tâches.")

        # 3. Désactivation des invites post-boot OOBE ("Terminer la configuration de votre appareil")
        if getattr(opts, "disable_device_setup_suggestions", True):
            cdm_path = r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager"
            self.set_value("NTUSER", r"Software\Microsoft\Windows\CurrentVersion\UserProfileEngagement", "ScoobeSystemSettingEnabled", "REG_DWORD", 0)
            self.set_value("NTUSER", cdm_path, "SubscribedContent-310093Enabled", "REG_DWORD", 0)
            self.set_value("NTUSER", cdm_path, "SubscribedContent-338389Enabled", "REG_DWORD", 0)
            self.set_value("NTUSER", cdm_path, "SubscribedContent-338388Enabled", "REG_DWORD", 0)
            self.log("[CONFORT] Écrans de harcèlement OOBE et suggestions post-boot désactivés.")

        # 4. Désactivation des astuces sur l'écran de verrouillage
        if getattr(opts, "disable_lockscreen_tips", True):
            cdm_path = r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager"
            self.set_value("NTUSER", cdm_path, "RotatingLockScreenOverlayEnabled", "REG_DWORD", 0)
            self.set_value("NTUSER", cdm_path, "SubscribedContent-338387Enabled", "REG_DWORD", 0)
            self.log("[CONFORT] Astuces et publicités de l'écran de verrouillage désactivées.")

    def apply_memory_and_paging_optimizations(self, opts: Any) -> None:
        """
        Optimise le sous-système de mémoire virtuelle et de pagination :
        - DisablePagingExecutive = 1 : Maintient le noyau et les pilotes en RAM physique
        - LargeSystemCache = 0 : Optimise le cache mémoire pour les applications utilisateur et jeux
        - ClearPageFileAtShutdown = 0 : Accélère l'extinction du système
        """
        if getattr(opts, "optimize_memory_paging", True):
            self.log("Application des optimisations de mémoire vive et pagination du noyau...")
            mm_key = r"ControlSet001\Control\Session Manager\Memory Management"
            self.set_value("SYSTEM", mm_key, "DisablePagingExecutive", "REG_DWORD", 1)
            self.set_value("SYSTEM", mm_key, "LargeSystemCache", "REG_DWORD", 0)
            self.set_value("SYSTEM", mm_key, "ClearPageFileAtShutdown", "REG_DWORD", 0)
            self.log("[PERF] Noyau et pilotes verrouillés en RAM physique (DisablePagingExecutive=1).")

    def apply_context_menu_pro(self, opts: Any) -> None:
        """
        Injecte les entrées avancées du menu contextuel Windows :
        - 'Ouvrir avec PowerShell (Admin)'
        - 'Redémarrer l'Explorateur'
        - 'Compacter avec CompactOS (LZX)'
        """
        self.log("Application des entrées professionnelles du menu contextuel...")

        # 1. Ouvrir avec PowerShell Administrateur
        if getattr(opts, "add_powershell_admin_context_menu", True):
            ps_key = r"Directory\Background\shell\PowerShellAdmin"
            self.set_value("SOFTWARE", f"Classes\\{ps_key}", None, "REG_SZ", "Ouvrir PowerShell (Admin)")
            self.set_value("SOFTWARE", f"Classes\\{ps_key}", "Icon", "REG_SZ", "powershell.exe")
            self.set_value(
                "SOFTWARE",
                f"Classes\\{ps_key}\\command",
                None,
                "REG_SZ",
                r'powershell.exe -Command "Start-Process powershell -Verb RunAs -WorkingDirectory \"%V\""'
            )
            self.log("[MENU] 'Ouvrir PowerShell (Admin)' ajouté au menu contextuel.")

        # 2. Redémarrer l'Explorateur Windows
        if getattr(opts, "add_restart_explorer_context_menu", False):
            restart_key = r"DesktopBackground\shell\RestartExplorer"
            self.set_value("SOFTWARE", f"Classes\\{restart_key}", None, "REG_SZ", "Redémarrer l'Explorateur")
            self.set_value("SOFTWARE", f"Classes\\{restart_key}", "Icon", "REG_SZ", "explorer.exe")
            self.set_value(
                "SOFTWARE",
                f"Classes\\{restart_key}\\command",
                None,
                "REG_SZ",
                r'cmd.exe /c taskkill /f /im explorer.exe & start explorer.exe'
            )
            self.log("[MENU] 'Redémarrer l'Explorateur' ajouté au menu contextuel du Bureau.")

        # 3. Compact OS (Compression de dossier LZX)
        if getattr(opts, "add_compact_os_context_menu", False):
            compact_key = r"Directory\shell\CompactOS"
            self.set_value("SOFTWARE", f"Classes\\{compact_key}", None, "REG_SZ", "Compacter le dossier (CompactOS LZX)")
            self.set_value("SOFTWARE", f"Classes\\{compact_key}", "Icon", "REG_SZ", "shell32.dll,48")
            self.set_value(
                "SOFTWARE",
                f"Classes\\{compact_key}\\command",
                None,
                "REG_SZ",
                r'cmd.exe /c compact.exe /c /s /i /exe:lzx \"%1\\*\"'
            )
            self.log("[MENU] 'Compacter le dossier (LZX)' ajouté au menu contextuel.")

    def apply_dns_presets(self, preset_name: str) -> None:
        """
        Configure les serveurs DNS publics à ultra-faible latence (Cloudflare, Google, Quad9).
        """
        dns_map = {
            "cloudflare": ("1.1.1.1,1.0.0.1", "Cloudflare DNS (1.1.1.1)"),
            "google": ("8.8.8.8,8.8.4.4", "Google DNS (8.8.8.8)"),
            "quad9": ("9.9.9.9,149.112.112.112", "Quad9 DNS (9.9.9.9)"),
            "adguard": ("94.140.14.14,94.140.15.15", "AdGuard DNS (Bloqueur de pubs)"),
        }
        key = preset_name.lower().strip()
        if key not in dns_map:
            return

        servers, label = dns_map[key]
        self.log(f"[DNS] Configuration des serveurs DNS rapides : {label}...")
        tcp_interfaces = r"ControlSet001\Services\Tcpip\Parameters\Interfaces"
        self.set_value("SYSTEM", r"ControlSet001\Services\Tcpip\Parameters", "NameServer", "REG_SZ", servers)
        self.set_value("SYSTEM", tcp_interfaces, "NameServer", "REG_SZ", servers)

    def apply_dns_cache_optimizations(self) -> None:
        """
        Optimise le cache du résolveur DNS local pour éliminer les latences réseau :
        - MaxCacheTtl = 86400 (Conserve le cache 24h)
        - MaxNegativeCacheTtl = 5 (Réduit à 5s l'attente sur les domaines non trouvés)
        """
        self.log("[DNS] Optimisation des temps de cache DNS local...")
        dns_cache_key = r"SYSTEM\ControlSet001\Services\Dnscache\Parameters"
        self.set_value("SYSTEM", dns_cache_key, "MaxCacheTtl", "REG_DWORD", 86400)
        self.set_value("SYSTEM", dns_cache_key, "MaxNegativeCacheTtl", "REG_DWORD", 5)

    def apply_defender_gaming_optimizations(self, add_exclusions: bool = True) -> None:
        """
        Optimise Windows Defender pour éliminer les micro-saccades en jeu :
        - Ajoute des exclusions automatiques pour C:\\Games et D:\\Games
        - Désactive l'envoi d'échantillons en arrière-plan (SubmitSamplesConsent)
        """
        self.log("Optimisation de Windows Defender pour le Gaming...")
        sp_key = r"SOFTWARE\Policies\Microsoft\Windows Defender\Spynet"
        self.set_value("SOFTWARE", sp_key, "SubmitSamplesConsent", "REG_DWORD", 2)  # Never send
        self.set_value("SOFTWARE", sp_key, "SpynetReporting", "REG_DWORD", 0)  # Disabled

        if add_exclusions:
            excl_paths = r"SOFTWARE\Microsoft\Windows Defender\Exclusions\Paths"
            self.set_value("SOFTWARE", excl_paths, r"C:\Games", "REG_DWORD", 0)
            self.set_value("SOFTWARE", excl_paths, r"D:\Games", "REG_DWORD", 0)
            self.log("[DEFENDER] Exclusions de dossiers C:\\Games et D:\\Games enregistrées.")

    def disable_automatic_maintenance(self) -> None:
        """
        Désactive la maintenance automatique de Windows qui s'exécute en arrière-plan
        et provoque des pics de charge CPU/disque inattendus.
        """
        self.log("[PERF] Neutralisation de la maintenance automatique de fond...")
        maint_key = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\Maintenance"
        self.set_value("SOFTWARE", maint_key, "MaintenanceDisabled", "REG_DWORD", 1)


