"""
Module d'optimisation réseau avancée pour le Gaming de compétition et la réduction de latence.
Configure la pile TCP/IP, le tampon Winsock, le planificateur MMCSS et injecte les résolveurs DNS rapides.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from core.registry_manager import RegistryManager


@dataclass
class DnsServerPreset:
    name: str
    description: str
    primary_ipv4: str
    secondary_ipv4: str
    primary_ipv6: Optional[str] = None
    secondary_ipv6: Optional[str] = None


DNS_PRESETS: Dict[str, DnsServerPreset] = {
    "cloudflare": DnsServerPreset(
        name="Cloudflare 1.1.1.1 (Gaming)",
        description="Le résolveur DNS public le plus rapide au monde, optimisé pour la latence minimale en jeu.",
        primary_ipv4="1.1.1.1",
        secondary_ipv4="1.0.0.1",
        primary_ipv6="2606:4700:4700::1111",
        secondary_ipv6="2606:4700:4700::1001",
    ),
    "cloudflare_security": DnsServerPreset(
        name="Cloudflare Security (Anti-Malware)",
        description="Résolveur 1.1.1.2 filtrant automatiquement les domaines malveillants et de phishing.",
        primary_ipv4="1.1.1.2",
        secondary_ipv4="1.0.0.2",
        primary_ipv6="2606:4700:4700::1112",
        secondary_ipv6="2606:4700:4700::1002",
    ),
    "quad9": DnsServerPreset(
        name="Quad9 (Sécurité & Confidentialité Suisse)",
        description="Protection maximale contre les cyberattaques basée sur les renseignements de sécurité IBM/CERT.",
        primary_ipv4="9.9.9.9",
        secondary_ipv4="149.112.112.112",
        primary_ipv6="2620:fe::fe",
        secondary_ipv6="2620:fe::9",
    ),
    "adguard": DnsServerPreset(
        name="AdGuard DNS (Bloqueur Pubs & Trackers)",
        description="Bloque les bannières publicitaires, traqueurs et compteurs au niveau DNS sur toute la machine.",
        primary_ipv4="94.140.14.14",
        secondary_ipv4="94.140.15.15",
        primary_ipv6="2a10:50c0::ad1:ff",
        secondary_ipv6="2a10:50c0::ad2:ff",
    ),
    "google": DnsServerPreset(
        name="Google Public DNS",
        description="Résolveur robuste et mondial avec très haute disponibilité.",
        primary_ipv4="8.8.8.8",
        secondary_ipv4="8.8.4.4",
        primary_ipv6="2001:4860:4860::8888",
        secondary_ipv6="2001:4860:4860::8844",
    ),
}


class NetworkOptimizer:
    """Gestionnaire d'optimisation réseau et de la pile protocolaire Windows."""

    @classmethod
    def get_dns_preset(cls, preset_key: str) -> Optional[DnsServerPreset]:
        """Récupère un preset DNS par sa clé."""
        return DNS_PRESETS.get(preset_key.lower())

    @classmethod
    def get_available_presets(cls) -> Dict[str, DnsServerPreset]:
        """Retourne la liste des presets disponibles."""
        return DNS_PRESETS

    @classmethod
    def apply_tcp_gaming_tweaks(cls, reg: RegistryManager) -> bool:
        """
        Applique les réglages TCP/IP pour réduire le ping et supprimer le bridage réseau :
        - Désactivation de Nagle (TcpAckFrequency=1, TCPNoDelay=1)
        - Suppression du throttling réseau multimédia (NetworkThrottlingIndex=0xffffffff)
        - Débridage de la réactivité système (SystemResponsiveness=0)
        - Augmentation de la plage de ports dynamiques (MaxUserPort=65534)
        """
        try:
            # 1. Ruche SOFTWARE : NetworkThrottlingIndex et SystemResponsiveness
            net_profile_key = r"Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
            reg.set_value("SOFTWARE", net_profile_key, "NetworkThrottlingIndex", "REG_DWORD", 0xFFFFFFFF)
            reg.set_value("SOFTWARE", net_profile_key, "SystemResponsiveness", "REG_DWORD", 0)

            games_key = r"Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
            reg.set_value("SOFTWARE", games_key, "GPU Priority", "REG_DWORD", 8)
            reg.set_value("SOFTWARE", games_key, "Priority", "REG_DWORD", 6)
            reg.set_value("SOFTWARE", games_key, "Scheduling Category", "REG_SZ", "High")
            reg.set_value("SOFTWARE", games_key, "SFIO Priority", "REG_SZ", "High")

            # 2. Ruche SYSTEM : Paramètres TCP/IP et Nagle
            tcp_params = r"ControlSet001\Services\Tcpip\Parameters"
            reg.set_value("SYSTEM", tcp_params, "DefaultTTL", "REG_DWORD", 64)
            reg.set_value("SYSTEM", tcp_params, "MaxUserPort", "REG_DWORD", 65534)
            reg.set_value("SYSTEM", tcp_params, "TcpTimedWaitDelay", "REG_DWORD", 30)
            reg.set_value("SYSTEM", tcp_params, "EnableDCA", "REG_DWORD", 1)

            interfaces_key = r"ControlSet001\Services\Tcpip\Parameters\Interfaces"
            reg.set_value("SYSTEM", interfaces_key, "TcpAckFrequency", "REG_DWORD", 1)
            reg.set_value("SYSTEM", interfaces_key, "TCPNoDelay", "REG_DWORD", 1)
            reg.set_value("SYSTEM", interfaces_key, "TcpDelAckTicks", "REG_DWORD", 0)

            return True
        except Exception:
            return False

    @classmethod
    def generate_setupcomplete_network_script(
        cls,
        dns_preset_key: Optional[str] = "cloudflare"
    ) -> str:
        """
        Génère les commandes de configuration netsh/PowerShell pour la pile réseau
        à injecter dans SetupComplete.cmd.
        """
        lines = [
            ":: Optimisation Réseau et Latence Gaming (OSBuilder-Win Studio PRO)",
            "netsh int tcp set global autotuninglevel=normal >nul 2>&1",
            "netsh int tcp set global congestionprovider=ctcp >nul 2>&1",
            "netsh int tcp set global ecncapability=enabled >nul 2>&1",
            "netsh int tcp set global rss=enabled >nul 2>&1",
            "netsh int tcp set global timestamps=disabled >nul 2>&1",
        ]

        if dns_preset_key and dns_preset_key.lower() in DNS_PRESETS:
            preset = DNS_PRESETS[dns_preset_key.lower()]
            lines.append(f":: Configuration DNS : {preset.name}")
            ps_cmd = (
                f"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"Get-NetAdapter | Where-Object {{ $_.Status -eq 'Up' }} | "
                f"ForEach-Object {{ Set-DnsClientServerAddress -InterfaceIndex $_.InterfaceIndex "
                f"-ServerAddresses ('{preset.primary_ipv4}','{preset.secondary_ipv4}') }}\""
            )
            lines.append(ps_cmd)

        return "\n".join(lines) + "\n"
