"""
Générateur de fichier de réponse autounattend.xml pour Windows Setup.
Automatise l'installation, crée un compte local, désactive l'OOBE et les exigences en ligne.
"""

from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom
from core.config import UnattendedConfig, TargetOS


SUPPORTED_LOCALES = {
    "Français (France)": {
        "locale": "fr-FR",
        "keyboard_layout": "040c:0000040c",
        "time_zone": "Romance Standard Time"
    },
    "English (United States)": {
        "locale": "en-US",
        "keyboard_layout": "0409:00000409",
        "time_zone": "Eastern Standard Time"
    },
    "English (United Kingdom)": {
        "locale": "en-GB",
        "keyboard_layout": "0809:00000809",
        "time_zone": "GMT Standard Time"
    },
    "Deutsch (Deutschland)": {
        "locale": "de-DE",
        "keyboard_layout": "0407:00000407",
        "time_zone": "W. Europe Standard Time"
    },
    "Español (España)": {
        "locale": "es-ES",
        "keyboard_layout": "0c0a:00000c0a",
        "time_zone": "Romance Standard Time"
    },
    "Italiano (Italia)": {
        "locale": "it-IT",
        "keyboard_layout": "0410:00000410",
        "time_zone": "W. Europe Standard Time"
    },
    "Français (Belgique)": {
        "locale": "fr-BE",
        "keyboard_layout": "080c:0000080c",
        "time_zone": "Romance Standard Time"
    },
    "Français (Suisse)": {
        "locale": "fr-CH",
        "keyboard_layout": "100c:0000100c",
        "time_zone": "W. Europe Standard Time"
    },
    "Français (Canada)": {
        "locale": "fr-CA",
        "keyboard_layout": "0c0c:00000c0c",
        "time_zone": "Eastern Standard Time"
    }
}


