==============================================================================
OSBuilder-Win - Dossier des Scripts et Utilitaires Personnalisés
==============================================================================

Ce dossier vous permet d'intégrer vos propres scripts d'automatisation, outils
ou configurations personnalisées directement au sein de votre image Windows.

FONCTIONNEMENT :
- Tout script (.cmd, .bat, .ps1) déposé dans ce dossier est automatiquement
  détecté par OSBuilder-Win lors du processus de compilation.
- Les scripts sont copiés dans le répertoire système :
  C:\Windows\Setup\Scripts\
- Ils peuvent être exécutés automatiquement avant l'ouverture de session
  (sous privilèges NT AUTHORITY\SYSTEM via SetupComplete.cmd)
  ou lors de la première ouverture de session utilisateur.

EXEMPLES D'UTILISATION :
- Scripts de configuration réseau ou VPN
- Scripts de déploiement d'outils ou d'environnements spécifiques
- Configurations système personnalisées

==============================================================================
LordMadTrix - OSBuilder-Win Studio
==============================================================================
