#!/usr/bin/env python
# -*- coding: utf-8 -*-

import win32print
from datetime import datetime
from utils.config import logger

# Commandes ESC/POS de base
ESC_INIT = b'\x1b\x40'  # Initialiser l'imprimante
ESC_BOLD_ON = b'\x1b\x45\x01'  # Activer le gras
ESC_BOLD_OFF = b'\x1b\x45\x00'  # Désactiver le gras
ESC_DOUBLE_HEIGHT_ON = b'\x1b\x21\x10'  # Activer double hauteur
ESC_DOUBLE_HEIGHT_OFF = b'\x1b\x21\x00'  # Désactiver double hauteur
ESC_CENTER = b'\x1b\x61\x01'  # Centrer le texte
ESC_LEFT = b'\x1b\x61\x00'  # Aligner à gauche
ESC_RIGHT = b'\x1b\x61\x02'  # Aligner à droite
ESC_CUT = b'\x1d\x56\x41'  # Couper le papier
ESC_FEED = b'\x1b\x64'  # Avancer le papier

def detect_printer_width(printer_name):
    """
    Tente de détecter automatiquement si l'imprimante est 58mm ou 80mm
    basé sur les informations du pilote et les capacités.
    
    Returns:
        str: "80mm" ou "58mm" (par défaut si indéterminé)
    """
    try:
        # Ouvrir l'imprimante pour accéder à ses propriétés
        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            # Obtenir les informations sur l'imprimante
            printer_info = win32print.GetPrinter(hPrinter, 2)
            
            # Extraire des indices à partir du nom et du pilote
            driver_name = printer_info.get('pDriverName', '').lower()
            port_name = printer_info.get('pPortName', '').lower()
            printer_name_lower = printer_name.lower()
            
            # Liste des mots-clés qui indiquent une imprimante 80mm
            keywords_80mm = ['80mm', '80 mm', 'pos80', 'tm-t88', 'tmt88', 
                           'tm88', 't88', 'tm-t20', 'tmt20', 't20',
                           '3inch', '3 inch', '80', 'large', 'wide']
            
            # Liste des mots-clés qui indiquent une imprimante 58mm
            keywords_58mm = ['58mm', '58 mm', 'pos58', 'tm-t20mini', 
                           'tmt20mini', '2inch', '2 inch', '58', 
                           'mini', 'compact', 'narrow']
            
            # Vérifier les mots-clés dans les noms et pilotes
            text_to_check = f"{printer_name_lower} {driver_name} {port_name}"
            
            for keyword in keywords_80mm:
                if keyword in text_to_check:
                    logger.info(f"Détection: {printer_name} identifiée comme imprimante 80mm")
                    return "80mm"
                    
            for keyword in keywords_58mm:
                if keyword in text_to_check:
                    logger.info(f"Détection: {printer_name} identifiée comme imprimante 58mm")
                    return "58mm"
            
            # Obtenir les capacités de l'imprimante (taille du papier)
            # Certains pilotes exposent ces informations
            try:
                printer_caps = win32print.DeviceCapabilities(printer_name, port_name, 
                                                           win32print.DC_PAPERSIZE)
                if printer_caps:
                    # Les dimensions sont en dixièmes de millimètres
                    # Chercher la largeur (x10) la plus proche de nos valeurs cibles
                    # 58mm = 580, 80mm = 800
                    widths = [size[0] for size in printer_caps]
                    if any(w > 700 for w in widths):  # Probablement 80mm ou plus
                        return "80mm"
                    elif any(500 <= w <= 700 for w in widths):  # Probablement 58mm
                        return "58mm"
            except:
                pass  # Continuer si cette méthode échoue
            
            # Si aucune détection n'a fonctionné, essayer une autre approche
            # Obtenir les capacités physiques
            try:
                paper_width = win32print.DeviceCapabilities(printer_name, port_name, 
                                                          win32print.DC_PAPERWIDTH)
                if paper_width:
                    # La valeur est en dixièmes de millimètres
                    width_mm = paper_width / 10
                    if width_mm >= 70:  # Probablement 80mm
                        return "80mm"
                    elif width_mm >= 50:  # Probablement 58mm
                        return "58mm"
            except:
                pass  # Continuer si cette méthode échoue
                
            # Valeur par défaut si aucune détection n'a fonctionné
            logger.info(f"Impossible de détecter automatiquement la largeur pour {printer_name}, utilisation de 58mm par défaut")
            return "58mm"
            
        finally:
            win32print.ClosePrinter(hPrinter)
    except Exception as e:
        logger.error(f"Erreur lors de la détection de la largeur pour {printer_name}: {e}")
        return "58mm"  # Valeur par défaut en cas d'erreur

def get_printers():
    """Récupère la liste des imprimantes disponibles avec détection de largeur"""
    try:
        printer_info = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | 
                                             win32print.PRINTER_ENUM_CONNECTIONS)
        printers = []
        for i, printer in enumerate(printer_info):
            printer_name = printer[2]
            
            # Détecter la largeur
            printer_width = detect_printer_width(printer_name)
            
            printers.append({
                'id': i,
                'name': printer_name,
                'port': printer[1],
                'driver': printer[3],
                'is_default': (printer_name == win32print.GetDefaultPrinter()),
                'width': printer_width  # Nouvelle propriété
            })
        return printers
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des imprimantes: {e}")
        return []

def print_raw(printer_name, data):
    """Imprime des données brutes sur l'imprimante spécifiée"""
    try:
        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Impression", None, "RAW"))
            try:
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, data)
                win32print.EndPagePrinter(hPrinter)
            finally:
                win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)
        logger.info(f"Impression réussie sur {printer_name}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'impression: {e}")
        return False

def print_test(printer_name):
    """Imprime un ticket de test sur l'imprimante spécifiée"""
    commands = bytearray()
    commands.extend(ESC_INIT)
    commands.extend(ESC_CENTER)
    commands.extend(ESC_BOLD_ON)
    commands.extend(ESC_DOUBLE_HEIGHT_ON)
    commands.extend("TEST D'IMPRESSION".encode('cp850', errors='replace'))
    commands.extend(b'\n')
    commands.extend(ESC_DOUBLE_HEIGHT_OFF)
    commands.extend(ESC_BOLD_OFF)
    commands.extend(b'\n')
    
    # Détecter la largeur de l'imprimante
    printer_width = detect_printer_width(printer_name)
    
    commands.extend(f"Imprimante: {printer_name}".encode('cp850', errors='replace'))
    commands.extend(b'\n')
    commands.extend(f"Type: {printer_width}".encode('cp850', errors='replace'))
    commands.extend(b'\n')
    commands.extend(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}".encode('cp850', errors='replace'))
    commands.extend(b'\n\n')
    
    commands.extend(ESC_LEFT)
    commands.extend(b"Texte normal\n")
    commands.extend(ESC_BOLD_ON)
    commands.extend(b"Texte en gras\n")
    commands.extend(ESC_BOLD_OFF)
    commands.extend(ESC_DOUBLE_HEIGHT_ON)
    commands.extend(b"Texte double hauteur\n")
    commands.extend(ESC_DOUBLE_HEIGHT_OFF)
    
    commands.extend(b'\n\n')
    commands.extend(ESC_CENTER)
    commands.extend(b"*** FIN DU TEST ***\n")
    commands.extend(b'\n\n\n')
    commands.extend(ESC_CUT)
    
    return print_raw(printer_name, commands)