#!/usr/bin/env python
# -*- coding: utf-8 -*-

import win32print
import unicodedata
import base64
import io
from datetime import datetime
from utils.config import logger


# ---------------------------------------------------------------------------
# Conversion image → ESC/POS raster (GS v 0)
# ---------------------------------------------------------------------------

def image_to_escpos(image_source, max_width_px=384, align='center'):
    """
    Convertit une image en commandes ESC/POS raster (GS v 0).
    Compatible avec toutes les imprimantes thermiques ESC/POS.

    Largeurs papier conseillees :
      58mm → max_width_px=384  (environ 200-250 pour un beau logo)
      80mm → max_width_px=576

    Args:
        image_source: chemin fichier (str), bytes bruts, ou base64 (str)
        max_width_px (int): largeur maximale en pixels
        align (str): 'left', 'center', 'right'

    Returns:
        bytes: commandes ESC/POS prete a envoyer
        None : si la conversion echoue
    """
    try:
        from PIL import Image, ImageOps
    except ImportError:
        logger.error("Pillow non installe: pip install pillow")
        return None

    try:
        # --- Charger l'image ---
        if isinstance(image_source, str):
            # Supprimer le prefixe data: URL si present (ex: "data:image/png;base64,...")
            if image_source.startswith('data:'):
                if ',' in image_source:
                    image_source = image_source.split(',', 1)[1]
                else:
                    logger.error("Format data URL invalide (pas de virgule)")
                    return None
            try:
                img_bytes = base64.b64decode(image_source)
                # Verifier que les donnees decoded sont bien une image et non du HTML
                if img_bytes[:9].lower().startswith((b'<!doctype', b'<html', b'<head', b'<?xml')):
                    logger.error(
                        "Le champ 'image' contient du HTML au lieu d'une image. "
                        "Verifiez que le client envoie uniquement la partie base64 "
                        "(sans le prefixe 'data:image/...;base64,')"
                    )
                    return None
                img = Image.open(io.BytesIO(img_bytes))
            except Exception:
                # image_source n'est pas du base64 valide : traiter comme chemin fichier
                img = Image.open(image_source)
        elif isinstance(image_source, bytes):
            try:
                img_bytes = base64.b64decode(image_source)
                img = Image.open(io.BytesIO(img_bytes))
            except Exception:
                img = Image.open(io.BytesIO(image_source))
        else:
            logger.error("image_source invalide")
            return None

        # --- Convertir en noir et blanc ---
        # Fond blanc pour les PNG transparents
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            background = Image.new('RGBA', img.size, (255, 255, 255, 255))
            background.paste(img.convert('RGBA'), mask=img.convert('RGBA').split()[3])
            img = background.convert('L')
        else:
            img = img.convert('L')

        img = ImageOps.invert(img)  # blanc=vide, noir=encre
        img = img.convert('1')      # 1-bit

        # --- Redimensionner si necessaire ---
        w, h = img.size
        if w > max_width_px:
            ratio = max_width_px / w
            img = img.resize((max_width_px, int(h * ratio)), Image.LANCZOS)
            w, h = img.size

        # La largeur doit etre un multiple de 8 (requis ESC/POS)
        if w % 8 != 0:
            new_w = ((w // 8) + 1) * 8
            padded = Image.new('1', (new_w, h), 0)
            padded.paste(img, (0, 0))
            img = padded
            w = new_w

        # --- Construire les commandes ESC/POS ---
        commands = bytearray()

        # Alignement
        if align == 'center':
            commands.extend(b'\x1b\x61\x01')
        elif align == 'right':
            commands.extend(b'\x1b\x61\x02')
        else:
            commands.extend(b'\x1b\x61\x00')

        # GS v 0 : impression raster
        bytes_per_row = w // 8
        xL = bytes_per_row & 0xFF
        xH = (bytes_per_row >> 8) & 0xFF
        yL = h & 0xFF
        yH = (h >> 8) & 0xFF

        commands.extend(b'\x1d\x76\x30\x00')
        commands.extend(bytes([xL, xH, yL, yH]))
        commands.extend(img.tobytes())

        # Retour alignement gauche + saut de ligne
        commands.extend(b'\x1b\x61\x00')
        commands.extend(b'\n')

        logger.info(f"Logo converti: {w}x{h}px, {bytes_per_row * h} bytes raster")
        return bytes(commands)

    except Exception as e:
        logger.error(f"Erreur conversion image ESC/POS: {e}")
        return None

# Commandes ESC/POS de base
ESC_INIT = b'\x1b\x40'  # Initialiser l'imprimante
ESC_INIT_ROBUST = b'\x1b\x40\x1b\x64\x01\x1d\x61\x00'  # Initialisation robuste + reset + avance
ESC_BOLD_ON = b'\x1b\x45\x01'  # Activer le gras
ESC_BOLD_OFF = b'\x1b\x45\x00'  # Désactiver le gras
ESC_DOUBLE_HEIGHT_ON = b'\x1b\x21\x10'  # Activer double hauteur
ESC_DOUBLE_HEIGHT_OFF = b'\x1b\x21\x00'  # Désactiver double hauteur
ESC_CENTER = b'\x1b\x61\x01'  # Centrer le texte
ESC_LEFT = b'\x1b\x61\x00'  # Aligner à gauche
ESC_RIGHT = b'\x1b\x61\x02'  # Aligner à droite
ESC_CUT = b'\x1d\x56\x41'  # Couper le papier (méthode 1)
ESC_CUT_FULL = b'\x1d\x56\x00'  # Coupe complète (méthode 2)
ESC_CUT_PARTIAL = b'\x1d\x56\x01'  # Coupe partielle (méthode 3)
ESC_FEED_CUT = b'\x1b\x64\x03\x1d\x56\x41'  # Avance + Coupe (solution robuste)
ESC_FEED = b'\x1b\x64'  # Avancer le papier

def get_codepage_command(encoding):
    """
    Retourne la commande ESC/POS pour définir la page de codes selon l'encodage
    OPTIMISÉ POUR ASCII PAR DÉFAUT
    
    Args:
        encoding (str): Encodage souhaité
        
    Returns:
        bytes: Commande ESC/POS pour la page de codes
    """
    # Commandes ESC/POS pour changer les pages de codes
    ESC_SET_CODEPAGE_PC437 = b'\x1b\x74\x00'      # ESC t 0  - PC437 USA
    ESC_SET_CODEPAGE_PC858 = b'\x1b\x74\x0e'      # ESC t 14 - PC858 avec € (index sur POS-58)
    ESC_SET_CODEPAGE_PC850 = b'\x1b\x74\x02'      # ESC t 2  - PC850 Europe
    ESC_SET_CODEPAGE_LATIN1 = b'\x1b\x74\x03'     # ESC t 3  - ISO 8859-1

    # Table de correspondance encodage → commande ESC/POS
    # PC858 par défaut : couvre les accents français ET le symbole € (0xD5)
    codepage_commands = {
        'ascii':   ESC_SET_CODEPAGE_PC858,      # ASCII → PC858 (safe_encode_french encode en cp858)
        'cp437':   ESC_SET_CODEPAGE_PC437,      # PC437 natif
        'cp1252':  ESC_SET_CODEPAGE_PC858,      # CP1252 → utiliser PC858 (€ supporté)
        'cp850':   ESC_SET_CODEPAGE_PC850,      # PC850 Europe
        'cp858':   ESC_SET_CODEPAGE_PC858,      # PC858 avec €
        'latin1':  ESC_SET_CODEPAGE_LATIN1,     # ISO 8859-1
        'auto':    ESC_SET_CODEPAGE_PC858,      # Auto → PC858
        'utf-8':   ESC_SET_CODEPAGE_PC858       # UTF-8 → PC858 avec conversion
    }
    
    # Retourner la commande appropriée (PC437 par défaut pour ASCII)
    command = codepage_commands.get(encoding.lower(), ESC_SET_CODEPAGE_PC437)
    
    logger.debug(f"Page de codes pour encodage '{encoding}': {command.hex()}")
    return command

def is_pos58_printer(printer_name):
    """
    Vérifie si l'imprimante est un modèle POS-58
    (Fonction conservée pour compatibilité mais maintenant tout est en ASCII)
    """
    if not printer_name:
        return False
    pos58_keywords = ['POS-58', 'POS58', 'pos-58', 'pos58']
    printer_name_lower = printer_name.lower()
    return any(keyword.lower() in printer_name_lower for keyword in pos58_keywords)

def convert_french_to_ascii_smart(text):
    """
    Convertit intelligemment le français vers ASCII en préservant la lisibilité
    FONCTION PRINCIPALE pour toutes les imprimantes maintenant
    """
    if not text:
        return text
    
    # Table de conversion française → ASCII optimisée pour la lisibilité
    french_conversions = {
        # Voyelles avec accents - préservation maximale de la lisibilité
        'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e', 
        'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
        'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u', 'ū': 'u',
        
        # Majuscules
        'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A', 'Å': 'A',
        'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
        'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I',
        'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O',
        'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U', 'Ū': 'U',
        
        # Caractères spéciaux français - TRÈS IMPORTANT
        'ç': 'c', 'Ç': 'C',          # Cédille
        'ñ': 'n', 'Ñ': 'N',          # Eñe espagnol
        'ÿ': 'y', 'Ý': 'Y',          # Y tréma
        
        # Ligatures françaises
        'œ': 'oe', 'Œ': 'OE',        # Très fréquent en français
        'æ': 'ae', 'Æ': 'AE',        # Moins fréquent mais important
        
        # Symboles monétaires et spéciaux
        # € géré par cp858 (0xD5), ici en fallback ASCII uniquement
        # NOTE: $ est ASCII standard, pas de conversion nécessaire
        '€': 'EUR', '£': 'GBP', '¢': 'c',
        '°': 'deg', '²': '2', '³': '3',
        '½': '1/2', '¼': '1/4', '¾': '3/4',
        '±': '+/-', '×': 'x', '÷': '/',
        
        # Guillemets et apostrophes (typographie française)
        '"': '"', '"': '"', '„': '"',
        ''': "'", ''': "'", '‚': "'",
        '«': '"', '»': '"',            # Guillemets français
        
        # Tirets et ponctuation
        '–': '-', '—': '-', '―': '-',  # Tirets longs
        '…': '...',                    # Points de suspension
        '•': '*', '◦': '-',           # Puces
        
        # Flèches
        '→': '->', '←': '<-', '↑': '^', '↓': 'v',
        '⇒': '=>', '⇐': '<=', '⟶': '->', '⟵': '<-',

        # Caractères mathématiques
        '∞': 'infini', '≤': '<=', '≥': '>=',
        '≠': '!=', '≈': '~=',
        
        # Symboles divers
        '™': 'TM', '®': '(R)', '©': '(C)',
        '§': 'sect.', '¶': 'par.',
        '†': '+', '‡': '++',
    }
    
    # Appliquer les conversions manuelles
    result = text
    for french_char, ascii_replacement in french_conversions.items():
        result = result.replace(french_char, ascii_replacement)
    
    # Utiliser unicodedata pour les caractères restants (fallback)
    try:
        # NFD = décomposition canonique (sépare les accents des lettres)
        result_nfd = unicodedata.normalize('NFD', result)
        # Garder seulement les caractères de base (enlever les accents)
        result_final = ''.join(
            char for char in result_nfd 
            if unicodedata.category(char) != 'Mn'  # Mn = Nonspacing_Mark (accents)
        )
        return result_final
    except:
        # Si unicodedata échoue, retourner le résultat des conversions manuelles
        return result

def detect_printer_width(printer_name):
    """
    Tente de détecter automatiquement si l'imprimante est 58mm ou 80mm
    """
    try:
        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            printer_info = win32print.GetPrinter(hPrinter, 2)
            driver_name = printer_info.get('pDriverName', '').lower()
            port_name = printer_info.get('pPortName', '').lower()
            printer_name_lower = printer_name.lower()
            
            # Mots-clés pour imprimantes 80mm
            keywords_80mm = ['80mm', '80 mm', 'pos80', 'tm-t88', 'tmt88', 
                           'tm88', 't88', 'tm-t20', 'tmt20', 't20',
                           '3inch', '3 inch', '80', 'large', 'wide']
            
            # Mots-clés pour imprimantes 58mm
            keywords_58mm = ['58mm', '58 mm', 'pos58', 'tm-t20mini', 
                           'tmt20mini', '2inch', '2 inch', '58', 
                           'mini', 'compact', 'narrow']
            
            text_to_check = f"{printer_name_lower} {driver_name} {port_name}"
            
            for keyword in keywords_80mm:
                if keyword in text_to_check:
                    logger.info(f"Détection: {printer_name} identifiée comme imprimante 80mm")
                    return "80mm"
                    
            for keyword in keywords_58mm:
                if keyword in text_to_check:
                    logger.info(f"Détection: {printer_name} identifiée comme imprimante 58mm")
                    return "58mm"
            
            # Essayer de détecter via les capacités du pilote
            try:
                printer_caps = win32print.DeviceCapabilities(printer_name, port_name, 
                                                           win32print.DC_PAPERSIZE)
                if printer_caps:
                    widths = [size[0] for size in printer_caps]
                    if any(w > 700 for w in widths):  # Probablement 80mm
                        return "80mm"
                    elif any(500 <= w <= 700 for w in widths):  # Probablement 58mm
                        return "58mm"
            except:
                pass
            
            logger.info(f"Impossible de détecter la largeur pour {printer_name}, utilisation de 58mm par défaut")
            return "58mm"
            
        finally:
            win32print.ClosePrinter(hPrinter)
    except Exception as e:
        logger.error(f"Erreur lors de la détection de la largeur pour {printer_name}: {e}")
        return "58mm"

def detect_printer_encoding(printer_name):
    """
    SIMPLIFIÉ: Retourne toujours ASCII pour TOUTES les imprimantes
    """
    logger.info(f"Configuration ASCII universelle: {printer_name} → Encodage ASCII (pour toutes les imprimantes)")
    return "ascii"

def _detect_connection_type(port_name):
    """Determine le type de connexion a partir du nom de port Windows."""
    if not port_name:
        return 'unknown'
    p = port_name.upper()
    if p.startswith('USB') or 'USBPRINT' in p:
        return 'usb'
    if p.startswith('COM') or p.startswith('BT') or 'BLUETOOTH' in p or 'RFCOMM' in p:
        return 'bluetooth_com'
    if p.startswith('IP_') or p.startswith('WSD') or '.' in port_name:
        return 'network'
    if p.startswith('LPT'):
        return 'parallel'
    return 'usb'  # par defaut (ex: port PDF, XPS...)


def get_printers():
    """
    Recupere la liste COMPLETE des imprimantes :
      - Imprimantes Windows (USB, BT avec driver, reseau) via win32print
      - Imprimantes BT sur port COM non enregistrees dans le spouleur
    Chaque entree contient 'connection_type' : 'usb', 'bluetooth_com', 'bluetooth_spooler', 'network'
    """
    printers = []
    spooler_com_ports = set()  # ports COM deja couverts par le spouleur

    # --- 1. Imprimantes Windows (spouleur) ---
    try:
        printer_info = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )
        try:
            default_name = win32print.GetDefaultPrinter()
        except Exception:
            default_name = ''

        for i, printer in enumerate(printer_info):
            printer_name = printer[2]
            port = printer[1]
            conn_type = _detect_connection_type(port)

            # BT avec driver installe = 'bluetooth_spooler'
            if conn_type == 'bluetooth_com':
                conn_type = 'bluetooth_spooler'
                spooler_com_ports.add(port.upper())

            printer_width = detect_printer_width(printer_name)

            printers.append({
                'id': i,
                'name': printer_name,
                'port': port,
                'driver': printer[3],
                'is_default': (printer_name == default_name),
                'width': printer_width,
                'encoding': 'ascii',
                'connection_type': conn_type,
            })

        logger.info(f"{len(printers)} imprimantes spouleur detectees")
    except Exception as e:
        logger.error(f"Erreur enumeration imprimantes Windows: {e}")

    # --- 2. Ports COM Bluetooth non enregistres dans le spouleur ---
    try:
        import serial.tools.list_ports
        for p in serial.tools.list_ports.comports():
            desc = (p.description or '').lower()
            hwid = (p.hwid or '').lower()
            is_bt = 'bluetooth' in desc or 'bth' in hwid or 'rfcomm' in desc
            if not is_bt:
                continue
            if p.device.upper() in spooler_com_ports:
                continue  # deja dans la liste spouleur
            printers.append({
                'id': len(printers),
                'name': p.description or p.device,
                'port': p.device,
                'driver': '',
                'is_default': False,
                'width': '58mm',
                'encoding': 'ascii',
                'connection_type': 'bluetooth_com',
                'com_port': p.device,
            })
            logger.info(f"Port COM Bluetooth ajoute: {p.device} ({p.description})")
    except ImportError:
        pass  # pyserial non installe, on ignore
    except Exception as e:
        logger.error(f"Erreur detection ports COM BT: {e}")

    logger.info(f"{len(printers)} imprimantes totales (USB + Bluetooth + reseau)")
    return printers

def get_robust_init_command(printer_name=None):
    """
    Retourne une séquence d'initialisation robuste pour l'imprimante
    
    Args:
        printer_name (str): Nom de l'imprimante
        
    Returns:
        bytes: Commande d'initialisation robuste
    """
    robust_init = bytearray()

    # Réinitialisation complète
    robust_init.extend(b'\x1b\x40')          # ESC @ - Reset complet

    # Activer le code page PC858 :
    # - € = 0xD5, accents français (é, è, à, ç, ô, ù...) supportés
    # - Sur cette imprimante POS-58 : PC858 = index 14 (lu depuis le ticket test interne)
    robust_init.extend(b'\x1b\x74\x0e')      # ESC t 14 - Code page PC858 (€ = 0xD5)

    # Avancer une ligne pour s'assurer que l'imprimante est prête
    robust_init.extend(b'\x1b\x64\x01')      # ESC d 1 - Avancer une ligne
    
    if printer_name:
        logger.debug(f"Initialisation robuste générée pour {printer_name}")
    
    return bytes(robust_init)

def get_robust_cut_command(printer_name=None):
    """
    Retourne une commande de coupe IMMÉDIATE qui force la coupe du premier reçu
    
    Args:
        printer_name (str): Nom de l'imprimante pour détecter le type
        
    Returns:
        bytes: Commande de coupe immédiate
    """
    robust_cut = bytearray()

    # Avancer suffisamment pour que le texte soit au-dessus de la lame
    robust_cut.extend(b'\x1b\x64\x05')      # ESC d 5 - Avancer 5 lignes

    # GS V 65 0 : coupe complète avec n=0 (forme 2-octets, universelle ESC/POS)
    robust_cut.extend(b'\x1d\x56\x41\x00')  # GS V 65 0 - Coupe complète
    # GS V 66 0 : coupe partielle avec n=0 (fallback pour imprimantes sans coupe complète)
    robust_cut.extend(b'\x1d\x56\x42\x00')  # GS V 66 0 - Coupe partielle
    
    if printer_name:
        logger.debug(f"Commande de coupe IMMÉDIATE générée pour {printer_name}")
    
    return bytes(robust_cut)

def safe_encode_french(text, encoding='ascii', printer_name=None):
    """
    Encodage sécurisé optimisé pour ASCII par défaut
    SIMPLIFIÉ: Utilise toujours la conversion ASCII intelligente
    
    Args:
        text (str): Texte à encoder
        encoding (str): Encodage souhaité (ignoré si ASCII universel)
        printer_name (str): Nom de l'imprimante (pour log)
    
    Returns:
        bytes: Texte encodé en ASCII avec conversion française intelligente
    """
    if not text:
        return b''

    # Normaliser les espaces insécables (\u202f de toLocaleString('fr-FR'), \u00a0)
    text = text.replace('\u202f', ' ').replace('\u00a0', ' ')

    # Convertir les symboles monétaires en texte ASCII lisible (même comportement que Tester ASCII)
    # Cela garantit un affichage cohérent sur toutes les imprimantes sans dépendre du code page
    currency_ascii = {
        '€': 'EUR', '£': 'GBP', '¥': 'JPY', '¤': '', '₦': 'NGN',
        '₣': 'CHF', '₹': 'INR', '₩': 'KRW', '₪': 'ILS',
    }
    for sym, code in currency_ascii.items():
        text = text.replace(sym, code)

    try:
        return text.encode('cp858')
    except (UnicodeEncodeError, LookupError):
        # Fallback ASCII avec conversion française pour les caractères hors CP858
        ascii_text = convert_french_to_ascii_smart(text)
        try:
            return ascii_text.encode('ascii', errors='strict')
        except UnicodeEncodeError:
            logger.warning(f"Caractères non encodables dans: '{text[:30]}...', remplacement forcé")
            return ascii_text.encode('ascii', errors='replace')

def print_raw(printer_name, data):
    """Imprime des donnees brutes via le spouleur Windows (USB, reseau, BT avec driver)."""
    try:
        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Impression Hotelia", None, "RAW"))
            try:
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, data)
                win32print.EndPagePrinter(hPrinter)
            finally:
                win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)

        import time
        time.sleep(0.1)
        logger.info(f"Impression reussie (spouleur) sur {printer_name}")
        return True
    except Exception as e:
        logger.error(f"Erreur impression spouleur {printer_name}: {e}")
        return False


