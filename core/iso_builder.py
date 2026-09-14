"""
Module de reconstruction d'images ISO Windows bootables.
Génère une ISO hybride dual-boot (UEFI x64 + Legacy BIOS MBR) via oscdimg.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional


class IsoBuilder:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log = log_callback or (lambda msg: None)
        self.oscdimg_path = self._find_oscdimg()

    def _find_oscdimg(self) -> Optional[str]:
        """Localise oscdimg.exe dans le projet, le PATH ou Windows ADK."""
        # 1. Dans le sous-dossier bin du projet
        project_bin = Path(__file__).resolve().parent.parent / "bin" / "oscdimg.exe"
        if project_bin.exists():
            return str(project_bin)

        # 2. Dans le PATH
        which_oscdimg = shutil.which("oscdimg.exe") or shutil.which("oscdimg")
        if which_oscdimg:
            return which_oscdimg

        # 3. Emplacements Windows ADK standards
        adk_paths = [
            r"C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg\oscdimg.exe",
            r"C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\x86\Oscdimg\oscdimg.exe",
            r"C:\Program Files (x86)\Windows Kits\8.1\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg\oscdimg.exe",
        ]
        for p in adk_paths:
            if os.path.exists(p):
                return p

        return None

    def build_iso(self, source_dir: Path | str, output_iso: Path | str, volume_label: str = "OSBUILDER_WIN") -> bool:
        """
        Reconstruit l'ISO d'installation Windows avec support dual-boot UEFI et BIOS.
        """
        src = Path(source_dir).resolve()
        out = Path(output_iso).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)

        if not self.oscdimg_path:
            err = ("oscdimg.exe est introuvable. Veuillez exécuter 'python tools/fetch_tools.py' "
                   "ou installer le Windows ADK (Deployment Tools).")
            self.log(f"[ERREUR] {err}")
            raise FileNotFoundError(err)

        # Vérification des chargeurs de démarrage (Bootloaders)
        bios_boot = src / "boot" / "etfsboot.com"
        uefi_boot = src / "efi" / "microsoft" / "boot" / "efisys.bin"

        self.log(f"Création de l'ISO bootable vers {out}...")

        # Construction des arguments oscdimg
        args = [
            self.oscdimg_path,
            "-m",          # Ignorer la taille max d'image CD
            "-o",          # Déduplication MD5 des fichiers identiques
            "-u2",         # Système de fichiers UDF uniquement
            "-udfver102",  # UDF version 1.02 pour compatibilité maximale
            f"-l{volume_label[:32]}",  # Label de volume (max 32 car.)
        ]

        if bios_boot.exists() and uefi_boot.exists():
            self.log("Configuration Dual-Boot détectée : BIOS MBR + UEFI x64.")
            boot_data = f"2#p0,e,b\"{bios_boot}\"#pEF,e,b\"{uefi_boot}\""
            args.append(f"-bootdata:{boot_data}")
        elif bios_boot.exists():
            self.log("Configuration BIOS MBR simple détectée.")
            args.extend(["-b" + str(bios_boot), "-p0", "-e"])
        elif uefi_boot.exists():
            self.log("Configuration UEFI simple détectée.")
            args.extend(["-b" + str(uefi_boot), "-pEF", "-e"])

        args.append(str(src))
        args.append(str(out))

        self.log(f"[OSCDIMG] Exécution : {' '.join(args)}")
        res = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if res.returncode != 0:
            self.log(f"[OSCDIMG ERREUR] Code {res.returncode} :\n{res.stdout}\n{res.stderr}")
            return False

        self.log(f"[SUCCÈS] ISO générée avec succès : {out} ({out.stat().st_size / (1024*1024):.2f} Mo)")
        return True
