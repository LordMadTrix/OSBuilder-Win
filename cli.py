#!/usr/bin/env python3
"""
OSBuilder-Win - Interface CLI Interactive & Pipeline de Build.
Architecture pour Windows 7, 10 et 11.
"""

import argparse
import sys
from pathlib import Path

# Forcer l'encodage UTF-8 pour le terminal Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

from core.config import load_profile_from_yaml, BuildProfile
from core.pipeline import BuildPipeline
from core.iso_inspector import IsoInspector
from tools.fetch_tools import verify_all_tools, print_status

console = Console()

BANNER = r"""[bold cyan]
   ____   _____ ____        _ _     _              __          ___       
  / __ \ / ____|  _ \      (_) |   | |             \ \        / (_)      
 | |  | | (___ | |_) |_   _ _| | __| | ___ _ __ ____\ \  /\  / / _ _ __  
 | |  | |\___ \|  _ <| | | | | |/ _` |/ _ \ '__|_____\ \/  \/ / | | '_ \ 
 | |__| |____) | |_) | |_| | | | (_| |  __/ |         \  /\  /  | | | | |
  \____/|_____/|____/ \__,_|_|_|\__,_|\___|_|          \/  \/   |_|_| |_|
[/bold cyan]
[bold magenta]⚡ ÉDITION SIGNATURE OFFICIELLE LORDMADTRIX • SUITE STUDIO v2.5 PRO ⚡[/bold magenta]
[dim white]Architecture industrielle de déploiement et d'optimisation Windows (7, 10, 11)[/dim white]
"""


def list_available_profiles() -> list[Path]:
    profiles_dir = Path(__file__).resolve().parent / "profiles"
    if not profiles_dir.exists():
        return []
    return list(profiles_dir.glob("*.yaml"))


def display_profiles():
    profiles = list_available_profiles()
    table = Table(title="[bold green]Profils de personnalisation disponibles[/bold green]")
    table.add_column("N°", justify="center", style="bold yellow")
    table.add_column("Fichier", style="cyan")
    table.add_column("OS Cible", justify="center", style="magenta")
    table.add_column("Nom du profil", style="white")
    table.add_column("Description", style="dim")

    loaded_profiles = []
    for idx, p in enumerate(profiles, start=1):
        try:
            prof = load_profile_from_yaml(p)
            loaded_profiles.append((p, prof))
            table.add_row(str(idx), p.name, prof.target_os.value.upper(), prof.name, prof.description)
        except Exception as e:
            table.add_row(str(idx), p.name, "ERR", f"Erreur de lecture : {e}", "")

    console.print(table)
    return loaded_profiles


