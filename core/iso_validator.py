"""
Module de validation et d'audit d'intégrité pour les images ISO Windows.
Vérifie la conformité des structures de démarrage BIOS / UEFI, l'intégrité de boot.wim
et des fichiers d'installation install.wim/esd/swm.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ValidationResult:
    is_valid: bool = True
    has_bios_boot: bool = False
    has_uefi_boot: bool = False
    has_boot_wim: bool = False
    has_install_image: bool = False
    install_image_format: str = "Inconnu"
    missing_files: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    total_size_mb: float = 0.0


class IsoValidator:
    """Validateur d'intégrité des supports d'installation Windows (dossier extrait)."""

    @staticmethod
    def validate_extracted_tree(root_dir: Path | str) -> ValidationResult:
        root = Path(root_dir).resolve()
        result = ValidationResult()

        if not root.exists() or not root.is_dir():
            result.is_valid = False
            result.missing_files.append(f"Répertoire racine inexistant: {root}")
            return result

        # 1. Vérification BIOS Bootloader
        bios_bootmgr = root / "bootmgr"
        bios_bcd = root / "boot" / "bcd"
        if bios_bootmgr.exists() and bios_bcd.exists():
            result.has_bios_boot = True
        else:
            if not bios_bootmgr.exists():
                result.missing_files.append("bootmgr (BIOS)")
            if not bios_bcd.exists():
                result.missing_files.append("boot/bcd (BIOS)")

        # 2. Vérification UEFI Bootloader
        uefi_boot = root / "efi" / "boot"
        uefi_loader_x64 = uefi_boot / "bootx64.efi"
        uefi_loader_ia32 = uefi_boot / "bootia32.efi"
        uefi_loader_arm64 = uefi_boot / "bootaa64.efi"
        uefi_bcd = root / "efi" / "microsoft" / "boot" / "bcd"

        if (uefi_loader_x64.exists() or uefi_loader_ia32.exists() or uefi_loader_arm64.exists()) and uefi_bcd.exists():
            result.has_uefi_boot = True
        else:
            if not (uefi_loader_x64.exists() or uefi_loader_ia32.exists() or uefi_loader_arm64.exists()):
                result.warnings.append("Chargeur EFI absent (efi/boot/boot*.efi) - Le démarrage UEFI natif peut échouer.")
            if not uefi_bcd.exists():
                result.warnings.append("BCD EFI absent (efi/microsoft/boot/bcd).")

        # 3. Vérification de boot.wim
        boot_wim = root / "sources" / "boot.wim"
        if boot_wim.exists() and boot_wim.stat().st_size > 10 * 1024 * 1024:
            result.has_boot_wim = True
        else:
            result.missing_files.append("sources/boot.wim")

        # 4. Vérification de install.wim / install.esd / install*.swm
        sources_dir = root / "sources"
        install_wim = sources_dir / "install.wim"
        install_esd = sources_dir / "install.esd"
        install_swm = list(sources_dir.glob("install*.swm"))

        if install_wim.exists():
            result.has_install_image = True
            result.install_image_format = "WIM"
        elif install_esd.exists():
            result.has_install_image = True
            result.install_image_format = "ESD"
        elif len(install_swm) > 0:
            result.has_install_image = True
            result.install_image_format = f"SWM ({len(install_swm)} parties)"
        else:
            result.missing_files.append("sources/install.(wim|esd|swm)")

        # Calcul de la taille totale
        try:
            total_bytes = sum(f.stat().st_size for f in root.rglob("*") if f.is_file())
            result.total_size_mb = round(total_bytes / (1024 * 1024), 2)
        except Exception:
            result.total_size_mb = 0.0

        # Résultat global
        result.is_valid = (
            (result.has_bios_boot or result.has_uefi_boot)
            and result.has_boot_wim
            and result.has_install_image
            and len(result.missing_files) == 0
        )

        return result

    @staticmethod
    def compute_file_hashes(
        file_path: Path | str,
        algorithms: Optional[List[str]] = None,
        chunk_size: int = 1024 * 1024
    ) -> dict[str, str]:
        """
        Calcule les empreintes cryptographiques (SHA256, MD5, SHA1) d'un fichier volumineux (ISO/WIM)
        par lecture séquentielle par blocs pour une empreinte mémoire minimale (< 5 Mo de RAM).
        """
        import hashlib

        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Fichier introuvable pour le calcul de hash : {path}")

        if algorithms is None:
            algorithms = ["sha256", "md5"]

        hashers = {}
        for algo in algorithms:
            algo_lower = algo.lower()
            if hasattr(hashlib, algo_lower):
                hashers[algo_lower] = getattr(hashlib, algo_lower)()

        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                for h in hashers.values():
                    h.update(chunk)

        return {algo: h.hexdigest().lower() for algo, h in hashers.items()}

    @staticmethod
    def generate_checksum_file(
        file_path: Path | str,
        algorithm: str = "sha256"
    ) -> Path:
        """
        Génère un fichier de somme de contrôle standard (ex: MonImage.iso.sha256)
        conforme aux spécifications GNU sha256sum.
        """
        path = Path(file_path)
        hashes = IsoValidator.compute_file_hashes(path, algorithms=[algorithm])
        digest = hashes.get(algorithm.lower(), "")

        checksum_file = path.parent / f"{path.name}.{algorithm.lower()}"
        checksum_content = f"{digest} *{path.name}\n"
        checksum_file.write_text(checksum_content, encoding="utf-8")
        return checksum_file

    @staticmethod
    def verify_checksum(
        file_path: Path | str,
        expected_hash: str,
        algorithm: str = "sha256"
    ) -> bool:
        """Vérifie si le hash d'un fichier correspond exactement à la valeur attendue."""
        hashes = IsoValidator.compute_file_hashes(file_path, algorithms=[algorithm])
        computed = hashes.get(algorithm.lower(), "").lower()
        return computed == expected_hash.strip().lower()

