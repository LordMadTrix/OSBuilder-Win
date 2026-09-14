#!/usr/bin/env python3
"""
OSBuilder-Win - Interface Graphique PyQt6 Studio Professionnelle
Suite industrielle pour la personnalisation et le déploiement de Windows 7, 10 et 11 (24H2).
Conçu et développé pour l'écosystème de projets de LordMadTrix.
"""

import ctypes
import json
from datetime import datetime
import hashlib
import os
from pathlib import Path
import shutil
import sys
from typing import Optional, List, Dict, Any
import webbrowser

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QTextCursor, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QTabWidget, QLabel, QLineEdit, QPushButton, QFileDialog,
    QComboBox, QCheckBox, QGroupBox, QProgressBar, QTextEdit,
    QMessageBox, QScrollArea, QFrame, QSplitter, QInputDialog, QListWidget,
    QDialog, QToolButton
)

from core.config import (
    BuildProfile, TargetOS, UnattendedConfig, Win7Options, Win11Options,
    ExplorerOptions, ServicesOptions, FeaturesOptions, PostInstallOptions,
    CompressionType, AppxPreset, OemOptions, load_profile_from_yaml, save_profile_to_yaml
)
from core.pipeline import BuildPipeline
from core.unattended_generator import SUPPORTED_LOCALES, UnattendedGenerator
from core.iso_inspector import IsoInspector
from core.usb_creator import UsbCreator
from tools.fetch_tools import verify_all_tools


def is_admin() -> bool:
    """Vérifie si l'application s'exécute avec les privilèges Administrateur sous Windows."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


# ==============================================================================
# PALETTES DE THÈMES PROFESSIONNELLES & MOTEUR GRAPHIQUE DYNAMIQUE
# ==============================================================================
THEME_PALETTES = {
    "cyber_cyan": {
        "name": "🌌 Cyber Cyan (Studio)",
        "bg_main": "#0b0e14",
        "bg_card": "#131826",
        "bg_input": "#192030",
        "bg_input_focus": "#1e263a",
        "border": "#222b3d",
        "border_subtle": "#1f2738",
        "accent": "#00d2ff",
        "accent_grad_start": "#0066eb",
        "accent_grad_end": "#00d2ff",
        "accent_hover_start": "#0056c7",
        "accent_hover_end": "#00bced",
        "subtab_selected": "#38ef7d",
        "text_primary": "#e2e8f0",
        "text_muted": "#8b9bb4",
        "console_bg": "#07090e",
        "tab_unselected": "#0f121b",
    },
    "dracula_neon": {
        "name": "💜 Dracula (Neon Purple)",
        "bg_main": "#0e0c15",
        "bg_card": "#171424",
        "bg_input": "#201c33",
        "bg_input_focus": "#282340",
        "border": "#2d2745",
        "border_subtle": "#251f3b",
        "accent": "#bd93f9",
        "accent_grad_start": "#7f5af0",
        "accent_grad_end": "#bd93f9",
        "accent_hover_start": "#6c48df",
        "accent_hover_end": "#ab7ef0",
        "subtab_selected": "#ff79c6",
        "text_primary": "#f8f8f2",
        "text_muted": "#9d96b8",
        "console_bg": "#09080e",
        "tab_unselected": "#120f1c",
    },
    "matrix_green": {
        "name": "🟢 Matrix (Cyber Green)",
        "bg_main": "#060a07",
        "bg_card": "#0c150e",
        "bg_input": "#122015",
        "bg_input_focus": "#172b1c",
        "border": "#1b3321",
        "border_subtle": "#15281a",
        "accent": "#00ff66",
        "accent_grad_start": "#009933",
        "accent_grad_end": "#00ff66",
        "accent_hover_start": "#00802b",
        "accent_hover_end": "#00e65c",
        "subtab_selected": "#00ffaa",
        "text_primary": "#e6f4ea",
        "text_muted": "#7ba885",
        "console_bg": "#040705",
        "tab_unselected": "#090f0b",
    },
    "solar_amber": {
        "name": "⚡ Solar Amber (High-Tech)",
        "bg_main": "#0f0d0a",
        "bg_card": "#1a1610",
        "bg_input": "#262016",
        "bg_input_focus": "#332a1c",
        "border": "#3b3020",
        "border_subtle": "#2e2518",
        "accent": "#ffb300",
        "accent_grad_start": "#e65100",
        "accent_grad_end": "#ffb300",
        "accent_hover_start": "#cc4400",
        "accent_hover_end": "#ffa000",
        "subtab_selected": "#ffcc00",
        "text_primary": "#fdf6e2",
        "text_muted": "#ad9b7d",
        "console_bg": "#0a0806",
        "tab_unselected": "#14110c",
    },
    "crimson_rog": {
        "name": "🔴 Crimson ROG (Gaming Red)",
        "bg_main": "#0e090b",
        "bg_card": "#181014",
        "bg_input": "#24171d",
        "bg_input_focus": "#301d27",
        "border": "#3a222f",
        "border_subtle": "#2c1923",
        "accent": "#ff3366",
        "accent_grad_start": "#c00832",
        "accent_grad_end": "#ff3366",
        "accent_hover_start": "#a5062a",
        "accent_hover_end": "#e62254",
        "subtab_selected": "#ff6b8b",
        "text_primary": "#fae8ee",
        "text_muted": "#aa8897",
        "console_bg": "#090507",
        "tab_unselected": "#130c0f",
    },
    "nordic_frost": {
        "name": "❄️ Nordic Frost (Clair Élégant)",
        "bg_main": "#f1f5f9",
        "bg_card": "#ffffff",
        "bg_input": "#ffffff",
        "bg_input_focus": "#f8fafc",
        "border": "#cbd5e1",
        "border_subtle": "#e2e8f0",
        "accent": "#0284c7",
        "accent_grad_start": "#0369a1",
        "accent_grad_end": "#0284c7",
        "accent_hover_start": "#075985",
        "accent_hover_end": "#0ea5e9",
        "subtab_selected": "#0284c7",
        "text_primary": "#0f172a",
        "text_muted": "#64748b",
        "console_bg": "#0f172a",
        "tab_unselected": "#e2e8f0",
    },
    "austere_mono": {
        "name": "⬛ Austère (Monochrome Sobre)",
        "bg_main": "#121212",
        "bg_card": "#1c1c1c",
        "bg_input": "#252525",
        "bg_input_focus": "#2e2e2e",
        "border": "#383838",
        "border_subtle": "#282828",
        "accent": "#d4d4d4",
        "accent_grad_start": "#383838",
        "accent_grad_end": "#525252",
        "accent_hover_start": "#444444",
        "accent_hover_end": "#606060",
        "subtab_selected": "#e5e5e5",
        "text_primary": "#f0f0f0",
        "text_muted": "#888888",
        "console_bg": "#0d0d0d",
        "tab_unselected": "#161616",
    },
    "mados_signature": {
        "name": "⚡ MadOS Signature (LordMadTrix Edition)",
        "bg_main": "#080a0f",
        "bg_card": "#101420",
        "bg_input": "#161c2e",
        "bg_input_focus": "#1e2740",
        "border": "#263352",
        "border_subtle": "#1b243b",
        "accent": "#00f0ff",
        "accent_grad_start": "#7928ca",
        "accent_grad_end": "#00f0ff",
        "accent_hover_start": "#631da8",
        "accent_hover_end": "#00d5e3",
        "subtab_selected": "#00f0ff",
        "text_primary": "#f0f6fc",
        "text_muted": "#8b9bb4",
        "console_bg": "#05070a",
        "tab_unselected": "#0c0e17",
    },
}


def get_theme_stylesheet(theme_key: str = "cyber_cyan") -> str:
    """Génère dynamiquement la feuille de style QSS adaptée à la palette sélectionnée."""
    pal = THEME_PALETTES.get(theme_key, THEME_PALETTES["cyber_cyan"])
    return f"""
QMainWindow {{
    background-color: {pal['bg_main']};
}}
QWidget {{
    background-color: {pal['bg_main']};
    color: {pal['text_primary']};
    font-family: 'Segoe UI Variable Display', 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}}
/* Onglets Principaux */
QTabWidget#MainTabs::pane {{
    border: 1px solid {pal['border_subtle']};
    border-radius: 10px;
    background-color: {pal['bg_card']};
    top: -1px;
}}
QTabWidget#MainTabs > QTabBar::tab {{
    background-color: {pal['tab_unselected']};
    color: {pal['text_muted']};
    padding: 11px 22px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border: 1px solid {pal['border_subtle']};
    border-bottom: none;
    font-weight: 600;
    font-size: 13px;
}}
QTabWidget#MainTabs > QTabBar::tab:selected {{
    background-color: {pal['bg_card']};
    color: {pal['accent']};
    border-top: 2px solid {pal['accent']};
    border-bottom: 2px solid {pal['bg_card']};
}}
QTabWidget#MainTabs > QTabBar::tab:hover:!selected {{
    background-color: {pal['bg_input_focus']};
    color: {pal['text_primary']};
}}

/* Onglets Secondaires (Tweaks) */
QTabWidget#SubTabs::pane {{
    border: 1px solid {pal['border']};
    border-radius: 8px;
    background-color: {pal['bg_card']};
    top: -1px;
}}
QTabWidget#SubTabs > QTabBar::tab {{
    background-color: {pal['bg_main']};
    color: {pal['text_muted']};
    padding: 8px 16px;
    margin-right: 3px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid {pal['border_subtle']};
    border-bottom: none;
    font-weight: 600;
    font-size: 12px;
}}
QTabWidget#SubTabs > QTabBar::tab:selected {{
    background-color: {pal['bg_card']};
    color: {pal['subtab_selected']};
    border-top: 2px solid {pal['subtab_selected']};
}}
QTabWidget#SubTabs > QTabBar::tab:hover:!selected {{
    background-color: {pal['bg_input_focus']};
    color: {pal['text_primary']};
}}

/* Cartes & GroupBoxes */
QGroupBox {{
    border: 1px solid {pal['border']};
    border-radius: 9px;
    margin-top: 14px;
    padding: 16px 14px 14px 14px;
    font-weight: bold;
    font-size: 13px;
    color: {pal['accent']};
    background-color: {pal['bg_card']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 8px;
    background-color: {pal['bg_card']};
    border-radius: 4px;
}}

/* Entrées Utilisateur */
QLineEdit, QComboBox {{
    background-color: {pal['bg_input']};
    border: 1px solid {pal['border']};
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 22px;
    color: {pal['text_primary']};
    selection-background-color: {pal['accent_grad_start']};
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {pal['accent']};
    background-color: {pal['bg_input_focus']};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {pal['bg_card']};
    border: 1px solid {pal['border']};
    selection-background-color: {pal['accent_grad_start']};
    selection-color: #ffffff;
    color: {pal['text_primary']};
    padding: 4px;
}}

/* Boutons */
QPushButton {{
    background-color: {pal['bg_input']};
    border: 1px solid {pal['border']};
    border-radius: 6px;
    padding: 8px 16px;
    min-height: 32px;
    font-weight: 600;
    color: {pal['text_primary']};
}}
QPushButton:hover {{
    background-color: {pal['bg_input_focus']};
    border-color: {pal['accent']};
    color: #ffffff;
}}
QPushButton:pressed {{
    background-color: {pal['bg_main']};
}}
QPushButton:disabled {{
    background-color: {pal['bg_main']};
    border-color: {pal['border_subtle']};
    color: {pal['text_muted']};
}}

/* Bouton Primaire Haut de Gamme */
QPushButton#PrimaryBtn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {pal['accent_grad_start']}, stop:1 {pal['accent_grad_end']});
    color: #ffffff;
    border: none;
    font-size: 14px;
    font-weight: bold;
    min-height: 40px;
    padding: 10px 24px;
    border-radius: 7px;
}}
QPushButton#PrimaryBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {pal['accent_hover_start']}, stop:1 {pal['accent_hover_end']});
}}

/* Bouton Annulation / Alerte */
QPushButton#DangerBtn {{
    background-color: #3d141a;
    border: 1px solid #701d29;
    color: #ff6b81;
    font-weight: bold;
}}
QPushButton#DangerBtn:hover {{
    background-color: #541924;
    border-color: #ff4757;
    color: #ffffff;
}}

/* Bouton Succès / Vert */
QPushButton#SuccessBtn {{
    background-color: #0d2e1c;
    border: 1px solid #145934;
    color: #2ed573;
    font-weight: bold;
}}
QPushButton#SuccessBtn:hover {{
    background-color: #124027;
    border-color: #2ed573;
    color: #ffffff;
}}

/* Cases à cocher */
QCheckBox {{
    spacing: 10px;
    color: {pal['text_primary']};
    font-size: 13px;
}}
QCheckBox:hover {{
    color: #ffffff;
}}
QCheckBox::indicator {{
    width: 19px;
    height: 19px;
    border-radius: 4px;
    border: 1px solid {pal['border']};
    background-color: {pal['bg_input']};
}}
QCheckBox::indicator:hover {{
    border-color: {pal['accent']};
    background-color: {pal['bg_input_focus']};
}}
QCheckBox::indicator:checked {{
    background-color: {pal['accent']};
    border-color: {pal['accent']};
}}

/* Barres de Défilement */
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollBar:vertical {{
    background: {pal['bg_main']};
    width: 8px;
    margin: 0;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {pal['border']};
    min-height: 25px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {pal['accent']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Barres de Progression */
QProgressBar {{
    background-color: {pal['bg_input']};
    border: 1px solid {pal['border']};
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {pal['accent_grad_start']}, stop:1 {pal['accent_grad_end']});
    border-radius: 5px;
}}

/* Terminal Console */
QTextEdit {{
    background-color: {pal['console_bg']};
    border: 1px solid {pal['border']};
    border-radius: 8px;
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    color: {pal['text_primary']};
    padding: 10px;
}}
QListWidget {{
    background-color: {pal['bg_input']};
    border: 1px solid {pal['border']};
    border-radius: 6px;
    color: {pal['text_primary']};
    padding: 4px;
}}
QListWidget::item {{
    padding: 4px 8px;
    border-radius: 4px;
}}
QListWidget::item:selected {{
    background-color: {pal['accent_grad_start']};
    color: #ffffff;
}}
"""

DARK_STYLESHEET = get_theme_stylesheet("cyber_cyan")


# ==============================================================================
# THREADS DE TRAVAIL EN ARRIÈRE-PLAN
# ==============================================================================
class BuildWorker(QThread):
    """Exécute le pipeline de construction ISO sans bloquer l'interface."""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    progress_signal = pyqtSignal(int)

    def __init__(self, profile: BuildProfile, source_iso: str, output_iso: str):
        super().__init__()
        self.profile = profile
        self.source_iso = source_iso
        self.output_iso = output_iso
        self.pipeline: Optional[BuildPipeline] = None

    def cancel(self):
        """Déclenche l'annulation immédiate et le démontage sécurisé du build."""
        if self.pipeline:
            self.pipeline.cancel()

    def run(self):
        def log_callback(msg: str):
            self.log_signal.emit(msg)
            if "[ÉTAPE 1/6]" in msg:
                self.progress_signal.emit(15)
            elif "[ÉTAPE 2/6]" in msg or "Conversion" in msg:
                self.progress_signal.emit(30)
            elif "[ÉTAPE 3/6]" in msg:
                self.progress_signal.emit(45)
            elif "[ÉTAPE 4/6]" in msg:
                self.progress_signal.emit(65)
            elif "[ÉTAPE 5/6]" in msg:
                self.progress_signal.emit(80)
            elif "[ÉTAPE 6/6]" in msg:
                self.progress_signal.emit(90)
            elif "[SUCCÈS]" in msg:
                self.progress_signal.emit(100)

        self.pipeline = BuildPipeline(self.profile, log_callback=log_callback)
        try:
            success = self.pipeline.run(self.source_iso, self.output_iso)
            self.finished_signal.emit(success, "Image ISO personnalisée générée avec succès !")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class HashCalculatorThread(QThread):
    """Calcule les empreintes SHA-1 et SHA-256 sans latence."""
    result_signal = pyqtSignal(str, str)
    error_signal = pyqtSignal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            sha1 = hashlib.sha1()
            sha256 = hashlib.sha256()
            with open(self.file_path, "rb") as f:
                while chunk := f.read(1024 * 1024):
                    sha1.update(chunk)
                    sha256.update(chunk)
            self.result_signal.emit("SHA-1", sha1.hexdigest().upper())
            self.result_signal.emit("SHA-256", sha256.hexdigest().upper())
        except Exception as e:
            self.error_signal.emit(str(e))


class IsoInspectorWorker(QThread):
    """Inspecte les éditions contenues dans un WIM/ESD d'ISO en arrière-plan."""
    finished_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, iso_path: str):
        super().__init__()
        self.iso_path = iso_path

    def run(self):
        try:
            inspector = IsoInspector()
            editions = inspector.inspect_iso(self.iso_path)
            self.finished_signal.emit(editions)
        except Exception as e:
            self.error_signal.emit(str(e))


class UsbDeployWorker(QThread):
    """Gère le formatage et le déploiement sur clé USB en tâche de fond."""
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, iso_path: str, target_drive: str, format_fat32: bool = True):
        super().__init__()
        self.iso_path = iso_path
        self.target_drive = target_drive
        self.format_fat32 = format_fat32

    def run(self):
        try:
            creator = UsbCreator()
            if self.format_fat32:
                self.progress_signal.emit(5, "Formatage rapide du volume USB en FAT32...")
                creator.format_usb_drive(self.target_drive)

            creator.deploy_iso_to_usb(
                self.iso_path,
                self.target_drive,
                progress_callback=lambda pct, msg: self.progress_signal.emit(pct, msg)
            )
            self.finished_signal.emit(True, f"La clé USB {self.target_drive} est prête et bootable !")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


