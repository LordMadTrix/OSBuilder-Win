"""
Catalogue standardisé et profils de suppression des applications pré-provisionnées AppX (Debloat).
Permet de sélectionner des ensembles cohérents d'applications à supprimer sans risque de casser
le Microsoft Store ou les composants essentiels du système.
"""

from enum import Enum
from typing import Dict, List, Set


class AppxPreset(str, Enum):
    NONE = "none"
    LIGHT = "light"
    RECOMMENDED = "recommended"
    AGGRESSIVE = "aggressive"


APPX_CATALOG: Dict[str, List[str]] = {
    "telemetry_and_feedback": [
        "*FeedbackHub*",
        "*GetHelp*",
        "*Tips*",
        "*WindowsFeedback*",
    ],
    "promos_and_social": [
        "*Clipchamp*",
        "*LinkedIn*",
        "*TikTok*",
        "*Instagram*",
        "*Facebook*",
        "*Spotify*",
        "*Disney*",
    ],
    "obsolete_tools": [
        "*Microsoft3DViewer*",
        "*MixedReality*",
        "*Print3D*",
        "*QuickAssist*",
        "*SoundRecorder*",
    ],
    "news_and_bing": [
        "*BingNews*",
        "*BingWeather*",
        "*BingFinance*",
        "*BingSports*",
        "*MicrosoftNews*",
    ],
    "gaming_and_xbox": [
        "*MicrosoftSolitaireCollection*",
        "*XboxApp*",
        "*XboxGameOverlay*",
        "*XboxGamingOverlay*",
        "*XboxIdentityProvider*",
        "*XboxSpeechToTextOverlay*",
        "*XboxTCUI*",
    ],
    "communication": [
        "*SkypeApp*",
        "*CommunicationsApps*",  # Courrier et Calendrier
        "*People*",
        "*Teams*",
    ],
    "media_players": [
        "*ZuneMusic*",
        "*ZuneVideo*",
    ],
    "office_and_notes": [
        "*MicrosoftOfficeHub*",
        "*OneNote*",
        "*PowerAutomateDesktop*",
    ]
}


def get_patterns_for_preset(preset: AppxPreset) -> List[str]:
    """Retourne la liste des motifs AppX associés à un profil de debloat."""
    patterns: Set[str] = set()

    if preset == AppxPreset.LIGHT:
        # Supprime les promotions, feedbacks et apps obsolètes
        for cat in ["telemetry_and_feedback", "promos_and_social", "obsolete_tools"]:
            patterns.update(APPX_CATALOG[cat])

    elif preset == AppxPreset.RECOMMENDED:
        # Profil standard recommandé : nettoie les promos, bing, feedback, jeux et outils obsolètes
        for cat in [
            "telemetry_and_feedback",
            "promos_and_social",
            "obsolete_tools",
            "news_and_bing",
            "gaming_and_xbox",
            "communication"
        ]:
            patterns.update(APPX_CATALOG[cat])

    elif preset == AppxPreset.AGGRESSIVE:
        # Suppression maximale de toutes les catégories du catalogue
        for cat in APPX_CATALOG:
            patterns.update(APPX_CATALOG[cat])

    return sorted(list(patterns))