def print_raw_com(com_port, data, baudrate=9600):
    """Imprime des donnees brutes via un port COM (Bluetooth SPP, serie)."""
    try:
        import serial
        with serial.Serial(com_port, baudrate=baudrate, timeout=5) as ser:
            ser.write(data)
            ser.flush()
        logger.info(f"Impression reussie (COM) sur {com_port}")
        return True
    except ImportError:
        logger.error("pyserial manquant: pip install pyserial")
        return False
    except Exception as e:
        logger.error(f"Erreur impression COM {com_port}: {e}")
        return False


def print_via_network(host, data, tcp_port=9100, timeout=10):
    """Imprime des donnees brutes via TCP/IP directement sur le port 9100 (imprimantes WiFi/Ethernet)."""
    import socket
    import time
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, tcp_port))
        sock.sendall(data)
        # Signaler la fin d'envoi et attendre que l'imprimante traite les données
        # avant de fermer la connexion (évite la troncature des données)
        sock.shutdown(socket.SHUT_WR)
        time.sleep(0.8)
        sock.close()
        logger.info(f"Impression reussie (reseau TCP) sur {host}:{tcp_port}")
        return True
    except Exception as e:
        logger.error(f"Erreur impression reseau {host}:{tcp_port}: {e}")
        return False


def print_smart(printer_info, data):
    """
    Route l'impression vers le bon canal selon connection_type :
      - 'bluetooth_com' : envoie via port COM (pyserial)
      - 'network'       : envoie via TCP/IP direct sur port 9100
      - tous les autres  : envoie via le spouleur Windows (win32print)

    Args:
        printer_info (dict): Entree retournee par get_printers()
        data (bytes): Donnees ESC/POS

    Returns:
        bool: True si succes
    """
    conn = printer_info.get('connection_type', 'usb')
    if conn == 'bluetooth_com':
        com_port = printer_info.get('com_port') or printer_info.get('port')
        logger.info(f"Routage impression → Bluetooth COM {com_port}")
        return print_raw_com(com_port, data)
    elif conn == 'network':
        ip = printer_info.get('ip') or printer_info.get('network_ip')
        tcp_port = printer_info.get('tcp_port', 9100)
        if not ip:
            logger.error("connection_type=network mais pas d'IP configuree dans printer_info")
            return False
        logger.info(f"Routage impression → réseau TCP {ip}:{tcp_port}")
        return print_via_network(ip, data, tcp_port=tcp_port)
    else:
        logger.info(f"Routage impression → spouleur Windows ({conn}): {printer_info['name']}")
        return print_raw(printer_info['name'], data)

