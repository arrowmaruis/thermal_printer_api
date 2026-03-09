#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Service Windows pour l'API d'impression thermique.

Ce module permet d'installer l'API comme un service Windows qui :
  - Demarre automatiquement avec Windows
  - Tourne en arriere-plan (aucune fenetre)
  - Se gere depuis les Services Windows ou la ligne de commande

Commandes (en tant qu'Administrateur) :
  python service.py install    -> Installer le service
  python service.py start      -> Demarrer le service
  python service.py stop       -> Arreter le service
  python service.py restart    -> Redemarrer le service
  python service.py remove     -> Desinstaller le service
  python service.py status     -> Afficher le statut
  python service.py debug      -> Lancer en mode debug (fenetre visible)
"""

import sys
import os
import time
import threading
import subprocess

# S'assurer que le repertoire du script est dans le path
SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SERVICE_DIR)

SERVICE_NAME = "ThermalPrinterAPI"
SERVICE_DISPLAY = "Thermal Printer API - Hotelia"
SERVICE_DESCRIPTION = (
    "API d'impression thermique pour imprimantes POS. "
    "Demarre automatiquement et ecoute sur le port 5789."
)


# ---------------------------------------------------------------------------
# Classe du service Windows
# ---------------------------------------------------------------------------

class ThermalPrinterService:
    """Service Windows pour l'API Flask d'impression thermique."""

    def __init__(self):
        # Changer le repertoire de travail vers le dossier du projet
        os.chdir(SERVICE_DIR)

    def start(self):
        """Demarre le serveur Flask dans un thread daemon."""
        self._running = True
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()

    def stop(self):
        """Arrete le service proprement."""
        self._running = False

    def _run_server(self):
        """Lance le serveur Flask."""
        try:
            from utils.config import load_config, logger, config
            load_config()
            logger.info(f"Service {SERVICE_NAME} demarre depuis {SERVICE_DIR}")

            from api.server import create_app
            app = create_app()

            host = config.get('host', '0.0.0.0')
            port = config.get('port', 5789)

            logger.info(f"API en ecoute sur http://{host}:{port}")
            # use_reloader=False obligatoire dans un service / thread
            app.run(host=host, port=port, use_reloader=False, threaded=True)
        except Exception as e:
            # Ecrire l'erreur dans un fichier log de secours
            _log_error(f"Erreur critique dans le service: {e}")


def _log_error(message):
    """Ecrit un message d'erreur dans un fichier de log de secours."""
    try:
        log_path = os.path.join(SERVICE_DIR, 'logs', 'service_error.log')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            import datetime
            f.write(f"[{datetime.datetime.now()}] {message}\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Integration pywin32 (win32serviceutil)
# ---------------------------------------------------------------------------

def _run_as_win32_service():
    """Lance le service via win32serviceutil si disponible."""
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager

    class Win32Service(win32serviceutil.ServiceFramework):
        _svc_name_ = SERVICE_NAME
        _svc_display_name_ = SERVICE_DISPLAY
        _svc_description_ = SERVICE_DESCRIPTION

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self._stop_event = win32event.CreateEvent(None, 0, 0, None)
            self._service = ThermalPrinterService()

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            self._service.stop()
            win32event.SetEvent(self._stop_event)

        def SvcDoRun(self):
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            self._service.start()
            # Attendre le signal d'arret
            win32event.WaitForSingleObject(self._stop_event, win32event.INFINITE)

    win32serviceutil.HandleCommandLine(Win32Service)


# ---------------------------------------------------------------------------
# Commandes de gestion (sans win32serviceutil)
# ---------------------------------------------------------------------------

def _get_python_exe():
    return sys.executable


def _run_service_command(cmd):
    """Execute une commande sc.exe ou net pour gerer le service."""
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.returncode, result.stdout, result.stderr


def _get_short_path(path):
    """Retourne le chemin court 8.3 Windows (sans espaces) via GetShortPathNameW."""
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(512)
        ctypes.windll.kernel32.GetShortPathNameW(str(path), buf, 512)
        short = buf.value
        if short:
            return short
    except Exception:
        pass
    return str(path)


def install_service():
    """Installe le service Windows via sc.exe."""
    python = _get_short_path(_get_python_exe())
    script = _get_short_path(os.path.abspath(__file__))

    print(f"Installation du service '{SERVICE_NAME}'...")
    code, out, err = _run_service_command(
        f'sc create "{SERVICE_NAME}" '
        f'binPath= "{python} {script} run" '
        f'DisplayName= "{SERVICE_DISPLAY}" '
        f'start= auto '
        f'obj= LocalSystem'
    )
    if code == 0:
        # Ajouter la description
        _run_service_command(
            f'sc description "{SERVICE_NAME}" "{SERVICE_DESCRIPTION}"'
        )
        # Configurer le redemarrage automatique en cas d'erreur
        _run_service_command(
            f'sc failure "{SERVICE_NAME}" reset= 60 actions= restart/5000/restart/10000/restart/30000'
        )
        print(f"Service '{SERVICE_NAME}' installe avec succes.")
        print("Demarrez-le avec : python service.py start")
        print("Ou depuis : Services Windows (services.msc)")
    else:
        print(f"Erreur installation (code {code}): {err or out}")
        if 'deja existe' in (err + out).lower() or '1073' in str(code):
            print("Le service existe deja. Utilisez 'remove' puis 're-installez'.")


def start_service():
    print(f"Demarrage du service '{SERVICE_NAME}'...")
    code, out, err = _run_service_command(f'net start "{SERVICE_NAME}"')
    if code == 0:
        print("Service demarre.")
    else:
        print(f"Erreur: {err or out}")


def stop_service():
    print(f"Arret du service '{SERVICE_NAME}'...")
    code, out, err = _run_service_command(f'net stop "{SERVICE_NAME}"')
    if code == 0:
        print("Service arrete.")
    else:
        print(f"Erreur: {err or out}")


def remove_service():
    stop_service()
    time.sleep(2)
    print(f"Suppression du service '{SERVICE_NAME}'...")
    code, out, err = _run_service_command(f'sc delete "{SERVICE_NAME}"')
    if code == 0:
        print("Service supprime.")
    else:
        print(f"Erreur: {err or out}")


def service_status():
    code, out, err = _run_service_command(f'sc query "{SERVICE_NAME}"')
    if 'RUNNING' in out:
        print(f"Statut: EN COURS D'EXECUTION")
    elif 'STOPPED' in out:
        print(f"Statut: ARRETE")
    elif 'does not exist' in (out + err).lower() or code != 0:
        print(f"Statut: NON INSTALLE")
    else:
        print(out)


def run_service():
    """Point d'entree quand le service est lance par le gestionnaire Windows."""
    service = ThermalPrinterService()
    service.start()
    # Garder le processus en vie
    try:
        while True:
            time.sleep(10)
    except (KeyboardInterrupt, SystemExit):
        service.stop()


def run_debug():
    """Lance l'API en mode debug (fenetre visible, Ctrl+C pour arreter)."""
    print(f"Mode DEBUG — API d'impression thermique")
    print(f"Repertoire: {SERVICE_DIR}")
    print(f"Ctrl+C pour arreter\n")
    service = ThermalPrinterService()
    service.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArret demande.")
        service.stop()


# ---------------------------------------------------------------------------
# Point d'entree
# ---------------------------------------------------------------------------

COMMANDS = {
    'install': install_service,
    'start':   start_service,
    'stop':    stop_service,
    'restart': lambda: (stop_service(), time.sleep(2), start_service()),
    'remove':  remove_service,
    'status':  service_status,
    'run':     run_service,    # utilise en interne par sc.exe
    'debug':   run_debug,
}

if __name__ == '__main__':
    # Essayer d'abord win32serviceutil (gestion native plus robuste)
    if len(sys.argv) >= 2 and sys.argv[1] in ('install', 'remove', 'start', 'stop',
                                                'restart', 'debug', 'status', 'update'):
        try:
            _run_as_win32_service()
            sys.exit(0)
        except Exception:
            pass  # pywin32 indisponible ou erreur — fallback sc.exe

    # Fallback : commandes manuelles via sc.exe / net
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        print(f"\nCommandes disponibles: {', '.join(c for c in COMMANDS if c != 'run')}")
        sys.exit(1)

    COMMANDS[sys.argv[1]]()