class UnattendedGenerator:
    def __init__(
        self,
        config: UnattendedConfig,
        target_os: TargetOS = TargetOS.WIN11,
        architecture: str = "amd64",
        post_install_commands: Optional[list[str]] = None
    ):
        self.config = config
        self.target_os = target_os
        # Windows unattended architecture: 'amd64' ou 'x86'
        self.arch = "amd64" if architecture.lower() in ("x64", "amd64") else "x86"
        
        # Consolidation des commandes FirstLogonCommands
        cmds = list(getattr(self.config, "first_logon_commands", []) or [])
        if post_install_commands:
            cmds.extend(post_install_commands)
        self.post_install_commands = cmds

    def generate_xml(self) -> str:
        """Génère le document XML autounattend.xml sous forme de chaîne formatée."""
        root = ET.Element("unattend", {
            "xmlns": "urn:schemas-microsoft-com:unattend",
            "xmlns:wcm": "http://schemas.microsoft.com/WMIConfig/2002/State"
        })

        # --- PASS 1: windowsPE ---
        settings_pe = ET.SubElement(root, "settings", pass_="windowsPE")
        
        # International-Core-WinPE
        intl_pe = ET.SubElement(settings_pe, "component", {
            "name": "Microsoft-Windows-International-Core-WinPE",
            "processorArchitecture": self.arch,
            "publicKeyToken": "31bf3856ad364e35",
            "language": "neutral",
            "versionScope": "nonSxS"
        })
        ET.SubElement(intl_pe, "SetupUILanguage").append(
            ET.Element("UILanguage", text=self.config.locale)
        )
        intl_pe.find("SetupUILanguage/UILanguage").text = self.config.locale
        ET.SubElement(intl_pe, "InputLocale").text = self.config.keyboard_layout
        ET.SubElement(intl_pe, "SystemLocale").text = self.config.locale
        ET.SubElement(intl_pe, "UILanguage").text = self.config.locale
        ET.SubElement(intl_pe, "UserLocale").text = self.config.locale

        # Windows Setup
        setup = ET.SubElement(settings_pe, "component", {
            "name": "Microsoft-Windows-Setup",
            "processorArchitecture": self.arch,
            "publicKeyToken": "31bf3856ad364e35",
            "language": "neutral",
            "versionScope": "nonSxS"
        })
        # Résolution d'affichage native pour WinPE Setup (1080p net au lieu de 1024x768 VGA)
        if getattr(self.config, "display_resolution", None):
            res_parts = self.config.display_resolution.lower().split("x")
            if len(res_parts) == 2:
                disp_pe = ET.SubElement(setup, "Display")
                ET.SubElement(disp_pe, "ColorDepth").text = "32"
                ET.SubElement(disp_pe, "HorizontalResolution").text = res_parts[0].strip()
                ET.SubElement(disp_pe, "VerticalResolution").text = res_parts[1].strip()
                ET.SubElement(disp_pe, "RefreshRate").text = "60"

        user_data = ET.SubElement(setup, "UserData")
        ET.SubElement(user_data, "AcceptEula").text = "true" if self.config.skip_eula else "false"

        # Clé de produit générique pour sauter la sélection d'édition et la demande de licence
        if self.config.product_key:
            prod_key = ET.SubElement(user_data, "ProductKey")
            ET.SubElement(prod_key, "Key").text = self.config.product_key
            ET.SubElement(prod_key, "WillShowUI").text = "OnError"

        # Mode Zéro-Clic : Partitionnement automatique GPT/UEFI du disque
        if self.config.auto_disk_partition:
            disk_config = ET.SubElement(setup, "DiskConfiguration")
            disk = ET.SubElement(disk_config, "Disk", {"wcm:action": "add"})
            ET.SubElement(disk, "DiskID").text = str(self.config.disk_id)
            ET.SubElement(disk, "WillWipeDisk").text = "true"

            # CreatePartitions (EFI 100 Mo, MSR 16 Mo, OS Restant)
            create_parts = ET.SubElement(disk, "CreatePartitions")
            
            p1 = ET.SubElement(create_parts, "CreatePartition", {"wcm:action": "add"})
            ET.SubElement(p1, "Order").text = "1"
            ET.SubElement(p1, "Size").text = "100"
            ET.SubElement(p1, "Type").text = "EFI"

            p2 = ET.SubElement(create_parts, "CreatePartition", {"wcm:action": "add"})
            ET.SubElement(p2, "Order").text = "2"
            ET.SubElement(p2, "Size").text = "16"
            ET.SubElement(p2, "Type").text = "MSR"

            p3 = ET.SubElement(create_parts, "CreatePartition", {"wcm:action": "add"})
            ET.SubElement(p3, "Order").text = "3"
            ET.SubElement(p3, "Extend").text = "true"
            ET.SubElement(p3, "Type").text = "Primary"

            # ModifyPartitions (Formatage FAT32 EFI, NTFS OS)
            modify_parts = ET.SubElement(disk, "ModifyPartitions")

            m1 = ET.SubElement(modify_parts, "ModifyPartition", {"wcm:action": "add"})
            ET.SubElement(m1, "Order").text = "1"
            ET.SubElement(m1, "PartitionID").text = "1"
            ET.SubElement(m1, "Format").text = "FAT32"
            ET.SubElement(m1, "Label").text = "System"

            m2 = ET.SubElement(modify_parts, "ModifyPartition", {"wcm:action": "add"})
            ET.SubElement(m2, "Order").text = "2"
            ET.SubElement(m2, "PartitionID").text = "2"

            m3 = ET.SubElement(modify_parts, "ModifyPartition", {"wcm:action": "add"})
            ET.SubElement(m3, "Order").text = "3"
            ET.SubElement(m3, "PartitionID").text = "3"
            ET.SubElement(m3, "Format").text = "NTFS"
            ET.SubElement(m3, "Label").text = "Windows"
            ET.SubElement(m3, "Letter").text = "C"

            # ImageInstall pour installer automatiquement sur la partition 3
            image_install = ET.SubElement(setup, "ImageInstall")
            os_image = ET.SubElement(image_install, "OSImage")
            install_to = ET.SubElement(os_image, "InstallTo")
            ET.SubElement(install_to, "DiskID").text = str(self.config.disk_id)
            ET.SubElement(install_to, "PartitionID").text = "3"
            ET.SubElement(os_image, "WillShowUI").text = "OnError"
        
        # Si Windows 11, injecter les commandes synchrones dans WinPE pour bypasser le TPM si pas encore fait
        if self.target_os == TargetOS.WIN11:
            run_sync = ET.SubElement(setup, "RunSynchronous")
            commands = [
                r'reg add "HKLM\SYSTEM\Setup\LabConfig" /v BypassTPMCheck /t REG_DWORD /d 1 /f',
                r'reg add "HKLM\SYSTEM\Setup\LabConfig" /v BypassSecureBootCheck /t REG_DWORD /d 1 /f',
                r'reg add "HKLM\SYSTEM\Setup\LabConfig" /v BypassRAMCheck /t REG_DWORD /d 1 /f',
                r'reg add "HKLM\SYSTEM\Setup\LabConfig" /v BypassCPUCheck /t REG_DWORD /d 1 /f',
                r'reg add "HKLM\SYSTEM\Setup\LabConfig" /v BypassStorageCheck /t REG_DWORD /d 1 /f'
            ]
            for idx, cmd in enumerate(commands, start=1):
                sync_cmd = ET.SubElement(run_sync, "RunSynchronousCommand", {"wcm:action": "add"})
                ET.SubElement(sync_cmd, "Order").text = str(idx)
                ET.SubElement(sync_cmd, "Path").text = f"cmd.exe /c {cmd}"
                ET.SubElement(sync_cmd, "Description").text = f"Bypass HW Check {idx}"

        # --- PASS 2: specialize ---
        settings_spec = ET.SubElement(root, "settings", pass_="specialize")
        shell_spec = ET.SubElement(settings_spec, "component", {
            "name": "Microsoft-Windows-Shell-Setup",
            "processorArchitecture": self.arch,
            "publicKeyToken": "31bf3856ad364e35",
            "language": "neutral",
            "versionScope": "nonSxS"
        })
        ET.SubElement(shell_spec, "ComputerName").text = self.config.computer_name
        ET.SubElement(shell_spec, "TimeZone").text = self.config.time_zone

        # Si activation du compte administrateur natif
        if self.config.use_builtin_admin:
            dep = ET.SubElement(settings_spec, "component", {
                "name": "Microsoft-Windows-Deployment",
                "processorArchitecture": self.arch,
                "publicKeyToken": "31bf3856ad364e35",
                "language": "neutral",
                "versionScope": "nonSxS"
            })
            run_spec = ET.SubElement(dep, "RunSynchronous")
            sync_admin = ET.SubElement(run_spec, "RunSynchronousCommand", {"wcm:action": "add"})
            ET.SubElement(sync_admin, "Order").text = "1"
            ET.SubElement(sync_admin, "Path").text = "cmd.exe /c net user Administrator /active:yes"
            ET.SubElement(sync_admin, "Description").text = "Activer Administrateur Integre"

        # --- PASS 3: oobeSystem ---
        settings_oobe = ET.SubElement(root, "settings", pass_="oobeSystem")
        shell_oobe = ET.SubElement(settings_oobe, "component", {
            "name": "Microsoft-Windows-Shell-Setup",
            "processorArchitecture": self.arch,
            "publicKeyToken": "31bf3856ad364e35",
            "language": "neutral",
            "versionScope": "nonSxS"
        })

        if getattr(self.config, "display_resolution", None):
            res_parts = self.config.display_resolution.lower().split("x")
            if len(res_parts) == 2:
                disp_oobe = ET.SubElement(shell_oobe, "Display")
                ET.SubElement(disp_oobe, "ColorDepth").text = "32"
                ET.SubElement(disp_oobe, "HorizontalResolution").text = res_parts[0].strip()
                ET.SubElement(disp_oobe, "VerticalResolution").text = res_parts[1].strip()

        oobe_block = ET.SubElement(shell_oobe, "OOBE")
        ET.SubElement(oobe_block, "HideEULAPage").text = "true"
        ET.SubElement(oobe_block, "HideOEMRegistrationScreen").text = "true"
        ET.SubElement(oobe_block, "HideOnlineAccountScreens").text = "true"  # Bypass MS Account !
        ET.SubElement(oobe_block, "HideWirelessSetupInOOBE").text = "true"
        ET.SubElement(oobe_block, "ProtectYourPC").text = "3"  # Pas de configuration expresse
        ET.SubElement(oobe_block, "NetworkLocation").text = "Work"

        user_accounts = ET.SubElement(shell_oobe, "UserAccounts")

        if self.config.use_builtin_admin:
            admin_pwd = ET.SubElement(user_accounts, "AdministratorPassword")
            ET.SubElement(admin_pwd, "Value").text = self.config.admin_password or ""
            ET.SubElement(admin_pwd, "PlainText").text = "true"
            target_user = "Administrator"
        else:
            # Création du compte local Administrateur
            local_accounts = ET.SubElement(user_accounts, "LocalAccounts")
            local_account = ET.SubElement(local_accounts, "LocalAccount", {"wcm:action": "add"})
            ET.SubElement(local_account, "Name").text = self.config.admin_username
            ET.SubElement(local_account, "Group").text = "Administrators"
            ET.SubElement(local_account, "DisplayName").text = self.config.admin_username
            ET.SubElement(local_account, "Description").text = "Compte administrateur local généré par OSBuilder-Win"

            password_elem = ET.SubElement(local_account, "Password")
            ET.SubElement(password_elem, "Value").text = self.config.admin_password or ""
            ET.SubElement(password_elem, "PlainText").text = "true"
            target_user = self.config.admin_username

        # AutoLogon si demandé
        if self.config.auto_logon:
            auto_logon = ET.SubElement(shell_oobe, "AutoLogon")
            ET.SubElement(auto_logon, "Enabled").text = "true"
            ET.SubElement(auto_logon, "Username").text = target_user
            ET.SubElement(auto_logon, "LogonCount").text = "1"
            pwd_al = ET.SubElement(auto_logon, "Password")
            ET.SubElement(pwd_al, "Value").text = self.config.admin_password or ""
            ET.SubElement(pwd_al, "PlainText").text = "true"

        # Commandes exécutées automatiquement à la première ouverture de session utilisateur
        if self.post_install_commands:
            first_logon = ET.SubElement(shell_oobe, "FirstLogonCommands")
            for idx, cmd in enumerate(self.post_install_commands, start=1):
                sync_cmd = ET.SubElement(first_logon, "SynchronousCommand", {"wcm:action": "add"})
                ET.SubElement(sync_cmd, "Order").text = str(idx)
                ET.SubElement(sync_cmd, "CommandLine").text = cmd
                ET.SubElement(sync_cmd, "Description").text = f"PostInstall App {idx}"

        xml_str = ET.tostring(root, encoding="utf-8")
        parsed = minidom.parseString(xml_str)
        # Remplacement de l'attribut pass_ en pass
        pretty_xml = parsed.toprettyxml(indent="  ")
        return pretty_xml.replace('pass_="windowsPE"', 'pass="windowsPE"') \
                         .replace('pass_="specialize"', 'pass="specialize"') \
                         .replace('pass_="oobeSystem"', 'pass="oobeSystem"')

    def write_to_file(self, dest_path: Path | str) -> Path:
        """Sauvegarde le fichier autounattend.xml à l'emplacement indiqué."""
        dest = Path(dest_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        xml_content = self.generate_xml()
        with open(dest, "w", encoding="utf-8") as f:
            f.write(xml_content)
        return dest