# ==============================================================================
# FENÊTRE PRINCIPALE STUDIO
# ==============================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OSBuilder-Win Studio — Suite Industrielle de Déploiement Windows")
        self.resize(1100, 840)
        self.setMinimumSize(940, 700)

        self.user_settings = self._load_user_settings()
        self.current_theme = self.user_settings.get("theme", "cyber_cyan")
        self.setStyleSheet(get_theme_stylesheet(self.current_theme))

        icon_path = Path(__file__).resolve().parent / "app.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.current_profile: Optional[BuildProfile] = None
        self.worker: Optional[BuildWorker] = None
        self.all_tweak_checkboxes: List[QCheckBox] = []

        self._init_ui()
        self._load_default_profiles()
        self._check_system_health()

    def _load_user_settings(self) -> dict:
        settings_file = Path(__file__).resolve().parent / "user_settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"theme": "cyber_cyan"}

    def _save_user_settings(self):
        settings_file = Path(__file__).resolve().parent / "user_settings.json"
        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(self.user_settings, f, indent=2)
        except Exception:
            pass

    def apply_theme(self, theme_key: str):
        if theme_key not in THEME_PALETTES:
            theme_key = "cyber_cyan"
        self.current_theme = theme_key
        self.setStyleSheet(get_theme_stylesheet(theme_key))
        self.user_settings["theme"] = theme_key
        self._save_user_settings()

    def _on_theme_changed(self, idx: int):
        if idx < 0:
            return
        theme_key = self.cb_theme.currentData()
        if theme_key:
            self.apply_theme(theme_key)

    def _init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(14)

        # 1. En-Tête & Statuts Système en Temps Réel
        main_layout.addLayout(self._create_header_layout())

        # 2. Onglets Principaux
        self.tabs = QTabWidget()
        self.tabs.setObjectName("MainTabs")
        self.tabs.addTab(self._create_main_tab(), "📁 Configuration && Fichiers ISO")
        self.tabs.addTab(self._create_tweaks_tab(), "⚡ Tweaks && Optimisations OS")
        self.tabs.addTab(self._create_usb_tab(), "💾 Créateur Clé USB Bootable")
        self.tabs.addTab(self._create_sources_tab(), "🌐 Sources && Intégrité ISO")
        self.console_widget = self._create_console_tab()
        self.tabs.addTab(self.console_widget, "📟 Console de Build && Logs")
        main_layout.addWidget(self.tabs)

        # 3. Footer / Barre d'action
        main_layout.addLayout(self._create_footer_layout())
        self.setCentralWidget(main_widget)

    # --- Header & Diagnostics ---
    def _create_header_layout(self) -> QHBoxLayout:
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title_row = QHBoxLayout()
        title_lbl = QLabel("OSBuilder-Win Studio")
        title_lbl.setStyleSheet("color: #00d2ff; font-size: 22px; font-weight: 800; letter-spacing: 0.5px;")
        version_lbl = QLabel("v2.5 PRO")
        version_lbl.setStyleSheet(
            "background-color: #1e293b; color: #38ef7d; font-size: 11px; font-weight: bold; "
            "padding: 2px 8px; border-radius: 4px; border: 1px solid #2e3d55;"
        )
        title_row.addWidget(title_lbl)
        title_row.addWidget(version_lbl)
        title_row.addStretch()
        title_box.addLayout(title_row)

        subtitle_lbl = QLabel("Architecture industrielle pour Windows 7 / 10 / 11 24H2 — Développé pour LordMadTrix")
        subtitle_lbl.setStyleSheet("color: #8b9bb4; font-size: 12px;")
        title_box.addWidget(subtitle_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Sélecteur de Thème Graphique
        theme_box = QHBoxLayout()
        lbl_theme = QLabel("🎨 Thème :")
        lbl_theme.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.cb_theme = QComboBox()
        self.cb_theme.setToolTip("Changer instantanément le thème visuel de l'interface")
        for k, v in THEME_PALETTES.items():
            self.cb_theme.addItem(v["name"], k)

        # Positionner sur le thème sauvegardé
        for i in range(self.cb_theme.count()):
            if self.cb_theme.itemData(i) == self.current_theme:
                self.cb_theme.setCurrentIndex(i)
                break

        self.cb_theme.currentIndexChanged.connect(self._on_theme_changed)
        theme_box.addWidget(lbl_theme)
        theme_box.addWidget(self.cb_theme)
        header_layout.addLayout(theme_box)

        # Diagnostic Status Chips
        self.chip_admin = QLabel()
        self.chip_admin.setStyleSheet("padding: 5px 12px; border-radius: 12px; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(self.chip_admin)

        self.btn_elevate = QPushButton("🛡️ Élever en Admin")
        self.btn_elevate.setObjectName("SuccessBtn")
        self.btn_elevate.clicked.connect(self._restart_as_admin)
        self.btn_elevate.setVisible(False)
        header_layout.addWidget(self.btn_elevate)

        btn_diag = QPushButton("🔍 Diagnostics Outils")
        btn_diag.clicked.connect(self._show_tools_diagnostics)
        header_layout.addWidget(btn_diag)

        return header_layout

    def _create_footer_layout(self) -> QHBoxLayout:
        footer_layout = QHBoxLayout()
        self.status_icon = QLabel("●")
        self.status_icon.setStyleSheet("color: #00d2ff; font-size: 14px;")
        footer_layout.addWidget(self.status_icon)

        self.status_lbl = QLabel("Prêt pour la configuration.")
        self.status_lbl.setStyleSheet("color: #94a3b8; font-weight: 500;")
        footer_layout.addWidget(self.status_lbl)
        footer_layout.addStretch()

        self.btn_build = QPushButton("🚀 Lancer la Création de l'ISO")
        self.btn_build.setObjectName("PrimaryBtn")
        self.btn_build.clicked.connect(self._start_build)
        footer_layout.addWidget(self.btn_build)

        return footer_layout

    def _check_system_health(self):
        if is_admin():
            self.chip_admin.setText("● UAC : ADMINISTRATEUR ACTIF")
            self.chip_admin.setStyleSheet("background-color: #0d2b1f; color: #00e676; border: 1px solid #165b3d;")
            self.btn_elevate.setVisible(False)
        else:
            self.chip_admin.setText("▲ UAC : DROITS RESTREINTS")
            self.chip_admin.setStyleSheet("background-color: #381a10; color: #ffab00; border: 1px solid #733c19;")
            self.btn_elevate.setVisible(True)

    def _show_tools_diagnostics(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Diagnostics des Outils et Moteurs Système")
        dialog.resize(680, 420)
        dialog.setStyleSheet(DARK_STYLESHEET)
        vbox = QVBoxLayout(dialog)
        vbox.setSpacing(12)

        title = QLabel("État des Dépendances & Accélérateurs Système")
        title.setStyleSheet("color: #00d2ff; font-size: 16px; font-weight: bold;")
        vbox.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)

        def refresh_grid():
            # Vider le layout
            while grid.count():
                item = grid.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            res = verify_all_tools()
            tools_data = [
                ("Moteur DISM (System32)", res.get("dism") is not None, res.get("dism") or "Introuvable (Requis)", None),
                ("Accélérateur Wimlib (Haute Vitesse)", res.get("wimlib") is not None, res.get("wimlib") or "Optionnel (Recommandé)", None),
                ("Extracteur 7-Zip", res.get("7zip") is not None, res.get("7zip") or "Optionnel (Repli PowerShell actif)", None),
                ("Générateur ISO Oscdimg (Windows ADK)", res.get("oscdimg") is not None, res.get("oscdimg") or "En attente (bin/oscdimg.exe ou ADK)", "oscdimg"),
                ("Droits Administrateur Élevés", res.get("admin", False), "Requis pour montage DISM hors-ligne", None),
            ]

            for i, (name, ok, path, tool_key) in enumerate(tools_data):
                lbl_name = QLabel(f"<b>{name}</b> :")
                lbl_stat = QLabel("🟢 PRÉSENT" if ok else "🟡 OPTIONNEL / MANQUANT")
                lbl_stat.setStyleSheet("color: #00e676; font-weight: bold;" if ok else "color: #ffab00; font-weight: bold;")
                lbl_path = QLabel(f"<small>{path}</small>")
                lbl_path.setStyleSheet("color: #8b9bb4;")

                grid.addWidget(lbl_name, i, 0)
                grid.addWidget(lbl_stat, i, 1)
                grid.addWidget(lbl_path, i, 2)

                if tool_key == "oscdimg" and not ok:
                    act_box = QHBoxLayout()
                    btn_inst = QPushButton("⚡ Installer ADK")
                    btn_inst.setObjectName("SuccessBtn")
                    btn_inst.setToolTip("Lance l'assistant d'installation Microsoft ADK pour intégrer Oscdimg")
                    btn_inst.clicked.connect(self._launch_adk_setup)
                    
                    btn_bin = QPushButton("📁 Dossier bin/")
                    btn_bin.setToolTip("Ouvre le dossier bin/ pour y déposer manuellement oscdimg.exe")
                    btn_bin.clicked.connect(lambda: os.startfile(Path(__file__).resolve().parent / "bin"))

                    act_box.addWidget(btn_inst)
                    act_box.addWidget(btn_bin)
                    grid.addLayout(act_box, i, 3)

        refresh_grid()
        vbox.addLayout(grid)

        hint_card = QGroupBox("💡 Comment obtenir Oscdimg ?")
        hl = QVBoxLayout(hint_card)
        hl.setSpacing(6)
        hint_text = QLabel(
            "Oscdimg est l'outil officiel de Microsoft pour générer des images ISO bootables UEFI + BIOS.<br>"
            "<b>Option A (Automatique) :</b> Cliquez sur <b>'⚡ Installer ADK'</b> pour installer les outils de déploiement officiels.<br>"
            "<b>Option B (Rapide) :</b> Cliquez sur <b>'📁 Dossier bin/'</b> et collez directement votre binaire <b>oscdimg.exe</b> (x64)."
        )
        hint_text.setWordWrap(True)
        hint_text.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        hl.addWidget(hint_text)
        vbox.addWidget(hint_card)

        vbox.addStretch()

        btn_row = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Réactualiser")
        btn_refresh.clicked.connect(refresh_grid)
        btn_row.addWidget(btn_refresh)
        btn_row.addStretch()

        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(dialog.accept)
        btn_row.addWidget(btn_close)
        vbox.addLayout(btn_row)

        dialog.exec()

    def _restart_as_admin(self):
        script_path = os.path.abspath(__file__)
        python_exe = sys.executable
        cmd = f'Start-Process "{python_exe}" -ArgumentList @(\'"{script_path}"\') -Verb RunAs'
        os.system(f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{cmd}"')
        sys.exit(0)

    # --- Onglet 1 : Configuration & Fichiers ---
    def _create_main_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        # 1. Sélection & Gestion du Profil
        grp_profile = QGroupBox("Profil de Personnalisation Windows")
        prof_layout = QHBoxLayout(grp_profile)
        prof_layout.setSpacing(10)

        self.cb_profiles = QComboBox()
        self.cb_profiles.currentIndexChanged.connect(self._on_profile_selected)
        prof_layout.addWidget(self.cb_profiles, stretch=3)

        btn_reload = QPushButton("🔄 Recharger Profils")
        btn_reload.clicked.connect(self._load_default_profiles)
        prof_layout.addWidget(btn_reload)

        btn_save_prof = QPushButton("💾 Enregistrer sous...")
        btn_save_prof.setToolTip("Sauvegarde la configuration complète des tweaks dans un nouveau fichier YAML")
        btn_save_prof.clicked.connect(self._save_custom_profile)
        prof_layout.addWidget(btn_save_prof)
        layout.addWidget(grp_profile)

        # 2. Groupe Fichiers ISO & Moteur WIM
        grp_files = QGroupBox("Fichiers Images ISO & Paramètres d'Édition")
        files_layout = QVBoxLayout(grp_files)
        files_layout.setSpacing(10)

        # ISO Source
        src_lbl = QLabel("Image ISO Windows source (Officielle MSDN / UUP / Microsoft) :")
        files_layout.addWidget(src_lbl)
        src_box = QHBoxLayout()
        self.txt_source_iso = QLineEdit()
        self.txt_source_iso.setPlaceholderText("Ex: D:\\ISOs\\fr-fr_windows_11_consumer_editions_24h2.iso")
        btn_browse_src = QPushButton("📁 Parcourir...")
        btn_browse_src.clicked.connect(self._browse_source_iso)
        self.btn_inspect_iso = QPushButton("🔍 Inspecter les Éditions")
        self.btn_inspect_iso.setObjectName("SuccessBtn")
        self.btn_inspect_iso.clicked.connect(self._inspect_iso)
        src_box.addWidget(self.txt_source_iso)
        src_box.addWidget(btn_browse_src)
        src_box.addWidget(self.btn_inspect_iso)
        files_layout.addLayout(src_box)

        # Éditions détectées
        self.lbl_editions = QLabel("Édition cible détectée (Index WIM/ESD) :")
        self.lbl_editions.setStyleSheet("color: #00d2ff; font-weight: bold;")
        self.lbl_editions.setVisible(False)
        files_layout.addWidget(self.lbl_editions)
        self.cb_editions = QComboBox()
        self.cb_editions.setVisible(False)
        self.cb_editions.currentIndexChanged.connect(self._on_edition_changed)
        files_layout.addWidget(self.cb_editions)

        # ISO Destination
        dst_lbl = QLabel("Emplacement de l'ISO personnalisée de sortie :")
        files_layout.addWidget(dst_lbl)
        dst_box = QHBoxLayout()
        self.txt_output_iso = QLineEdit()
        self.txt_output_iso.setPlaceholderText("Ex: D:\\ISOs\\Windows_11_24H2_SuperLite_LordMadTrix.iso")
        self.txt_output_iso.textChanged.connect(self._update_disk_space_label)
        btn_browse_dst = QPushButton("💾 Définir...")
        btn_browse_dst.clicked.connect(self._browse_output_iso)
        dst_box.addWidget(self.txt_output_iso)
        dst_box.addWidget(btn_browse_dst)
        files_layout.addLayout(dst_box)

        # Indicateur d'espace disque disponible
        self.lbl_disk_space = QLabel("Espace disque disponible : En attente de chemin...")
        self.lbl_disk_space.setStyleSheet("color: #8b9bb4; font-size: 11px;")
        files_layout.addWidget(self.lbl_disk_space)

        # Options d'export WIM
        opt_box = QHBoxLayout()
        self.chk_single_edition = QCheckBox("Mode Mono-Édition (Allège l'ISO de 35% en supprimant les index inutiles)")
        self.chk_single_edition.setChecked(True)
        opt_box.addWidget(self.chk_single_edition)

        comp_lbl = QLabel("Format & Compression :")
        opt_box.addWidget(comp_lbl)
        self.cb_compression = QComboBox()
        self.cb_compression.addItem("Maximum (LZX standard - Recommandé)", CompressionType.MAXIMUM.value)
        self.cb_compression.addItem("Rapide (LZX build test rapide)", CompressionType.FAST.value)
        self.cb_compression.addItem("Ultra Compact (LZMS - .esd recovery)", CompressionType.RECOVERY.value)
        opt_box.addWidget(self.cb_compression)
        files_layout.addLayout(opt_box)

        # Mises à jour Windows hors-ligne (.msu / .cab)
        upd_lbl = QLabel("Mises à jour cumulatives / SSU hors-ligne (.msu / .cab ordonnancés automatiquement) :")
        files_layout.addWidget(upd_lbl)
        upd_box = QHBoxLayout()
        self.txt_updates_dir = QLineEdit()
        self.txt_updates_dir.setPlaceholderText("Ex: D:\\Updates\\Win11_24H2_Cumulative (Optionnel)")
        btn_browse_upd = QPushButton("📁 Parcourir MàJ...")
        btn_browse_upd.clicked.connect(self._browse_updates_dir)
        upd_box.addWidget(self.txt_updates_dir)
        upd_box.addWidget(btn_browse_upd)
        files_layout.addLayout(upd_box)

        # Résolution d'affichage Setup
        res_box = QHBoxLayout()
        res_lbl = QLabel("Résolution d'affichage native WinPE & Setup :")
        res_lbl.setStyleSheet("color: #38ef7d; font-weight: bold;")
        self.cb_display_res = QComboBox()
        self.cb_display_res.addItem("1920x1080 (1080p FHD 60Hz - Recommandé)", "1920x1080")
        self.cb_display_res.addItem("2560x1440 (2K QHD)", "2560x1440")
        self.cb_display_res.addItem("3840x2160 (4K UHD)", "3840x2160")
        self.cb_display_res.addItem("1366x768 (Portables standard)", "1366x768")
        self.cb_display_res.addItem("1280x720 (720p HD)", "1280x720")
        self.cb_display_res.addItem("1024x768 (Résolution héritée)", "1024x768")
        res_box.addWidget(res_lbl)
        res_box.addWidget(self.cb_display_res)
        res_box.addStretch()
        files_layout.addLayout(res_box)
        layout.addWidget(grp_files)

        # 3. Groupe Pilotes Matériels Additionnels
        grp_drivers = QGroupBox("Pilotes Matériels Additionnels (.INF / Drivers Réseau, WiFi, NVMe, GPU)")
        drivers_layout = QVBoxLayout(grp_drivers)
        drivers_layout.setSpacing(8)

        vmd_lbl = QLabel("Pilotes Intel RST / VMD (Détection SSD NVMe PC récents Intel 11e-14e gén) :")
        vmd_lbl.setStyleSheet("color: #00d2ff; font-weight: bold; font-size: 12px;")
        drivers_layout.addWidget(vmd_lbl)
        vmd_box = QHBoxLayout()
        self.txt_intel_vmd = QLineEdit()
        self.txt_intel_vmd.setPlaceholderText("Dossier contenant iaStorVD.inf / Intel RST...")
        btn_browse_vmd = QPushButton("📁 Parcourir VMD...")
        btn_browse_vmd.clicked.connect(self._browse_vmd_dir)
        vmd_box.addWidget(self.txt_intel_vmd)
        vmd_box.addWidget(btn_browse_vmd)
        drivers_layout.addLayout(vmd_box)

        lbl_drv_info = QLabel("Répertoires de pilotes additionnels injectés récursivement dans l'image système :")
        lbl_drv_info.setStyleSheet("color: #8b9bb4; font-size: 11px;")
        drivers_layout.addWidget(lbl_drv_info)

        self.list_drivers = QListWidget()
        self.list_drivers.setMaximumHeight(80)
        drivers_layout.addWidget(self.list_drivers)

        drv_btn_box = QHBoxLayout()
        btn_add_drv = QPushButton("➕ Ajouter Dossier de Pilotes...")
        btn_add_drv.clicked.connect(self._add_driver_dir)
        btn_del_drv = QPushButton("❌ Retirer Dossier")
        btn_del_drv.clicked.connect(self._remove_driver_dir)
        drv_btn_box.addWidget(btn_add_drv)
        drv_btn_box.addWidget(btn_del_drv)
        drv_btn_box.addStretch()
        drivers_layout.addLayout(drv_btn_box)

        self.chk_inject_winre = QCheckBox("🛡️ Injecter les pilotes critiques (NVMe / Réseau) dans WinRE (Environnement de Récupération)")
        self.chk_inject_winre.setStyleSheet("color: #00e676; font-weight: bold;")
        self.chk_inject_winre.setChecked(True)
        drivers_layout.addWidget(self.chk_inject_winre)

        layout.addWidget(grp_drivers)

        # Détails du Profil sélectionné
        grp_summary = QGroupBox("Description & Métadonnées du Profil")
        sum_layout = QVBoxLayout(grp_summary)
        self.lbl_profile_desc = QLabel()
        self.lbl_profile_desc.setWordWrap(True)
        self.lbl_profile_desc.setStyleSheet("color: #cbd5e1;")
        sum_layout.addWidget(self.lbl_profile_desc)
        layout.addWidget(grp_summary)

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    def _update_disk_space_label(self, path_str: str):
        if not path_str or len(path_str) < 3:
            self.lbl_disk_space.setText("Espace disque disponible : Spécifiez un chemin valide")
            return
        try:
            drive_root = os.path.splitdrive(path_str)[0] + "\\"
            if os.path.exists(drive_root):
                total, used, free = shutil.disk_usage(drive_root)
                free_gb = free / (1024 ** 3)
                color = "#00e676" if free_gb >= 15 else "#ffab00"
                self.lbl_disk_space.setText(
                    f"Espace libre sur <b>{drive_root}</b> : "
                    f"<span style='color:{color}; font-weight:bold;'>{free_gb:.1f} Go libres</span> "
                    f"(Minimum recommandé : 15 Go)"
                )
            else:
                self.lbl_disk_space.setText(f"Lecteur cible introuvable : {drive_root}")
        except Exception:
            pass

    # --- Onglet 2 : Tweaks & Optimisations OS (Refonte Majeure Ergonomique) ---
    def _create_tweaks_tab(self) -> QWidget:
        main_container = QWidget()
        vbox = QVBoxLayout(main_container)
        vbox.setContentsMargins(14, 14, 14, 14)
        vbox.setSpacing(12)

        # Barre d'outils supérieure des Tweaks (Recherche + Presets rapides)
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.txt_tweak_search = QLineEdit()
        self.txt_tweak_search.setPlaceholderText("🔍 Filtrer les tweaks en direct (ex: bitlocker, ram, dark, nagle, nvme, taskbar...)")
        self.txt_tweak_search.textChanged.connect(self._filter_tweaks)
        self.txt_tweak_search.setClearButtonEnabled(True)
        toolbar.addWidget(self.txt_tweak_search, stretch=3)

        btn_preset_recom = QPushButton("✨ Tout Recommander")
        btn_preset_recom.setToolTip("Active les tweaks éprouvés et stables pour un système ultra-rapide")
        btn_preset_recom.clicked.connect(self._apply_preset_recommended)
        toolbar.addWidget(btn_preset_recom)

        btn_preset_gaming = QPushButton("🎮 Esport / Gaming")
        btn_preset_gaming.setToolTip("Active le verrouillage kernel en RAM, Nagle off, MMCSS, HAGS et GameDVR off")
        btn_preset_gaming.clicked.connect(self._apply_preset_gaming)
        toolbar.addWidget(btn_preset_gaming)

        btn_clear_tweaks = QPushButton("🧹 Tout Décocher")
        btn_clear_tweaks.clicked.connect(self._clear_all_tweaks)
        toolbar.addWidget(btn_clear_tweaks)

        vbox.addLayout(toolbar)

        # Sous-onglets thématiques pour une lisibilité maximale
        self.tweak_tabs = QTabWidget()
        self.tweak_tabs.setObjectName("SubTabs")

        self.tweak_tabs.addTab(self._create_subtab_win11(), "🛡️ Windows 11 / 24H2")
        self.tweak_tabs.addTab(self._create_subtab_performance(), "⚡ Performances & Noyau")
        self.tweak_tabs.addTab(self._create_subtab_explorer(), "🖥️ Explorateur & UI")
        self.tweak_tabs.addTab(self._create_subtab_services(), "🔧 Services & Vie Privée")
        self.tweak_tabs.addTab(self._create_subtab_components(), "📦 Débloat & Runtimes")
        self.tweak_tabs.addTab(self._create_subtab_oem(), "🏷️ OEM & Matériel")
        self.tweak_tabs.addTab(self._create_subtab_unattended(), "⚙️ Déploiement Zéro-Clic")

        vbox.addWidget(self.tweak_tabs)
        return main_container

    def _register_chk(self, chk: QCheckBox) -> QCheckBox:
        """Enregistre la checkbox dans le registre pour le filtre de recherche dynamique."""
        self.all_tweak_checkboxes.append(chk)
        return chk

    def _filter_tweaks(self, query: str):
        query = query.strip().lower()
        for chk in self.all_tweak_checkboxes:
            if not query:
                chk.setVisible(True)
                chk.setStyleSheet("")
            else:
                matches = query in chk.text().lower()
                chk.setVisible(matches)
                if matches:
                    chk.setStyleSheet("color: #00d2ff; font-weight: bold;")
                else:
                    chk.setStyleSheet("")

    def _create_subtab_win11(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(14, 14, 14, 14)
        l.setSpacing(12)

        grp_hw = QGroupBox("Contournements Matériels Windows 11 (Bypass Checks)")
        hw_layout = QVBoxLayout(grp_hw)
        self.chk_w11_tpm = self._register_chk(QCheckBox("Bypass TPM 2.0 (BypassTPMCheck)"))
        self.chk_w11_secureboot = self._register_chk(QCheckBox("Bypass Secure Boot (BypassSecureBootCheck)"))
        self.chk_w11_ram = self._register_chk(QCheckBox("Bypass restriction 4 Go RAM (BypassRAMCheck)"))
        self.chk_w11_cpu = self._register_chk(QCheckBox("Bypass processeur non supporté (BypassCPUCheck)"))
        self.chk_w11_storage = self._register_chk(QCheckBox("Bypass stockage minimum (BypassStorageCheck)"))
        self.chk_w11_nro = self._register_chk(QCheckBox("Bypass Compte Microsoft en ligne obligatoire (BypassNRO / Forcer compte local)"))

        for c in (self.chk_w11_tpm, self.chk_w11_secureboot, self.chk_w11_ram, self.chk_w11_cpu, self.chk_w11_storage, self.chk_w11_nro):
            hw_layout.addWidget(c)
        l.addWidget(grp_hw)

        grp_24h2 = QGroupBox("Ajustements Spécifiques Windows 11 24H2")
        l24 = QVBoxLayout(grp_24h2)
        self.chk_w11_prevent_bitlocker = self._register_chk(QCheckBox("Neutraliser le chiffrement automatique forcé BitLocker (PreventDeviceEncryption=1)"))
        self.chk_w11_prevent_bitlocker.setStyleSheet("color: #ffab00; font-weight: bold;")
        self.chk_w11_disable_onedrive = self._register_chk(QCheckBox("Bloquer l'auto-installation de OneDrive et retirer son icône de l'Explorateur"))
        self.chk_w11_taskbar_left = self._register_chk(QCheckBox("Aligner le menu Démarrer et la barre des tâches à gauche (style ergonomique classique)"))
        self.chk_w11_disable_chat = self._register_chk(QCheckBox("Masquer l'icône Chat / Microsoft Teams de la barre des tâches"))
        self.chk_w11_disable_oobe_nag = self._register_chk(QCheckBox("Désactiver l'écran de harcèlement OOBE post-installation ('Finissons de configurer votre appareil')"))
        self.chk_w11_disable_lockscreen_tips = self._register_chk(QCheckBox("Désactiver les astuces Bing et bannières publicitaires sur l'écran de verrouillage"))
        self.chk_w11_context = self._register_chk(QCheckBox("Restaurer le menu contextuel classique complet de Windows 10/7 (Sans 'Afficher plus d'options')"))
        self.chk_w11_copilot = self._register_chk(QCheckBox("Désactiver définitivement Windows Copilot et Recall"))
        self.chk_w11_widgets = self._register_chk(QCheckBox("Désactiver les Widgets et le flux d'actualités"))
        self.chk_w11_ad_id = self._register_chk(QCheckBox("Désactiver l'identifiant publicitaire (Advertising ID) et le profilage utilisateur"))

        for c in (self.chk_w11_prevent_bitlocker, self.chk_w11_disable_onedrive, self.chk_w11_taskbar_left,
                  self.chk_w11_disable_chat, self.chk_w11_disable_oobe_nag, self.chk_w11_disable_lockscreen_tips,
                  self.chk_w11_context, self.chk_w11_copilot, self.chk_w11_widgets, self.chk_w11_ad_id):
            l24.addWidget(c)
        l.addWidget(grp_24h2)

        l.addStretch()
        scroll.setWidget(w)
        return scroll

    def _create_subtab_performance(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(14, 14, 14, 14)
        l.setSpacing(12)

        grp_mem = QGroupBox("Gestion du Noyau Système & Mémoire Physique RAM")
        mem_layout = QVBoxLayout(grp_mem)
        self.chk_mem_paging = self._register_chk(QCheckBox("Verrouiller le noyau Windows et les pilotes en RAM physique (DisablePagingExecutive=1)"))
        self.chk_mem_paging.setStyleSheet("color: #38ef7d; font-weight: bold;")
        self.chk_mem_paging.setToolTip("Empêche le swap sur disque du kernel : élimine les micro-stutters et la latence DPC sur PC modernes")
        self.chk_gaming = self._register_chk(QCheckBox("Optimisations Gaming globales (GameDVR off, NetworkThrottlingIndex désactivé)"))
        self.chk_mmcss = self._register_chk(QCheckBox("Priorité 100% aux jeux & multimédia en temps réel (MMCSS SystemResponsiveness = 0)"))
        self.chk_cpu_quantum = self._register_chk(QCheckBox("Prioriser le processus actif de premier plan (Win32PrioritySeparation = 38)"))
        self.chk_hpet_synthetic = self._register_chk(QCheckBox("Optimiser la réactivité des timers multimédia gaming (réduit les saccades)"))
        
        for c in (self.chk_mem_paging, self.chk_gaming, self.chk_mmcss, self.chk_cpu_quantum, self.chk_hpet_synthetic):
            mem_layout.addWidget(c)
        l.addWidget(grp_mem)

        grp_hw_opt = QGroupBox("Matériel, Réseau & Disque SSD")
        hw_layout = QVBoxLayout(grp_hw_opt)
        self.chk_nagle = self._register_chk(QCheckBox("Désactiver l'algorithme de Nagle (TcpAckFrequency / TCPNoDelay - Ping minimal en ligne)"))
        self.chk_hags = self._register_chk(QCheckBox("Activer Hardware Accelerated GPU Scheduling (HAGS) pour cartes graphiques modernes"))
        self.chk_ultimate_perf = self._register_chk(QCheckBox("Débloquer le profil d'alimentation caché 'Performances Ultimes' (Ultimate Performance)"))
        self.chk_ntfs_trim = self._register_chk(QCheckBox("Forcer l'activation du TRIM SSD et désactiver l'horodatage NTFS superflu"))
        self.chk_reserved_storage = self._register_chk(QCheckBox("Désactiver l'espace réservé Windows Update (~7 Go récupérés immédiatement)"))
        self.chk_edge_prelaunch = self._register_chk(QCheckBox("Désactiver le pré-lancement en tâche de fond de Microsoft Edge"))
        self.chk_edge_telemetry = self._register_chk(QCheckBox("Désactiver la télémétrie, suggestions d'achats et annonces Microsoft Edge"))
        self.chk_defender_gaming = self._register_chk(QCheckBox("Optimiser Windows Defender pour le Gaming (Exclusions C:\\Games et D:\\Games)"))
        self.chk_defender_gaming.setStyleSheet("color: #00e676; font-weight: bold;")

        dns_box = QHBoxLayout()
        dns_lbl = QLabel("Profil DNS Gaming & Latence :")
        self.cb_dns_preset = QComboBox()
        self.cb_dns_preset.addItem("Par défaut (FAI / DHCP)", "")
        self.cb_dns_preset.addItem("Cloudflare (1.1.1.1 / 1.0.0.1) — Latence minimale", "cloudflare")
        self.cb_dns_preset.addItem("Google Public DNS (8.8.8.8 / 8.8.4.4)", "google")
        self.cb_dns_preset.addItem("Quad9 (9.9.9.9) — Sécurité & Filtrage malware", "quad9")
        self.cb_dns_preset.addItem("AdGuard DNS — Bloqueur de publicités intégré", "adguard")
        dns_box.addWidget(dns_lbl)
        dns_box.addWidget(self.cb_dns_preset)

        for c in (self.chk_nagle, self.chk_hags, self.chk_ultimate_perf, self.chk_ntfs_trim,
                  self.chk_reserved_storage, self.chk_edge_prelaunch, self.chk_edge_telemetry,
                  self.chk_smartscreen, self.chk_defender_gaming):
            hw_layout.addWidget(c)
        hw_layout.addLayout(dns_box)
        l.addWidget(grp_hw_opt)

        l.addStretch()
        scroll.setWidget(w)
        return scroll

    def _create_subtab_explorer(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(14, 14, 14, 14)
        l.setSpacing(12)

        grp_exp = QGroupBox("Affichage & Comportement de l'Explorateur de Fichiers")
        el = QVBoxLayout(grp_exp)
        self.chk_dark_mode = self._register_chk(QCheckBox("Activer le Mode Sombre universel par défaut (Système et Applications)"))
        self.chk_show_ext = self._register_chk(QCheckBox("Toujours afficher les extensions de fichiers connues (.exe, .iso, .txt...)"))
        self.chk_show_hidden = self._register_chk(QCheckBox("Afficher les fichiers et dossiers cachés"))
        self.chk_open_this_pc = self._register_chk(QCheckBox("Ouvrir l'Explorateur sur 'Ce PC' par défaut plutôt que 'Accès Rapide'"))
        self.chk_hide_3d_objects = self._register_chk(QCheckBox("Masquer le dossier 'Objets 3D' dans Ce PC"))
        self.chk_disable_web_search = self._register_chk(QCheckBox("Désactiver la recherche web Bing dans le menu Démarrer (Recherche locale instantanée à 0ms)"))

        for c in (self.chk_dark_mode, self.chk_show_ext, self.chk_show_hidden, self.chk_open_this_pc, self.chk_hide_3d_objects, self.chk_disable_web_search):
            el.addWidget(c)
        l.addWidget(grp_exp)

        grp_ctx = QGroupBox("Extensions du Menu Contextuel Bureau & Fichiers")
        cl = QVBoxLayout(grp_ctx)
        self.chk_take_ownership = self._register_chk(QCheckBox("Ajouter 'Prendre possession' (Take Ownership) sur les fichiers protégés"))
        self.chk_restart_explorer = self._register_chk(QCheckBox("Ajouter 'Redémarrer l'Explorateur' au menu contextuel du Bureau"))
        self.chk_open_notepad = self._register_chk(QCheckBox("Ajouter 'Ouvrir avec le Bloc-notes' au menu contextuel de tous les fichiers"))
        self.chk_cmd_admin = self._register_chk(QCheckBox("Ajouter 'Invite de commandes Administrateur ici' au menu contextuel des dossiers"))
        self.chk_powershell_admin = self._register_chk(QCheckBox("Ajouter 'Ouvrir avec PowerShell (Admin)' au menu contextuel des dossiers"))
        self.chk_compact_os = self._register_chk(QCheckBox("Ajouter 'Compacter le dossier (CompactOS LZX)' au menu contextuel"))

        for c in (self.chk_take_ownership, self.chk_restart_explorer, self.chk_open_notepad,
                  self.chk_cmd_admin, self.chk_powershell_admin, self.chk_compact_os):
            cl.addWidget(c)
        l.addWidget(grp_ctx)

        grp_mados = QGroupBox("⚡ Thème Signature MadOS (LordMadTrix Special Edition)")
        ml = QVBoxLayout(grp_mados)
        self.chk_mados_theme = self._register_chk(QCheckBox("Activer le Thème Windows Style MadOS (Dark mode total, accent néon cyan/ultraviolet, réactivité 0ms)"))
        self.chk_mados_theme.setStyleSheet("color: #00f0ff; font-weight: bold;")
        self.chk_mados_theme.setToolTip("Applique le look signature MadOS à Windows : DWM AccentColor #00f0ff, barres de titre colorées, MenuShowDelay=0")
        ml.addWidget(self.chk_mados_theme)
        l.addWidget(grp_mados)

        l.addStretch()
        scroll.setWidget(w)
        return scroll

    def _create_subtab_services(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(14, 14, 14, 14)
        l.setSpacing(12)

        grp_srv = QGroupBox("Services Windows à Optimiser / Désactiver")
        sl = QVBoxLayout(grp_srv)
        self.chk_telemetry = self._register_chk(QCheckBox("Neutraliser la télémétrie Windows & service DiagTrack"))
        self.chk_srv_telemetry_tasks = self._register_chk(QCheckBox("Neutraliser les tâches planifiées de télémétrie (Microsoft Compatibility Appraiser...)"))
        self.chk_srv_sysmain = self._register_chk(QCheckBox("Désactiver SysMain / Superfetch (Fortement recommandé pour SSD NVMe/SATA)"))
        self.chk_srv_indexing = self._register_chk(QCheckBox("Désactiver Windows Search (Indexation permanente en arrière-plan)"))
        self.chk_srv_spooler = self._register_chk(QCheckBox("Désactiver le Spouleur d'impression (si aucun usage d'imprimante)"))
        self.chk_srv_wer = self._register_chk(QCheckBox("Désactiver le service de rapport d'erreurs (WerSvc)"))
        self.chk_fast_startup = self._register_chk(QCheckBox("Désactiver Fast Startup & Hibernation (Supprime hiberfil.sys et libère sa taille en RAM)"))
        self.chk_srv_wu_reboot = self._register_chk(QCheckBox("Empêcher les redémarrages intempestifs forcés de Windows Update"))
        self.chk_srv_dosvc = self._register_chk(QCheckBox("Désactiver le service Delivery Optimization P2P (DoSvc)"))
        self.chk_auto_maintenance = self._register_chk(QCheckBox("Neutraliser la maintenance automatique Windows (évite les réveils et saturations disque)"))

        for c in (self.chk_telemetry, self.chk_srv_telemetry_tasks, self.chk_srv_sysmain, self.chk_srv_indexing,
                  self.chk_srv_spooler, self.chk_srv_wer, self.chk_fast_startup, self.chk_srv_wu_reboot,
                  self.chk_srv_dosvc, self.chk_auto_maintenance):
            sl.addWidget(c)
        l.addWidget(grp_srv)

        l.addStretch()
        scroll.setWidget(w)
        return scroll

    def _create_subtab_components(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(14, 14, 14, 14)
        l.setSpacing(12)

        # Nettoyage WinSxS & Debloat AppX
        grp_deb = QGroupBox("Nettoyage WinSxS & Suppression des Bloatwares AppX")
        self.chk_cleanup_store = self._register_chk(QCheckBox("Nettoyer et compresser le magasin WinSxS (/StartComponentCleanup /ResetBase - Gain 1-3 Go)"))
        self.chk_cleanup_store.setStyleSheet("color: #00e676; font-weight: bold;")
        self.chk_optimize_wim = self._register_chk(QCheckBox("Recompression & défragmentation WIM (Reclaim des clusters orphelins)"))
        self.chk_optimize_wim.setChecked(True)
        self.chk_debloat_appx = self._register_chk(QCheckBox("Supprimer les applications préinstallées UWP (Xbox, Bing, Cortana, Clipchamp...)"))

        preset_box = QHBoxLayout()
        preset_lbl = QLabel("Profil de Debloat AppX :")
        self.cb_appx_preset = QComboBox()
        self.cb_appx_preset.addItem("Aucun (Liste personnalisée)", "none")
        self.cb_appx_preset.addItem("Léger (Promotions & Outils obsolètes)", "light")
        self.cb_appx_preset.addItem("Recommandé (Debloat équilibré préservant le Store)", "recommended")
        self.cb_appx_preset.addItem("Agressif (Nettoyage SuperLite complet)", "aggressive")
        preset_box.addWidget(preset_lbl)
        preset_box.addWidget(self.cb_appx_preset)

        dl.addWidget(self.chk_cleanup_store)
        dl.addWidget(self.chk_optimize_wim)
        dl.addWidget(self.chk_debloat_appx)
        dl.addLayout(preset_box)
        l.addWidget(grp_deb)

        # Runtimes & Fonctionnalités
        grp_feat = QGroupBox("Fonctionnalités & Runtimes Essentiels")
        fl = QVBoxLayout(grp_feat)
        self.chk_net35 = self._register_chk(QCheckBox("Pré-activer .NET Framework 3.5 hors-ligne (sources\\sxs)"))
        self.chk_directplay = self._register_chk(QCheckBox("Activer DirectPlay (Jeux vidéo rétro / DirectX 9)"))
        self.chk_vcredist = self._register_chk(QCheckBox("Installer les Runtimes Visual C++ All-In-One (2005-2022) au 1er boot"))
        self.chk_hwid_act = self._register_chk(QCheckBox("Activer Windows définitivement et automatiquement via licence numérique HWID (Massgrave)"))
        self.chk_hwid_act.setStyleSheet("color: #00e676; font-weight: bold;")

        feat_preset_box = QHBoxLayout()
        feat_preset_lbl = QLabel("Profil de Fonctionnalités & Capacités (FOD) :")
        self.cb_features_preset = QComboBox()
        self.cb_features_preset.addItem("Par défaut (Personnalisé)", "")
        self.cb_features_preset.addItem("🎮 Gaming & Performance (DirectPlay, NetFx3, FOD épurés)", "gaming")
        self.cb_features_preset.addItem("💻 Développeur & DevOps (WSL, Hyper-V, Sandbox, SSH)", "developer")
        self.cb_features_preset.addItem("🛡️ Durcissement Sécurité (Sandbox, SMB1/Telnet désactivés)", "hardened")
        self.cb_features_preset.addItem("⚡ Ultra-Lite (Suppression maximale des capacités)", "superlite")
        feat_preset_box.addWidget(feat_preset_lbl)
        feat_preset_box.addWidget(self.cb_features_preset)

        for c in (self.chk_net35, self.chk_directplay, self.chk_vcredist, self.chk_hwid_act):
            fl.addWidget(c)
        fl.addLayout(feat_preset_box)
        l.addWidget(grp_feat)

        # Applications Post-Installation
        grp_apps = QGroupBox("Installation Silencieuse d'Applications (WinGet)")
        apps_layout = QGridLayout(grp_apps)
        apps_layout.setSpacing(8)
        self.chk_app_7zip = QCheckBox("7-Zip")
        self.chk_app_chrome = QCheckBox("Google Chrome")
        self.chk_app_firefox = QCheckBox("Mozilla Firefox")
        self.chk_app_vlc = QCheckBox("VLC Media Player")
        self.chk_app_steam = QCheckBox("Steam")
        self.chk_app_discord = QCheckBox("Discord")
        self.chk_app_notepad = QCheckBox("Notepad++")

        apps_layout.addWidget(self.chk_app_7zip, 0, 0)
        apps_layout.addWidget(self.chk_app_chrome, 0, 1)
        apps_layout.addWidget(self.chk_app_firefox, 0, 2)
        apps_layout.addWidget(self.chk_app_vlc, 1, 0)
        apps_layout.addWidget(self.chk_app_steam, 1, 1)
        apps_layout.addWidget(self.chk_app_discord, 1, 2)
        apps_layout.addWidget(self.chk_app_notepad, 2, 0)

        lbl_custom_apps = QLabel("Packages WinGet additionnels (séparés par des virgules) :")
        lbl_custom_apps.setStyleSheet("color: #8b9bb4; font-size: 11px;")
        apps_layout.addWidget(lbl_custom_apps, 3, 0, 1, 3)

        self.txt_custom_winget = QLineEdit()
        self.txt_custom_winget.setPlaceholderText("Ex: Git.Git, Spotify.Spotify, Microsoft.VisualStudioCode, Obsidian.Obsidian")
        apps_layout.addWidget(self.txt_custom_winget, 4, 0, 1, 3)
        l.addWidget(grp_apps)

        l.addStretch()
        scroll.setWidget(w)
        return scroll

    def _create_subtab_oem(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(14, 14, 14, 14)
        l.setSpacing(12)

        # Drivers Machine Hôte & Windows 7
        grp_drv = QGroupBox("Pilotes Système Spécifiques")
        drl = QVBoxLayout(grp_drv)
        self.chk_auto_host_drivers = self._register_chk(QCheckBox("Capturer et injecter automatiquement les pilotes réseau (Wi-Fi/LAN) de cette machine hôte"))
        self.chk_auto_host_drivers.setStyleSheet("color: #00d2ff; font-weight: bold;")
        self.chk_w7_nvme = self._register_chk(QCheckBox("Windows 7 : Injecter les pilotes NVMe génériques (boot.wim & install.wim)"))
        self.chk_w7_usb3 = self._register_chk(QCheckBox("Windows 7 : Injecter les pilotes xHCI USB 3.0 / 3.1 (boot.wim & install.wim)"))

        drl.addWidget(self.chk_auto_host_drivers)
        drl.addWidget(self.chk_w7_nvme)
        drl.addWidget(self.chk_w7_usb3)
        l.addWidget(grp_drv)

        # Branding OEM Constructeur
        grp_oem = QGroupBox("Personnalisation OEM & Branding Constructeur")
        oem_layout = QVBoxLayout(grp_oem)
        self.chk_oem_enabled = self._register_chk(QCheckBox("Activer les métadonnées et le branding constructeur OEM"))
        self.chk_oem_enabled.setStyleSheet("color: #00d2ff; font-weight: bold;")
        oem_layout.addWidget(self.chk_oem_enabled)

        oem_grid = QGridLayout()
        oem_grid.addWidget(QLabel("Fabricant / Constructeur :"), 0, 0)
        self.txt_oem_manufacturer = QLineEdit("LordMadTrix Custom Rig")
        oem_grid.addWidget(self.txt_oem_manufacturer, 0, 1)

        oem_grid.addWidget(QLabel("Modèle de machine :"), 0, 2)
        self.txt_oem_model = QLineEdit("OSBuilder-Win Gaming Edition")
        oem_grid.addWidget(self.txt_oem_model, 0, 3)

        oem_grid.addWidget(QLabel("Lien Web Support :"), 1, 0)
        self.txt_oem_support_url = QLineEdit("https://github.com/LordMadTrix")
        oem_grid.addWidget(self.txt_oem_support_url, 1, 1)

        oem_grid.addWidget(QLabel("Heures de support :"), 1, 2)
        self.txt_oem_support_hours = QLineEdit("24/7")
        oem_grid.addWidget(self.txt_oem_support_hours, 1, 3)

        oem_grid.addWidget(QLabel("Logo OEM (.bmp 120x120) :"), 2, 0)
        oem_logo_box = QHBoxLayout()
        self.txt_oem_logo = QLineEdit()
        self.txt_oem_logo.setPlaceholderText("Optionnel (Chemin vers oemlogo.bmp)")
        btn_browse_logo = QPushButton("📁 Logo...")
        btn_browse_logo.clicked.connect(self._browse_oem_logo)
        oem_logo_box.addWidget(self.txt_oem_logo)
        oem_logo_box.addWidget(btn_browse_logo)
        oem_grid.addLayout(oem_logo_box, 2, 1)

        oem_grid.addWidget(QLabel("Fond d'écran personnalisé (.jpg) :"), 2, 2)
        oem_wall_box = QHBoxLayout()
        self.txt_oem_wallpaper = QLineEdit()
        self.txt_oem_wallpaper.setPlaceholderText("Optionnel (Remplace img0.jpg par défaut)")
        btn_browse_wall = QPushButton("📁 Fond...")
        btn_browse_wall.clicked.connect(self._browse_oem_wallpaper)
        oem_wall_box.addWidget(self.txt_oem_wallpaper)
        oem_wall_box.addWidget(btn_browse_wall)
        oem_grid.addLayout(oem_wall_box, 2, 3)

        oem_layout.addLayout(oem_grid)
        l.addWidget(grp_oem)

        l.addStretch()
        scroll.setWidget(w)
        return scroll

    def _create_subtab_unattended(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(14, 14, 14, 14)
        l.setSpacing(12)

        grp_creds = QGroupBox("Configuration autounattend.xml (Installation Zéro-Clic)")
        creds_layout = QGridLayout(grp_creds)
        creds_layout.setSpacing(10)

        self.chk_unattended = self._register_chk(QCheckBox("Activer l'automatisation totale (autounattend.xml - Contourne l'OOBE)"))
        self.chk_unattended.setStyleSheet("color: #00d2ff; font-weight: bold;")
        creds_layout.addWidget(self.chk_unattended, 0, 0, 1, 2)

        lbl_loc = QLabel("Langue, Fuseau & Clavier :")
        self.cb_locales = QComboBox()
        for loc_name in SUPPORTED_LOCALES.keys():
            self.cb_locales.addItem(loc_name)
        creds_layout.addWidget(lbl_loc, 1, 0)
        creds_layout.addWidget(self.cb_locales, 1, 1)

        lbl_user = QLabel("Nom du compte Administrateur local :")
        self.txt_admin_user = QLineEdit("Administrateur")
        creds_layout.addWidget(lbl_user, 2, 0)
        creds_layout.addWidget(self.txt_admin_user, 2, 1)

        lbl_pc = QLabel("Nom de l'ordinateur (ComputerName) :")
        self.txt_computer_name = QLineEdit("LORDMADTRIX-PC")
        creds_layout.addWidget(lbl_pc, 3, 0)
        creds_layout.addWidget(self.txt_computer_name, 3, 1)

        lbl_key = QLabel("Clé de produit Windows (Optionnel) :")
        self.txt_product_key = QLineEdit()
        self.txt_product_key.setPlaceholderText("Laisser vide pour utiliser la clé générique automatique")
        creds_layout.addWidget(lbl_key, 4, 0)
        creds_layout.addWidget(self.txt_product_key, 4, 1)

        self.chk_auto_partition = self._register_chk(QCheckBox("Mode Zéro-Clic : Partitionner et formater automatiquement en GPT/UEFI (Disque 0)"))
        self.chk_auto_partition.setStyleSheet("color: #ffab00; font-weight: bold;")
        creds_layout.addWidget(self.chk_auto_partition, 5, 0, 1, 2)

        self.chk_builtin_admin = self._register_chk(QCheckBox("Activer directement le compte Administrateur natif (au lieu de créer un compte)"))
        creds_layout.addWidget(self.chk_builtin_admin, 6, 0, 1, 2)

        self.chk_split_fat32 = self._register_chk(QCheckBox("Découper install.wim en fichiers .swm (< 4 Go pour clé USB FAT32 / UEFI)"))
        creds_layout.addWidget(self.chk_split_fat32, 7, 0, 1, 2)

        self.btn_preview_xml = QPushButton("👁️ Prévisualiser autounattend.xml en direct")
        self.btn_preview_xml.setObjectName("PrimaryBtn")
        self.btn_preview_xml.clicked.connect(self._preview_unattend_xml)
        creds_layout.addWidget(self.btn_preview_xml, 8, 0, 1, 2)

        l.addWidget(grp_creds)

        # Commandes SetupComplete.cmd
        grp_setup_complete = QGroupBox("Commandes SetupComplete.cmd (Exécutées en NT AUTHORITY\\SYSTEM avant le 1er login)")
        sc_layout = QVBoxLayout(grp_setup_complete)
        sc_desc = QLabel("Commandes batch exécutées avec privilèges SYSTEM maximum à la fin de l'installation, avant l'OOBE :")
        sc_desc.setStyleSheet("color: #8b9bb4; font-size: 11px;")
        sc_layout.addWidget(sc_desc)
        self.txt_setup_complete = QPlainTextEdit()
        self.txt_setup_complete.setPlaceholderText("Exemple :\r\nnet stop wuauserv\r\nbcdedit /set {default} bootmenupolicy legacy")
        self.txt_setup_complete.setMaximumHeight(85)
        sc_layout.addWidget(self.txt_setup_complete)

        btn_open_custom_scripts = QPushButton("📁 Ouvrir le dossier des scripts personnalisés (custom_scripts/)")
        btn_open_custom_scripts.setToolTip("Ouvre le dossier custom_scripts/ pour y déposer vos propres scripts (.cmd, .bat, .ps1) injectés automatiquement")
        btn_open_custom_scripts.clicked.connect(lambda: os.startfile(Path(__file__).resolve().parent / "custom_scripts"))
        sc_layout.addWidget(btn_open_custom_scripts)

        l.addWidget(grp_setup_complete)

        l.addStretch()
        scroll.setWidget(w)
        return scroll

    # --- Presets Rapides ---
    def _apply_preset_recommended(self):
        """Active la configuration recommandée équilibrée et moderne."""
        self.chk_w11_tpm.setChecked(True)
        self.chk_w11_secureboot.setChecked(True)
        self.chk_w11_ram.setChecked(True)
        self.chk_w11_cpu.setChecked(True)
        self.chk_w11_storage.setChecked(True)
        self.chk_w11_nro.setChecked(True)
        self.chk_w11_prevent_bitlocker.setChecked(True)
        self.chk_w11_disable_onedrive.setChecked(True)
        self.chk_w11_taskbar_left.setChecked(True)
        self.chk_w11_disable_chat.setChecked(True)
        self.chk_w11_disable_oobe_nag.setChecked(True)
        self.chk_w11_disable_lockscreen_tips.setChecked(True)
        self.chk_w11_context.setChecked(True)
        self.chk_w11_copilot.setChecked(True)
        self.chk_w11_widgets.setChecked(True)
        self.chk_w11_ad_id.setChecked(True)

        self.chk_mem_paging.setChecked(True)
        self.chk_gaming.setChecked(True)
        self.chk_mmcss.setChecked(True)
        self.chk_cpu_quantum.setChecked(True)
        self.chk_hpet_synthetic.setChecked(True)
        self.chk_nagle.setChecked(True)
        self.chk_hags.setChecked(True)
        self.chk_ultimate_perf.setChecked(True)
        self.chk_ntfs_trim.setChecked(True)
        self.chk_reserved_storage.setChecked(True)
        self.chk_edge_prelaunch.setChecked(True)
        self.chk_edge_telemetry.setChecked(True)

        self.chk_dark_mode.setChecked(True)
        self.chk_show_ext.setChecked(True)
        self.chk_show_hidden.setChecked(True)
        self.chk_open_this_pc.setChecked(True)
        self.chk_hide_3d_objects.setChecked(True)
        self.chk_disable_web_search.setChecked(True)
        self.chk_mados_theme.setChecked(True)

        self.chk_telemetry.setChecked(True)
        self.chk_srv_telemetry_tasks.setChecked(True)
        self.chk_srv_sysmain.setChecked(True)
        self.chk_srv_wer.setChecked(True)
        self.chk_fast_startup.setChecked(True)
        self.chk_srv_wu_reboot.setChecked(True)
        self.chk_srv_dosvc.setChecked(True)

        self.chk_cleanup_store.setChecked(True)
        self.chk_debloat_appx.setChecked(True)
        self.chk_net35.setChecked(True)
        self.chk_directplay.setChecked(True)
        self.chk_vcredist.setChecked(True)
        self.chk_hwid_act.setChecked(True)
        self.status_lbl.setText("Preset Recommandé appliqué avec succès.")

    def _apply_preset_gaming(self):
        """Active toutes les optimisations de latence pour le gaming de compétition."""
        self._apply_preset_recommended()
        self.chk_srv_indexing.setChecked(True)
        self.chk_srv_spooler.setChecked(True)
        self.chk_smartscreen.setChecked(True)
        self.chk_app_steam.setChecked(True)
        self.chk_app_discord.setChecked(True)
        self.status_lbl.setText("Preset Esport / Gaming Ultra Latence appliqué.")

    def _clear_all_tweaks(self):
        for chk in self.all_tweak_checkboxes:
            chk.setChecked(False)
        self.status_lbl.setText("Tous les tweaks ont été désactivés.")

    # --- Onglet 3 : Créateur Clé USB Bootable ---
    def _create_usb_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        grp_iso = QGroupBox("1. Sélection de l'Image ISO à Déployer")
        iso_layout = QVBoxLayout(grp_iso)
        iso_box = QHBoxLayout()
        self.txt_usb_iso = QLineEdit()
        self.txt_usb_iso.setPlaceholderText("Chemin vers l'ISO personnalisée à flasher sur la clé USB...")
        btn_browse_usb_iso = QPushButton("📁 Parcourir...")
        btn_browse_usb_iso.clicked.connect(self._browse_usb_iso)
        btn_use_current = QPushButton("⚡ Utiliser l'ISO en sortie")
        btn_use_current.clicked.connect(lambda: self.txt_usb_iso.setText(self.txt_output_iso.text().strip()))
        iso_box.addWidget(self.txt_usb_iso)
        iso_box.addWidget(btn_browse_usb_iso)
        iso_box.addWidget(btn_use_current)
        iso_layout.addLayout(iso_box)
        layout.addWidget(grp_iso)

        grp_drive = QGroupBox("2. Lecteur Clé USB Cible")
        drive_layout = QVBoxLayout(grp_drive)
        d_box = QHBoxLayout()
        self.cb_usb_drives = QComboBox()
        btn_refresh = QPushButton("🔄 Actualiser les Lecteurs")
        btn_refresh.clicked.connect(self._refresh_usb_drives)
        d_box.addWidget(self.cb_usb_drives, stretch=3)
        d_box.addWidget(btn_refresh)
        drive_layout.addLayout(d_box)

        self.chk_format_usb = QCheckBox("Formater automatiquement en FAT32 (Compatible 100% UEFI universel)")
        self.chk_format_usb.setChecked(True)
        drive_layout.addWidget(self.chk_format_usb)

        lbl_warn = QLabel("⚠️ <b>ATTENTION :</b> Le formatage effacera l'intégralité des données présentes sur la clé sélectionnée.")
        lbl_warn.setStyleSheet("color: #ffab00; font-size: 11px;")
        drive_layout.addWidget(lbl_warn)
        layout.addWidget(grp_drive)

        grp_flash = QGroupBox("3. Gravure et Découpage Automatique")
        flash_layout = QVBoxLayout(grp_flash)
        flash_layout.setSpacing(10)
        self.usb_progress_bar = QProgressBar()
        self.usb_progress_bar.setValue(0)
        self.usb_progress_bar.setFixedHeight(22)
        self.usb_status_lbl = QLabel("Sélectionnez une ISO et une clé USB, puis cliquez sur Créer.")
        self.usb_status_lbl.setStyleSheet("color: #8b9bb4;")

        self.btn_flash_usb = QPushButton("⚡ Créer la Clé USB Bootable (UEFI / BIOS)")
        self.btn_flash_usb.setObjectName("PrimaryBtn")
        self.btn_flash_usb.setMinimumHeight(44)
        self.btn_flash_usb.clicked.connect(self._start_usb_creation)

        flash_layout.addWidget(self.btn_flash_usb)
        flash_layout.addWidget(self.usb_progress_bar)
        flash_layout.addWidget(self.usb_status_lbl)
        layout.addWidget(grp_flash)

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    # --- Onglet 4 : Sources & Intégrité ISO ---
    def _create_sources_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        grp_fido = QGroupBox("Téléchargeur Direct Officiel Microsoft (Fido / Rufus Engine)")
        fido_layout = QVBoxLayout(grp_fido)
        fido_layout.setSpacing(10)
        fido_desc = QLabel(
            "Fido est le moteur officiel utilisé par <b>Rufus</b> pour générer des liens de téléchargement "
            "<b>directs et authentiques</b> depuis les serveurs CDN de Microsoft (Windows 11, 10, 8.1)."
        )
        fido_desc.setWordWrap(True)
        fido_desc.setStyleSheet("color: #cbd5e1;")
        fido_layout.addWidget(fido_desc)

        btn_launch_fido = QPushButton("⚡ Lancer le Téléchargeur Officiel Microsoft (Fido)")
        btn_launch_fido.setObjectName("PrimaryBtn")
        btn_launch_fido.setMinimumHeight(42)
        btn_launch_fido.clicked.connect(self._launch_fido)
        fido_layout.addWidget(btn_launch_fido)
        layout.addWidget(grp_fido)

        grp_links = QGroupBox("Répertoires et Sources d'ISOs Authentiques MSDN")
        links_layout = QGridLayout(grp_links)
        links_layout.setSpacing(10)

        btn_massgrave = QPushButton("🌐 Répertoire Massgrave (MSDN)")
        btn_massgrave.setMinimumHeight(38)
        btn_massgrave.clicked.connect(lambda: webbrowser.open("https://massgrave.dev/genuine-installation-media"))
        links_layout.addWidget(btn_massgrave, 0, 0)

        btn_win7_links = QPushButton("🌐 Le Crabe Info (Win 7 SP1 FR)")
        btn_win7_links.setMinimumHeight(38)
        btn_win7_links.clicked.connect(lambda: webbrowser.open("https://lecrabeinfo.net/telecharger-les-iso-de-windows-7.html"))
        links_layout.addWidget(btn_win7_links, 0, 1)

        btn_uup = QPushButton("🌐 UUP dump (Windows Update Builds)")
        btn_uup.setMinimumHeight(38)
        btn_uup.clicked.connect(lambda: webbrowser.open("https://uupdump.net"))
        links_layout.addWidget(btn_uup, 1, 0)

        btn_adk = QPushButton("⚙️ Outils ADK (Oscdimg)")
        btn_adk.setMinimumHeight(38)
        btn_adk.clicked.connect(self._launch_adk_setup)
        links_layout.addWidget(btn_adk, 1, 1)

        btn_crabe_tools = QPushButton("🌐 Le Crabe Info (Tutoriels & Outils Windows)")
        btn_crabe_tools.setMinimumHeight(38)
        btn_crabe_tools.clicked.connect(lambda: webbrowser.open("https://lecrabeinfo.net"))
        links_layout.addWidget(btn_crabe_tools, 2, 0, 1, 2)

        layout.addWidget(grp_links)

        # Vérificateur d'empreinte SHA-1 / SHA-256 avec comparateur
        grp_hash = QGroupBox("Vérificateur d'Intégrité ISO & Comparateur de Hash Officiel")
        hash_layout = QVBoxLayout(grp_hash)
        hash_layout.setSpacing(10)

        h_box = QHBoxLayout()
        self.txt_hash_file = QLineEdit()
        self.txt_hash_file.setPlaceholderText("Sélectionnez une image ISO à vérifier...")
        btn_browse_hash = QPushButton("📁 Parcourir...")
        btn_browse_hash.clicked.connect(self._browse_hash_file)
        btn_calc = QPushButton("⚡ Calculer Empreintes")
        btn_calc.setObjectName("SuccessBtn")
        btn_calc.clicked.connect(self._start_hash_calc)
        h_box.addWidget(self.txt_hash_file)
        h_box.addWidget(btn_browse_hash)
        h_box.addWidget(btn_calc)
        hash_layout.addLayout(h_box)

        exp_box = QHBoxLayout()
        self.txt_expected_hash = QLineEdit()
        self.txt_expected_hash.setPlaceholderText("Optionnel : Collez ici le SHA-1 ou SHA-256 officiel pour vérification automatique...")
        self.txt_expected_hash.textChanged.connect(self._compare_hashes)
        exp_box.addWidget(self.txt_expected_hash)
        hash_layout.addLayout(exp_box)

        self.lbl_sha1 = QLabel("SHA-1 : En attente...")
        self.lbl_sha1.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lbl_sha256 = QLabel("SHA-256 : En attente...")
        self.lbl_sha256.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lbl_hash_match = QLabel("")
        self.lbl_hash_match.setStyleSheet("font-weight: bold; font-size: 13px;")

        hash_layout.addWidget(self.lbl_sha1)
        hash_layout.addWidget(self.lbl_sha256)
        hash_layout.addWidget(self.lbl_hash_match)

        layout.addWidget(grp_hash)
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    # --- Onglet 5 : Console de Build & Logs ---
    def _create_console_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(24)
        layout.addWidget(self.progress_bar)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        layout.addWidget(self.console_output)

        action_bar = QHBoxLayout()
        self.btn_cancel_build = QPushButton("🛑 Annuler le Build")
        self.btn_cancel_build.setObjectName("DangerBtn")
        self.btn_cancel_build.setEnabled(False)
        self.btn_cancel_build.clicked.connect(self._cancel_build)
        action_bar.addWidget(self.btn_cancel_build)

        btn_copy = QPushButton("📋 Copier les Logs")
        btn_copy.clicked.connect(self._copy_logs_to_clipboard)
        action_bar.addWidget(btn_copy)

        btn_export = QPushButton("💾 Exporter Logs (.txt)...")
        btn_export.clicked.connect(self._export_logs_to_file)
        action_bar.addWidget(btn_export)

        action_bar.addStretch()

        btn_clear = QPushButton("🧹 Effacer la console")
        btn_clear.clicked.connect(self.console_output.clear)
        action_bar.addWidget(btn_clear)
        layout.addLayout(action_bar)

        return widget

    def _copy_logs_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.console_output.toPlainText())
        self.status_lbl.setText("Logs copiés dans le presse-papier.")

    def _export_logs_to_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter les Logs de Construction",
            f"OSBuilder_Build_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            "Fichiers Logs (*.log *.txt)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.console_output.toPlainText())
                QMessageBox.information(self, "Export Réussi", f"Le journal a été enregistré dans :\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur Export", f"Impossible d'exporter les logs :\n{e}")

    def _cancel_build(self):
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Confirmation d'annulation",
                "Êtes-vous sûr de vouloir interrompre la construction ?\n\n"
                "Les modifications en cours seront annulées et l'image WIM sera démontée proprement sans corrompre votre système.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.btn_cancel_build.setEnabled(False)
                self.status_lbl.setText("Annulation en cours...")
                self.worker.cancel()

    # --- Actions Explorateur, Lanceurs & Dialogues ---
    def _launch_adk_setup(self):
        adk_path = Path(__file__).resolve().parent / "bin" / "adksetup.exe"
        if not adk_path.exists():
            webbrowser.open("https://learn.microsoft.com/en-us/windows-hardware/get-started/adk-install")
            return
        import subprocess
        # Fermer d'éventuelles instances bloquées en arrière-plan avant de relancer
        subprocess.run("taskkill /f /im adksetup.exe", shell=True, capture_output=True)
        subprocess.Popen([str(adk_path)])

    def _launch_fido(self):
        fido_path = Path(__file__).resolve().parent / "tools" / "Fido.ps1"
        if not fido_path.exists():
            QMessageBox.warning(self, "Fichier Manquant", f"Le script Fido est introuvable dans :\n{fido_path}")
            return
        cmd = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{fido_path}"'
        import subprocess
        subprocess.Popen(cmd, shell=True)

    def _browse_vmd_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Sélectionnez le dossier des pilotes Intel VMD / RST (.inf)")
        if dir_path:
            self.txt_intel_vmd.setText(dir_path)

    def _browse_updates_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Sélectionnez le dossier des paquets de mises à jour (.msu, .cab)")
        if dir_path:
            self.txt_updates_dir.setText(dir_path)

    def _browse_oem_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionnez le logo OEM (Bitmap 120x120)", "", "Images Bitmap (*.bmp)")
        if file_path:
            self.txt_oem_logo.setText(file_path)

    def _browse_oem_wallpaper(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionnez le fond d'écran personnalisé (JPEG)", "", "Images JPEG (*.jpg *.jpeg)")
        if file_path:
            self.txt_oem_wallpaper.setText(file_path)

    def _preview_unattend_xml(self):
        loc_name = self.cb_locales.currentText()
        loc_info = SUPPORTED_LOCALES.get(loc_name, {
            "locale": "fr-FR",
            "keyboard_layout": "040c:0000040c",
            "time_zone": "Romance Standard Time"
        })

        unattend_cfg = UnattendedConfig(
            enabled=True,
            admin_username=self.txt_admin_user.text().strip() or "Administrateur",
            computer_name=self.txt_computer_name.text().strip() or "LORDMADTRIX-PC",
            time_zone=loc_info["time_zone"],
            locale=loc_info["locale"],
            keyboard_layout=loc_info["keyboard_layout"],
            bypass_nro=self.chk_w11_nro.isChecked(),
            auto_disk_partition=self.chk_auto_partition.isChecked(),
            use_builtin_admin=self.chk_builtin_admin.isChecked(),
            product_key=self.txt_product_key.text().strip() or None,
            display_resolution=self.cb_display_res.currentData() or "1920x1080"
        )

        target_os = getattr(self.current_profile, "target_os", TargetOS.WIN11)
        generator = UnattendedGenerator(unattend_cfg, target_os=target_os)
        xml_content = generator.generate_xml()

        dialog = QMessageBox(self)
        dialog.setWindowTitle("Prévisualisation autounattend.xml")
        dialog.setText(f"<b>Fichier de réponse XML généré ({target_os.value.upper()}) :</b>")
        txt_view = QTextEdit(dialog)
        txt_view.setReadOnly(True)
        txt_view.setPlainText(xml_content)
        txt_view.setMinimumSize(700, 440)
        txt_view.setStyleSheet("font-family: 'Cascadia Code', monospace; font-size: 11px; background-color: #07090e; color: #00d2ff;")
        dialog.layout().addWidget(txt_view, 1, 0, 1, dialog.layout().columnCount())
        dialog.exec()

    # --- Gestion des Données et Profils ---
    def _load_default_profiles(self):
        self.cb_profiles.clear()
        profiles_dir = Path(__file__).resolve().parent / "profiles"
        if not profiles_dir.exists():
            return

        self.loaded_profiles: Dict[str, Any] = {}
        for p in profiles_dir.glob("*.yaml"):
            try:
                prof = load_profile_from_yaml(p)
                self.loaded_profiles[prof.name] = (p, prof)
                self.cb_profiles.addItem(f"{prof.name} ({prof.target_os.value.upper()})", prof.name)
            except Exception:
                pass

    def _on_profile_selected(self, index: int):
        prof_name = self.cb_profiles.currentData()
        if not prof_name or prof_name not in self.loaded_profiles:
            return

        p_path, profile = self.loaded_profiles[prof_name]
        self.current_profile = profile
        self.lbl_profile_desc.setText(
            f"<b>Nom :</b> {profile.name}<br>"
            f"<b>Description :</b> {profile.description}<br>"
            f"<b>Système Cible :</b> {profile.target_os.value.upper()} ({profile.architecture})<br>"
            f"<b>Fichier Source :</b> {p_path.name}"
        )

        # Mettre à jour toutes les checkboxes
        self.chk_w11_tpm.setChecked(profile.win11.bypass_tpm)
        self.chk_w11_secureboot.setChecked(profile.win11.bypass_secureboot)
        self.chk_w11_ram.setChecked(profile.win11.bypass_ram)
        self.chk_w11_cpu.setChecked(profile.win11.bypass_cpu)
        self.chk_w11_storage.setChecked(profile.win11.bypass_storage)
        self.chk_w11_nro.setChecked(profile.unattended.bypass_nro)
        self.chk_w11_context.setChecked(profile.win11.classic_context_menu)
        self.chk_w11_copilot.setChecked(profile.win11.disable_copilot)
        self.chk_w11_widgets.setChecked(profile.win11.disable_widgets)
        self.chk_w11_ad_id.setChecked(getattr(profile.win11, "disable_advertising_id", True))
        self.chk_w11_prevent_bitlocker.setChecked(getattr(profile.win11, "prevent_automatic_bitlocker", True))
        self.chk_w11_disable_onedrive.setChecked(getattr(profile.win11, "disable_onedrive_autoinstall", True))
        self.chk_w11_taskbar_left.setChecked(getattr(profile.win11, "taskbar_align_left", True))
        self.chk_w11_disable_chat.setChecked(getattr(profile.win11, "disable_taskbar_chat", True))
        self.chk_w11_disable_oobe_nag.setChecked(getattr(profile.win11, "disable_device_setup_suggestions", True))
        self.chk_w11_disable_lockscreen_tips.setChecked(getattr(profile.win11, "disable_lockscreen_tips", True))

        self.chk_w7_nvme.setChecked(profile.win7.inject_nvme)
        self.chk_w7_usb3.setChecked(profile.win7.inject_usb3)

        self.chk_telemetry.setChecked(profile.disable_telemetry)
        self.chk_gaming.setChecked(profile.enable_gaming_tweaks)
        self.chk_debloat_appx.setChecked(len(profile.remove_appx_patterns) > 0)
        self.chk_auto_host_drivers.setChecked(getattr(profile, "auto_inject_host_network_drivers", False))
        self.chk_cleanup_store.setChecked(getattr(profile, "cleanup_component_store", False))

        # Appx Preset
        current_preset = getattr(profile, "appx_preset", AppxPreset.NONE)
        preset_val = current_preset.value if hasattr(current_preset, "value") else str(current_preset)
        for i in range(self.cb_appx_preset.count()):
            if self.cb_appx_preset.itemData(i) == preset_val:
                self.cb_appx_preset.setCurrentIndex(i)
                break

        self.chk_unattended.setChecked(profile.unattended.enabled)
        self.chk_split_fat32.setChecked(getattr(profile, "split_wim_fat32", False))
        self.chk_single_edition.setChecked(getattr(profile, "single_edition_only", False))

        # Compression
        current_comp = getattr(profile, "compression_type", CompressionType.MAXIMUM)
        comp_val = current_comp.value if hasattr(current_comp, "value") else str(current_comp)
        for i in range(self.cb_compression.count()):
            if self.cb_compression.itemData(i) == comp_val:
                self.cb_compression.setCurrentIndex(i)
                break

        self.txt_intel_vmd.setText(profile.intel_vmd_drivers_dir or "")

        # Explorer
        self.chk_dark_mode.setChecked(profile.explorer.dark_mode)
        self.chk_show_ext.setChecked(profile.explorer.show_file_extensions)
        self.chk_show_hidden.setChecked(profile.explorer.show_hidden_files)
        self.chk_open_this_pc.setChecked(profile.explorer.open_to_this_pc)
        self.chk_hide_3d_objects.setChecked(profile.explorer.hide_3d_objects)
        self.chk_take_ownership.setChecked(profile.explorer.add_take_ownership)
        self.chk_disable_web_search.setChecked(getattr(profile.explorer, "disable_start_web_search", True))
        self.chk_restart_explorer.setChecked(getattr(profile.explorer, "add_restart_explorer_context_menu", False))
        self.chk_open_notepad.setChecked(getattr(profile.explorer, "add_open_with_notepad", False))
        self.chk_cmd_admin.setChecked(getattr(profile.explorer, "add_cmd_admin_here", False))
        self.chk_powershell_admin.setChecked(getattr(profile.explorer, "add_powershell_admin_context_menu", True))
        self.chk_compact_os.setChecked(getattr(profile.explorer, "add_compact_os_context_menu", False))
        self.chk_mados_theme.setChecked(getattr(profile.explorer, "apply_mados_theme", False))

        # Features & Paging
        self.chk_net35.setChecked(profile.system_features.enable_net35)
        self.chk_directplay.setChecked(profile.system_features.enable_directplay)
        self.chk_nagle.setChecked(profile.system_features.disable_nagle_algorithm)
        self.chk_reserved_storage.setChecked(getattr(profile.system_features, "disable_reserved_storage", True))
        self.chk_hags.setChecked(getattr(profile.system_features, "enable_hags", True))
        self.chk_ultimate_perf.setChecked(getattr(profile.system_features, "enable_ultimate_performance", True))
        self.chk_ntfs_trim.setChecked(getattr(profile.system_features, "optimize_ntfs_trim", True))
        self.chk_hpet_synthetic.setChecked(getattr(profile.system_features, "disable_hpet_synthetic", True))
        self.chk_mmcss.setChecked(getattr(profile.system_features, "optimize_mmcss_latency", True))
        self.chk_cpu_quantum.setChecked(getattr(profile.system_features, "optimize_processor_scheduling", True))
        self.chk_edge_prelaunch.setChecked(getattr(profile.system_features, "disable_edge_prelaunch", True))
        self.chk_edge_telemetry.setChecked(getattr(profile.system_features, "disable_edge_telemetry", True))
        self.chk_smartscreen.setChecked(getattr(profile.system_features, "disable_smartscreen", False))
        self.chk_mem_paging.setChecked(getattr(profile.system_features, "optimize_memory_paging", True))
        self.chk_defender_gaming.setChecked(getattr(profile.system_features, "defender_gaming_exclusions", True))
        self.chk_optimize_wim.setChecked(getattr(profile, "optimize_wim", True))
        self.chk_vcredist.setChecked(profile.post_install.install_vcredist)
        self.chk_hwid_act.setChecked(profile.post_install.enable_hwid_activation)

        dns_val = getattr(profile.system_features, "dns_preset", "") or ""
        for i in range(self.cb_dns_preset.count()):
            if self.cb_dns_preset.itemData(i) == dns_val:
                self.cb_dns_preset.setCurrentIndex(i)
                break

        feat_val = getattr(profile.system_features, "features_preset", "") or ""
        for i in range(self.cb_features_preset.count()):
            if self.cb_features_preset.itemData(i) == feat_val:
                self.cb_features_preset.setCurrentIndex(i)
                break

        # Services
        self.chk_srv_sysmain.setChecked(profile.services.disable_sysmain)
        self.chk_srv_indexing.setChecked(profile.services.disable_indexing)
        self.chk_srv_spooler.setChecked(profile.services.disable_spooler)
        self.chk_srv_wer.setChecked(profile.services.disable_error_reporting)
        self.chk_fast_startup.setChecked(profile.services.disable_fast_startup)
        self.chk_srv_telemetry_tasks.setChecked(getattr(profile.services, "disable_telemetry_tasks", True))
        self.chk_srv_wu_reboot.setChecked(getattr(profile.services, "disable_windows_update_auto_reboot", True))
        self.chk_srv_dosvc.setChecked(getattr(profile.services, "disable_delivery_optimization", True))
        self.chk_auto_maintenance.setChecked(getattr(profile.services, "disable_automatic_maintenance", True))

        # WinGet Apps
        apps = profile.post_install.winget_apps
        self.chk_app_7zip.setChecked("7zip.7zip" in apps)
        self.chk_app_chrome.setChecked("Google.Chrome" in apps)
        self.chk_app_firefox.setChecked("Mozilla.Firefox" in apps)
        self.chk_app_vlc.setChecked("VideoLAN.VLC" in apps)
        self.chk_app_steam.setChecked("Valve.Steam" in apps)
        self.chk_app_discord.setChecked("Discord.Discord" in apps)
        self.chk_app_notepad.setChecked("Notepad++.Notepad++" in apps)

        known_preset_ids = {"7zip.7zip", "Google.Chrome", "Mozilla.Firefox", "VideoLAN.VLC", "Valve.Steam", "Discord.Discord", "Notepad++.Notepad++"}
        custom_apps = [a for a in apps if a not in known_preset_ids]
        self.txt_custom_winget.setText(", ".join(custom_apps))

        # OOBE
        self.txt_admin_user.setText(profile.unattended.admin_username or "Administrateur")
        self.txt_computer_name.setText(profile.unattended.computer_name or "LORDMADTRIX-PC")
        self.txt_product_key.setText(profile.unattended.product_key or "")
        self.chk_auto_partition.setChecked(getattr(profile.unattended, "auto_disk_partition", False))
        self.chk_builtin_admin.setChecked(getattr(profile.unattended, "use_builtin_admin", False))

        # Locale
        prof_locale = getattr(profile.unattended, "locale", "fr-FR")
        for idx in range(self.cb_locales.count()):
            loc_key = self.cb_locales.itemText(idx)
            if SUPPORTED_LOCALES.get(loc_key, {}).get("locale") == prof_locale:
                self.cb_locales.setCurrentIndex(idx)
                break

        # Drivers additionnels
        self.list_drivers.clear()
        for d in profile.driver_dirs:
            self.list_drivers.addItem(str(d))

        self.chk_inject_winre.setChecked(getattr(profile, "inject_drivers_to_winre", True))
        setup_cmds = getattr(profile, "setup_complete_commands", []) or []
        self.txt_setup_complete.setPlainText("\r\n".join(setup_cmds))

        self.txt_updates_dir.setText(getattr(profile, "updates_dir", "") or "")

        # Résolution Setup
        res_val = getattr(profile.unattended, "display_resolution", "1920x1080") or "1920x1080"
        for idx in range(self.cb_display_res.count()):
            if self.cb_display_res.itemData(idx) == res_val:
                self.cb_display_res.setCurrentIndex(idx)
                break

        # OEM Branding
        oem_cfg = getattr(profile, "oem", None)
        if oem_cfg:
            self.chk_oem_enabled.setChecked(getattr(oem_cfg, "enabled", False))
            self.txt_oem_manufacturer.setText(getattr(oem_cfg, "manufacturer", "LordMadTrix Custom Rig"))
            self.txt_oem_model.setText(getattr(oem_cfg, "model", "OSBuilder-Win Gaming Edition"))
            self.txt_oem_support_url.setText(getattr(oem_cfg, "support_url", "https://github.com/LordMadTrix"))
            self.txt_oem_support_hours.setText(getattr(oem_cfg, "support_hours", "24/7"))
            self.txt_oem_logo.setText(getattr(oem_cfg, "logo_path", "") or "")
            self.txt_oem_wallpaper.setText(getattr(oem_cfg, "wallpaper_path", "") or "")
        else:
            self.chk_oem_enabled.setChecked(False)

        if not self.txt_output_iso.text():
            self.txt_output_iso.setText(f"D:\\OSBuilder_{profile.target_os.value.upper()}_{profile.architecture.upper()}.iso")

    def _launch_fido(self):
        fido_path = Path(__file__).resolve().parent / "tools" / "Fido.ps1"
        if not fido_path.exists():
            QMessageBox.warning(self, "Fichier Manquant", f"Le script Fido est introuvable dans :\n{fido_path}")
            return
        cmd = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{fido_path}"'
        import subprocess
        subprocess.Popen(cmd, shell=True)

    def _launch_adk_setup(self):
        adk_path = Path(__file__).resolve().parent / "bin" / "adksetup.exe"
        if not adk_path.exists():
            webbrowser.open("https://learn.microsoft.com/en-us/windows-hardware/get-started/adk-install")
            return
        import subprocess
        subprocess.Popen([str(adk_path)])

    def _browse_source_iso(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionnez l'ISO Windows source", "", "Images ISO (*.iso)")
        if file_path:
            self.txt_source_iso.setText(file_path)
            self.cb_editions.setVisible(False)
            self.lbl_editions.setVisible(False)
            self.cb_editions.clear()

    def _inspect_iso(self):
        src = self.txt_source_iso.text().strip()
        if not src or not os.path.exists(src):
            QMessageBox.warning(self, "Fichier Manquant", "Veuillez sélectionner un fichier ISO valide à inspecter.")
            return

        self.btn_inspect_iso.setEnabled(False)
        self.btn_inspect_iso.setText("⏳ Analyse...")
        self.lbl_editions.setVisible(True)
        self.lbl_editions.setText("Analyse des métadonnées WIM/ESD en cours...")
        self.cb_editions.setVisible(False)
        self.cb_editions.clear()

        self.inspector_worker = IsoInspectorWorker(src)
        self.inspector_worker.finished_signal.connect(self._on_inspect_finished)
        self.inspector_worker.error_signal.connect(self._on_inspect_error)
        self.inspector_worker.start()

    def _on_inspect_finished(self, editions: list):
        self.btn_inspect_iso.setEnabled(True)
        self.btn_inspect_iso.setText("🔍 Inspecter les Éditions")
        if not editions:
            self.lbl_editions.setText("Aucune édition détectée ou fichier WIM/ESD introuvable.")
            return

        self.lbl_editions.setText(f"Éditions détectées ({len(editions)}) — Choisissez l'index cible :")
        self.cb_editions.clear()
        for ed in editions:
            idx = ed.get("index", "1")
            name = ed.get("name", f"Édition {idx}")
            arch = ed.get("architecture", "")
            size = ed.get("size", "")
            details = f" ({arch} - {size})" if size else f" ({arch})"
            self.cb_editions.addItem(f"Index {idx} : {name}{details}", int(idx))

        self.cb_editions.setVisible(True)
        if self.current_profile and self.current_profile.image_index:
            for i in range(self.cb_editions.count()):
                if self.cb_editions.itemData(i) == self.current_profile.image_index:
                    self.cb_editions.setCurrentIndex(i)
                    break

    def _on_inspect_error(self, err_msg: str):
        self.btn_inspect_iso.setEnabled(True)
        self.btn_inspect_iso.setText("🔍 Inspecter les Éditions")
        self.lbl_editions.setText("Échec de l'inspection de l'ISO.")
        QMessageBox.warning(self, "Erreur Inspection", f"Impossible d'inspecter l'ISO :\n{err_msg}")

    def _on_edition_changed(self, idx: int):
        if idx < 0:
            return
        img_idx = self.cb_editions.currentData()
        if img_idx and self.current_profile:
            self.current_profile.image_index = int(img_idx)

    def _browse_output_iso(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Définir l'emplacement de l'ISO personnalisée", "", "Images ISO (*.iso)")
        if file_path:
            self.txt_output_iso.setText(file_path)

    def _add_driver_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Sélectionnez le dossier de pilotes (.inf)")
        if dir_path:
            items = [self.list_drivers.item(i).text() for i in range(self.list_drivers.count())]
            if dir_path not in items:
                self.list_drivers.addItem(dir_path)

    def _remove_driver_dir(self):
        current_row = self.list_drivers.currentRow()
        if current_row >= 0:
            self.list_drivers.takeItem(current_row)

    def _browse_hash_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionnez l'ISO à vérifier", "", "Images ISO (*.iso)")
        if file_path:
            self.txt_hash_file.setText(file_path)

    def _start_hash_calc(self):
        path = self.txt_hash_file.text().strip()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un fichier ISO valide.")
            return

        self.lbl_sha1.setText("SHA-1 : Calcul en cours...")
        self.lbl_sha256.setText("SHA-256 : Calcul en cours...")
        self.lbl_hash_match.setText("")

        self.hash_worker = HashCalculatorThread(path)
        self.hash_worker.result_signal.connect(self._on_hash_result)
        self.hash_worker.error_signal.connect(lambda e: QMessageBox.critical(self, "Erreur Hash", e))
        self.hash_worker.start()

    def _on_hash_result(self, algo: str, value: str):
        if algo == "SHA-1":
            self.lbl_sha1.setText(f"<b>SHA-1 :</b> <span style='color:#00e676;'>{value}</span>")
            self.current_sha1 = value
        elif algo == "SHA-256":
            self.lbl_sha256.setText(f"<b>SHA-256 :</b> <span style='color:#00d2ff;'>{value}</span>")
            self.current_sha256 = value
        self._compare_hashes()

    def _compare_hashes(self):
        exp = self.txt_expected_hash.text().strip().upper()
        if not exp:
            self.lbl_hash_match.setText("")
            return

        c_sha1 = getattr(self, "current_sha1", "")
        c_sha256 = getattr(self, "current_sha256", "")

        if exp in (c_sha1, c_sha256):
            self.lbl_hash_match.setText("✅ AUTHENTICITÉ CONFIRMÉE : Le hash correspond exactement à l'image officielle !")
            self.lbl_hash_match.setStyleSheet("color: #00e676; font-weight: bold;")
        elif c_sha1 or c_sha256:
            self.lbl_hash_match.setText("❌ DIFFÉRENCE DÉTECTÉE : L'empreinte ne correspond pas au hash attendu.")
            self.lbl_hash_match.setStyleSheet("color: #ff4757; font-weight: bold;")

    # --- Méthodes Clé USB & Profil Custom ---
    def _browse_usb_iso(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionnez l'ISO à graver", "", "Images ISO (*.iso)")
        if file_path:
            self.txt_usb_iso.setText(file_path)

    def _refresh_usb_drives(self):
        self.cb_usb_drives.clear()
        try:
            creator = UsbCreator()
            drives = creator.list_usb_drives()
            if not drives:
                self.cb_usb_drives.addItem("Aucun lecteur USB amovible détecté", "")
                return
            for d in drives:
                name = d.get("Name", "Disque USB")
                size = d.get("SizeGB", 0)
                letter = d.get("PrimaryLetter", "")
                label = f"{name} ({size} Go) - Lecteur {letter}" if letter else f"{name} ({size} Go)"
                self.cb_usb_drives.addItem(label, letter)
        except Exception as e:
            self.cb_usb_drives.addItem(f"Erreur détection : {e}", "")

    def _start_usb_creation(self):
        iso = self.txt_usb_iso.text().strip()
        drive = self.cb_usb_drives.currentData()

        if not iso or not os.path.exists(iso):
            QMessageBox.warning(self, "Fichier Manquant", "Veuillez sélectionner un fichier ISO valide à déployer.")
            return

        if not drive:
            QMessageBox.warning(self, "Lecteur Manquant", "Veuillez sélectionner un lecteur USB cible valide avec une lettre de lecteur.")
            return

        reply = QMessageBox.warning(
            self,
            "Confirmation de Formatage",
            f"Êtes-vous ABSOLUMENT certain de vouloir préparer la clé USB {drive} ?\n\n"
            f"Toutes les données présentes sur le lecteur {drive} seront définitivement effacées.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.btn_flash_usb.setEnabled(False)
        self.usb_progress_bar.setValue(0)
        self.usb_status_lbl.setText("Initialisation de la création USB...")

        format_fat32 = self.chk_format_usb.isChecked()
        self.usb_worker = UsbDeployWorker(iso, drive, format_fat32=format_fat32)
        self.usb_worker.progress_signal.connect(self._on_usb_progress)
        self.usb_worker.finished_signal.connect(self._on_usb_finished)
        self.usb_worker.start()

    def _on_usb_progress(self, pct: int, msg: str):
        self.usb_progress_bar.setValue(pct)
        self.usb_status_lbl.setText(msg)

    def _on_usb_finished(self, success: bool, msg: str):
        self.btn_flash_usb.setEnabled(True)
        if success:
            self.usb_status_lbl.setText("Terminé avec succès !")
            QMessageBox.information(self, "Succès Clé USB", msg)
        else:
            self.usb_status_lbl.setText("Échec du déploiement USB.")
            QMessageBox.critical(self, "Erreur Clé USB", msg)

    def _save_custom_profile(self):
        if not self.current_profile:
            QMessageBox.warning(self, "Erreur", "Aucun profil n'est chargé.")
            return

        name, ok = QInputDialog.getText(
            self,
            "Enregistrer le Profil",
            "Entrez un nom pour votre nouveau profil de personnalisation :",
            text=f"{self.current_profile.name} (Custom)"
        )
        if not ok or not name.strip():
            return

        from copy import deepcopy
        new_profile = deepcopy(self.current_profile)
        new_profile.name = name.strip()
        new_profile.description = f"Profil personnalisé créé le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"

        new_profile.win11.bypass_tpm = self.chk_w11_tpm.isChecked()
        new_profile.win11.bypass_secureboot = self.chk_w11_secureboot.isChecked()
        new_profile.win11.bypass_ram = self.chk_w11_ram.isChecked()
        new_profile.win11.bypass_cpu = self.chk_w11_cpu.isChecked()
        new_profile.win11.bypass_storage = self.chk_w11_storage.isChecked()
        new_profile.unattended.bypass_nro = self.chk_w11_nro.isChecked()
        new_profile.win11.classic_context_menu = self.chk_w11_context.isChecked()
        new_profile.win11.disable_copilot = self.chk_w11_copilot.isChecked()
        new_profile.win11.disable_widgets = self.chk_w11_widgets.isChecked()
        new_profile.win11.disable_advertising_id = self.chk_w11_ad_id.isChecked()
        new_profile.win11.prevent_automatic_bitlocker = self.chk_w11_prevent_bitlocker.isChecked()
        new_profile.win11.disable_onedrive_autoinstall = self.chk_w11_disable_onedrive.isChecked()
        new_profile.win11.taskbar_align_left = self.chk_w11_taskbar_left.isChecked()
        new_profile.win11.disable_taskbar_chat = self.chk_w11_disable_chat.isChecked()
        new_profile.win11.disable_device_setup_suggestions = self.chk_w11_disable_oobe_nag.isChecked()
        new_profile.win11.disable_lockscreen_tips = self.chk_w11_disable_lockscreen_tips.isChecked()

        new_profile.win7.inject_nvme = self.chk_w7_nvme.isChecked()
        new_profile.win7.inject_usb3 = self.chk_w7_usb3.isChecked()

        new_profile.disable_telemetry = self.chk_telemetry.isChecked()
        new_profile.enable_gaming_tweaks = self.chk_gaming.isChecked()
        new_profile.auto_inject_host_network_drivers = self.chk_auto_host_drivers.isChecked()
        new_profile.cleanup_component_store = self.chk_cleanup_store.isChecked()
        new_profile.appx_preset = AppxPreset(self.cb_appx_preset.currentData() or "none")
        new_profile.unattended.enabled = self.chk_unattended.isChecked()
        new_profile.split_wim_fat32 = self.chk_split_fat32.isChecked()
        new_profile.single_edition_only = self.chk_single_edition.isChecked()
        new_profile.compression_type = CompressionType(self.cb_compression.currentData() or "maximum")
        new_profile.intel_vmd_drivers_dir = self.txt_intel_vmd.text().strip() or None
        new_profile.inject_drivers_to_winre = self.chk_inject_winre.isChecked()
        new_profile.setup_complete_commands = [l.strip() for l in self.txt_setup_complete.toPlainText().strip().splitlines() if l.strip()]

        new_profile.explorer.dark_mode = self.chk_dark_mode.isChecked()
        new_profile.explorer.show_file_extensions = self.chk_show_ext.isChecked()
        new_profile.explorer.show_hidden_files = self.chk_show_hidden.isChecked()
        new_profile.explorer.open_to_this_pc = self.chk_open_this_pc.isChecked()
        new_profile.explorer.hide_3d_objects = self.chk_hide_3d_objects.isChecked()
        new_profile.explorer.add_take_ownership = self.chk_take_ownership.isChecked()
        new_profile.explorer.disable_start_web_search = self.chk_disable_web_search.isChecked()
        new_profile.explorer.add_restart_explorer_context_menu = self.chk_restart_explorer.isChecked()
        new_profile.explorer.add_open_with_notepad = self.chk_open_notepad.isChecked()
        new_profile.explorer.add_cmd_admin_here = self.chk_cmd_admin.isChecked()
        new_profile.explorer.add_powershell_admin_context_menu = self.chk_powershell_admin.isChecked()
        new_profile.explorer.add_compact_os_context_menu = self.chk_compact_os.isChecked()
        new_profile.explorer.apply_mados_theme = self.chk_mados_theme.isChecked()

        new_profile.system_features.enable_net35 = self.chk_net35.isChecked()
        new_profile.system_features.enable_directplay = self.chk_directplay.isChecked()
        new_profile.system_features.disable_nagle_algorithm = self.chk_nagle.isChecked()
        new_profile.system_features.disable_reserved_storage = self.chk_reserved_storage.isChecked()
        new_profile.system_features.enable_hags = self.chk_hags.isChecked()
        new_profile.system_features.enable_ultimate_performance = self.chk_ultimate_perf.isChecked()
        new_profile.system_features.optimize_ntfs_trim = self.chk_ntfs_trim.isChecked()
        new_profile.system_features.disable_hpet_synthetic = self.chk_hpet_synthetic.isChecked()
        new_profile.system_features.optimize_mmcss_latency = self.chk_mmcss.isChecked()
        new_profile.system_features.optimize_processor_scheduling = self.chk_cpu_quantum.isChecked()
        new_profile.system_features.disable_edge_prelaunch = self.chk_edge_prelaunch.isChecked()
        new_profile.system_features.disable_edge_telemetry = self.chk_edge_telemetry.isChecked()
        new_profile.system_features.disable_smartscreen = self.chk_smartscreen.isChecked()
        new_profile.system_features.optimize_memory_paging = self.chk_mem_paging.isChecked()
        new_profile.system_features.defender_gaming_exclusions = self.chk_defender_gaming.isChecked()
        new_profile.system_features.dns_preset = self.cb_dns_preset.currentData() or None
        new_profile.system_features.features_preset = self.cb_features_preset.currentData() or None
        new_profile.optimize_wim = self.chk_optimize_wim.isChecked()
        new_profile.post_install.install_vcredist = self.chk_vcredist.isChecked()
        new_profile.post_install.enable_hwid_activation = self.chk_hwid_act.isChecked()

        new_profile.services.disable_sysmain = self.chk_srv_sysmain.isChecked()
        new_profile.services.disable_indexing = self.chk_srv_indexing.isChecked()
        new_profile.services.disable_spooler = self.chk_srv_spooler.isChecked()
        new_profile.services.disable_error_reporting = self.chk_srv_wer.isChecked()
        new_profile.services.disable_fast_startup = self.chk_fast_startup.isChecked()
        new_profile.services.disable_telemetry_tasks = self.chk_srv_telemetry_tasks.isChecked()
        new_profile.services.disable_windows_update_auto_reboot = self.chk_srv_wu_reboot.isChecked()
        new_profile.services.disable_delivery_optimization = self.chk_srv_dosvc.isChecked()
        new_profile.services.disable_automatic_maintenance = self.chk_auto_maintenance.isChecked()

        selected_apps = []
        if self.chk_app_7zip.isChecked(): selected_apps.append("7zip.7zip")
        if self.chk_app_chrome.isChecked(): selected_apps.append("Google.Chrome")
        if self.chk_app_firefox.isChecked(): selected_apps.append("Mozilla.Firefox")
        if self.chk_app_vlc.isChecked(): selected_apps.append("VideoLAN.VLC")
        if self.chk_app_steam.isChecked(): selected_apps.append("Valve.Steam")
        if self.chk_app_discord.isChecked(): selected_apps.append("Discord.Discord")
        if self.chk_app_notepad.isChecked(): selected_apps.append("Notepad++.Notepad++")
        custom_apps_str = self.txt_custom_winget.text().strip()
        if custom_apps_str:
            for item in custom_apps_str.split(","):
                pkg = item.strip()
                if pkg and pkg not in selected_apps:
                    selected_apps.append(pkg)
        new_profile.post_install.winget_apps = selected_apps

        new_profile.unattended.admin_username = self.txt_admin_user.text().strip() or "Administrateur"
        new_profile.unattended.computer_name = self.txt_computer_name.text().strip() or "LORDMADTRIX-PC"
        key_val = self.txt_product_key.text().strip()
        new_profile.unattended.product_key = key_val if key_val else None
        new_profile.unattended.auto_disk_partition = self.chk_auto_partition.isChecked()
        new_profile.unattended.use_builtin_admin = self.chk_builtin_admin.isChecked()

        loc_data = SUPPORTED_LOCALES.get(self.cb_locales.currentText())
        if loc_data:
            new_profile.unattended.locale = loc_data["locale"]
            new_profile.unattended.keyboard_layout = loc_data["keyboard_layout"]
            new_profile.unattended.time_zone = loc_data["time_zone"]

        new_profile.driver_dirs = [self.list_drivers.item(i).text() for i in range(self.list_drivers.count())]
        new_profile.updates_dir = self.txt_updates_dir.text().strip() or None
        new_profile.unattended.display_resolution = self.cb_display_res.currentData() or "1920x1080"

        new_profile.oem = OemOptions(
            enabled=self.chk_oem_enabled.isChecked(),
            manufacturer=self.txt_oem_manufacturer.text().strip() or "LordMadTrix Custom Rig",
            model=self.txt_oem_model.text().strip() or "OSBuilder-Win Gaming Edition",
            support_url=self.txt_oem_support_url.text().strip() or "https://github.com/LordMadTrix",
            support_hours=self.txt_oem_support_hours.text().strip() or "24/7",
            logo_path=self.txt_oem_logo.text().strip() or None,
            wallpaper_path=self.txt_oem_wallpaper.text().strip() or None
        )

        import re
        slug = re.sub(r'[^a-zA-Z0-9_-]', '_', name.strip().lower())
        file_path = Path(__file__).resolve().parent / "profiles" / f"{slug}.yaml"

        try:
            save_profile_to_yaml(new_profile, file_path)
            self._load_default_profiles()
            for i in range(self.cb_profiles.count()):
                if self.cb_profiles.itemData(i) == new_profile.name:
                    self.cb_profiles.setCurrentIndex(i)
                    break
            QMessageBox.information(self, "Profil Enregistré", f"Le profil a été sauvegardé avec succès dans :\n{file_path.name}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur Sauvegarde", f"Impossible d'enregistrer le profil :\n{e}")

    # --- Lancement du Build ---
    def _start_build(self):
        if not is_admin():
            res = QMessageBox.question(
                self,
                "Privilèges Administrateur Requis",
                "OSBuilder-Win nécessite les privilèges Administrateur pour manipuler DISM et le registre.\n"
                "Souhaitez-vous relancer l'application en mode Administrateur maintenant ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if res == QMessageBox.StandardButton.Yes:
                self._restart_as_admin()
                return

        src = self.txt_source_iso.text().strip()
        out = self.txt_output_iso.text().strip()

        if not src or not os.path.exists(src):
            QMessageBox.warning(self, "Fichier Manquant", "Veuillez spécifier une image ISO source valide.")
            return

        if not out:
            QMessageBox.warning(self, "Fichier Manquant", "Veuillez spécifier le chemin de l'ISO de sortie.")
            return

        if not self.current_profile:
            QMessageBox.warning(self, "Profil Manquant", "Veuillez sélectionner un profil de configuration.")
            return

        # Synchronisation finale de toutes les options
        self.current_profile.win11.bypass_tpm = self.chk_w11_tpm.isChecked()
        self.current_profile.win11.bypass_secureboot = self.chk_w11_secureboot.isChecked()
        self.current_profile.win11.bypass_ram = self.chk_w11_ram.isChecked()
        self.current_profile.win11.bypass_cpu = self.chk_w11_cpu.isChecked()
        self.current_profile.win11.bypass_storage = self.chk_w11_storage.isChecked()
        self.current_profile.unattended.bypass_nro = self.chk_w11_nro.isChecked()
        self.current_profile.win11.classic_context_menu = self.chk_w11_context.isChecked()
        self.current_profile.win11.disable_copilot = self.chk_w11_copilot.isChecked()
        self.current_profile.win11.disable_widgets = self.chk_w11_widgets.isChecked()
        self.current_profile.win11.disable_advertising_id = self.chk_w11_ad_id.isChecked()
        self.current_profile.win11.prevent_automatic_bitlocker = self.chk_w11_prevent_bitlocker.isChecked()
        self.current_profile.win11.disable_onedrive_autoinstall = self.chk_w11_disable_onedrive.isChecked()
        self.current_profile.win11.taskbar_align_left = self.chk_w11_taskbar_left.isChecked()
        self.current_profile.win11.disable_taskbar_chat = self.chk_w11_disable_chat.isChecked()
        self.current_profile.win11.disable_device_setup_suggestions = self.chk_w11_disable_oobe_nag.isChecked()
        self.current_profile.win11.disable_lockscreen_tips = self.chk_w11_disable_lockscreen_tips.isChecked()

        self.current_profile.win7.inject_nvme = self.chk_w7_nvme.isChecked()
        self.current_profile.win7.inject_usb3 = self.chk_w7_usb3.isChecked()

        self.current_profile.disable_telemetry = self.chk_telemetry.isChecked()
        self.current_profile.enable_gaming_tweaks = self.chk_gaming.isChecked()
        self.current_profile.cleanup_component_store = self.chk_cleanup_store.isChecked()
        self.current_profile.unattended.enabled = self.chk_unattended.isChecked()
        self.current_profile.split_wim_fat32 = self.chk_split_fat32.isChecked()
        self.current_profile.single_edition_only = self.chk_single_edition.isChecked()
        self.current_profile.compression_type = CompressionType(self.cb_compression.currentData() or "maximum")
        self.current_profile.intel_vmd_drivers_dir = self.txt_intel_vmd.text().strip() or None
        self.current_profile.auto_inject_host_network_drivers = self.chk_auto_host_drivers.isChecked()
        self.current_profile.inject_drivers_to_winre = self.chk_inject_winre.isChecked()
        self.current_profile.setup_complete_commands = [l.strip() for l in self.txt_setup_complete.toPlainText().strip().splitlines() if l.strip()]
        self.current_profile.appx_preset = AppxPreset(self.cb_appx_preset.currentData() or "none")

        # Explorer
        self.current_profile.explorer.dark_mode = self.chk_dark_mode.isChecked()
        self.current_profile.explorer.show_file_extensions = self.chk_show_ext.isChecked()
        self.current_profile.explorer.show_hidden_files = self.chk_show_hidden.isChecked()
        self.current_profile.explorer.open_to_this_pc = self.chk_open_this_pc.isChecked()
        self.current_profile.explorer.hide_3d_objects = self.chk_hide_3d_objects.isChecked()
        self.current_profile.explorer.add_take_ownership = self.chk_take_ownership.isChecked()
        self.current_profile.explorer.disable_start_web_search = self.chk_disable_web_search.isChecked()
        self.current_profile.explorer.add_restart_explorer_context_menu = self.chk_restart_explorer.isChecked()
        self.current_profile.explorer.add_open_with_notepad = self.chk_open_notepad.isChecked()
        self.current_profile.explorer.add_cmd_admin_here = self.chk_cmd_admin.isChecked()
        self.current_profile.explorer.add_powershell_admin_context_menu = self.chk_powershell_admin.isChecked()
        self.current_profile.explorer.add_compact_os_context_menu = self.chk_compact_os.isChecked()
        self.current_profile.explorer.apply_mados_theme = self.chk_mados_theme.isChecked()

        # Features
        self.current_profile.system_features.enable_net35 = self.chk_net35.isChecked()
        self.current_profile.system_features.enable_directplay = self.chk_directplay.isChecked()
        self.current_profile.system_features.disable_nagle_algorithm = self.chk_nagle.isChecked()
        self.current_profile.system_features.disable_reserved_storage = self.chk_reserved_storage.isChecked()
        self.current_profile.system_features.enable_hags = self.chk_hags.isChecked()
        self.current_profile.system_features.enable_ultimate_performance = self.chk_ultimate_perf.isChecked()
        self.current_profile.system_features.optimize_ntfs_trim = self.chk_ntfs_trim.isChecked()
        self.current_profile.system_features.disable_hpet_synthetic = self.chk_hpet_synthetic.isChecked()
        self.current_profile.system_features.optimize_mmcss_latency = self.chk_mmcss.isChecked()
        self.current_profile.system_features.optimize_processor_scheduling = self.chk_cpu_quantum.isChecked()
        self.current_profile.system_features.disable_edge_prelaunch = self.chk_edge_prelaunch.isChecked()
        self.current_profile.system_features.disable_edge_telemetry = self.chk_edge_telemetry.isChecked()
        self.current_profile.system_features.disable_smartscreen = self.chk_smartscreen.isChecked()
        self.current_profile.system_features.optimize_memory_paging = self.chk_mem_paging.isChecked()
        self.current_profile.system_features.defender_gaming_exclusions = self.chk_defender_gaming.isChecked()
        self.current_profile.system_features.dns_preset = self.cb_dns_preset.currentData() or None
        self.current_profile.system_features.features_preset = self.cb_features_preset.currentData() or None
        self.current_profile.optimize_wim = self.chk_optimize_wim.isChecked()
        self.current_profile.post_install.install_vcredist = self.chk_vcredist.isChecked()
        self.current_profile.post_install.enable_hwid_activation = self.chk_hwid_act.isChecked()

        # Services
        self.current_profile.services.disable_sysmain = self.chk_srv_sysmain.isChecked()
        self.current_profile.services.disable_indexing = self.chk_srv_indexing.isChecked()
        self.current_profile.services.disable_spooler = self.chk_srv_spooler.isChecked()
        self.current_profile.services.disable_error_reporting = self.chk_srv_wer.isChecked()
        self.current_profile.services.disable_fast_startup = self.chk_fast_startup.isChecked()
        self.current_profile.services.disable_telemetry_tasks = self.chk_srv_telemetry_tasks.isChecked()
        self.current_profile.services.disable_windows_update_auto_reboot = self.chk_srv_wu_reboot.isChecked()
        self.current_profile.services.disable_delivery_optimization = self.chk_srv_dosvc.isChecked()
        self.current_profile.services.disable_automatic_maintenance = self.chk_auto_maintenance.isChecked()

        # Unattended
        self.current_profile.unattended.admin_username = self.txt_admin_user.text().strip() or "Administrateur"
        self.current_profile.unattended.computer_name = self.txt_computer_name.text().strip() or "LORDMADTRIX-PC"
        key_val = self.txt_product_key.text().strip()
        self.current_profile.unattended.product_key = key_val if key_val else None
        self.current_profile.unattended.auto_disk_partition = self.chk_auto_partition.isChecked()
        self.current_profile.unattended.use_builtin_admin = self.chk_builtin_admin.isChecked()

        loc_data = SUPPORTED_LOCALES.get(self.cb_locales.currentText())
        if loc_data:
            self.current_profile.unattended.locale = loc_data["locale"]
            self.current_profile.unattended.keyboard_layout = loc_data["keyboard_layout"]
            self.current_profile.unattended.time_zone = loc_data["time_zone"]

        selected_apps = []
        if self.chk_app_7zip.isChecked(): selected_apps.append("7zip.7zip")
        if self.chk_app_chrome.isChecked(): selected_apps.append("Google.Chrome")
        if self.chk_app_firefox.isChecked(): selected_apps.append("Mozilla.Firefox")
        if self.chk_app_vlc.isChecked(): selected_apps.append("VideoLAN.VLC")
        if self.chk_app_steam.isChecked(): selected_apps.append("Valve.Steam")
        if self.chk_app_discord.isChecked(): selected_apps.append("Discord.Discord")
        if self.chk_app_notepad.isChecked(): selected_apps.append("Notepad++.Notepad++")
        self.current_profile.post_install.winget_apps = selected_apps

        self.current_profile.driver_dirs = [self.list_drivers.item(i).text() for i in range(self.list_drivers.count())]
        self.current_profile.updates_dir = self.txt_updates_dir.text().strip() or None
        self.current_profile.unattended.display_resolution = self.cb_display_res.currentData() or "1920x1080"

        self.current_profile.oem = OemOptions(
            enabled=self.chk_oem_enabled.isChecked(),
            manufacturer=self.txt_oem_manufacturer.text().strip() or "LordMadTrix Custom Rig",
            model=self.txt_oem_model.text().strip() or "OSBuilder-Win Gaming Edition",
            support_url=self.txt_oem_support_url.text().strip() or "https://github.com/LordMadTrix",
            support_hours=self.txt_oem_support_hours.text().strip() or "24/7",
            logo_path=self.txt_oem_logo.text().strip() or None,
            wallpaper_path=self.txt_oem_wallpaper.text().strip() or None
        )

        # Basculer vers l'onglet console
        self.tabs.setCurrentWidget(self.console_widget)
        self.btn_build.setEnabled(False)
        self.btn_cancel_build.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_lbl.setText("Construction de l'image ISO en cours...")
        self.status_icon.setStyleSheet("color: #ffab00; font-size: 14px;")

        self.worker = BuildWorker(self.current_profile, src, out)
        self.worker.log_signal.connect(self._append_log)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self._on_build_finished)
        self.worker.start()

    def _append_log(self, msg: str):
        color = "#cbd5e1"
        if "[ERREUR" in msg:
            color = "#ff4757"
        elif "[SUCCÈS]" in msg or "[OK]" in msg:
            color = "#00e676"
        elif "[ATTENTION]" in msg:
            color = "#ffab00"
        elif "[ÉTAPE" in msg:
            color = "#00d2ff"

        html = f"<span style='color: {color};'>{msg}</span>"
        self.console_output.append(html)
        self.console_output.moveCursor(QTextCursor.MoveOperation.End)

    def _on_build_finished(self, success: bool, message: str):
        self.btn_build.setEnabled(True)
        self.btn_cancel_build.setEnabled(False)
        if success:
            self.status_lbl.setText("Construction terminée avec succès !")
            self.status_icon.setStyleSheet("color: #00e676; font-size: 14px;")
            QMessageBox.information(self, "Succès du Build", message)
        else:
            self.status_lbl.setText("Échec de la construction.")
            self.status_icon.setStyleSheet("color: #ff4757; font-size: 14px;")
            QMessageBox.critical(self, "Erreur lors du Build", message)


def main():
    app = QApplication(sys.argv)
    icon_path = Path(__file__).resolve().parent / "app.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
