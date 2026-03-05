#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de build — genere ThermalPrinterAPI_Setup.exe

Utilisation (depuis le dossier du projet) :
    python build.py

Prerequis :
    pip install pyinstaller

Resultat :
    dist/ThermalPrinterAPI_Setup.exe  <- fichier a distribuer
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

PROJECT_DIR  = Path(__file__).parent
DIST_DIR     = PROJECT_DIR / "dist"
BUILD_DIR    = PROJECT_DIR / "build"
OUTPUT_NAME  = "ThermalPrinterAPI_Setup"

# Fichiers et dossiers a embarquer dans l'installateur
INCLUDE_FILES = [
    "main.py",
    "run.py",
    "service.py",
    "start.bat",
    "requirements.txt",
    "README.md",
]

INCLUDE_DIRS = [
    "api",
    "printer",
    "utils",
    "gui",
]

# Fichiers a exclure des dossiers
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".git",
    ".claude",
    "dist",
    "build",
    "logs",
    "static",
    "printer_config.json",
]


def check_pyinstaller():
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} detecte.")
    except ImportError:
        print("PyInstaller non installe. Installation...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)


def clean():
    """Supprime les anciens artifacts de build."""
    for d in (DIST_DIR, BUILD_DIR):
        if d.exists():
            shutil.rmtree(d)
            print(f"Supprime : {d}")
    spec = PROJECT_DIR / f"{OUTPUT_NAME}.spec"
    if spec.exists():
        spec.unlink()


def collect_datas():
    """
    Construit la liste des arguments --add-data pour PyInstaller.
    Chaque element est 'source;destination' (separateur Windows).
    """
    datas = []

    for fname in INCLUDE_FILES:
        src = PROJECT_DIR / fname
        if src.exists():
            datas.append(f"{src};.")

    for dname in INCLUDE_DIRS:
        src = PROJECT_DIR / dname
        if src.is_dir():
            datas.append(f"{src};{dname}")

    return datas


def build():
    print("\n" + "=" * 55)
    print("  Build : ThermalPrinterAPI_Setup.exe")
    print("=" * 55 + "\n")

    check_pyinstaller()
    clean()

    datas = collect_datas()
    add_data_args = []
    for d in datas:
        add_data_args += ["--add-data", d]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                          # Un seul .exe
        "--windowed",                         # Pas de console noire (GUI tkinter)
        "--clean",
        f"--name={OUTPUT_NAME}",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        "--hidden-import=win32print",
        "--hidden-import=win32service",
        "--hidden-import=win32serviceutil",
        "--hidden-import=win32event",
        "--hidden-import=servicemanager",
        "--hidden-import=serial",
        "--hidden-import=serial.tools.list_ports",
        "--hidden-import=flask",
        "--hidden-import=flask_cors",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        *add_data_args,
        str(PROJECT_DIR / "installer_main.py"),  # Script principal de l'installateur
    ]

    print("Lancement de PyInstaller...\n")
    result = subprocess.run(cmd, cwd=PROJECT_DIR)

    if result.returncode != 0:
        print("\nEchec du build. Verifiez les erreurs ci-dessus.")
        sys.exit(1)

    output = DIST_DIR / f"{OUTPUT_NAME}.exe"
    if output.exists():
        size_mb = output.stat().st_size / 1024 / 1024
        print("\n" + "=" * 55)
        print(f"  Build reussi !")
        print(f"  Fichier : {output}")
        print(f"  Taille  : {size_mb:.1f} MB")
        print("=" * 55)
        print("\nDistribuez ce fichier a vos clients.")
        print("Ils double-cliquent et tout s'installe automatiquement.")
    else:
        print("\nFichier de sortie introuvable. Build echoue.")
        sys.exit(1)


if __name__ == "__main__":
    build()
