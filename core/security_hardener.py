"""
Module de durcissement de sécurité, politique Windows Update et protection de la vie privée.
Permet d'empêcher les mises à jour forcées de pilotes par Windows Update, de bloquer les domaines
de télémétrie dans le fichier hosts et de neutraliser l'espionnage Recall / Copilot / DiagTrack.
"""

from enum import Enum
from pathlib import Path
from typing import List
from core.registry_manager import RegistryManager


class WindowsUpdatePolicy(str, Enum):
    DEFAULT = "default"              # Comportement par défaut de Windows
    SECURITY_ONLY = "security_only"  # MàJ de sécurité seules, exclut les pilotes et bloatware
    NOTIFY_ONLY = "notify_only"      # Notifier avant téléchargement et installation (jamais automatique)
    DISABLED = "disabled"            # Désactiver totalement le service Windows Update


TELEMETRY_HOSTS: List[str] = [
    "v10.events.data.microsoft.com",
    "v20.events.data.microsoft.com",
    "telemetry.microsoft.com",
    "v10.vortex-win.data.microsoft.com",
    "settings-win.data.microsoft.com",
    "watson.telemetry.microsoft.com",
    "activity.windows.com",
    "diagnostics.support.microsoft.com",
    "feedback.search.microsoft.com",
    "corpext.msitadfs.glbdns2.microsoft.com",
    "onesettings-db5.metron.live.com.akadns.net",
    "df.telemetry.microsoft.com",
    "reports.wes.df.telemetry.microsoft.com",
    "cs1.wpc.v0cdn.net",
    "vortex.data.microsoft.com",
]


class SecurityHardener:
    """Gestionnaire de durcissement de la sécurité et neutralisation de la télémétrie."""

    @classmethod
    def apply_windows_update_policy(
        cls,
        reg: RegistryManager,
        policy: WindowsUpdatePolicy = WindowsUpdatePolicy.NOTIFY_ONLY,
        block_driver_updates: bool = True
    ) -> bool:
        """Configure les stratégies Windows Update dans la ruche SOFTWARE hors-ligne."""
        try:
            wu_key = r"Policies\Microsoft\Windows\WindowsUpdate"
            au_key = r"Policies\Microsoft\Windows\WindowsUpdate\AU"

            # 1. Empêcher Windows Update d'écraser les pilotes graphiques/audio personnalisés
            if block_driver_updates:
                reg.set_value("SOFTWARE", wu_key, "ExcludeWUDriversInQualityUpdate", "REG_DWORD", 1)

            # 2. Appliquer la stratégie sélectionnée
            if policy == WindowsUpdatePolicy.NOTIFY_ONLY:
                reg.set_value("SOFTWARE", au_key, "NoAutoUpdate", "REG_DWORD", 0)
                reg.set_value("SOFTWARE", au_key, "AUOptions", "REG_DWORD", 2)
                reg.set_value("SOFTWARE", au_key, "NoAutoRebootWithLoggedOnUsers", "REG_DWORD", 1)
                reg.set_value("SOFTWARE", au_key, "AlwaysAutoRebootAtScheduledTime", "REG_DWORD", 0)
            elif policy == WindowsUpdatePolicy.SECURITY_ONLY:
                reg.set_value("SOFTWARE", au_key, "NoAutoUpdate", "REG_DWORD", 0)
                reg.set_value("SOFTWARE", au_key, "AUOptions", "REG_DWORD", 3)
                reg.set_value("SOFTWARE", au_key, "NoAutoRebootWithLoggedOnUsers", "REG_DWORD", 1)
                reg.set_value("SOFTWARE", wu_key, "DeferFeatureUpdates", "REG_DWORD", 1)
                reg.set_value("SOFTWARE", wu_key, "DeferFeatureUpdatesPeriodInDays", "REG_DWORD", 365)
            elif policy == WindowsUpdatePolicy.DISABLED:
                reg.set_value("SOFTWARE", au_key, "NoAutoUpdate", "REG_DWORD", 1)

            return True
        except Exception:
            return False

    @classmethod
    def apply_deep_privacy_hardening(cls, reg: RegistryManager) -> bool:
        """
        Applique un durcissement de confidentialité poussé :
        - Neutralisation de Recall & Windows Copilot
        - Désactivation de l'historique d'activités (Timeline)
        - Désactivation de Cortana et de la collecte publicitaire
        """
        try:
            # 1. Neutralisation totale de Windows Recall (24H2)
            ai_key = r"Policies\Microsoft\Windows\WindowsAI"
            reg.set_value("SOFTWARE", ai_key, "DisableAIDataAnalysis", "REG_DWORD", 1)
            reg.set_value("SOFTWARE", ai_key, "TurnOffSavingSnapshots", "REG_DWORD", 1)

            # 2. Neutralisation de Windows Copilot
            copilot_key = r"Policies\Microsoft\Windows\WindowsCopilot"
            reg.set_value("SOFTWARE", copilot_key, "TurnOffWindowsCopilot", "REG_DWORD", 1)

            # 3. Neutralisation de l'historique d'activité
            sys_key = r"Policies\Microsoft\Windows\System"
            reg.set_value("SOFTWARE", sys_key, "EnableActivityFeed", "REG_DWORD", 0)
            reg.set_value("SOFTWARE", sys_key, "PublishUserActivities", "REG_DWORD", 0)
            reg.set_value("SOFTWARE", sys_key, "UploadUserActivities", "REG_DWORD", 0)

            # 4. Désactivation Cortana et Suggestions Bing
            search_key = r"Policies\Microsoft\Windows\Windows Search"
            reg.set_value("SOFTWARE", search_key, "AllowCortana", "REG_DWORD", 0)
            reg.set_value("SOFTWARE", search_key, "DisableWebSearch", "REG_DWORD", 1)
            reg.set_value("SOFTWARE", search_key, "ConnectedSearchUseWeb", "REG_DWORD", 0)

            # 5. Désactivation de la publicité ciblée
            adv_key = r"Policies\Microsoft\Windows\AdvertisingInfo"
            reg.set_value("SOFTWARE", adv_key, "DisabledByGroupPolicy", "REG_DWORD", 1)

            return True
        except Exception:
            return False

    @classmethod
    def disable_tracking_services(cls, reg: RegistryManager) -> bool:
        """Désactive DiagTrack et dmwappushservice dans la ruche SYSTEM."""
        try:
            reg.set_value("SYSTEM", r"ControlSet001\Services\DiagTrack", "Start", "REG_DWORD", 4)
            reg.set_value("SYSTEM", r"ControlSet001\Services\dmwappushservice", "Start", "REG_DWORD", 4)
            return True
        except Exception:
            return False

    @classmethod
    def inject_telemetry_hosts_blocklist(cls, mount_dir: Path | str) -> bool:
        """
        Injecte le blocage des serveurs de télémétrie Microsoft directement dans
        le fichier Windows\\System32\\drivers\\etc\\hosts de l'image montée.
        """
        hosts_file = Path(mount_dir) / "Windows" / "System32" / "drivers" / "etc" / "hosts"
        if not hosts_file.exists():
            return False

        try:
            content = hosts_file.read_text(encoding="utf-8", errors="ignore")
            block_lines = [
                "",
                "# --- Bloquage de la télémétrie par OSBuilder-Win Studio PRO ---"
            ]
            for host in TELEMETRY_HOSTS:
                if host not in content:
                    block_lines.append(f"0.0.0.0 {host}")

            if len(block_lines) > 2:
                with open(hosts_file, "a", encoding="utf-8") as f:
                    f.write("\n".join(block_lines) + "\n")
            return True
        except Exception:
            return False
