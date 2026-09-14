"""
Module de déploiement d'images ISO Windows sur clé USB bootable (UEFI / BIOS).
Prend en charge la détection sécurisée des disques USB, le formatage FAT32
et le découpage automatique à la volée des WIM > 4 Go en fichiers .swm.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class UsbCreatorError(Exception):
    pass


class UsbCreator:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log = log_callback or (lambda msg: None)
        self.wimlib_exe = Path(__file__).resolve().parent.parent / "bin" / "wimlib-imagex.exe"

    def list_usb_drives(self) -> List[Dict[str, Any]]:
        """
        Détecte et liste de manière sécurisée les disques et volumes USB connectés.
        Retourne une liste de dictionnaires avec numéro de disque, nom, lettre de lecteur et taille.
        """
        ps_cmd = """
        $disks = Get-Disk | Where-Object BusType -eq 'USB'
        $result = @()
        foreach ($d in $disks) {
            $parts = Get-Partition -DiskNumber $d.Number -ErrorAction SilentlyContinue | Where-Object DriveLetter
            $letters = ($parts.DriveLetter | ForEach-Object { "$($_):" }) -join ', '
            $sizeGb = [math]::Round($d.Size / 1GB, 2)
            $result += [PSCustomObject]@{
                DiskNumber = $d.Number
                Name = $d.FriendlyName
                SizeGB = $sizeGb
                DriveLetters = $letters
                PrimaryLetter = if ($parts.Count -gt 0) { "$($parts[0].DriveLetter):" } else { "" }
            }
        }
        $result | ConvertTo-Json -Compress
        """
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True,
            text=True
        )
        if res.returncode != 0 or not res.stdout.strip():
            return []

        try:
            data = json.loads(res.stdout.strip())
            if isinstance(data, dict):
                data = [data]
            return data
        except Exception:
            return []

    def format_usb_drive(self, drive_letter: str, label: str = "WIN_SETUP") -> bool:
        """Formate le lecteur USB spécifié en FAT32 pour assurer le boot UEFI universel."""
        drive = drive_letter.strip().rstrip("\\")
        if not drive.endswith(":"):
            drive += ":"

        self.log(f"Formatage rapide du volume USB {drive} en FAT32 (Label: {label})...")
        ps_format = f"""
        Format-Volume -DriveLetter '{drive[0]}' -FileSystem FAT32 -NewFileSystemLabel '{label}' -Force -Confirm:$false | Out-Null
        """
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_format],
            capture_output=True,
            text=True
        )
        return res.returncode == 0

    def deploy_iso_to_usb(self, iso_path: Path | str, target_drive: str, progress_callback: Optional[Callable[[int, str], None]] = None) -> bool:
        """
        Monte l'image ISO source, copie son contenu sur la clé USB cible,
        découpe le fichier install.wim en fichiers .swm si nécessaire (> 4 Go en FAT32),
        et applique le secteur de boot bootsect.
        """
        iso = Path(iso_path).resolve()
        drive = target_drive.strip().rstrip("\\")
        if not drive.endswith(":"):
            drive += ":"

        if not iso.exists():
            raise FileNotFoundError(f"L'ISO source spécifiée n'existe pas : {iso}")

        target_root = Path(drive + "\\")
        if not target_root.exists():
            raise FileNotFoundError(f"Le lecteur cible {drive} est introuvable ou déconnecté.")

        # 1. Montage de l'ISO en lecture seule
        self.log(f"Montage de l'image ISO {iso.name}...")
        ps_mount = f"""
        $mount = Mount-DiskImage -ImagePath '{iso}' -StorageType ISO -Access ReadOnly -PassThru
        $vol = $mount | Get-Volume
        if ($vol.DriveLetter) {{
            Write-Output ($vol.DriveLetter + ':')
        }} else {{
            (Get-DiskImage -ImagePath '{iso}' | Get-Volume).DriveLetter + ':'
        }}
        """
        res_mount = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_mount],
            capture_output=True,
            text=True
        )
        iso_letter = res_mount.stdout.strip()
        if not iso_letter or not iso_letter.endswith(":"):
            raise UsbCreatorError("Impossible de monter l'image ISO.")

        iso_root = Path(iso_letter + "\\")

        try:
            # 2. Copie de tous les fichiers sauf install.wim s'il est > 4 Go
            self.log(f"Copie des fichiers de démarrage et d'installation vers {drive}...")
            total_items = list(iso_root.iterdir())
            total_count = len(total_items)

            for idx, item in enumerate(total_items, start=1):
                pct = int((idx / max(total_count, 1)) * 60)
                if progress_callback:
                    progress_callback(pct, f"Copie de {item.name}...")

                dst_item = target_root / item.name
                if item.is_dir():
                    if item.name.lower() == "sources":
                        # Traitement spécial pour le dossier sources (gestion de install.wim > 4 Go)
                        self._copy_sources_dir(item, dst_item)
                    else:
                        shutil.copytree(item, dst_item, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dst_item)

            # 3. Application du secteur de boot via bootsect si présent
            bootsect_exe = target_root / "boot" / "bootsect.exe"
            if bootsect_exe.exists():
                self.log(f"Mise à jour du secteur de boot sur {drive} (bootsect /nt60)...")
                cmd_boot = [str(bootsect_exe), "/nt60", drive, "/force"]
                subprocess.run(cmd_boot, capture_output=True)

            if progress_callback:
                progress_callback(100, "Clé USB bootable prête avec succès !")
            self.log(f"[SUCCÈS] La clé USB {drive} est prête et bootable en UEFI/BIOS.")
            return True

        finally:
            # Toujours démonter l'image ISO
            ps_dismount = f"Dismount-DiskImage -ImagePath '{iso}' | Out-Null"
            subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_dismount], capture_output=True)

    def _copy_sources_dir(self, src_sources: Path, dst_sources: Path) -> None:
        """Copie le répertoire sources en découpant install.wim si > 3800 Mo."""
        dst_sources.mkdir(parents=True, exist_ok=True)

        for sub in src_sources.iterdir():
            target_sub = dst_sources / sub.name
            if sub.is_file() and sub.name.lower() == "install.wim":
                size_mb = sub.stat().st_size / (1024 * 1024)
                if size_mb > 3800:
                    self.log(f"install.wim dépasse 3,8 Go ({size_mb:.1f} Mo). Découpage SWM direct sur la clé USB...")
                    swm_target = dst_sources / "install.swm"
                    # Utilisation prioritaire de wimlib si disponible
                    if self.wimlib_exe.exists():
                        cmd = [str(self.wimlib_exe), "split", str(sub), str(swm_target), "3800"]
                        res = subprocess.run(cmd, capture_output=True, text=True)
                        if res.returncode == 0:
                            self.log("[OK] Découpage SWM wimlib effectué avec succès sur la clé USB.")
                            continue
                    # Repli DISM
                    cmd_dism = [
                        "dism.exe", "/Split-Image",
                        f"/ImageFile:{str(sub)}",
                        f"/SWMFile:{str(swm_target)}",
                        "/FileSize:3800"
                    ]
                    subprocess.run(cmd_dism, capture_output=True)
                    continue

            if sub.is_dir():
                shutil.copytree(sub, target_sub, dirs_exist_ok=True)
            else:
                shutil.copy2(sub, target_sub)
