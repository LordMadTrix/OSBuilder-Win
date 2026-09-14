"""
Module d'inspection rapide d'images ISO Windows.
Monte temporairement l'ISO en mémoire pour extraire la liste exacte
des éditions et des index (Home, Pro, Enterprise...) sans copier de fichiers.
"""

import json
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional


class IsoInspector:
    def __init__(self, wimlib_path: Optional[str] = None):
        if not wimlib_path:
            project_bin = Path(__file__).resolve().parent.parent / "bin" / "wimlib-imagex.exe"
            if project_bin.exists():
                wimlib_path = str(project_bin)
        self.wimlib_exe = wimlib_path

    def inspect_iso(self, iso_path: Path | str) -> List[Dict[str, str]]:
        """
        Monte l'image ISO en lecture seule via PowerShell, extrait les métadonnées
        des éditions disponibles dans install.wim / install.esd, puis démonte l'ISO.
        """
        iso = Path(iso_path).resolve()
        if not iso.exists():
            raise FileNotFoundError(f"L'ISO spécifiée n'existe pas : {iso}")

        # Script PowerShell pour monter l'ISO et retourner la lettre de lecteur
        ps_mount = f"""
        $mount = Mount-DiskImage -ImagePath '{iso}' -StorageType ISO -Access ReadOnly -PassThru
        $vol = $mount | Get-Volume
        if ($vol.DriveLetter) {{
            Write-Output ($vol.DriveLetter + ':')
        }} else {{
            # Si pas de lettre automatique
            (Get-DiskImage -ImagePath '{iso}' | Get-Volume).DriveLetter + ':'
        }}
        """

        res_mount = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_mount],
            capture_output=True,
            text=True
        )

        drive_letter = res_mount.stdout.strip()
        if not drive_letter or not drive_letter.endswith(":"):
            # Tentative de récupération via DISM si déjà extrait
            return []

        editions = []
        try:
            drive_path = Path(drive_letter + "\\")
            sources_dir = drive_path / "sources"

            target_img = None
            if (sources_dir / "install.wim").exists():
                target_img = sources_dir / "install.wim"
            elif (sources_dir / "install.esd").exists():
                target_img = sources_dir / "install.esd"

            if target_img:
                editions = self.inspect_wim_file(target_img)
        finally:
            # Toujours démonter l'ISO proprement
            ps_dismount = f"Dismount-DiskImage -ImagePath '{iso}' | Out-Null"
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_dismount],
                capture_output=True
            )

        return editions

    def inspect_wim_file(self, wim_path: Path | str) -> List[Dict[str, str]]:
        """Extrait les informations d'un fichier WIM ou ESD (via wimlib-imagex ou DISM)."""
        wim_str = str(Path(wim_path).resolve())

        # 1. Utilisation de wimlib avec sortie XML (ultra rapide et complet)
        if self.wimlib_exe and os.path.exists(self.wimlib_exe):
            cmd = [self.wimlib_exe, "info", wim_str, "--xml"]
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if res.returncode == 0 and "<WIM>" in res.stdout:
                return self._parse_wimlib_xml(res.stdout)

        # 2. Repli sur DISM /Get-WimInfo
        return self._parse_dism_info(wim_str)

    def _parse_wimlib_xml(self, xml_text: str) -> List[Dict[str, str]]:
        editions = []
        try:
            # Extraction du bloc XML valide
            start = xml_text.find("<WIM>")
            end = xml_text.rfind("</WIM>") + len("</WIM>")
            xml_clean = xml_text[start:end]
            
            root = ET.fromstring(xml_clean)
            for img in root.findall("IMAGE"):
                idx = img.get("INDEX", "1")
                name = img.findtext("NAME") or f"Édition {idx}"
                desc = img.findtext("DESCRIPTION") or ""
                
                arch = "x64"
                windows_elem = img.find("WINDOWS")
                build = ""
                edition_id = ""
                if windows_elem is not None:
                    edition_id = windows_elem.findtext("EDITIONID") or ""
                    build = windows_elem.findtext("VERSION/BUILD") or ""
                    arch_code = windows_elem.findtext("ARCH")
                    if arch_code == "9":
                        arch = "x64"
                    elif arch_code == "0":
                        arch = "x86"
                    elif arch_code == "12":
                        arch = "ARM64"

                # Taille décompressée en Go
                total_bytes = img.findtext("TOTALBYTES")
                size_gb = ""
                if total_bytes and total_bytes.isdigit():
                    size_gb = f"{int(total_bytes) / (1024**3):.2f} Go"

                editions.append({
                    "index": idx,
                    "name": name,
                    "description": desc,
                    "edition_id": edition_id,
                    "architecture": arch,
                    "build": build,
                    "size": size_gb,
                })
        except Exception:
            pass
        return editions

    def _parse_dism_info(self, wim_path: str) -> List[Dict[str, str]]:
        cmd = ["dism.exe", "/Get-WimInfo", f"/WimFile:{wim_path}"]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        editions = []
        current_img = {}
        for line in res.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("Index :") or line.startswith("Index:"):
                if current_img:
                    editions.append(current_img)
                idx_val = line.split(":", 1)[1].strip()
                current_img = {"index": idx_val}
            elif ":" in line and current_img:
                key, val = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                current_img[key] = val.strip()
        if current_img:
            editions.append(current_img)
            
        return editions
