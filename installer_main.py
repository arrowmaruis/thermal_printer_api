#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Installateur graphique de Thermal Printer API.

Ce fichier est compile par PyInstaller en ThermalPrinterAPI_Setup.exe.
L'utilisateur double-clique dessus — tout s'installe automatiquement.

Ce que fait l'installateur :
  1. Verifie les droits administrateur (se relance si necessaire)
  2. Copie les fichiers dans C:\Program Files\ThermalPrinterAPI\
  3. Installe les dependances Python dans le dossier d'installation
  4. Enregistre le service Windows (demarrage auto)
  5. Demarre le service immediatement
  6. Cree un raccourci dans le menu Demarrer
"""

import os
import sys
import shutil
import subprocess
import ctypes
import time
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

APP_NAME        = "ThermalPrinterAPI"
APP_DISPLAY     = "Thermal Printer API"
APP_VERSION     = "1.0.0"
SERVICE_NAME    = "ThermalPrinterAPI"
SERVICE_DISPLAY = "Thermal Printer API - Hotelia"
SERVICE_DESC    = "API d'impression thermique POS. Demarre automatiquement au demarrage de Windows."
INSTALL_DIR     = Path(r"C:\Program Files\ThermalPrinterAPI")
SERVICE_EXE     = INSTALL_DIR / "thermal_printer_api.exe"
PYTHON_EMBED_DIR = INSTALL_DIR / "python"


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin():
    """Relance le meme exe avec les droits administrateur."""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)


def run(cmd, check=True):
    """Execute une commande et retourne (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd, capture_output=True, text=True, shell=True
    )
    return result.returncode, result.stdout, result.stderr


def get_source_dir():
    """
    Retourne le dossier source des fichiers a copier.
    - En mode PyInstaller : sys._MEIPASS (fichiers extraits du .exe)
    - En mode developpement : dossier du script
    """
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


# ---------------------------------------------------------------------------
# Etapes d'installation
# ---------------------------------------------------------------------------

def step_copy_files(log):
    """Copie les fichiers de l'application dans le dossier d'installation."""
    log("Copie des fichiers...")
    src = get_source_dir()

    if INSTALL_DIR.exists():
        # Conserver la configuration existante
        config_backup = None
        config_file = INSTALL_DIR / "printer_config.json"
        if config_file.exists():
            config_backup = config_file.read_text(encoding='utf-8')

        shutil.rmtree(INSTALL_DIR)

        if config_backup:
            INSTALL_DIR.mkdir(parents=True)
            config_file.write_text(config_backup, encoding='utf-8')

    INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    # Copier tous les fichiers/dossiers sources
    for item in src.iterdir():
        name = item.name
        # Ignorer les dossiers temporaires PyInstaller et les fichiers inutiles
        if name in ('__pycache__', '.claude', 'logs', 'static', '.git',
                    'dist', 'build', '__init__.py'):
            continue
        dest = INSTALL_DIR / name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True,
                           ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        else:
            shutil.copy2(item, dest)

    # Creer les dossiers necessaires
    (INSTALL_DIR / "logs").mkdir(exist_ok=True)
    (INSTALL_DIR / "static").mkdir(exist_ok=True)

    log("Fichiers copies.")


def step_install_dependencies(log):
    """Installe les dependances pip dans le dossier d'installation."""
    log("Installation des dependances Python...")

    req_file = INSTALL_DIR / "requirements.txt"
    if not req_file.exists():
        log("requirements.txt introuvable, etape ignoree.")
        return

    # Chercher python dans l'ordre de preference
    python_candidates = [
        sys.executable,
        r"C:\Python313\python.exe",
        r"C:\Python312\python.exe",
        r"C:\Python311\python.exe",
        r"C:\Python310\python.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe",
    ]
    # Ajouter Python depuis le PATH
    code, out, _ = run("where python")
    if code == 0:
        for p in out.strip().splitlines():
            python_candidates.insert(0, p.strip())

    python_exe = None
    for candidate in python_candidates:
        candidate = os.path.expandvars(candidate)
        if os.path.exists(candidate):
            python_exe = candidate
            break

    if not python_exe:
        log("Python introuvable — les dependances ne sont pas installees.")
        log("Installez Python 3.8+ depuis python.org si l'API ne demarre pas.")
        return

    code, out, err = run(
        f'"{python_exe}" -m pip install -r "{req_file}" --quiet'
    )
    if code == 0:
        log("Dependances installees.")
    else:
        log(f"Avertissement dependances : {(err or out)[:200]}")


