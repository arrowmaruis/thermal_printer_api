#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Point d'entree de l'interface de configuration.

Compile par PyInstaller en ThermalPrinterAPI_Config.exe.
Lance le dashboard GUI pour configurer l'imprimante par defaut et tester l'impression.
"""

import sys
import os
import ctypes


# ---------------------------------------------------------------------------
# DPI awareness — doit etre appele AVANT toute initialisation tkinter
# Evite le rendu flou sur Windows 10/11 avec ecrans haute resolution
# ---------------------------------------------------------------------------
def _set_dpi_aware():
    try:
        # Windows 8.1+ : Per-Monitor DPI awareness (v2 si disponible)
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            # Fallback Windows Vista/7/8
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

_set_dpi_aware()

# ---------------------------------------------------------------------------
# Chemins — fonctionne en mode gele (PyInstaller) et en mode dev
# ---------------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    # Exe PyInstaller : l'exe se trouve dans le dossier d'installation
    INSTALL_DIR = os.path.dirname(sys.executable)
    # Les modules Python (utils/, printer/, gui/) sont dans _MEIPASS
    if hasattr(sys, '_MEIPASS') and sys._MEIPASS not in sys.path:
        sys.path.insert(0, sys._MEIPASS)
else:
    INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))
    if INSTALL_DIR not in sys.path:
        sys.path.insert(0, INSTALL_DIR)

# Changer le repertoire courant vers le dossier d'installation
# pour que printer_config.json et logs/ soient au bon endroit
os.chdir(INSTALL_DIR)

# ---------------------------------------------------------------------------
# Lancement du GUI
# ---------------------------------------------------------------------------
from utils.config import load_config
load_config()

from gui.config_app import launch_config_gui
launch_config_gui()