def interactive_mode():
    console.print(BANNER)
    
    # 1. Vérification de l'environnement
    console.print("[bold yellow]Vérification des outils système...[/bold yellow]")
    tools = verify_all_tools()
    
    if not tools["admin"]:
        console.print(Panel(
            "[bold red]ATTENTION : Vous n'exécutez pas ce script en tant qu'Administrateur.[/bold red]\n"
            "DISM et la manipulation du registre hors-ligne nécessitent une élévation de privilèges.\n"
            "Relancez votre terminal avec 'Exécuter en tant qu'administrateur'.",
            title="Avertissement Privilèges",
            border_style="red"
        ))
        if not Confirm.ask("Voulez-vous tout de même continuer en mode restreint ?", default=False):
            sys.exit(1)

    # 2. Choix du profil
    profiles = display_profiles()
    if not profiles:
        console.print("[red]Aucun profil trouvé dans le dossier profiles/.[/red]")
        sys.exit(1)

    choice = Prompt.ask("\nSélectionnez le numéro du profil à appliquer", default="1")
    try:
        idx = int(choice) - 1
        selected_file, selected_profile = profiles[idx]
    except (ValueError, IndexError):
        console.print("[red]Choix invalide.[/red]")
        sys.exit(1)

    console.print(f"\n[green]Profil sélectionné :[/green] [bold]{selected_profile.name}[/bold] ({selected_file.name})")

    # 3. Chemin de l'ISO source
    iso_input = Prompt.ask("\nChemin absolu vers l'ISO Windows source")
    source_iso = Path(iso_input.strip('"'))
    while not source_iso.exists():
        console.print(f"[red]Fichier introuvable : {source_iso}[/red]")
        iso_input = Prompt.ask("Veuillez réindiquer le chemin vers l'ISO source")
        source_iso = Path(iso_input.strip('"'))

    # 4. Inspection optionnelle des éditions WIM
    if Confirm.ask("\nInspecter les éditions disponibles dans l'ISO source ?", default=True):
        try:
            with console.status("[bold cyan]Analyse du contenu de l'image (montage temporaire)...[/bold cyan]"):
                inspector = IsoInspector()
                editions = inspector.inspect_iso(source_iso)

            if editions:
                console.print(f"\n[bold green]Éditions détectées ({len(editions)}) :[/bold green]")
                for ed in editions:
                    idx = ed.get("index", "1")
                    name = ed.get("name", "")
                    arch = ed.get("architecture", "")
                    sz = ed.get("size", "")
                    console.print(f"  [[bold cyan]{idx}[/bold cyan]] {name} ({arch} - {sz})")

                chosen_idx = Prompt.ask(
                    "Index de l'édition Windows cible",
                    default=str(selected_profile.image_index or 1)
                )
                try:
                    selected_profile.image_index = int(chosen_idx)
                except ValueError:
                    pass
            else:
                console.print("[dim]Aucune édition listable automatiquement.[/dim]")
        except Exception as e:
            console.print(f"[yellow]Inspection ignorée : {e}[/yellow]")

    # 5. Option Découpage FAT32 & Mono-Édition
    split_choice = Confirm.ask(
        "\nDécouper install.wim en fichiers .swm (< 4 Go pour clé USB FAT32 / UEFI) ?",
        default=getattr(selected_profile, "split_wim_fat32", False)
    )
    selected_profile.split_wim_fat32 = split_choice

    single_choice = Confirm.ask(
        "Activer le mode Mono-Édition (n'exporter que l'édition sélectionnée pour alléger l'ISO de 40%) ?",
        default=getattr(selected_profile, "single_edition_only", False)
    )
    selected_profile.single_edition_only = single_choice

    # 6. Chemin de l'ISO de sortie
    default_out = f"OSBuilder_{selected_profile.target_os.value}_{selected_profile.architecture}.iso"
    iso_output = Prompt.ask("\nNom ou chemin de l'ISO personnalisée générée", default=default_out)
    output_iso = Path(iso_output.strip('"')).resolve()

    # 7. Confirmation
    apps_str = ", ".join(selected_profile.post_install.winget_apps) if selected_profile.post_install.winget_apps else "Aucune"
    console.print(Panel(
        f"[bold]Profil :[/bold] {selected_profile.name}\n"
        f"[bold]OS Cible :[/bold] {selected_profile.target_os.value.upper()} ({selected_profile.architecture})\n"
        f"[bold]Index WIM :[/bold] {selected_profile.image_index}\n"
        f"[bold]Mono-Édition :[/bold] {'Oui (-40% taille)' if selected_profile.single_edition_only else 'Non (Multi-index)'}\n"
        f"[bold]Découpage FAT32 :[/bold] {'Oui (.swm)' if selected_profile.split_wim_fat32 else 'Non (.wim)'}\n"
        f"[bold]Mode Sombre / Explorer :[/bold] {'Oui' if selected_profile.explorer.dark_mode else 'Standard'}\n"
        f"[bold].NET 3.5 & DirectPlay :[/bold] {'Oui' if selected_profile.system_features.enable_net35 else 'Non'}\n"
        f"[bold]Espace réservé ~7 Go :[/bold] {'Désactivé' if selected_profile.system_features.disable_reserved_storage else 'Actif'}\n"
        f"[bold]Gaming HAGS / Ultimate Perf :[/bold] {'Oui' if selected_profile.system_features.enable_hags else 'Non'}\n"
        f"[bold]Runtimes VC++ All-In-One :[/bold] {'Oui' if selected_profile.post_install.install_vcredist else 'Non'}\n"
        f"[bold]Apps WinGet :[/bold] {apps_str}\n"
        f"[bold]Bypass TPM/RAM :[/bold] {'Oui' if selected_profile.target_os.value == 'win11' and selected_profile.win11.bypass_tpm else 'N/A'}\n"
        f"[bold]Drivers NVMe/USB3 :[/bold] {'Oui' if selected_profile.target_os.value == 'win7' and selected_profile.win7.inject_nvme else 'N/A'}\n"
        f"[bold]ISO Source :[/bold] {source_iso}\n"
        f"[bold]ISO Sortie :[/bold] {output_iso}",
        title="Récapitulatif du Build",
        border_style="cyan"
    ))

    if not Confirm.ask("Lancer la construction de l'image ?", default=True):
        console.print("[yellow]Opération annulée par l'utilisateur.[/yellow]")
        sys.exit(0)

    # 8. Exécution du Pipeline
    def log_to_console(msg: str):
        console.print(f"[dim]{msg}[/dim]")

    pipeline = BuildPipeline(selected_profile, log_callback=log_to_console)
    try:
        pipeline.run(source_iso, output_iso)
        console.print(Panel(
            f"[bold green]Votre ISO personnalisée est prête ![/bold green]\n"
            f"Emplacement : [cyan]{output_iso}[/cyan]",
            title="Build Terminé"
        ))
    except Exception as e:
        console.print(Panel(
            f"[bold red]Erreur durant la construction :[/bold red]\n{e}",
            title="Échec du Build",
            border_style="red"
        ))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="OSBuilder-Win - Moteur de personnalisation d'images Windows 7, 10 et 11")
    parser.add_argument("--check-env", action="store_true", help="Vérifie les dépendances et outils système")
    parser.add_argument("--list-profiles", action="store_true", help="Affiche la liste des profils disponibles")
    parser.add_argument("--profile", type=str, help="Chemin vers le fichier de profil YAML")
    parser.add_argument("--iso", type=str, help="Chemin vers l'ISO Windows source")
    parser.add_argument("--output", type=str, help="Chemin de sortie de l'ISO personnalisée")
    parser.add_argument("--index", type=int, help="Index de l'image WIM à modifier (ex: 1 pour Pro)")
    parser.add_argument("--split-fat32", action="store_true", help="Découpe install.wim en fichiers .swm (< 4 Go)")
    parser.add_argument("--single-edition", action="store_true", help="Exporte uniquement l'index choisi pour alléger l'ISO (-40 pour cent)")
    parser.add_argument("--compression", choices=["fast", "maximum", "recovery"], default=None, help="Niveau de compression WIM/ESD")
    parser.add_argument("--zero-click", action="store_true", help="Active l'installation zéro-clic avec partitionnement automatique GPT/UEFI")
    parser.add_argument("--vmd-drivers", type=str, default=None, help="Chemin vers les pilotes Intel RST/VMD pour détection NVMe")
    parser.add_argument("--appx-preset", choices=["none", "light", "recommended", "aggressive"], default=None, help="Profil prédéfini de suppression des applications AppX")
    parser.add_argument("--auto-host-drivers", action="store_true", help="Capture et injecte automatiquement les pilotes réseau/stockage de la machine hôte")
    parser.add_argument("--disable-web-search", action="store_true", help="Désactive la recherche Bing dans le menu Démarrer (recherche locale à 0ms)")
    parser.add_argument("--updates-dir", type=str, default=None, help="Dossier de mises à jour (.msu/.cab) à trier (SSU avant LCU) et injecter")
    parser.add_argument("--display-res", type=str, default=None, help="Résolution d'affichage native pour WinPE Setup et OOBE (ex: 1920x1080)")
    parser.add_argument("--prevent-bitlocker", action="store_true", help="Désactive le chiffrement BitLocker automatique imposé par Windows 11 24H2")
    parser.add_argument("--disable-onedrive", action="store_true", help="Bloque l'auto-installation de OneDrive au premier démarrage")
    parser.add_argument("--cleanup-store", action="store_true", help="Nettoie et compresse le magasin WinSxS (/StartComponentCleanup /ResetBase, gain 1-3 Go)")
    parser.add_argument("--taskbar-left", action="store_true", help="Aligne la barre des tâches à gauche (style Windows 10/7 classique)")
    parser.add_argument("--disable-chat", action="store_true", help="Masque l'icône Chat/Teams de la barre des tâches")

    args = parser.parse_args()

    if args.check_env:
        print_status()
        return

    if args.list_profiles:
        display_profiles()
        return

    if args.profile and args.iso and args.output:
        from core.config import CompressionType, AppxPreset
        prof = load_profile_from_yaml(args.profile)
        if args.index:
            prof.image_index = args.index
        if args.split_fat32:
            prof.split_wim_fat32 = True
        if args.single_edition:
            prof.single_edition_only = True
        if args.compression:
            prof.compression_type = CompressionType(args.compression)
        if args.zero_click:
            prof.unattended.auto_disk_partition = True
        if args.vmd_drivers:
            prof.intel_vmd_drivers_dir = args.vmd_drivers
        if args.appx_preset:
            prof.appx_preset = AppxPreset(args.appx_preset)
        if args.auto_host_drivers:
            prof.auto_inject_host_network_drivers = True
        if args.disable_web_search:
            prof.explorer.disable_start_web_search = True
        if args.updates_dir:
            prof.updates_dir = args.updates_dir
        if args.display_res:
            prof.unattended.display_resolution = args.display_res
        if args.prevent_bitlocker:
            prof.win11.prevent_automatic_bitlocker = True
        if args.disable_onedrive:
            prof.win11.disable_onedrive_autoinstall = True
        if args.cleanup_store:
            prof.cleanup_component_store = True
        if args.taskbar_left:
            prof.win11.taskbar_align_left = True
        if args.disable_chat:
            prof.win11.disable_taskbar_chat = True

        pipeline = BuildPipeline(prof, log_callback=lambda m: console.print(f"[dim]{m}[/dim]"))
        pipeline.run(Path(args.iso), Path(args.output))
        return


    # Si aucun argument spécifique, lancer le mode interactif
    interactive_mode()


if __name__ == "__main__":
    main()