def step_register_service(log):
    """Enregistre et configure le service Windows."""
    log("Enregistrement du service Windows...")

    # Supprimer l'ancien service si present
    run(f'net stop "{SERVICE_NAME}" >nul 2>&1')
    time.sleep(1)
    run(f'sc delete "{SERVICE_NAME}" >nul 2>&1')
    time.sleep(1)

    # Trouver python pour lancer le service
    python_candidates = [sys.executable]
    code, out, _ = run("where python")
    if code == 0:
        for p in out.strip().splitlines():
            python_candidates.insert(0, p.strip())

    python_exe = None
    for candidate in python_candidates:
        if os.path.exists(os.path.expandvars(candidate)):
            python_exe = os.path.expandvars(candidate)
            break

    if not python_exe:
        python_exe = sys.executable

    service_script = INSTALL_DIR / "service.py"
    bin_path = f'"{python_exe}" "{service_script}" run'

    code, out, err = run(
        f'sc create "{SERVICE_NAME}" '
        f'binPath= "{bin_path}" '
        f'DisplayName= "{SERVICE_DISPLAY}" '
        f'start= auto '
        f'obj= LocalSystem'
    )

    if code != 0:
        log(f"Erreur creation service (code {code}): {err or out}")
        return False

    # Description du service
    run(f'sc description "{SERVICE_NAME}" "{SERVICE_DESC}"')

    # Redemarrage automatique en cas de crash
    run(f'sc failure "{SERVICE_NAME}" reset= 60 actions= restart/5000/restart/10000/restart/30000')

    log("Service enregistre.")
    return True


def step_start_service(log):
    """Demarre le service."""
    log("Demarrage du service...")
    code, out, err = run(f'net start "{SERVICE_NAME}"')
    if code == 0:
        log("Service demarre.")
        return True
    else:
        log(f"Impossible de demarrer: {(err or out)[:150]}")
        log("Verifiez les logs dans : C:\\Program Files\\ThermalPrinterAPI\\logs\\")
        return False


def step_create_shortcut(log):
    """Cree un raccourci dans le menu Demarrer."""
    log("Creation du raccourci menu Demarrer...")
    try:
        import winshell
        from win32com.client import Dispatch

        start_menu = Path(os.environ.get('PROGRAMDATA', r'C:\ProgramData'))
        start_menu = start_menu / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        start_menu.mkdir(parents=True, exist_ok=True)

        shortcut_path = str(start_menu / f"{APP_DISPLAY}.lnk")
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = str(INSTALL_DIR / "start.bat")
        shortcut.WorkingDirectory = str(INSTALL_DIR)
        shortcut.Description = SERVICE_DESC
        shortcut.save()
        log("Raccourci cree.")
    except Exception as e:
        log(f"Raccourci non cree ({e}) — ignoré.")


def step_add_uninstaller(log):
    """Ecrit un script de desinstallation."""
    log("Creation du desinstallateur...")
    uninstall_script = INSTALL_DIR / "uninstall.bat"
    uninstall_script.write_text(
        f'@echo off\n'
        f'net stop "{SERVICE_NAME}"\n'
        f'sc delete "{SERVICE_NAME}"\n'
        f'timeout /t 2 /nobreak >nul\n'
        f'rd /s /q "{INSTALL_DIR}"\n'
        f'echo Desinstallation terminee.\n'
        f'pause\n',
        encoding='utf-8'
    )
    log("Desinstallateur cree.")


