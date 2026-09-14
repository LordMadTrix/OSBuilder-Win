"""
Module d'ordonnancement et d'injection des mises à jour hors-ligne (SSU / LCU / CAB / MSU) pour OSBuilder-Win.
Assure le tri indispensable des paquets (Servicing Stack Update avant Cumulative Update)
pour éviter les erreurs d'injection DISM (0x800f0823).
"""

import os
from pathlib import Path
from typing import Callable, List, Optional


class UpdateManager:
    """Gestionnaire de paquets de mises à jour Windows (.msu, .cab)."""

    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log_callback = log_callback

    def log(self, message: str) -> None:
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def scan_updates(self, folder_path: Path | str, target_arch: str = "x64") -> List[Path]:
        """
        Scanne un dossier à la recherche de fichiers .msu et .cab.
        Filtre les architectures discordantes et trie intelligemment les paquets
        (SSU prioritaire, puis LCU / KB par ordre alphabétique).
        """
        folder = Path(folder_path).resolve()
        if not folder.exists() or not folder.is_dir():
            return []

        all_pkgs: List[Path] = []
        for ext in ("*.msu", "*.cab"):
            all_pkgs.extend(folder.glob(ext))

        if not all_pkgs:
            return []

        # Filtrage par architecture
        valid_pkgs: List[Path] = []
        for pkg in all_pkgs:
            name_lower = pkg.name.lower()
            if target_arch.lower() == "x64":
                if "x86" in name_lower or "arm64" in name_lower:
                    self.log(f"[INFO] Paquet ignoré car incompatible x64 : {pkg.name}")
                    continue
            elif target_arch.lower() == "x86":
                if "x64" in name_lower or "arm64" in name_lower or "amd64" in name_lower:
                    continue
            elif target_arch.lower() == "arm64":
                if "x64" in name_lower or "x86" in name_lower:
                    continue
            valid_pkgs.append(pkg)

        # Tri intelligent : SSU (Servicing Stack Updates) d'abord, puis les autres
        def sort_key(p: Path) -> tuple[int, str]:
            lower = p.name.lower()
            # 0 si SSU, 1 sinon
            is_ssu = 0 if ("ssu" in lower or "servicing_stack" in lower) else 1
            return (is_ssu, lower)

        sorted_pkgs = sorted(valid_pkgs, key=sort_key)
        self.log(f"Détection de {len(sorted_pkgs)} paquets de mise à jour valides pour {target_arch.upper()}.")
        return sorted_pkgs
