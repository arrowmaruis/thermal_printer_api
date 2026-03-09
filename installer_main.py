#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Installateur graphique de Thermal Printer API.

Ce fichier est compile par PyInstaller en ThermalPrinterAPI_Setup.exe.
Il embarque ThermalPrinterAPI.exe (le serveur Flask autonome).

Ce que fait l'installateur :
  1. Verifie les droits administrateur (se relance si necessaire)
  2. Copie ThermalPrinterAPI.exe dans C:\Program Files\ThermalPrinterAPI\
  3. Enregistre le service Windows (demarrage auto via sc.exe)
  4. Demarre le service immediatement
  5. Cree un raccourci dans le menu Demarrer

Aucun Python ni pip requis sur la machine cible.
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
SERVICE_EXE     = INSTALL_DIR / "ThermalPrinterAPI.exe"


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run(cmd):
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


def _get_short_path(path):
    """Retourne le chemin court 8.3 Windows (sans espaces) via GetShortPathNameW."""
    try:
        buf = ctypes.create_unicode_buffer(512)
        ctypes.windll.kernel32.GetShortPathNameW(str(path), buf, 512)
        short = buf.value
        if short:
            return short
    except Exception:
        pass
    return str(path)


# ---------------------------------------------------------------------------
# Etapes d'installation
# ---------------------------------------------------------------------------

def step_copy_files(log):
    """Copie ThermalPrinterAPI.exe et les ressources dans le dossier d'installation."""
    log("Copie des fichiers...")
    src = get_source_dir()

    if INSTALL_DIR.exists():
        # Conserver la configuration existante
        config_backup = None
        config_file = INSTALL_DIR / "printer_config.json"
        if config_file.exists():
            config_backup = config_file.read_text(encoding='utf-8')

        try:
            shutil.rmtree(INSTALL_DIR)
        except Exception as e:
            log(f"Avertissement nettoyage : {e}")

        if config_backup:
            INSTALL_DIR.mkdir(parents=True)
            config_file.write_text(config_backup, encoding='utf-8')

    INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    # Fichiers a copier depuis la source embarquee
    files_to_copy = ["ThermalPrinterAPI.exe", "logo.png", "icon.ico", "README.md"]
    for fname in files_to_copy:
        src_file = src / fname
        if src_file.exists():
            shutil.copy2(src_file, INSTALL_DIR / fname)

    # Creer les dossiers necessaires
    (INSTALL_DIR / "logs").mkdir(exist_ok=True)
    (INSTALL_DIR / "static").mkdir(exist_ok=True)

    # Generer start.bat pour lancement manuel
    (INSTALL_DIR / "start.bat").write_text(
        f'@echo off\n'
        f'echo Demarrage de {APP_DISPLAY}...\n'
        f'"{SERVICE_EXE}"\n',
        encoding='utf-8'
    )

    log("Fichiers copies.")


def step_register_service(log):
    """Enregistre le service Windows via sc.exe — pas de Python requis."""
    log("Enregistrement du service Windows...")

    # Supprimer l'ancien service si present
    run(f'net stop "{SERVICE_NAME}"')
    time.sleep(1)
    run(f'sc delete "{SERVICE_NAME}"')
    time.sleep(2)

    if not SERVICE_EXE.exists():
        log(f"Erreur : ThermalPrinterAPI.exe introuvable dans {INSTALL_DIR}")
        return False

    # Chemin court 8.3 pour eviter les espaces dans binPath
    # C:\Program Files -> C:\PROGRA~1 (pas d'espace)
    exe_short = _get_short_path(str(SERVICE_EXE))
    log(f"Binaire : {exe_short}")

    sc_cmd = (
        f'sc create "{SERVICE_NAME}"'
        f' binPath= "{exe_short}"'
        f' DisplayName= "{SERVICE_DISPLAY}"'
        f' start= auto'
        f' obj= LocalSystem'
    )
    code, out, err = run(sc_cmd)
    if code != 0:
        log(f"Erreur creation service (code {code}) : {(err or out)[:200]}")
        return False

    run(f'sc description "{SERVICE_NAME}" "{SERVICE_DESC}"')
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
        log(f"Impossible de demarrer : {(err or out)[:150]}")
        log(f"Consultez : {INSTALL_DIR}\\logs\\")
        return False


