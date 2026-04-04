#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Thermal Printer API - Binaire de service Windows autonome.

Ce fichier est compile par PyInstaller en ThermalPrinterAPI.exe.
Il ne necessite PAS Python installe sur la machine cible.

Comportement :
  - Lance par le gestionnaire de services Windows (SCM) -> mode service silencieux
  - Lance directement (double-clic) -> mode console, affiche les logs
"""

import sys
import os
import threading
import ctypes
import ctypes.wintypes
import time

# ---------------------------------------------------------------------------
# Repertoire d'installation (fonctionne en mode gele et en mode dev)
# ---------------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    # Exe PyInstaller : l'exe se trouve dans le dossier d'installation
    SERVICE_DIR = os.path.dirname(sys.executable)
else:
    SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))

# S'assurer que les modules Python internes (api/, utils/, printer/) sont trouvables.
# En mode gele, sys._MEIPASS contient les modules extraits.
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    if sys._MEIPASS not in sys.path:
        sys.path.insert(0, sys._MEIPASS)
else:
    if SERVICE_DIR not in sys.path:
        sys.path.insert(0, SERVICE_DIR)

# Creer les dossiers necessaires
LOG_DIR    = os.path.join(SERVICE_DIR, 'logs')
STATIC_DIR = os.path.join(SERVICE_DIR, 'static')
os.makedirs(LOG_DIR,    exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Implementation du service Windows via ctypes (sans pywin32)
# ---------------------------------------------------------------------------
SERVICE_WIN32_OWN_PROCESS = 0x10
SERVICE_CONTROL_STOP      = 1
SERVICE_CONTROL_SHUTDOWN  = 5
SERVICE_START_PENDING     = 2
SERVICE_RUNNING           = 4
SERVICE_STOP_PENDING      = 3
SERVICE_STOPPED           = 1
SERVICE_ACCEPT_STOP       = 1
NO_ERROR                  = 0

SERVICE_NAME = "ThermalPrinterAPI"


class _SERVICE_STATUS(ctypes.Structure):
    _fields_ = [
        ("dwServiceType",             ctypes.wintypes.DWORD),
        ("dwCurrentState",            ctypes.wintypes.DWORD),
        ("dwControlsAccepted",        ctypes.wintypes.DWORD),
        ("dwWin32ExitCode",           ctypes.wintypes.DWORD),
        ("dwServiceSpecificExitCode", ctypes.wintypes.DWORD),
        ("dwCheckPoint",              ctypes.wintypes.DWORD),
        ("dwWaitHint",                ctypes.wintypes.DWORD),
    ]


advapi32   = ctypes.windll.advapi32
_h_status  = None
_stop_event = threading.Event()

_CTRL_FUNC = ctypes.WINFUNCTYPE(None, ctypes.wintypes.DWORD)

# Déclaration explicite des types pour les fonctions advapi32.
# CRITIQUE : sans cela, sur Windows 64-bit les handles (64-bit) sont tronqués
# en c_int (32-bit) par défaut, ce qui corrompt tous les appels suivants.
advapi32.RegisterServiceCtrlHandlerW.restype  = ctypes.c_void_p
advapi32.RegisterServiceCtrlHandlerW.argtypes = [ctypes.c_wchar_p, _CTRL_FUNC]
advapi32.SetServiceStatus.restype             = ctypes.wintypes.BOOL
advapi32.SetServiceStatus.argtypes            = [ctypes.c_void_p,
                                                  ctypes.POINTER(_SERVICE_STATUS)]
advapi32.StartServiceCtrlDispatcherW.restype  = ctypes.wintypes.BOOL


def _ctrl_handler(ctrl_code):
    if ctrl_code in (SERVICE_CONTROL_STOP, SERVICE_CONTROL_SHUTDOWN):
        _report_status(SERVICE_STOP_PENDING, wait_hint=5000)
        _stop_event.set()


_ctrl_handler_cb = _CTRL_FUNC(_ctrl_handler)  # garder la reference alive


def _report_status(state, exit_code=NO_ERROR, wait_hint=0):
    global _h_status
    if _h_status is None:
        return
    ss = _SERVICE_STATUS(
        dwServiceType             = SERVICE_WIN32_OWN_PROCESS,
        dwCurrentState            = state,
        dwControlsAccepted        = SERVICE_ACCEPT_STOP if state == SERVICE_RUNNING else 0,
        dwWin32ExitCode           = exit_code,
        dwServiceSpecificExitCode = 0,
        dwCheckPoint              = 0,
        dwWaitHint                = wait_hint,
    )
    advapi32.SetServiceStatus(_h_status, ctypes.byref(ss))


_SVC_MAIN_FUNC = ctypes.WINFUNCTYPE(
    None, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.c_wchar_p)
)


def _service_main(argc, argv):
    """Appelee par le SCM quand le service demarre."""
    global _h_status

    svc_name = argv[0] if argc > 0 else SERVICE_NAME

    _h_status = advapi32.RegisterServiceCtrlHandlerW(svc_name, _ctrl_handler_cb)
    if not _h_status:
        _log_error("RegisterServiceCtrlHandlerW a echoue")
        return

    _report_status(SERVICE_START_PENDING, wait_hint=15000)

    # Changer le repertoire courant vers le dossier d'installation
    os.chdir(SERVICE_DIR)

    # Lancer Flask dans un thread daemon
    flask_thread = threading.Thread(target=_run_flask, daemon=True)
    flask_thread.start()

    _report_status(SERVICE_RUNNING)

    # Attendre le signal d'arret (STOP/SHUTDOWN)
    _stop_event.wait()

    _report_status(SERVICE_STOPPED)


_svc_main_cb = _SVC_MAIN_FUNC(_service_main)


class _ServiceTableEntry(ctypes.Structure):
    _fields_ = [
        ("lpServiceName", ctypes.c_wchar_p),
        ("lpServiceProc", _SVC_MAIN_FUNC),
    ]


def _start_as_service():
    """
    Tente de se connecter au SCM.
    Retourne True si on est lance par le gestionnaire de services.
    Retourne False si on est lance directement (console).
    """
    table = (_ServiceTableEntry * 2)()
    table[0].lpServiceName = SERVICE_NAME
    table[0].lpServiceProc = _svc_main_cb
    table[1].lpServiceName = None
    table[1].lpServiceProc = ctypes.cast(None, _SVC_MAIN_FUNC)
    return bool(advapi32.StartServiceCtrlDispatcherW(table))


# ---------------------------------------------------------------------------
# Serveur Flask
# ---------------------------------------------------------------------------
def _log_error(msg):
    try:
        import traceback
        log_path = os.path.join(LOG_DIR, 'service_error.log')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
            if sys.exc_info()[0]:
                f.write(traceback.format_exc())
    except Exception:
        pass


def _run_flask():
    """Lance le serveur Flask. Appelee dans un thread daemon."""
    try:
        os.chdir(SERVICE_DIR)
        from utils.config import load_config, config
        load_config()
        from api.server import create_app
        app = create_app()
        host = config.get('host', '0.0.0.0')
        port = config.get('port', 5789)
        app.run(host=host, port=port, use_reloader=False, threaded=True)
    except Exception as e:
        _log_error(f"Erreur critique Flask : {e}")


# ---------------------------------------------------------------------------
# Point d'entree
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    if sys.platform != 'win32':
        # Linux / Mac : mode console direct
        _run_flask()
    elif not _start_as_service():
        # Lance directement (pas par le SCM) : mode console
        print("[ThermalPrinterAPI] Demarrage en mode console...")
        print("[ThermalPrinterAPI] API disponible sur http://localhost:5789")
        print("[ThermalPrinterAPI] Appuyez sur Ctrl+C pour arreter.\n")
        os.chdir(SERVICE_DIR)
        _run_flask()
        try:
            while True:
                time.sleep(10)
        except (KeyboardInterrupt, SystemExit):
            print("\n[ThermalPrinterAPI] Arret.")
    # Si _start_as_service() retourne True :
    # tout a ete gere dans _service_main() via le SCM.
