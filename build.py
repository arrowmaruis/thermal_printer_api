#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de build en 2 etapes — genere ThermalPrinterAPI_Setup.exe

Etape 1 : compile ThermalPrinterAPI.exe  (serveur Flask autonome)
Etape 2 : compile ThermalPrinterAPI_Setup.exe (installateur, embarque l'etape 1)

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

# Noms des sorties
SERVICE_EXE_NAME  = "ThermalPrinterAPI"        # le serveur Flask
INSTALLER_NAME    = "ThermalPrinterAPI_Setup"  # l'installateur

SERVICE_EXE_PATH  = DIST_DIR / f"{SERVICE_EXE_NAME}.exe"
INSTALLER_PATH    = DIST_DIR / f"{INSTALLER_NAME}.exe"


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def check_pyinstaller():
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} detecte.")
    except ImportError:
        print("PyInstaller non installe. Installation...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)


def clean():
    """Supprime les anciens artifacts (gere les fichiers verrouilles)."""
    for name in (SERVICE_EXE_NAME, INSTALLER_NAME):
        old = DIST_DIR / f"{name}.exe"
        if old.exists():
            for suffix in ('.old', '.old2', '.old3'):
                renamed = old.with_suffix(suffix)
                try:
                    old.rename(renamed)
                    print(f"Renomme : {old.name} -> {renamed.name}")
                    break
                except Exception:
                    pass

    for d in (DIST_DIR, BUILD_DIR):
        if d.exists():
            try:
                shutil.rmtree(d)
                print(f"Supprime : {d}")
            except Exception as e:
                print(f"Avertissement nettoyage : {e}")
                for f in d.rglob("*"):
                    try:
                        if f.is_file():
                            f.unlink()
                    except Exception:
                        pass

    for spec in (PROJECT_DIR / f"{SERVICE_EXE_NAME}.spec",
                 PROJECT_DIR / f"{INSTALLER_NAME}.spec"):
        if spec.exists():
            spec.unlink()


def run_pyinstaller(args):
    cmd = [sys.executable, "-m", "PyInstaller"] + args
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    if result.returncode != 0:
        print("\nEchec du build. Verifiez les erreurs ci-dessus.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Etape 1 : ThermalPrinterAPI.exe (serveur Flask + service Windows)
# ---------------------------------------------------------------------------

def build_service_exe():
    print("\n" + "=" * 60)
    print("  Etape 1/2 : ThermalPrinterAPI.exe (serveur Flask autonome)")
    print("=" * 60)

    icon_path = PROJECT_DIR / "icon.ico"

    args = [
        "--onefile",
        "--console",           # pas de fenetre — tourne en service silencieux
        "--clean",
        f"--name={SERVICE_EXE_NAME}",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR / 'service'}",
        # Dossiers Python a embarquer (utils, api, printer)
        "--add-data", f"{PROJECT_DIR / 'api'};api",
        "--add-data", f"{PROJECT_DIR / 'printer'};printer",
        "--add-data", f"{PROJECT_DIR / 'utils'};utils",
        # Imports caches (PyInstaller ne detecte pas toujours tout)
        "--hidden-import=win32print",
        "--hidden-import=flask",
        "--hidden-import=flask_cors",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=serial",
        "--hidden-import=serial.tools.list_ports",
        "--hidden-import=werkzeug",
        "--hidden-import=click",
    ]

    if icon_path.exists():
        args.append(f"--icon={icon_path}")

    args.append(str(PROJECT_DIR / "service_exe.py"))

    run_pyinstaller(args)

    if SERVICE_EXE_PATH.exists():
        size_mb = SERVICE_EXE_PATH.stat().st_size / 1024 / 1024
        print(f"\n  OK : {SERVICE_EXE_PATH}  ({size_mb:.1f} MB)")
    else:
        print("\nEchec : ThermalPrinterAPI.exe introuvable.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Etape 2 : ThermalPrinterAPI_Setup.exe (installateur)
# ---------------------------------------------------------------------------

def build_installer_exe():
    print("\n" + "=" * 60)
    print("  Etape 2/2 : ThermalPrinterAPI_Setup.exe (installateur)")
    print("=" * 60)

    icon_path = PROJECT_DIR / "icon.ico"

    # L'installateur embarque le binaire de service + logo + icone
    add_datas = [
        "--add-data", f"{SERVICE_EXE_PATH};.",
    ]
    for fname in ("logo.png", "icon.ico", "README.md"):
        f = PROJECT_DIR / fname
        if f.exists():
            add_datas += ["--add-data", f"{f};."]

    args = [
        "--onefile",
        "--windowed",          # pas de console noire (GUI tkinter)
        "--clean",
        f"--name={INSTALLER_NAME}",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR / 'installer'}",
        # Imports tkinter + win32com pour le raccourci
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=win32com",
        "--hidden-import=win32com.client",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=PIL.ImageTk",
        *add_datas,
    ]

    if icon_path.exists():
        args.append(f"--icon={icon_path}")

    args.append(str(PROJECT_DIR / "installer_main.py"))

    run_pyinstaller(args)

    if INSTALLER_PATH.exists():
        size_mb = INSTALLER_PATH.stat().st_size / 1024 / 1024
        print(f"\n  OK : {INSTALLER_PATH}  ({size_mb:.1f} MB)")
    else:
        print("\nEchec : ThermalPrinterAPI_Setup.exe introuvable.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Build complet
# ---------------------------------------------------------------------------

def build():
    print("\n" + "=" * 60)
    print("  Build : Thermal Printer API — installateur autonome")
    print("=" * 60 + "\n")

    check_pyinstaller()
    clean()

    build_service_exe()
    build_installer_exe()

    print("\n" + "=" * 60)
    print("  Build reussi !")
    print(f"  Distribuer : {INSTALLER_PATH}")
    size_mb = INSTALLER_PATH.stat().st_size / 1024 / 1024
    print(f"  Taille     : {size_mb:.1f} MB")
    print("=" * 60)
    print("\nL'utilisateur double-clique sur ThermalPrinterAPI_Setup.exe")
    print("Aucun Python requis sur la machine cible.")


if __name__ == "__main__":
    build()
