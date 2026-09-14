"""
Vérificateur et assistant d'installation des dépendances système pour OSBuilder-Win.
"""

import ctypes
import os
import shutil
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console()
except ImportError:
    console = None


def check_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def find_oscdimg() -> str | None:
    # 1. bin/
    bin_p = Path(__file__).resolve().parent.parent / "bin" / "oscdimg.exe"
    if bin_p.exists():
        return str(bin_p)
    # 2. PATH
    which_p = shutil.which("oscdimg.exe") or shutil.which("oscdimg")
    if which_p:
        return which_p
    # 3. ADK
    adk_paths = [
        r"C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg\oscdimg.exe",
        r"C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\x86\Oscdimg\oscdimg.exe",
        r"C:\Program Files (x86)\Windows Kits\8.1\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg\oscdimg.exe",
    ]
    for p in adk_paths:
        if os.path.exists(p):
            return p
    return None


def find_7z() -> str | None:
    which_p = shutil.which("7z.exe") or shutil.which("7za.exe")
    if which_p:
        return which_p
    common_paths = [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p
    return None


def find_wimlib() -> str | None:
    bin_p = Path(__file__).resolve().parent.parent / "bin" / "wimlib-imagex.exe"
    if bin_p.exists():
        return str(bin_p)
    which_p = shutil.which("wimlib-imagex.exe") or shutil.which("wimlib-imagex")
    if which_p:
        return which_p
    return None


def verify_all_tools() -> dict:
    dism_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "Dism.exe")
    dism_ok = os.path.exists(dism_path)
    seven_z = find_7z()
    oscdimg = find_oscdimg()
    wimlib = find_wimlib()
    is_admin = check_admin()

    results = {
        "admin": is_admin,
        "dism": dism_path if dism_ok else None,
        "wimlib": wimlib,
        "7zip": seven_z,
        "oscdimg": oscdimg,
    }
    return results


def print_status():
    res = verify_all_tools()
    
    if console:
        table = Table(title="[bold cyan]État de l'environnement OSBuilder-Win[/bold cyan]")
        table.add_column("Composant", style="bold white")
        table.add_column("Statut", justify="center")
        table.add_column("Emplacement / Détail", style="dim")

        # Admin
        if res["admin"]:
            table.add_row("Privilèges Administrateur", "[green]ACTIF[/green]", "Droits élevés détectés")
        else:
            table.add_row("Privilèges Administrateur", "[yellow]STANDARD[/yellow]", "Élévation requise lors du build")

        # DISM
        if res["dism"]:
            table.add_row("DISM (Moteur Système)", "[green]PRÉSENT[/green]", res["dism"])
        else:
            table.add_row("DISM (Moteur Système)", "[red]INTROUVABLE[/red]", "Requis (System32)")

        # Wimlib
        if res["wimlib"]:
            table.add_row("Wimlib (Moteur Haute Vitesse)", "[green]PRÉSENT[/green]", res["wimlib"])
        else:
            table.add_row("Wimlib (Moteur Haute Vitesse)", "[yellow]OPTIONNEL[/yellow]", "Accélérateur de compression")

        # 7-Zip
        if res["7zip"]:
            table.add_row("7-Zip (Extraction ISO)", "[green]PRÉSENT[/green]", res["7zip"])
        else:
            table.add_row("7-Zip (Extraction ISO)", "[yellow]OPTIONNEL[/yellow]", "Repli sur PowerShell Mount-DiskImage")

        # Oscdimg
        if res["oscdimg"]:
            table.add_row("Oscdimg (Création ISO)", "[green]PRÉSENT[/green]", res["oscdimg"])
        else:
            table.add_row("Oscdimg (Création ISO)", "[yellow]EN ATTENTE[/yellow]", "Requis pour l'ISO finale (Windows ADK)")

        console.print(table)
        
        if not res["oscdimg"]:
            console.print(Panel(
                "[yellow]Note :[/yellow] Pour générer l'ISO bootable finale, placez le binaire officiel [bold]oscdimg.exe[/bold] "
                "dans le sous-dossier [bold cyan]bin/[/bold cyan] ou installez les outils de déploiement du Windows ADK.",
                title="Recommandation ISO"
            ))
    else:
        print("--- Diagnostic Environnement OSBuilder-Win ---")
        for k, v in res.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    print_status()
