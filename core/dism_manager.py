"""
Gestionnaire d'opérations DISM (Deployment Image Servicing and Management).
Assure le montage, le servicing (pilotes, paquets, AppX, fonctionnalités)
et l'optimisation des images WIM/ESD de Windows.
"""

import ctypes
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Optional


class DismError(Exception):
    pass


class DismManager:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log = log_callback or (lambda msg: None)
        self.dism_exe = self._find_dism()

    @staticmethod
    def is_admin() -> bool:
        """Vérifie si le script tourne avec les privilèges Administrateur."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def _find_dism(self) -> str:
        dism = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "Dism.exe")
        if os.path.exists(dism):
            return dism
        return "dism.exe"

    def _run_dism(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Exécute une commande DISM avec capture des sorties."""
        cmd = [self.dism_exe] + args
        self.log(f"[DISM] Exécution : {' '.join(cmd)}")
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if check and res.returncode != 0:
            err_msg = f"Échec DISM (code {res.returncode}):\n{res.stdout}\n{res.stderr}"
            self.log(f"[DISM ERREUR] {err_msg}")
            raise DismError(err_msg)
        return res

    def _find_wimlib(self) -> Optional[str]:
        project_bin = Path(__file__).resolve().parent.parent / "bin" / "wimlib-imagex.exe"
        if project_bin.exists():
            return str(project_bin)
        which_bin = shutil.which("wimlib-imagex")
        if which_bin:
            return which_bin
        return None

    def _run_wimlib(self, args: List[str]) -> subprocess.CompletedProcess:
        """Exécute une commande wimlib-imagex avec capture des sorties."""
        wimlib_bin = self._find_wimlib()
        if not wimlib_bin:
            raise FileNotFoundError("wimlib-imagex.exe introuvable.")
        cmd = [wimlib_bin] + args
        self.log(f"[WIMLIB] Exécution : {' '.join(cmd)}")
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

    def cleanup_mountpoints(self) -> bool:
        """Nettoie les points de montage orphelins (DISM /Cleanup-Wim)."""
        self.log("Nettoyage préventif des points de montage DISM...")
        res = self._run_dism(["/Cleanup-Wim"], check=False)
        return res.returncode == 0

    def get_image_info(self, wim_path: Path | str) -> List[Dict[str, str]]:
        """Récupère la liste des éditions / index disponibles dans le fichier WIM ou ESD."""
        path_str = str(Path(wim_path).resolve())
        res = self._run_dism(["/Get-WimInfo", f"/WimFile:{path_str}"])
        
        images = []
        current_img = {}
        
        for line in res.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            
            # Format: Index : 1
            if line.startswith("Index :") or line.startswith("Index:"):
                if current_img:
                    images.append(current_img)
                idx_val = line.split(":", 1)[1].strip()
                current_img = {"index": idx_val}
            elif ":" in line and current_img:
                key, val = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                current_img[key] = val.strip()
                
        if current_img:
            images.append(current_img)
            
        return images

    def convert_esd_to_wim(self, esd_path: Path | str, dest_wim_path: Path | str, index: int = 1) -> bool:
        """Convertit une image ESD compressée en WIM modifiable (via wimlib si présent, sinon DISM)."""
        esd = str(Path(esd_path).resolve())
        wim = str(Path(dest_wim_path).resolve())
        self.log(f"Conversion de {esd} (Index {index}) vers {wim}...")

        # 1. Utilisation prioritaire de wimlib-imagex si disponible (multi-threadé, beaucoup plus rapide)
        project_bin = Path(__file__).resolve().parent.parent / "bin" / "wimlib-imagex.exe"
        if project_bin.exists():
            cmd = [str(project_bin), "export", esd, str(index), wim, "--compress=maximum"]
            self.log(f"[WIMLIB] Export rapide ESD vers WIM : {' '.join(cmd)}")
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if res.returncode == 0:
                self.log("[OK] Image convertie avec succès via wimlib-imagex.")
                return True
            else:
                self.log(f"[ATTENTION] wimlib a échoué ({res.stderr.strip()}), basculement sur DISM...")

        # 2. Repli natif sur DISM standard
        args = [
            "/Export-Image",
            f"/SourceImageFile:{esd}",
            f"/SourceIndex:{index}",
            f"/DestinationImageFile:{wim}",
            "/Compress:max",
            "/CheckIntegrity"
        ]
        res = self._run_dism(args)
        return res.returncode == 0

    def mount_image(self, wim_path: Path | str, mount_dir: Path | str, index: int = 1, read_only: bool = False) -> bool:
        """Monte un index spécifique d'une image WIM dans un répertoire."""
        wim = str(Path(wim_path).resolve())
        mount = str(Path(mount_dir).resolve())
        os.makedirs(mount, exist_ok=True)
        
        self.log(f"Montage de {wim} (Index {index}) dans {mount}...")
        args = [
            "/Mount-Wim",
            f"/WimFile:{wim}",
            f"/Index:{index}",
            f"/MountDir:{mount}"
        ]
        if read_only:
            args.append("/ReadOnly")
            
        res = self._run_dism(args)
        return res.returncode == 0

    def unmount_image(self, mount_dir: Path | str, commit: bool = True) -> bool:
        """Démonte l'image en validant ou en annulant les modifications."""
        mount = str(Path(mount_dir).resolve())
        action = "/Commit" if commit else "/Discard"
        self.log(f"Démontage de {mount} ({action})...")
        
        args = [
            "/Unmount-Wim",
            f"/MountDir:{mount}",
            action
        ]
        res = self._run_dism(args)
        return res.returncode == 0

    def add_drivers(self, mount_dir: Path | str, driver_dir: Path | str, recurse: bool = True, force_unsigned: bool = False) -> bool:
        """Injecte des pilotes (.INF) dans l'image montée."""
        mount = str(Path(mount_dir).resolve())
        drv = str(Path(driver_dir).resolve())
        
        if not os.path.exists(drv):
            self.log(f"Dossier de pilotes introuvable : {drv}")
            return False
            
        self.log(f"Injection des pilotes depuis {drv}...")
        args = [
            f"/Image:{mount}",
            f"/Add-Driver",
            f"/Driver:{drv}"
        ]
        if recurse:
            args.append("/Recurse")
        if force_unsigned:
            args.append("/ForceUnsigned")
            
        res = self._run_dism(args, check=False)
        return res.returncode == 0

    def inject_drivers_to_winre(
        self,
        install_mount_dir: Path | str,
        driver_dirs: List[Path | str],
        scratch_dir: Optional[Path | str] = None,
        force_unsigned: bool = True
    ) -> bool:
        """
        Injecte les pilotes critiques (NVMe, RAID, stockage, réseau) dans l'environnement
        de récupération Windows (Winre.wim logé dans Windows\\System32\\Recovery\\Winre.wim).
        Permet d'éviter les boucles de boot et garantit l'accès aux disques lors d'une réparation.
        """
        install_mount = Path(install_mount_dir).resolve()
        winre_path = install_mount / "Windows" / "System32" / "Recovery" / "Winre.wim"

        if not winre_path.exists():
            self.log("[WINRE] Winre.wim introuvable dans l'image (peut être absent sur certaines éditions).")
            return False

        valid_drivers = [str(Path(d).resolve()) for d in driver_dirs if os.path.exists(str(d))]
        if not valid_drivers:
            self.log("[WINRE] Aucun dossier de pilotes valide fourni pour WinRE.")
            return False

        # Lever temporairement les attributs système/lecture seule
        try:
            os.chmod(winre_path, 0o777)
            subprocess.run(["attrib", "-s", "-h", "-r", str(winre_path)], capture_output=True)
        except Exception:
            pass

        base_scratch = Path(scratch_dir).resolve() if scratch_dir else install_mount.parent
        winre_mount_dir = base_scratch / "winre_mount"
        winre_mount_dir.mkdir(parents=True, exist_ok=True)

        self.log(f"[WINRE] Montage de l'environnement de récupération WinRE : {winre_path}...")
        mount_res = self._run_dism([
            "/Mount-Wim",
            f"/WimFile:{str(winre_path)}",
            "/Index:1",
            f"/MountDir:{str(winre_mount_dir)}"
        ], check=False)

        if mount_res.returncode != 0:
            self.log(f"[WINRE ATTENTION] Impossible de monter Winre.wim (code {mount_res.returncode}).")
            return False

        success = True
        try:
            for drv in valid_drivers:
                self.log(f"[WINRE] Injection des pilotes depuis {drv}...")
                args = [f"/Image:{str(winre_mount_dir)}", "/Add-Driver", f"/Driver:{drv}", "/Recurse"]
                if force_unsigned:
                    args.append("/ForceUnsigned")
                res = self._run_dism(args, check=False)
                if res.returncode != 0:
                    self.log(f"[WINRE ATTENTION] Avertissement lors de l'injection dans WinRE pour {drv}")

            self.log("[WINRE] Démontage et enregistrement des modifications de Winre.wim...")
            unmount_res = self._run_dism([
                "/Unmount-Wim",
                f"/MountDir:{str(winre_mount_dir)}",
                "/Commit"
            ], check=False)
            if unmount_res.returncode == 0:
                self.log("[WINRE OK] Pilotes injectés avec succès dans l'environnement de récupération WinRE.")
                return True
            else:
                self.log(f"[WINRE ERREUR] Échec du démontage /Commit de Winre.wim (code {unmount_res.returncode}).")
                success = False
        except Exception as e:
            self.log(f"[WINRE ERREUR] Exception pendant l'injection WinRE : {e}")
            success = False
        finally:
            if not success:
                try:
                    self._run_dism(["/Unmount-Wim", f"/MountDir:{str(winre_mount_dir)}", "/Discard"], check=False)
                except Exception:
                    pass
            try:
                if winre_mount_dir.exists():
                    winre_mount_dir.rmdir()
            except Exception:
                pass

        return success

    def add_packages(self, mount_dir: Path | str, package_path: Path | str) -> bool:
        """Injecte des mises à jour ou packages (.CAB / .MSU)."""
        mount = str(Path(mount_dir).resolve())
        pkg = str(Path(package_path).resolve())
        
        if not os.path.exists(pkg):
            self.log(f"Chemin de package introuvable : {pkg}")
            return False
            
        self.log(f"Injection des packages depuis {pkg}...")
        args = [
            f"/Image:{mount}",
            f"/Add-Package",
            f"/PackagePath:{pkg}"
        ]
        res = self._run_dism(args, check=False)
        return res.returncode == 0

    def get_provisioned_appx_packages(self, mount_dir: Path | str) -> List[str]:
        """Liste les paquets UWP pré-provisionnés dans l'image."""
        mount = str(Path(mount_dir).resolve())
        res = self._run_dism([f"/Image:{mount}", "/Get-ProvisionedAppxPackages"], check=False)
        
        packages = []
        for line in res.stdout.splitlines():
            line = line.strip()
            if line.startswith("PackageName :") or line.startswith("PackageName:"):
                pkg_name = line.split(":", 1)[1].strip()
                packages.append(pkg_name)
        return packages

    def remove_appx_package(self, mount_dir: Path | str, package_name: str) -> bool:
        """Supprime un paquet UWP pré-provisionné."""
        mount = str(Path(mount_dir).resolve())
        self.log(f"Suppression du paquet AppX : {package_name}")
        args = [
            f"/Image:{mount}",
            f"/Remove-ProvisionedAppxPackage",
            f"/PackageName:{package_name}"
        ]
        res = self._run_dism(args, check=False)
        return res.returncode == 0

    def remove_appx_by_patterns(self, mount_dir: Path | str, patterns: List[str]) -> int:
        """Supprime tous les paquets AppX correspondant aux motifs spécifiés (ex: *Xbox*, *Bing*)."""
        all_pkgs = self.get_provisioned_appx_packages(mount_dir)
        removed_count = 0
        
        for pattern in patterns:
            # Convertir wildcard glob en regex
            regex_str = "^" + pattern.replace(".", "\\.").replace("*", ".*") + "$"
            regex = re.compile(regex_str, re.IGNORECASE)
            
            for pkg in all_pkgs:
                if regex.search(pkg):
                    if self.remove_appx_package(mount_dir, pkg):
                        removed_count += 1
                        
        self.log(f"Total des paquets AppX supprimés : {removed_count}")
        return removed_count

    def enable_feature(self, mount_dir: Path | str, feature_name: str) -> bool:
        """Active une fonctionnalité Windows optionnelle."""
        mount = str(Path(mount_dir).resolve())
        args = [
            f"/Image:{mount}",
            f"/Enable-Feature",
            f"/FeatureName:{feature_name}",
            "/All"
        ]
        res = self._run_dism(args, check=False)
        return res.returncode == 0

    def disable_feature(self, mount_dir: Path | str, feature_name: str) -> bool:
        """Désactive une fonctionnalité Windows optionnelle."""
        mount = str(Path(mount_dir).resolve())
        args = [
            f"/Image:{mount}",
            f"/Disable-Feature",
            f"/FeatureName:{feature_name}"
        ]
        res = self._run_dism(args, check=False)
        return res.returncode == 0

    def add_capability(self, mount_dir: Path | str, capability_name: str, source: Optional[str] = None) -> bool:
        """Ajoute une capacité Windows modulaire (DISM /Add-Capability, ex: OpenSSH.Client)."""
        mount = str(Path(mount_dir).resolve())
        self.log(f"Ajout de la capacité Windows : {capability_name}...")
        args = [
            f"/Image:{mount}",
            "/Add-Capability",
            f"/CapabilityName:{capability_name}"
        ]
        if source:
            args.append(f"/Source:{source}")
        res = self._run_dism(args, check=False)
        return res.returncode == 0

    def remove_capability(self, mount_dir: Path | str, capability_name: str) -> bool:
        """Supprime une capacité Windows modulaire (DISM /Remove-Capability)."""
        mount = str(Path(mount_dir).resolve())
        self.log(f"Suppression de la capacité Windows : {capability_name}...")
        args = [
            f"/Image:{mount}",
            "/Remove-Capability",
            f"/CapabilityName:{capability_name}"
        ]
        res = self._run_dism(args, check=False)
        return res.returncode == 0

    def get_capabilities(self, mount_dir: Path | str) -> List[Dict[str, str]]:
        """Récupère la liste des capacités modulaires présentes dans l'image (DISM /Get-Capabilities)."""
        mount = str(Path(mount_dir).resolve())
        res = self._run_dism([f"/Image:{mount}", "/Get-Capabilities"], check=False)
        capabilities = []
        current_cap = {}
        for line in res.stdout.splitlines():
            line = line.strip()
            if line.startswith("Capability Identity :") or line.startswith("Identité de la capacité :"):
                if current_cap:
                    capabilities.append(current_cap)
                    current_cap = {}
                current_cap["name"] = line.split(":", 1)[1].strip()
            elif line.startswith("State :") or line.startswith("État :"):
                current_cap["state"] = line.split(":", 1)[1].strip()
        if current_cap:
            capabilities.append(current_cap)
        return capabilities

    def optimize_image(self, mount_dir: Path | str) -> bool:
        """Nettoie et compresse les composants Windows (StartComponentCleanup / ResetBase)."""
        mount = str(Path(mount_dir).resolve())
        self.log("Optimisation et réduction de la taille des composants (ResetBase)...")
        args = [
            f"/Image:{mount}",
            "/Cleanup-Image",
            "/StartComponentCleanup",
            "/ResetBase"
        ]
        res = self._run_dism(args, check=False)
        return res.returncode == 0

    def split_image(self, wim_path: Path | str, swm_path: Path | str, file_size_mb: int = 3800) -> bool:
        """Découpe un fichier WIM en fichiers SWM via DISM /Split-Image."""
        wim = str(Path(wim_path).resolve())
        swm = str(Path(swm_path).resolve())
        self.log(f"Découpage DISM de {wim} vers {swm} (Taille max : {file_size_mb} Mo)...")
        args = [
            "/Split-Image",
            f"/ImageFile:{wim}",
            f"/SWMFile:{swm}",
            f"/FileSize:{file_size_mb}"
        ]
        res = self._run_dism(args, check=False)
        return res.returncode == 0

    def enable_net35_offline(self, mount_dir: Path | str, sxs_source_dir: Path | str) -> bool:
        """Active .NET Framework 3.5 en mode hors-ligne à partir des paquets SxS du support d'installation."""
        mount = str(Path(mount_dir).resolve())
        sxs = str(Path(sxs_source_dir).resolve())
        if not os.path.exists(sxs):
            self.log(f"[INFO] Dossier SxS introuvable ({sxs}), activation de NetFx3 en mode standard...")
            return self.enable_feature(mount_dir, "NetFx3")

        self.log(f"Activation de .NET Framework 3.5 hors-ligne depuis {sxs}...")
        args = [
            f"/Image:{mount}",
            "/Enable-Feature",
            "/FeatureName:NetFx3",
            "/All",
            "/LimitAccess",
            f"/Source:{sxs}"
        ]
        res = self._run_dism(args, check=False)
        if res.returncode == 0:
            self.log("[OK] .NET Framework 3.5 pré-activé avec succès.")
            return True
        else:
            self.log(f"[ATTENTION] Échec activation .NET 3.5 : {res.stderr}")
            return False

    def enable_directplay(self, mount_dir: Path | str) -> bool:
        """Active DirectPlay pour la compatibilité avec les jeux vidéo plus anciens."""
        self.log("Activation du composant DirectPlay (Jeux rétro)...")
        return self.enable_feature(mount_dir, "DirectPlay")

    def set_reserved_storage(self, mount_dir: Path | str, state: bool = False) -> bool:
        """
        Active ou désactive l'espace de stockage réservé de Windows 10/11 (~7 Go).
        Désactivé par défaut pour libérer immédiatement de la place sur le disque système.
        """
        mount = str(Path(mount_dir).resolve())
        state_str = "Enabled" if state else "Disabled"
        self.log(f"Configuration du stockage réservé Windows Update ({state_str})...")
        args = [
            f"/Image:{mount}",
            "/Set-ReservedStorageState",
            f"/State:{state_str}"
        ]
        res = self._run_dism(args, check=False)
        if res.returncode == 0:
            self.log(f"[OK] Stockage réservé Windows Update configuré avec succès : {state_str}.")
            return True
        else:
            self.log(f"[INFO] Set-ReservedStorageState non supporté par cette édition/version (ignoré).")
            return False

    def export_single_image(
        self,
        src_image: Path | str,
        dest_image: Path | str,
        index: int = 1,
        compression: str = "maximum"
    ) -> bool:
        """
        Exporte un index WIM unique vers un nouveau fichier WIM/ESD pour alléger l'ISO
        de 40% en éliminant les éditions superflues.
        Supporte compression 'fast', 'maximum' (LZX) et 'recovery' (LZMS / ESD compact).
        """
        src = str(Path(src_image).resolve())
        dest = str(Path(dest_image).resolve())
        self.log(f"Export de l'index {index} vers {dest} (Compression : {compression})...")

        # 1. Utilisation prioritaire de wimlib-imagex
        if self._find_wimlib():
            wimlib_comp = "--compress=maximum"
            if compression.lower() in ("recovery", "esd"):
                wimlib_comp = "--compress=recovery"
            elif compression.lower() == "fast":
                wimlib_comp = "--compress=fast"

            cmd = ["export", src, str(index), dest, wimlib_comp]
            try:
                res = self._run_wimlib(cmd)
                if res.returncode == 0:
                    self.log("[OK] Image mono-édition exportée avec succès via wimlib-imagex.")
                    return True
                else:
                    self.log(f"[ATTENTION] wimlib a échoué ({res.stderr.strip()}), repli sur DISM...")
            except Exception as e:
                self.log(f"[ATTENTION] Exception wimlib ({e}), repli sur DISM...")

        # 2. Repli sur DISM standard
        dism_comp = "max"
        if compression.lower() in ("recovery", "esd"):
            dism_comp = "recovery"
        elif compression.lower() == "fast":
            dism_comp = "fast"

        args = [
            "/Export-Image",
            f"/SourceImageFile:{src}",
            f"/SourceIndex:{index}",
            f"/DestinationImageFile:{dest}",
            f"/Compress:{dism_comp}",
            "/CheckIntegrity"
        ]
        res = self._run_dism(args, check=False)
        return res.returncode == 0

    def cleanup_image_component_store(self, mount_dir: Path | str, reset_base: bool = True) -> bool:
        """
        Nettoie le magasin de composants (WinSxS) de l'image montée.
        L'option /ResetBase supprime les versions obsolètes de fichiers de mise à jour,
        permettant un allègement majeur (1 à 3 Go) de install.wim.
        """
        mount = str(Path(mount_dir).resolve())
        self.log(f"[OPTIMISATION] Nettoyage du magasin de composants WinSxS (ResetBase={reset_base})...")
        
        args = ["/Image:" + mount, "/Cleanup-Image", "/StartComponentCleanup"]
        if reset_base:
            args.append("/ResetBase")

        res = self._run_dism(args, check=False)
        if res.returncode == 0:
            self.log("[OK] Magasin de composants WinSxS nettoyé et compressé avec succès.")
            return True
        else:
            if reset_base:
                self.log("[AVERTISSEMENT] Échec avec /ResetBase, tentative sans /ResetBase...")
                res_fallback = self._run_dism(["/Image:" + mount, "/Cleanup-Image", "/StartComponentCleanup"], check=False)
                if res_fallback.returncode == 0:
                    self.log("[OK] Magasin WinSxS nettoyé (sans ResetBase).")
                    return True
            self.log(f"[AVERTISSEMENT] Impossible de nettoyer WinSxS (code {res.returncode}). Opération ignorée.")
            return False

    def force_cleanup_and_unmount(self, mount_dir: Path | str) -> bool:
        """Démontage d'urgence forcé d'une image WIM bloquée et nettoyage des points de montage orphelins."""
        mount = str(Path(mount_dir).resolve())
        self.log(f"[URGENCE] Tentative de démontage forcé et nettoyage DISM pour {mount}...")
        try:
            self._run_dism(["/Unmount-Wim", f"/MountDir:{mount}", "/Discard"], check=False)
        except Exception:
            pass
        res = self._run_dism(["/Cleanup-Wim"], check=False)
        return res.returncode == 0
