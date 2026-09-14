"""
Module d'extraction d'images ISO Windows.
Utilise 7-Zip en priorité avec repli transparent sur PowerShell Mount-DiskImage.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional


class IsoExtractor:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log = log_callback or (lambda msg: None)
        self._7z_path = self._find_7z()

    def _find_7z(self) -> Optional[str]:
        """Recherche 7-Zip sur le système."""
        # 1. Dans le PATH
        which_7z = shutil.which("7z.exe") or shutil.which("7za.exe") or shutil.which("7z")
        if which_7z:
            return which_7z
        
        # 2. Emplacements standards Windows
        common_paths = [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
            os.path.join(os.getcwd(), "bin", "7z.exe"),
        ]
        for p in common_paths:
            if os.path.exists(p):
                return p
        return None

    def extract(self, iso_path: Path | str, dest_dir: Path | str) -> bool:
        """Extrait l'ensemble des fichiers d'une ISO Windows vers un dossier cible."""
        iso_file = Path(iso_path).resolve()
        dest = Path(dest_dir).resolve()

        if not iso_file.exists():
            raise FileNotFoundError(f"L'image ISO n'existe pas : {iso_file}")

        dest.mkdir(parents=True, exist_ok=True)

        if self._7z_path:
            self.log(f"Utilisation de 7-Zip ({self._7z_path}) pour extraire l'ISO...")
            return self._extract_with_7z(iso_file, dest)
        else:
            self.log("7-Zip non détecté, utilisation de PowerShell (Mount-DiskImage)...")
            return self._extract_with_powershell(iso_file, dest)

    def _extract_with_7z(self, iso_file: Path, dest: Path) -> bool:
        cmd = [
            self._7z_path,
            "x",
            str(iso_file),
            f"-o{dest}",
            "-y",
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            self.log(f"Erreur 7-Zip lors de l'extraction : {res.stderr}")
            return False
        return True

    def _extract_with_powershell(self, iso_file: Path, dest: Path) -> bool:
        ps_script = f"""
        $isoPath = '{iso_file}'
        $destPath = '{dest}'
        $mount = Mount-DiskImage -ImagePath $isoPath -PassThru
        $driveLetter = ($mount | Get-Volume).DriveLetter + ':'
        try {{
            Copy-Item -Path "$driveLetter\\*" -Destination $destPath -Recurse -Force
        }} finally {{
            Dismount-DiskImage -ImagePath $isoPath | Out-Null
        }}
        """
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            self.log(f"Erreur PowerShell lors du montage/copie de l'ISO : {res.stderr}")
            return False
        return True

    @staticmethod
    def inspect_extracted_sources(extracted_dir: Path | str) -> dict:
        """Inspecte le dossier sources pour localiser install.wim / install.esd et boot.wim."""
        sources = Path(extracted_dir) / "sources"
        if not sources.exists():
            raise FileNotFoundError(f"Dossier sources introuvable dans : {extracted_dir}")

        wim_path = sources / "install.wim"
        esd_path = sources / "install.esd"
        boot_wim = sources / "boot.wim"

        image_path = None
        image_type = None

        if wim_path.exists():
            image_path = wim_path
            image_type = "WIM"
        elif esd_path.exists():
            image_path = esd_path
            image_type = "ESD"

        return {
            "sources_dir": str(sources),
            "boot_wim": str(boot_wim) if boot_wim.exists() else None,
            "install_image": str(image_path) if image_path else None,
            "image_type": image_type,
        }
