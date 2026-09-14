"""
Module de personnalisation OEM et branding pour OSBuilder-Win.
Permet d'injecter des informations constructeur (Fabricant, Modèle, Support, Logo)
dans 'À propos de ce PC' et de personnaliser le fond d'écran par défaut du système.
"""

import os
import shutil
from pathlib import Path
from typing import Callable, Optional
from pydantic import BaseModel, Field


class OemOptions(BaseModel):
    enabled: bool = False
    manufacturer: str = "LordMadTrix Custom Rig"
    model: str = "OSBuilder-Win Gaming Edition"
    support_hours: str = "24/7"
    support_phone: str = ""
    support_url: str = "https://github.com/LordMadTrix"
    logo_path: Optional[str] = None       # Chemin vers un fichier BMP (120x120 pixels)
    wallpaper_path: Optional[str] = None  # Chemin vers un fichier JPG/PNG (fond d'écran par défaut)


class OemManager:
    """Gestionnaire d'injection des informations et assets OEM dans l'image Windows hors-ligne."""

    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log_callback = log_callback

    def log(self, message: str) -> None:
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def apply_oem_branding(
        self,
        mount_dir: Path | str,
        reg_set_value_fn: Callable[[str, str, str, str, any], bool],
        oem_opts: OemOptions
    ) -> bool:
        """Applique les métadonnées OEM dans la ruche SOFTWARE et copie les assets graphiques."""
        if not oem_opts.enabled:
            return False

        self.log("Application de la personnalisation OEM (Branding constructeur)...")
        mount = Path(mount_dir).resolve()
        oem_key = r"Microsoft\Windows\CurrentVersion\OEMInformation"

        # 1. Inscription dans le Registre
        reg_set_value_fn("SOFTWARE", oem_key, "Manufacturer", "REG_SZ", oem_opts.manufacturer)
        reg_set_value_fn("SOFTWARE", oem_key, "Model", "REG_SZ", oem_opts.model)
        reg_set_value_fn("SOFTWARE", oem_key, "SupportHours", "REG_SZ", oem_opts.support_hours)
        if oem_opts.support_phone:
            reg_set_value_fn("SOFTWARE", oem_key, "SupportPhone", "REG_SZ", oem_opts.support_phone)
        if oem_opts.support_url:
            reg_set_value_fn("SOFTWARE", oem_key, "SupportURL", "REG_SZ", oem_opts.support_url)

        # 2. Copie du Logo OEM si spécifié
        if oem_opts.logo_path and os.path.exists(oem_opts.logo_path):
            system32 = mount / "Windows" / "System32"
            system32.mkdir(parents=True, exist_ok=True)
            target_logo = system32 / "oemlogo.bmp"
            try:
                shutil.copy2(oem_opts.logo_path, target_logo)
                reg_set_value_fn("SOFTWARE", oem_key, "Logo", "REG_SZ", r"C:\Windows\System32\oemlogo.bmp")
                self.log(f"[OEM] Logo constructeur copié : {target_logo}")
            except Exception as e:
                self.log(f"[ATTENTION OEM] Échec de la copie du logo : {e}")

        # 3. Remplacement du Fond d'écran par défaut (img0.jpg)
        if oem_opts.wallpaper_path and os.path.exists(oem_opts.wallpaper_path):
            wallpaper_dir = mount / "Windows" / "Web" / "Wallpaper" / "Windows"
            wallpaper_dir.mkdir(parents=True, exist_ok=True)
            target_wall = wallpaper_dir / "img0.jpg"
            try:
                shutil.copy2(oem_opts.wallpaper_path, target_wall)
                self.log(f"[OEM] Fond d'écran par défaut personnalisé : {target_wall}")
            except Exception as e:
                self.log(f"[ATTENTION OEM] Échec de la copie du fond d'écran : {e}")

        self.log(f"[OK] Branding OEM appliqué : {oem_opts.manufacturer} - {oem_opts.model}")
        return True