def step_create_shortcut(log):
    """Cree un raccourci dans le menu Demarrer."""
    log("Creation du raccourci menu Demarrer...")
    try:
        from win32com.client import Dispatch

        start_menu = Path(os.environ.get('PROGRAMDATA', r'C:\ProgramData'))
        start_menu = start_menu / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        start_menu.mkdir(parents=True, exist_ok=True)

        shortcut_path = str(start_menu / f"{APP_DISPLAY}.lnk")
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = str(SERVICE_EXE)
        shortcut.WorkingDirectory = str(INSTALL_DIR)
        shortcut.Description = SERVICE_DESC
        icon_path = INSTALL_DIR / "icon.ico"
        if icon_path.exists():
            shortcut.IconLocation = str(icon_path)
        shortcut.save()
        log("Raccourci cree.")
    except Exception as e:
        log(f"Raccourci non cree ({e}) — ignore.")


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
        self.root.geometry("520x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")

        # Centrer la fenetre
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 520) // 2
        y = (self.root.winfo_screenheight() - 480) // 2
        self.root.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        bg     = "#1a1a2e"
        accent = "#6c5ce7"

        # Logo
        try:
            from PIL import Image, ImageTk
            logo_path = get_source_dir() / "logo.png"
            if logo_path.exists():
                img = Image.open(logo_path).resize((72, 72), Image.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
                tk.Label(self.root, image=self._logo_img, bg=bg).pack(pady=(16, 4))
        except Exception:
            pass

        tk.Label(self.root, text="Thermal Printer API",
                 font=("Arial", 18, "bold"), bg=bg, fg=accent).pack(pady=(4, 4))
        tk.Label(self.root, text=f"Version {APP_VERSION} — Service Windows autonome",
                 font=("Arial", 10), bg=bg, fg="#a0a0a0").pack()
        tk.Label(self.root, text=f"Dossier : {INSTALL_DIR}",
                 font=("Arial", 9), bg=bg, fg="#a0a0a0").pack(pady=(10, 0))

        self.progress = ttk.Progressbar(self.root, length=460, mode='determinate')
        self.progress.pack(pady=(16, 0))

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar", troughcolor="#252541",
                        background=accent, thickness=18)

        frame = tk.Frame(self.root, bg="#252541", bd=1, relief=tk.FLAT)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.log_text = tk.Text(frame, height=10, bg="#252541", fg="#d0d0d0",
                                font=("Courier New", 9), bd=0, state=tk.DISABLED,
                                wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.btn = tk.Button(self.root, text="  Installer  ",
                             font=("Arial", 11, "bold"),
                             bg=accent, fg="white", relief=tk.FLAT,
                             activebackground="#5a4ec7", activeforeground="white",
                             cursor="hand2", command=self._start_install)
        self.btn.pack(pady=(0, 18))

    def log(self, message):
        def _update():
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"  {message}\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.root.after(0, _update)

    def set_progress(self, value):
        self.root.after(0, lambda: self.progress.configure(value=value))

    def _start_install(self):
        self.btn.configure(state=tk.DISABLED, text="Installation...")
        import threading
        threading.Thread(target=self._run_install, daemon=True).start()

    def _run_install(self):
        steps = [
            (20,  "Copie des fichiers",        step_copy_files),
            (55,  "Enregistrement du service", step_register_service),
            (75,  "Demarrage du service",       step_start_service),
            (90,  "Raccourci menu Demarrer",    step_create_shortcut),
            (95,  "Creation desinstallateur",   step_add_uninstaller),
        ]

        success = True
        for progress_val, label, func in steps:
            self.log(f">>> {label}...")
            try:
                result = func(self.log)
                if result is False:
                    success = False
            except Exception as e:
                self.log(f"Erreur : {e}")
                success = False
            self.set_progress(progress_val)

        self.set_progress(100)
        self.root.after(0, lambda: self._finish_install(success))

    def _finish_install(self, success):
        if success:
            self.log("")
            self.log("Installation terminee !")
            self.log("API disponible sur http://localhost:5789")
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
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable,
            f'"{os.path.abspath(__file__)}"', None, 1
        )
        sys.exit(0)

    app = InstallerGUI()
    app.run()
