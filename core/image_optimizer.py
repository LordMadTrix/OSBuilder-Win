"""
Module d'optimisation et de recompression des images Windows (WIM / ESD).
Permet de réduire considérablement la taille de l'image install.wim / install.esd
en éliminant les blocs orphelins après debloat et en appliquant une compression
haute densité (LZX / LZMS Recovery).
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional


class ImageOptimizer:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log = log_callback or (lambda msg: None)
        self.wimlib_exe = self._find_wimlib()
        self.dism_exe = self._find_dism()

    def _find_wimlib(self) -> Optional[str]:
        project_bin = Path(__file__).resolve().parent.parent / "bin" / "wimlib-imagex.exe"
        if project_bin.exists():
            return str(project_bin)
        which_bin = shutil.which("wimlib-imagex")
        if which_bin:
            return which_bin
        return None

    def _find_dism(self) -> str:
        dism = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "Dism.exe")
        if os.path.exists(dism):
            return dism
        return "dism.exe"

    def optimize_wim(self, wim_path: Path | str, compression: str = "maximum") -> bool:
        """
        Réduit la taille d'un fichier WIM en éliminant les fragments inutilisés
        (résidus de suppressions AppX, paquets et fichiers temporaires).
        """
        wim_file = Path(wim_path).resolve()
        if not wim_file.exists():
            self.log(f"[OPTIMISEUR] Fichier WIM introuvable : {wim_file}")
            return False

        init_size_mb = wim_file.stat().st_size / (1024 * 1024)
        self.log(f"[OPTIMISEUR] Optimisation et défragmentation de {wim_file.name} (Taille initiale : {init_size_mb:.1f} Mo)...")

        # 1. Utilisation de wimlib-imagex optimize si disponible
        if self.wimlib_exe:
            comp_flag = "--compress=maximum"
            if compression.lower() in ("recovery", "esd"):
                comp_flag = "--compress=recovery"
            elif compression.lower() == "fast":
                comp_flag = "--compress=fast"

            cmd = [self.wimlib_exe, "optimize", str(wim_file), comp_flag, "--check"]
            self.log(f"[OPTIMISEUR] Exécution de wimlib optimize : {' '.join(cmd)}")
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
                if res.returncode == 0:
                    final_size_mb = wim_file.stat().st_size / (1024 * 1024)
                    saved_mb = init_size_mb - final_size_mb
                    self.log(f"[OK] WIM optimisé avec succès via wimlib ! Nouvelle taille : {final_size_mb:.1f} Mo (Gain : {saved_mb:.1f} Mo).")
                    return True
                else:
                    self.log(f"[ATTENTION] wimlib optimize a retourné {res.returncode} : {res.stderr.strip()}")
            except Exception as e:
                self.log(f"[ATTENTION] Erreur wimlib optimize : {e}")

        # 2. Repli via DISM /Export-Image vers un fichier temporaire
        temp_wim = wim_file.parent / f"{wim_file.stem}_optimized{wim_file.suffix}"
        dism_comp = "recovery" if compression.lower() in ("recovery", "esd") else "max"
        
        args = [
            self.dism_exe,
            "/Export-Image",
            f"/SourceImageFile:{str(wim_file)}",
            "/SourceIndex:1",
            f"/DestinationImageFile:{str(temp_wim)}",
            f"/Compress:{dism_comp}",
            "/CheckIntegrity"
        ]
        self.log(f"[OPTIMISEUR] Repli sur DISM /Export-Image ({dism_comp})...")
        res = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res.returncode == 0 and temp_wim.exists():
            final_size_mb = temp_wim.stat().st_size / (1024 * 1024)
            saved_mb = init_size_mb - final_size_mb
            wim_file.unlink()
            temp_wim.rename(wim_file)
            self.log(f"[OK] WIM recompressé via DISM ! Nouvelle taille : {final_size_mb:.1f} Mo (Gain : {saved_mb:.1f} Mo).")
            return True
        else:
            if temp_wim.exists():
                temp_wim.unlink()
            self.log(f"[ATTENTION] Échec de l'optimisation DISM (code {res.returncode}). Le fichier original est conservé.")
            return False

    def convert_wim_to_esd(self, wim_path: Path | str, target_esd_path: Optional[Path | str] = None, index: int = 1) -> Optional[Path]:
        """
        Convertit un fichier WIM en ESD ultra-compressé (LZMS Recovery).
        Réduit la taille de l'image de 30 à 45% par rapport au format WIM standard.
        Retourne le chemin du fichier ESD généré.
        """
        wim_file = Path(wim_path).resolve()
        if not wim_file.exists():
            self.log(f"[ESD] Fichier WIM source introuvable : {wim_file}")
            return None

        out_esd = Path(target_esd_path).resolve() if target_esd_path else wim_file.parent / "install.esd"
        init_size_mb = wim_file.stat().st_size / (1024 * 1024)
        self.log(f"[ESD] Conversion de {wim_file.name} ({init_size_mb:.1f} Mo) vers ESD compact (LZMS)...")

        # Priorité wimlib-imagex
        if self.wimlib_exe:
            cmd = [self.wimlib_exe, "export", str(wim_file), str(index), str(out_esd), "--compress=recovery", "--check"]
            self.log(f"[ESD] Exécution wimlib export : {' '.join(cmd)}")
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
                if res.returncode == 0 and out_esd.exists():
                    final_size_mb = out_esd.stat().st_size / (1024 * 1024)
                    saved_mb = init_size_mb - final_size_mb
                    self.log(f"[OK] Image ESD générée avec succès ! Taille : {final_size_mb:.1f} Mo (Économie : {saved_mb:.1f} Mo / {(saved_mb/init_size_mb)*100:.1f}%).")
                    return out_esd
            except Exception as e:
                self.log(f"[ESD ATTENTION] Erreur wimlib : {e}")

        # Repli DISM
        args = [
            self.dism_exe,
            "/Export-Image",
            f"/SourceImageFile:{str(wim_file)}",
            f"/SourceIndex:{index}",
            f"/DestinationImageFile:{str(out_esd)}",
            "/Compress:recovery",
            "/CheckIntegrity"
        ]
        self.log(f"[ESD] Repli sur DISM /Export-Image /Compress:recovery...")
        res = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res.returncode == 0 and out_esd.exists():
            final_size_mb = out_esd.stat().st_size / (1024 * 1024)
            saved_mb = init_size_mb - final_size_mb
            self.log(f"[OK] Image ESD générée via DISM ! Taille : {final_size_mb:.1f} Mo (Gain : {saved_mb:.1f} Mo).")
            return out_esd

        self.log(f"[ESD ERREUR] Échec de la conversion ESD (code {res.returncode}).")
        return None