def print_test(printer_name):
    """Imprime un ticket de test optimisé avec conversion ASCII pour toutes les imprimantes"""
    commands = bytearray()
    commands.extend(get_robust_init_command(printer_name))
    
    # Détection automatique des caractéristiques
    printer_width = detect_printer_width(printer_name)
    encoding = "ascii"  # ASCII pour tout maintenant
    
    # Utiliser PC437 pour ASCII (optimal)
    commands.extend(get_codepage_command(encoding))
    
    commands.extend(ESC_CENTER)
    commands.extend(ESC_BOLD_ON)
    commands.extend(ESC_DOUBLE_HEIGHT_ON)
    commands.extend(safe_encode_french("TEST D'IMPRESSION", encoding, printer_name))
    commands.extend(b'\n')
    commands.extend(ESC_DOUBLE_HEIGHT_OFF)
    commands.extend(ESC_BOLD_OFF)
    commands.extend(b'\n')
    
    commands.extend(ESC_LEFT)
    commands.extend(safe_encode_french(f"Imprimante: {printer_name}", encoding, printer_name))
    commands.extend(b'\n')
    commands.extend(safe_encode_french(f"Type: {printer_width}", encoding, printer_name))
    commands.extend(b'\n')
    commands.extend(safe_encode_french(f"Encodage: {encoding} (ASCII universel)", encoding, printer_name))
    commands.extend(b'\n')
    commands.extend(safe_encode_french(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", encoding, printer_name))
    commands.extend(b'\n\n')
    
    # Test de conversion française vers ASCII pour TOUTES les imprimantes
    commands.extend(safe_encode_french("=== TEST FRANÇAIS → ASCII ===", encoding, printer_name))
    commands.extend(b'\n')
    test_phrases = [
        "Café français → Cafe francais",
        "Hôtel de luxe → Hotel de luxe", 
        "Réservation → Reservation",
        "À bientôt → A bientot",
        "François → Francois",
        "15,50€ → 15,50 EUR",
        "Crème brûlée → Creme brulee"
    ]
    
    for phrase in test_phrases:
        commands.extend(safe_encode_french(phrase, encoding, printer_name))
        commands.extend(b'\n')
    
    commands.extend(b'\n')
    commands.extend(ESC_CENTER)
    commands.extend(safe_encode_french("*** ASCII UNIVERSEL - TEST OK ***", encoding, printer_name))
    commands.extend(b'\n\n\n')
    commands.extend(get_robust_cut_command(printer_name))
    
    return print_raw(printer_name, commands)

def test_all_encodings_on_printer(printer_name):
    """
    Teste tous les encodages disponibles sur une imprimante spécifique
    MODIFIÉ: Met l'accent sur ASCII comme recommandation
    
    Args:
        printer_name (str): Nom de l'imprimante à tester
        
    Returns:
        dict: Résultats des tests par encodage
    """
    test_phrase = "Café français: éèàùç € 15,50"
    encodings_to_test = ['ascii', 'cp1252', 'cp850', 'cp437', 'latin1']  # ASCII en premier
    results = {}
    
    logger.info(f"Test de tous les encodages sur {printer_name} (ASCII recommandé)")
    
    for encoding in encodings_to_test:
        try:
            encoded_text = safe_encode_french(test_phrase, encoding, printer_name)
            results[encoding] = {
                'success': True,
                'actual_encoding': encoding,
                'encoded_length': len(encoded_text),
                'sample': encoded_text[:50].decode('ascii', errors='replace'),
                'recommended': encoding == 'ascii'  # Marquer ASCII comme recommandé
            }
                
        except Exception as e:
            results[encoding] = {
                'success': False,
                'error': str(e),
                'actual_encoding': encoding,
                'recommended': False
            }
    
    return results

def print_encoding_test_results(printer_name):
    """
    Imprime les résultats de test d'encodage sur console
    """
    results = test_all_encodings_on_printer(printer_name)
    
    print(f"\n🧪 RÉSULTATS TEST ENCODAGE - {printer_name}")
    print("=" * 60)
    
    for encoding, result in results.items():
        if result['success']:
            recommended = " ⭐ RECOMMANDÉ" if result.get('recommended') else ""
            print(f"✅ {encoding:<8} → {result['actual_encoding']:<8} ({result['encoded_length']} bytes){recommended}")
            print(f"   Aperçu: {result['sample']}")
        else:
            print(f"❌ {encoding:<8} → ÉCHEC: {result['error']}")
        print()
    
    # Recommandation universelle
    print("🎯 RECOMMANDATION: ASCII est maintenant l'encodage universel pour toutes les imprimantes")
    print("   → Conversion française automatique: café → cafe, hôtel → hotel")
    print("   → Symboles: 15,50€ → 15,50 EUR")
    
    return results

def test_immediate_cut(printer_name):
    """
    Teste spécifiquement le problème de coupe décalée
    Imprime un reçu de test qui DOIT se couper immédiatement
    """
    logger.info(f"🧪 TEST DE COUPE IMMÉDIATE pour {printer_name}")
    
    commands = bytearray()
    
    # Initialisation robuste
    commands.extend(get_robust_init_command(printer_name))
    commands.extend(get_codepage_command('ascii'))
    
    # Contenu du test
    commands.extend(ESC_CENTER)
    commands.extend(ESC_BOLD_ON)
    commands.extend(safe_encode_french("TEST COUPE IMMÉDIATE", 'ascii', printer_name))
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_OFF)
    commands.extend(b'\n')
    
    commands.extend(ESC_LEFT)
    commands.extend(safe_encode_french(f"Imprimante: {printer_name}", 'ascii', printer_name))
    commands.extend(b'\n')
    commands.extend(safe_encode_french(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 'ascii', printer_name))
    commands.extend(b'\n\n')
    
    commands.extend(safe_encode_french("Ce reçu DOIT se couper", 'ascii', printer_name))
    commands.extend(b'\n')
    commands.extend(safe_encode_french("immédiatement après impression", 'ascii', printer_name))
    commands.extend(b'\n')
    commands.extend(safe_encode_french("sans attendre le prochain job.", 'ascii', printer_name))
    commands.extend(b'\n\n')
    
    commands.extend(ESC_CENTER)
    commands.extend(ESC_BOLD_ON)
    commands.extend(safe_encode_french("*** COUPE FORCÉE ***", 'ascii', printer_name))
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_OFF)
    
    # COUPE IMMÉDIATE FORCÉE
    commands.extend(get_robust_cut_command(printer_name))
    
    # Imprimer avec flush forcé
    success = print_raw(printer_name, commands)
    
    if success:
        print(f"✅ Test de coupe immédiate envoyé à {printer_name}")
        print("🔍 Vérifiez que le reçu se coupe IMMÉDIATEMENT")
        print("❌ Si il ne se coupe pas, le problème persiste")
    else:
        print(f"❌ Échec du test sur {printer_name}")
    
    return success

def test_french_conversion():
    """Teste la conversion française → ASCII pour validation"""
    test_phrases = [
        "Café de la Paix",
        "Hôtel François 1er", 
        "Réservation confirmée",
        "Crème brûlée à 8,50€",
        "À bientôt chez nous !",
        "Naïveté et cœur généreux",
        "Menu spécial: entrée, plat, dessert"
    ]
    
    print("🧪 TEST CONVERSION FRANÇAIS → ASCII (UNIVERSEL)")
    print("=" * 55)
    
    for phrase in test_phrases:
        ascii_result = convert_french_to_ascii_smart(phrase)
        print(f"'{phrase}'")
        print(f"→ '{ascii_result}'")
        print()
    
    return True