# ---------------------------------------------------------------------------
# Interface graphique de l'installateur
# ---------------------------------------------------------------------------

class InstallerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Installation — {APP_DISPLAY} v{APP_VERSION}")
        self.root.geometry("520x420")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")

        # Centrer la fenetre
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 520) // 2
        y = (self.root.winfo_screenheight() - 420) // 2
        self.root.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        bg = "#1a1a2e"
        fg = "#ffffff"
        accent = "#6c5ce7"

        # Titre
        tk.Label(self.root, text=f"Thermal Printer API", font=("Arial", 18, "bold"),
                 bg=bg, fg=accent).pack(pady=(20, 4))
        tk.Label(self.root, text=f"Version {APP_VERSION} — Service Windows",
                 font=("Arial", 10), bg=bg, fg="#a0a0a0").pack()

        # Dossier d'installation
        tk.Label(self.root, text=f"Dossier : {INSTALL_DIR}",
                 font=("Arial", 9), bg=bg, fg="#a0a0a0").pack(pady=(10, 0))

        # Barre de progression
        self.progress = ttk.Progressbar(self.root, length=460, mode='determinate')
        self.progress.pack(pady=(16, 0))

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar", troughcolor="#252541",
                        background=accent, thickness=18)

        # Zone de logs
        frame = tk.Frame(self.root, bg="#252541", bd=1, relief=tk.FLAT)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.log_text = tk.Text(frame, height=10, bg="#252541", fg="#d0d0d0",
                                font=("Courier New", 9), bd=0, state=tk.DISABLED,
                                wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Bouton
        self.btn = tk.Button(self.root, text="  Installer  ",
                             font=("Arial", 11, "bold"),
                             bg=accent, fg="white", relief=tk.FLAT,
                             activebackground="#5a4ec7", activeforeground="white",
                             cursor="hand2", command=self._start_install)
        self.btn.pack(pady=(0, 18))

    def log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"  {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.root.update()

    def set_progress(self, value):
        self.progress['value'] = value
        self.root.update()

    def _start_install(self):
        self.btn.configure(state=tk.DISABLED, text="Installation...")

        steps = [
            (10,  "Copie des fichiers",           step_copy_files),
            (35,  "Installation des dependances", step_install_dependencies),
            (65,  "Enregistrement du service",    step_register_service),
            (80,  "Demarrage du service",          step_start_service),
            (90,  "Raccourci menu Demarrer",       step_create_shortcut),
            (95,  "Creation desinstallateur",      step_add_uninstaller),
        ]

        success = True
        for progress_val, label, func in steps:
            self.log(f">>> {label}...")
            try:
                result = func(self.log)
                if result is False:
                    success = False
            except Exception as e:
                self.log(f"Erreur: {e}")
                success = False
            self.set_progress(progress_val)

        self.set_progress(100)

        if success:
            self.log("")
            self.log("Installation terminee !")
            self.log(f"API disponible sur http://localhost:5789")
            self.btn.configure(state=tk.NORMAL, text="  Fermer  ",
                               command=self.root.destroy, bg="#00b894")
            messagebox.showinfo(
                "Installation reussie",
                f"{APP_DISPLAY} est installe et demarre automatiquement avec Windows.\n\n"
                f"API accessible sur :\nhttp://localhost:5789"
            )
        else:
            self.log("")
            self.log("Installation avec avertissements.")
            self.log("Consultez les logs si l'API ne repond pas.")
            self.btn.configure(state=tk.NORMAL, text="  Fermer  ",
                               command=self.root.destroy)

    def run(self):
        self.root.mainloop()


# ---------------------------------------------------------------------------
# Point d'entree
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    # Demander les droits admin si necessaire
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable,
            f'"{os.path.abspath(__file__)}"', None, 1
        )
        sys.exit(0)

    app = InstallerGUI()
    app.run()
