<div align="center">

# ⚡ OSBuilder-Win Studio v2.5 PRO
### Moteur Industriel de Création, Personnalisation et Optimisation d'Images ISO Windows

[![Windows 11 / 10 / 7](https://img.shields.io/badge/Windows-11%20%7C%2010%20%7C%207-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/LordMadTrix/OSBuilder-Win)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![DISM Engine](https://img.shields.io/badge/Servicing-Native%20DISM%20%2B%20Wimlib-00f0ff?style=for-the-badge&logo=powershell&logoColor=black)](https://github.com/LordMadTrix/OSBuilder-Win)
[![Tests 50/50 Pass](https://img.shields.io/badge/Tests-50%2F50%20Passing%20(100%25)-00e676?style=for-the-badge&logo=checkmarx&logoColor=white)](https://github.com/LordMadTrix/OSBuilder-Win)
[![Made for LordMadTrix](https://img.shields.io/badge/Edition-LordMadTrix%20Signature-7928ca?style=for-the-badge&logo=visualstudiocode&logoColor=white)](https://github.com/LordMadTrix)

<p align="center">
  <b>Conçu pour les passionnés d'optimisation, les joueurs esport et les techniciens système exigeants.</b><br>
  <i>Déploiement zéro-clic, debloat chirurgical, compression ESD haute densité, intégration hors-ligne et ergonomie MadOS.</i>
</p>

[Fonctionnalités](#-fonctionnalités-phares) • [Thèmes Graphiques](#-moteur-multi-thèmes) • [Installation](#-installation-rapide) • [Utilisation](#-guide-dutilisation) • [Profils Inclus](#-profils-de-build-inclus)

---

</div>

## 🌟 Présentation

**OSBuilder-Win Studio** est un environnement complet permettant de forger des images ISO Windows hautement personnalisées, allégées et optimisées pour le matériel moderne. Inspiré par les méthodologies industrielles de déploiement, il opère directement sur les images **WIM/ESD** et les **ruches de registre hors-ligne** sans altérer le système hôte.

Que ce soit pour ressusciter une machine sous **Windows 7** avec prise en charge intégrale du NVMe et de l'USB 3.1, ou pour déployer un **Windows 11 24H2** libéré de tout bridage (Bypass TPM, pas de compte Microsoft obligatoire, zéro pub, anti-BitLocker forcé, neutralisation de `appraiserres.dll`), OSBuilder-Win apporte une réponse clé en main avec une interface graphique moderne et un installeur natif.

---

## 🚀 Fonctionnalités Phares

### 🛡️ 1. Débridage Intégral de Windows 11 & 24H2
- **Neutralisation Universelle de `sources\appraiserres.dll`** : L'installateur Windows 11 ne vérifie plus aucun prérequis matériel, autorisant à la fois les clean installs et les mises à niveau directes sans perte de données.
- **Bypass Matériel Absolu** : Contournement natif dans `boot.wim` (Index 2 Setup) et `install.wim` :
  - `BypassTPMCheck` (Ignorer la présence d'une puce TPM 2.0)
  - `BypassSecureBootCheck` (Ignorer l'obligation du Secure Boot UEFI)
  - `BypassRAMCheck` (Installation possible avec moins de 4 Go de RAM)
  - `BypassCPUCheck` (Installation sur tout processeur x64, y compris anciennes générations)
  - `BypassStorageCheck` (Déploiement sur disques compacts)
- **Protection Spécifique Windows 11 24H2** :
  - **Anti-BitLocker Forcé** : Neutralisation hors-ligne du chiffrement automatique imposé par la 24H2 (`PreventDeviceEncryption = 1`). Évite le blocage soudain de vos partitions.
  - **Anti-OneDrive** : Blocage préventif de l'auto-installation de OneDrive et suppression de l'icône dans l'Explorateur.
- **Bypass Compte Microsoft & Télémétrie OOBE** :
  - Forçage du compte local administrateur sans connexion réseau (`BypassNRO = 1`).
  - Suppression définitive des écrans de harcèlement post-installation ("*Terminer la configuration de votre appareil*").
  - Restauration immédiate du **menu contextuel classique de Windows 10/7**.
  - Neutralisation complète de **Copilot, Widgets, Recall et de l'identifiant publicitaire**.

### 🔧 2. Matériel Moderne, NVMe & Rétablissement WinRE
- **Pré-Injection Sécurisée dans WinRE (`Winre.wim`)** :
  - Les pilotes de stockage critiques (NVMe, Intel VMD / RST, RAID) sont injectés directement dans l'environnement de récupération Windows (`Windows\System32\Recovery\Winre.wim`).
  - **Bénéfice majeur** : En cas de défaillance matérielle ou de crash, les outils de réparation Windows détectent immédiatement votre SSD NVMe et permettent la restauration du système.
- **Prise en charge Intel VMD / RST (11e à 14e Génération)** :
  - Résolution automatique du problème "Aucun lecteur détecté" lors du setup d'installation.
- **Windows 7 sur Matériel Récent** :
  - Injection automatique des pilotes NVMe et des contrôleurs d'hôtes xHCI USB 3.0 / 3.1. Clavier, souris et SSD fonctionnent immédiatement dès l'écran de bienvenue du Setup.

### 🎮 3. Latence Zéro & Optimisations Gaming (MadOS Engine)
- **Verrouillage du Noyau en RAM Physique** : Activation de `DisablePagingExecutive = 1` pour empêcher le kernel et les pilotes de basculer sur le fichier d'échange. Supprime les micro-saccades (stutters).
- **Réseau Esport Ultra-Faible Latence** : Désactivation de l'algorithme de Nagle (`TcpAckFrequency = 1`, `TCPNoDelay = 1`) pour un ping stable et réduit en jeu en ligne.
- **Résolution DNS Haute Performance** : Profils de serveurs DNS rapides intégrés (Cloudflare `1.1.1.1`, Google `8.8.8.8`, Quad9 `9.9.9.9`, AdGuard) avec tuning du cache local (`MaxCacheTtl = 86400`).
- **Optimisation Windows Defender Gaming** : Ajout d'exclusions automatiques pour les dossiers de jeux (`C:\Games`, `D:\Games`) et suppression de la collecte télémétrique d'échantillons.
- **Neutralisation de la Maintenance Automatique** : Empêche les réveils inopinés et les accès disque intensifs en arrière-plan.
- **Plan d'Alimentation 'Performances Ultimes'** : Débloqué nativement et activé par défaut.
- **Accélération Matérielle GPU (HAGS)** : Activée par défaut pour les GPU récents.
- **Priorité Multimédia & Processeur** : `MMCSS SystemResponsiveness = 0` et `Win32PrioritySeparation = 38` pour allouer 100% des cycles CPU au processus de jeu au premier plan.
- **Suite Menu Contextuel Pro** : Ajout de "Ouvrir avec PowerShell (Admin)", "Redémarrer l'Explorateur" et "Compacter le dossier (CompactOS LZX)".

### 📦 4. Compression Haute Densité & Optimisation WIM/ESD
- **Optimiseur WIM (`ImageOptimizer`)** : Défragmentation automatique du conteneur WIM après le debloat pour éliminer les clusters orphelins et récupérer jusqu'à plusieurs gigaoctets.
- **Conversion ESD Compacte (LZMS Recovery)** : Réduit la taille de l'image de 30% à 45% par rapport à un WIM standard, idéale pour les téléchargements rapides et supports USB compacts.
- **Nettoyage WinSxS (`/ResetBase`)** : Allègement de 1 à 3 Go en supprimant les anciens fichiers de mises à jour cumulatives devenus obsolètes.
- **Découpage FAT32 / SWM Automatique** : Découpage intelligent en fichiers `install.swm` (< 3800 Mo) pour compatibilité totale UEFI sans NTFS requis sur la clé USB.

### 💿 5. Intégration Logicielle Hors-Ligne (`custom_apps/`)
- **Dossier `custom_apps/`** : Déposez vos installeurs (.exe, .msi) pour qu'ils soient automatiquement injectés dans l'image (`Windows\Setup\Apps\`).
- **Détection Automatique des Switchs Silencieux** : InnoSetup, NSIS, InstallShield, MSI et installateurs standards configurés automatiquement.
- **Script Orchestrateur `InstallApps.cmd`** : Exécution ordonnée et silencieuse dès la finalisation du déploiement.

### 🧩 6. Profils de Fonctionnalités & Capacités (FOD)
- **Presets Intégrés** :
  - 🎮 **Gaming & Performance** : Active DirectPlay, NetFx3, et supprime les capacités obsolètes (WordPad, MathRecognizer, StepsRecorder, XPS).
  - 💻 **Développeur & DevOps** : Active WSL2, VirtualMachinePlatform, Hyper-V, Sandbox et OpenSSH Client/Server.
  - 🛡️ **Durcissement Sécurité** : Désactive SMBv1, Telnet, TFTP et active Windows Sandbox.
  - ⚡ **Ultra-Lite** : Épuration maximale des capacités et fonctionnalités inutilisées.

---

## 🎨 Moteur Multi-Thèmes Dynamique

OSBuilder-Win intègre un moteur de thèmes à chaud avec mémorisation des préférences utilisateur dans `user_settings.json` :

| Thème | Ambiance & Identité Visuelle | Description |
| :--- | :--- | :--- |
| ⚡ **MadOS Signature** | Noir Abyssal `#080a0f` • Cyan `#00f0ff` • Violet `#7928ca` | **Édition officielle LordMadTrix**. Look cyber-néon haute visibilité et style épuré. |
| 🌌 **Cyber Cyan** | Obsidian `#0b0e14` • Cyan Néon `#00d2ff` • Cartes `#131826` | Thème Studio sombre et équilibré avec accents haute technologie. |
| 💜 **Dracula Neon** | Nuit Violette `#0e0c15` • Magenta `#ff79c6` • Violet `#bd93f9` | Ambiance rétro-futuriste pour le développement nocturne. |
| 🟢 **Matrix Green** | Noir Terminal `#060a07` • Vert Cyber `#00ff66` • Émeraude `#00e676` | Style terminal console pour les puristes de l'automatisation. |
| ⚡ **Solar Amber** | Anthracite Chaud `#0f0d0a` • Ambre Haute Visibilité `#ffb300` | Ergonomie industrielle inspirée de l'instrumentation de précision. |
| 🔴 **Crimson ROG** | Carbone `#0e090b` • Rouge Rubis `#ff3366` • Cramoisi `#ff4757` | Ambiance gaming agressive pour machines de compétition. |
| ❄️ **Nordic Frost** | Fond Immaculé `#f1f5f9` • Bleu Arctique `#0284c7` • Cartes Blanches | Thème clair élégant, reposant et lumineux pour environnement de bureau. |
| ⬛ **Austère Mono** | Noir Charbon Mat `#121212` • Panneaux `#1c1c1c` • Acier `#d4d4d4` | Minimalisme industriel sobre, sans dégradé tape-à-l'œil, contraste pur. |

---

## 💾 Installation Rapide

### Option A : Installeur Graphique Dédié (`Setup.exe`)
1. Téléchargez ou clonez le dépôt.
2. Lancez **`Setup.exe`** en double-cliquant dessus.
3. L'assistant crée automatiquement les raccourcis Bureau et Menu Démarrer avec l'icône native haute résolution et enregistre l'application dans Windows (Apps & Fonctionnalités).

### Option B : Script d'Installation Rapide (`Install.cmd`)
Exécutez simplement `Install.cmd` en Administrateur pour vérifier les modules Python et déployer le raccourci sur votre bureau.

---

## 🖥️ Guide d'Utilisation

1. **Lancement de l'Application** :
   - Double-cliquez sur **`OSBuilder-Win.exe`** (ou sur votre raccourci Bureau). L'application s'élève automatiquement en mode Administrateur pour manipuler DISM et les ruches de registre.
2. **Sélection de l'Image Source & Profil** :
   - Choisissez votre fichier ISO officiel (Windows 11, 10 ou 7).
   - Cliquez sur **`🔍 Inspecter les Éditions`** pour sélectionner l'index cible (ex: *Windows 11 Professionnel*).
   - Choisissez l'un des profils optimisés ou personnalisez vos options dans l'onglet **⚡ Tweaks & Optimisations OS**.
3. **Personnalisation & Scripts** :
   - Activez les options matérielles (Intel VMD, pré-injection WinRE, Dark Mode MadOS, DNS rapide).
   - Déposez vos utilitaires dans `custom_scripts/` et vos installeurs dans `custom_apps/`.
4. **Lancement de la Compilation** :
   - Définissez l'emplacement de votre ISO de sortie et cliquez sur **`🚀 Lancer la Création de l'ISO`**.
   - Suivez la progression en direct dans l'onglet **📟 Console de Build**.
5. **Déploiement sur Clé USB** :
   - Basculez sur l'onglet **💾 Créateur Clé USB Bootable** pour flasher directement l'image sur votre support amovible avec formatage UEFI FAT32.

---

## 📋 Profils de Build Inclus

- ⚡ **`mados_edition.yaml`** : Profil ultime MadOS Signature de LordMadTrix (Bypass intégral, tweaks de latence gaming, thème MadOS #00f0ff, DNS Cloudflare, debloat recommandé, WinRE sécurisé).
- 🛡️ **`win11_unlocked.yaml`** : Windows 11 débridé (Bypass TPM/SecureBoot/RAM/CPU, compte local, sans Copilot/Recall, menu classique).
- 🧹 **`win10_debloat.yaml`** : Windows 10 ultra-allégé, télémétrie supprimée, optimisations SSD TRIM et services épurés.
- 🖥️ **`win7_modern_hw.yaml`** : Windows 7 SP1 x64 modernisé avec pilotes NVMe et USB 3.x injectés dans le setup et le système.

---

## 🧪 Qualité & Couverture de Tests

OSBuilder-Win fait l'objet d'une suite de tests unitaires automatisée validant 100% de la chaîne technique :

```powershell
python -m unittest tests/test_osbuilder.py
..................................................
----------------------------------------------------------------------
Ran 50 tests in 0.164s

OK (100% pass rate)
```

---

## 🤝 Crédits & Remerciements

- **Conception & Architecture** : [LordMadTrix](https://github.com/LordMadTrix)
- **Moteur DISM & WIM** : Microsoft Corporation / Wimlib Project
- **Déploiement Automatisé** : Microsoft Unattended Setup Engine
- **Ressources & Documentation** : [Le Crabe Info](https://lecrabeinfo.net) & Communauté MyDigitalLife

---

<div align="center">
  <sub>Développé avec passion pour l'écosystème LordMadTrix. Tous droits réservés © 2026.</sub>
</div>
