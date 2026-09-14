================================================================================
OSBuilder-Win - Intégration d'Applications Hors-Ligne (custom_apps/)
================================================================================

Déposez dans ce dossier tous les programmes d'installation (.exe, .msi, .cmd, .bat)
que vous souhaitez intégrer directement à l'image Windows pour une installation
silencieuse et 100% hors-ligne lors du premier démarrage.

Fonctionnement :
- Les fichiers déposés ici sont automatiquement injectés dans le répertoire :
  Windows\Setup\Apps\
- OSBuilder-Win détecte automatiquement les paramètres silencieux selon le type d'installateur :
  * InnoSetup / NSIS / InstallShield / MSI / Exécutables standards
- Un script orchestrateur "InstallApps.cmd" est généré pour exécuter l'ensemble des
  programmes de manière ordonnée et silencieuse.
================================================================================
