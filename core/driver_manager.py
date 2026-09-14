"""
Module de gestion avancée des pilotes pour OSBuilder-Win.
Permet la capture automatisée des pilotes réseau (Wi-Fi/LAN) et stockage de la machine hôte
via pnputil / dism, l'inspection des fichiers .inf et l'injection dans les images WIM.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, List, Optional, Set


class DriverManager:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log_callback = log_callback

    def log(self, message: str) -> None:
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def scan_inf_drivers(self, folder_path: Path | str) -> List[Path]:
        """Scanne récursivement un dossier et retourne la liste des fichiers .inf valides."""
        root = Path(folder_path)
        if not root.exists() or not root.is_dir():
            return []
        
        inf_files = list(root.rglob("*.inf"))
        return inf_files

    def export_host_drivers(
        self,
        dest_dir: Path | str,
        filter_network_storage_only: bool = True
    ) -> List[Path]:
        """
        Exporte les pilotes installés sur la machine hôte vers un dossier cible.
        Utilise pnputil /export-driver pour extraire les fichiers .inf, .sys et .cat.
        Si filter_network_storage_only est True, conserve principalement les pilotes
        de cartes réseau (Wi-Fi, Ethernet, Bluetooth) et contrôleurs de stockage.
        """
        out_path = Path(dest_dir).resolve()
        out_path.mkdir(parents=True, exist_ok=True)

        self.log(f"Exportation des pilotes tiers de la machine hôte vers {out_path}...")
        
        # Commande standard Windows : pnputil.exe /export-driver * <Destination>
        pnputil_bin = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32" / "pnputil.exe"
        cmd = [str(pnputil_bin), "/export-driver", "*", str(out_path)]

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if res.returncode != 0:
                self.log(f"[ATTENTION] pnputil a retourné le code {res.returncode}: {res.stderr.strip()}")
            else:
                self.log("[OK] Exportation pnputil terminée avec succès.")
        except Exception as e:
            self.log(f"[ERREUR] Échec de l'exécution de pnputil: {e}")
            return []

        all_infs = self.scan_inf_drivers(out_path)
        if not filter_network_storage_only:
            self.log(f"Total des pilotes exportés : {len(all_infs)}")
            return all_infs

        # Filtrage des catégories réseau (Net, Netwtw, NetAdapter) et stockage (SCSIAdapter, HDC, NVMe)
        retained_infs: List[Path] = []
        network_keywords = {"net", "wifi", "wlan", "ethernet", "wireless", "gigabit", "realtek", "intel", "lan"}
        storage_keywords = {"nvme", "storage", "ahci", "raid", "vmd", "iastor", "scsi"}

        for inf in all_infs:
            try:
                content = inf.read_text(encoding="utf-8", errors="ignore").lower()
                is_retained = False
                for kw in network_keywords.union(storage_keywords):
                    if kw in content:
                        is_retained = True
                        break
                if is_retained:
                    retained_infs.append(inf)
                else:
                    parent = inf.parent
                    if parent != out_path and parent.is_dir():
                        shutil.rmtree(parent, ignore_errors=True)
            except Exception:
                retained_infs.append(inf)

        self.log(f"Pilotes critiques réseau/stockage conservés : {len(retained_infs)} (sur {len(all_infs)} exportés)")
        return retained_infs
