#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilitaires pour l'impression via Bluetooth.

Deux methodes de connexion supportees :
  1. Port COM (methode principale sur Windows) :
     Les imprimantes BT appairees apparaissent comme un port COM virtuel (ex: COM3).
     Utilise pyserial pour ecrire directement sur ce port.

  2. Socket RFCOMM (connexion directe par adresse MAC) :
     Utilise pybluez (bluetooth) si installe, sinon socket Windows AF_BTH.
     Permet de se connecter sans avoir d'abord appaire l'imprimante.
"""

import socket
from datetime import datetime
from utils.config import logger


# ---------------------------------------------------------------------------
# Detection des ports COM
# ---------------------------------------------------------------------------

def get_all_com_ports():
    """
    Retourne tous les ports COM disponibles (Bluetooth et serie classique).

    Returns:
        list[dict]: Liste de ports avec 'port', 'name', 'hwid', 'is_bluetooth'
    """
    ports = []
    try:
        import serial.tools.list_ports
        for p in serial.tools.list_ports.comports():
            desc = (p.description or '').lower()
            hwid = (p.hwid or '').lower()
            is_bt = 'bluetooth' in desc or 'bth' in hwid or 'rfcomm' in desc
            ports.append({
                'port': p.device,
                'name': p.description,
                'hwid': p.hwid,
                'is_bluetooth': is_bt,
                'type': 'bluetooth_com' if is_bt else 'serial_com',
            })
    except ImportError:
        logger.error("Module 'pyserial' manquant. Installez-le: pip install pyserial")
    except Exception as e:
        logger.error(f"Erreur liste ports COM: {e}")
    return ports


def get_bluetooth_com_ports():
    """
    Retourne uniquement les ports COM identifies comme Bluetooth.

    Returns:
        list[dict]: Ports COM Bluetooth uniquement
    """
    return [p for p in get_all_com_ports() if p['is_bluetooth']]


# ---------------------------------------------------------------------------
# Decouverte Bluetooth (scan radio)
# ---------------------------------------------------------------------------

def discover_bluetooth_devices(duration=8):
    """
    Scanne les appareils Bluetooth a portee.
    Necessite le module 'bluetooth' (pybluez) : pip install pybluez

    Args:
        duration (int): Duree du scan en secondes

    Returns:
        list[dict]: Appareils trouves avec 'address', 'name', 'is_printer'
    """
    devices = []
    try:
        import bluetooth
        nearby = bluetooth.discover_devices(
            duration=duration,
            lookup_names=True,
            lookup_class=True,
            flush_cache=True,
        )
        for addr, name, device_class in nearby:
            # Classe d'appareil 0x600 = imprimante (bits 8-12)
            is_printer = bool((device_class & 0x1F00) == 0x600)
            devices.append({
                'address': addr,
                'name': name or 'Inconnu',
                'device_class': device_class,
                'is_printer': is_printer,
                'type': 'bluetooth_device',
            })
        logger.info(f"{len(devices)} appareils Bluetooth decouverts")
    except ImportError:
        logger.warning("Module 'bluetooth' (pybluez) non installe. Impossible de scanner.")
        return {'error': 'pybluez non installe', 'devices': []}
    except Exception as e:
        logger.error(f"Erreur scan Bluetooth: {e}")
    return devices


# ---------------------------------------------------------------------------
# Impression via port COM (methode principale)
# ---------------------------------------------------------------------------

def print_via_com_port(port, data, baudrate=9600, timeout=5):
    """
    Envoie des donnees ESC/POS vers une imprimante via un port COM.

    Args:
        port (str): Ex: 'COM3', 'COM4'
        data (bytes): Donnees ESC/POS
        baudrate (int): 9600 par defaut (standard imprimantes thermiques BT)
        timeout (int): Timeout en secondes

    Returns:
        bool: True si succes
    """
    try:
        import serial
        with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:
            ser.write(data)
            ser.flush()
        logger.info(f"Impression OK via port COM {port}")
        return True
    except ImportError:
        logger.error("Module 'pyserial' manquant. Installez-le: pip install pyserial")
        return False
    except Exception as e:
        logger.error(f"Erreur impression port COM {port}: {e}")
        return False


# ---------------------------------------------------------------------------
# Impression via socket Bluetooth (adresse MAC)
# ---------------------------------------------------------------------------

def print_via_bluetooth_socket(address, data, rfcomm_port=1, timeout=10):
    """
    Envoie des donnees ESC/POS directement via une socket RFCOMM Bluetooth.

    Essaie d'abord pybluez, puis le socket Windows AF_BTH en fallback.

    Args:
        address (str): Adresse MAC, ex: 'AA:BB:CC:DD:EE:FF'
        data (bytes): Donnees ESC/POS
        rfcomm_port (int): Canal RFCOMM (1 par defaut)
        timeout (int): Timeout en secondes

    Returns:
        bool: True si succes
    """
    sock = None
    try:
        # --- Tentative 1: pybluez ---
        try:
            import bluetooth
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            logger.debug(f"Connexion BT via pybluez vers {address}:{rfcomm_port}")
        except ImportError:
            # --- Tentative 2: socket Windows AF_BTH ---
            logger.debug(f"pybluez absent, utilisation socket AF_BTH vers {address}:{rfcomm_port}")
            AF_BTH = 32          # valeur Windows
            BTPROTO_RFCOMM = 3
            sock = socket.socket(AF_BTH, socket.SOCK_STREAM, BTPROTO_RFCOMM)

        sock.settimeout(timeout)
        sock.connect((address, rfcomm_port))
        sock.sendall(data)
        logger.info(f"Impression BT OK vers {address}")
        return True

    except Exception as e:
        logger.error(f"Erreur connexion Bluetooth {address}: {e}")
        return False
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Ticket de test
# ---------------------------------------------------------------------------

def build_test_ticket(display_name, connection_type):
    """Construit les bytes ESC/POS d'un ticket de test Bluetooth."""
    from printer.printer_utils import (
        get_robust_init_command, get_robust_cut_command,
        get_codepage_command, safe_encode_french,
        ESC_CENTER, ESC_LEFT, ESC_BOLD_ON, ESC_BOLD_OFF,
        ESC_DOUBLE_HEIGHT_ON, ESC_DOUBLE_HEIGHT_OFF,
    )

    enc = 'ascii'
    commands = bytearray()
    commands.extend(get_robust_init_command())
    commands.extend(get_codepage_command(enc))

    commands.extend(ESC_CENTER)
    commands.extend(ESC_BOLD_ON)
    commands.extend(ESC_DOUBLE_HEIGHT_ON)
    commands.extend(safe_encode_french("TEST BLUETOOTH", enc))
    commands.extend(b'\n')
    commands.extend(ESC_DOUBLE_HEIGHT_OFF)
    commands.extend(ESC_BOLD_OFF)
    commands.extend(b'\n')

    commands.extend(ESC_LEFT)
    commands.extend(safe_encode_french(f"Imprimante: {display_name}", enc))
    commands.extend(b'\n')
    commands.extend(safe_encode_french(f"Connexion: {connection_type.upper()}", enc))
    commands.extend(b'\n')
    commands.extend(safe_encode_french(
        f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", enc))
    commands.extend(b'\n\n')

    commands.extend(ESC_CENTER)
    commands.extend(ESC_BOLD_ON)
    commands.extend(safe_encode_french("*** CONNEXION BT OK ***", enc))
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_OFF)
    commands.extend(get_robust_cut_command())

    return bytes(commands)


def test_bluetooth_printer_com(port):
    """Test d'impression via port COM."""
    data = build_test_ticket(port, 'COM')
    return print_via_com_port(port, data)


def test_bluetooth_printer_socket(address, rfcomm_port=1):
    """Test d'impression via socket Bluetooth."""
    data = build_test_ticket(address, 'SOCKET')
    return print_via_bluetooth_socket(address, data, rfcomm_port)
