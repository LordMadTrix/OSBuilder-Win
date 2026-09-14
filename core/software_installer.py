"""
Module d'intégration et d'automatisation des applications logicielles et runtimes
pour le déploiement hors-ligne et en premier démarrage (FirstLogon / SetupComplete).
"""

import os
import shutil
from pathlib import Path
from typing import Callable, List, Optional, Tuple


class SoftwareInstaller:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log = log_callback or (lambda msg: None)

    @staticmethod
    def detect_installer_silent_flags(filename: str) -> str:
        """
        Détermine automatiquement les drapeaux d'installation silencieuse
        en fonction du nom ou de l'extension de l'installateur.
        """
        lower = filename.lower()
        if lower.endswith(".msi"):
            return "/qn /norestart"
        elif "inno" in lower or "setup" in lower:
            return "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
        elif "7z" in lower or "nsis" in lower:
            return "/S"
        elif "vcredist" in lower or "vc_redist" in lower:
            return "/quiet /norestart"
        elif "directx" in lower or "dxwebsetup" in lower or "dxsetup" in lower:
            return "/Q"
        elif "chrome" in lower or "firefox" in lower or "brave" in lower:
            return "/silent /install"
        else:
            return "/quiet /norestart"

    def stage_offline_applications(
        self,
        source_apps_dir: Path | str,
        image_mount_dir: Path | str
    ) -> List[Tuple[str, str]]:
        """
        Copie les installeurs (.exe, .msi) depuis un dossier source local
        vers Windows\\Setup\\Apps\\ dans l'image montée et prépare les lignes
        de commande pour l'installation silencieuse.
        Retourne la liste des tuples (nom_fichier, commande_silencieuse).
        """
        src_path = Path(source_apps_dir).resolve()
        mount_path = Path(image_mount_dir).resolve()

        if not src_path.exists():
            self.log(f"[APPS HORS-LIGNE] Dossier source introuvable : {src_path}")
            return []

        dest_apps_dir = mount_path / "Windows" / "Setup" / "Apps"
        dest_apps_dir.mkdir(parents=True, exist_ok=True)

        staged = []
        for item in src_path.iterdir():
            if item.is_file() and item.suffix.lower() in (".exe", ".msi", ".cmd", ".bat"):
                dest_file = dest_apps_dir / item.name
                self.log(f"[APPS HORS-LIGNE] Intégration de l'installateur : {item.name}...")
                shutil.copy2(item, dest_file)

                if item.suffix.lower() in (".cmd", ".bat"):
                    cmd = f'call "%WINDIR%\\Setup\\Apps\\{item.name}"'
                elif item.suffix.lower() == ".msi":
                    cmd = f'msiexec.exe /i "%WINDIR%\\Setup\\Apps\\{item.name}" /qn /norestart'
                else:
                    flags = self.detect_installer_silent_flags(item.name)
                    cmd = f'start /wait "" "%WINDIR%\\Setup\\Apps\\{item.name}" {flags}'

                staged.append((item.name, cmd))

        if staged:
            self.log(f"[OK] {len(staged)} application(s) hors-ligne intégrée(s) dans Windows\\Setup\\Apps\\.")
        return staged

    def generate_apps_install_script(
        self,
        image_mount_dir: Path | str,
        staged_commands: List[str]
    ) -> Optional[Path]:
        """
        Génère un script batch Windows\\Setup\\Scripts\\InstallApps.cmd orchestrant
        l'installation ordonnée et silencieuse de toutes les applications packagées.
        """
        if not staged_commands:
            return None

        mount_path = Path(image_mount_dir).resolve()
        scripts_dir = mount_path / "Windows" / "Setup" / "Scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        script_file = scripts_dir / "InstallApps.cmd"

        lines = [
            "@echo off",
            ":: ===================================================================",
            ":: OSBuilder-Win - Déploiement silencieux des applications hors-ligne",
            ":: ===================================================================",
            "echo [OSBuilder-Win] Installation des applications integrees...",
            ""
        ]

        for cmd in staged_commands:
            lines.append(f"echo Installation : {cmd}")
            lines.append(cmd)
            lines.append("if %errorlevel% neq 0 echo [ATTENTION] Code retour : %errorlevel%")
            lines.append("")

        lines.append("echo [OK] Toutes les applications ont ete installees.")
        lines.append("exit /b 0")

        with open(script_file, "w", encoding="utf-8") as f:
            f.write("\r\n".join(lines))

        self.log(f"[APPS HORS-LIGNE] Script d'orchestration généré : {script_file}")
        return script_file
