"""
Générateur de rapport d'audit et de build pour OSBuilder-Win.
Produit un résumé HTML et Markdown détaillé à la fin de chaque compilation ISO.
"""

from datetime import datetime
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional
from core.config import BuildProfile


class BuildReporter:
    def __init__(self, profile: BuildProfile, source_iso: Path | str, output_iso: Path | str):
        self.profile = profile
        self.source_iso = Path(source_iso)
        self.output_iso = Path(output_iso)
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None

    def calculate_output_hash(self) -> Dict[str, str]:
        """Calcule les hashs SHA-1 et SHA-256 de l'ISO finale générée."""
        if not self.output_iso.exists():
            return {"sha1": "N/A", "sha256": "N/A", "size_gb": 0.0}

        sha1 = hashlib.sha1()
        sha256 = hashlib.sha256()
        with open(self.output_iso, "rb") as f:
            while chunk := f.read(1024 * 1024 * 2):
                sha1.update(chunk)
                sha256.update(chunk)

        size_gb = self.output_iso.stat().st_size / (1024 ** 3)
        return {
            "sha1": sha1.hexdigest().upper(),
            "sha256": sha256.hexdigest().upper(),
            "size_gb": size_gb
        }

    def generate_markdown_report(self, dest_path: Optional[Path | str] = None) -> Path:
        """Génère un rapport au format Markdown."""
        self.end_time = datetime.now()
        duration = str(self.end_time - self.start_time).split(".")[0]
        hashes = self.calculate_output_hash()

        md_content = f"""# Rapport de Compilation OSBuilder-Win
*Généré automatiquement le {self.end_time.strftime('%d/%m/%Y à %H:%M:%S')}*

---

## 📌 Informations Générales
- **Profil appliqué :** {self.profile.name}
- **Système d'exploitation cible :** {self.profile.target_os.value.upper()} ({self.profile.architecture})
- **Index WIM sélectionné :** {self.profile.image_index}
- **Durée totale du build :** {duration}
- **Fichier source :** `{self.source_iso.name}`
- **Fichier généré :** `{self.output_iso.name}` ({hashes['size_gb']:.2f} Go)

## 🔐 Empreintes Cryptographiques de l'ISO
- **SHA-256 :** `{hashes['sha256']}`
- **SHA-1 :** `{hashes['sha1']}`

---

## ⚙️ Détail des Personnalisations Appliquées

### 1. Contournements Matériels & Licence
- **Bypass Windows 11 :** TPM 2.0: {'Oui' if self.profile.win11.bypass_tpm else 'Non'}, SecureBoot: {'Oui' if self.profile.win11.bypass_secureboot else 'Non'}, RAM: {'Oui' if self.profile.win11.bypass_ram else 'Non'}, CPU: {'Oui' if self.profile.win11.bypass_cpu else 'Non'}
- **Bypass Compte Microsoft (BypassNRO) :** {'Oui (Compte Local ' + self.profile.unattended.admin_username + ')' if self.profile.unattended.bypass_nro else 'Non'}
- **Clé générique d'installation :** `{self.profile.unattended.product_key or 'Non définie'}`

### 2. Ergonomie & Explorateur
- **Mode Sombre par défaut :** {'Activé' if self.profile.explorer.dark_mode else 'Désactivé'}
- **Afficher les extensions de fichiers :** {'Oui' if self.profile.explorer.show_file_extensions else 'Non'}
- **Ouvrir sur "Ce PC" :** {'Oui' if self.profile.explorer.open_to_this_pc else 'Non'}
- **Menu contextuel classique Win10/Win7 :** {'Restauré' if self.profile.win11.classic_context_menu else 'Standard'}

### 3. Composants & Performances
- **Pré-activation .NET Framework 3.5 :** {'Oui (Hors-ligne)' if self.profile.system_features.enable_net35 else 'Non'}
- **DirectPlay (Rétrogaming) :** {'Oui' if self.profile.system_features.enable_directplay else 'Non'}
- **Optimisation SSD (SysMain désactivé) :** {'Oui' if self.profile.services.disable_sysmain else 'Non'}
- **Télémétrie & DiagTrack neutralisés :** {'Oui' if self.profile.disable_telemetry else 'Non'}
- **Découpage FAT32 USB (.swm < 4 Go) :** {'Oui' if self.profile.split_wim_fat32 else 'Non'}

### 4. Logiciels Post-Installation
- **Runtimes Visual C++ All-In-One :** {'Inclus au 1er boot' if self.profile.post_install.install_vcredist else 'Non'}
- **Applications WinGet pré-configurées :** {', '.join(self.profile.post_install.winget_apps) if self.profile.post_install.winget_apps else 'Aucune'}

---
*Compilé avec succès par OSBuilder-Win - Écosystème LordMadTrix*
"""
        if not dest_path:
            dest_path = self.output_iso.parent / f"{self.output_iso.stem}_Rapport.md"
        dest = Path(dest_path)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(md_content)
        return dest
