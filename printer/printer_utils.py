#!/usr/bin/env python
# -*- coding: utf-8 -*-

import win32print
import unicodedata
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

def get_codepage_command(encoding):
    """
    Retourne la commande ESC/POS pour définir la page de codes selon l'encodage
    
    Args:
        encoding (str): Encodage souhaité
        
    Returns:
        bytes: Commande ESC/POS pour la page de codes
    """
    # Commandes ESC/POS pour changer les pages de codes
    ESC_SET_CODEPAGE_WPC1252 = b'\x1b\x74\x10'    # ESC t 16 - Windows-1252 (cp1252)
    ESC_SET_CODEPAGE_PC858 = b'\x1b\x74\x13'      # ESC t 19 - PC858 avec €
    ESC_SET_CODEPAGE_PC850 = b'\x1b\x74\x02'      # ESC t 2  - PC850 Europe
    ESC_SET_CODEPAGE_PC437 = b'\x1b\x74\x00'      # ESC t 0  - PC437 USA
    ESC_SET_CODEPAGE_LATIN1 = b'\x1b\x74\x03'     # ESC t 3  - ISO 8859-1
    
    # Table de correspondance encodage → commande ESC/POS
    codepage_commands = {
        'cp1252': ESC_SET_CODEPAGE_WPC1252,
        'cp850': ESC_SET_CODEPAGE_PC850,
        'cp858': ESC_SET_CODEPAGE_PC858,
        'cp437': ESC_SET_CODEPAGE_PC437,
        'latin1': ESC_SET_CODEPAGE_LATIN1,
        'ascii': ESC_SET_CODEPAGE_PC437,        # ASCII utilise PC437 comme base
        'auto': ESC_SET_CODEPAGE_WPC1252,       # Auto utilise WPC1252 par défaut
        'utf-8': ESC_SET_CODEPAGE_WPC1252       # UTF-8 → WPC1252 pour compatibilité
    }
    
    # Retourner la commande appropriée
    command = codepage_commands.get(encoding.lower(), ESC_SET_CODEPAGE_WPC1252)
    
    logger.debug(f"Page de codes pour encodage '{encoding}': {command.hex()}")
    return command

def is_pos58_printer(printer_name):
    """
    Vérifie si l'imprimante est un modèle POS-58
    """
    if not printer_name:
        return False
    pos58_keywords = ['POS-58', 'POS58', 'pos-58', 'pos58']
    printer_name_lower = printer_name.lower()
    return any(keyword.lower() in printer_name_lower for keyword in pos58_keywords)

def convert_french_to_ascii_smart(text):
    """
    Convertit intelligemment le français vers ASCII en préservant la lisibilité
    Optimisé pour que les textes français restent parfaitement compréhensibles
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
        '€': 'EUR', '£': 'GBP', '¢': 'c', '$': 'USD',
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
    Détecte l'encodage optimal pour une imprimante donnée
    POS-58 → ASCII automatiquement, autres → selon détection
    """
    try:
        # Règle 1: POS-58 → ASCII obligatoire (on sait que ça marche)
        if is_pos58_printer(printer_name):
            logger.info(f"Imprimante POS-58 détectée: {printer_name} → Encodage ASCII forcé (solution optimale)")
            return "ascii"
        
        # Règle 2: Autres imprimantes → détection classique
        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            printer_info = win32print.GetPrinter(hPrinter, 2)
            driver_name = printer_info.get('pDriverName', '').lower()
            printer_name_lower = printer_name.lower()
            
            # Imprimantes connues pour supporter cp1252 (comme Word)
            cp1252_keywords = ['epson', 'star', 'citizen', 'bixolon', 'custom', 'zebra']
            
            # Imprimantes nécessitant cp850 (Europe)
            cp850_keywords = ['tm-t88', 'tm-t20', 'thermal', 'receipt', 'pos', 'tmu220']
            
            text_to_check = f"{printer_name_lower} {driver_name}"
            
            # Vérifier cp1252 en priorité (optimal pour français)
            for keyword in cp1252_keywords:
                if keyword in text_to_check:
                    logger.info(f"Encodage cp1252 (Windows-1252) détecté pour {printer_name}")
                    return "cp1252"
            
            # Puis cp850 (Europe occidentale)
            for keyword in cp850_keywords:
                if keyword in text_to_check:
                    logger.info(f"Encodage cp850 détecté pour {printer_name}")
                    return "cp850"
            
            # Par défaut cp1252 pour les imprimantes non-POS-58
            logger.info(f"Utilisation de cp1252 par défaut pour {printer_name}")
            return "cp1252"
            
        finally:
            win32print.ClosePrinter(hPrinter)
    except Exception as e:
        logger.error(f"Erreur lors de la détection d'encodage pour {printer_name}: {e}")
        # Fallback sécurisé
        if is_pos58_printer(printer_name):
            return "ascii"
        return "cp1252"

def get_printers():
    """Récupère la liste des imprimantes avec détection automatique de largeur et encodage"""
    try:
        printer_info = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | 
                                             win32print.PRINTER_ENUM_CONNECTIONS)
        printers = []
        for i, printer in enumerate(printer_info):
            printer_name = printer[2]
            
            # Détection automatique
            printer_width = detect_printer_width(printer_name)
            printer_encoding = detect_printer_encoding(printer_name)
            
            printers.append({
                'id': i,
                'name': printer_name,
                'port': printer[1],
                'driver': printer[3],
                'is_default': (printer_name == win32print.GetDefaultPrinter()),
                'width': printer_width,
                'encoding': printer_encoding
            })
        return printers
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des imprimantes: {e}")
        return []

def safe_encode_french(text, encoding='auto', printer_name=None):
    """
    Encodage sécurisé optimisé pour le français avec détection automatique intelligente
    
    Args:
        text (str): Texte à encoder
        encoding (str): Encodage souhaité ('auto', 'ascii', 'cp1252', etc.)
        printer_name (str): Nom de l'imprimante (pour détection automatique)
    
    Returns:
        bytes: Texte encodé de façon optimale
    """
    if not text:
        return b''
    
    # Détection automatique de l'encodage optimal
    if encoding == 'auto' or encoding is None:
        if printer_name and is_pos58_printer(printer_name):
            encoding = 'ascii'
            logger.debug(f"Encodage automatique: POS-58 détectée → ASCII")
        else:
            encoding = 'cp1252'
            logger.debug(f"Encodage automatique: autre imprimante → cp1252")
    
    # ASCII : conversion intelligente française
    if encoding.lower() == 'ascii':
        text_ascii = convert_french_to_ascii_smart(text)
        try:
            return text_ascii.encode('ascii', errors='strict')
        except UnicodeEncodeError:
            # Si même après conversion il y a des problèmes, forcer le remplacement
            return text_ascii.encode('ascii', errors='replace')
    
    # Autres encodages : système de fallback intelligent
    encoding_priority = [
        encoding,           # Encodage demandé en premier
        'cp1252',          # Windows-1252 (comme Word) - excellent pour français
        'cp850',           # CP850 - bon pour français
        'latin1',          # ISO 8859-1 - compatible français
        'cp437',           # CP437 - basique mais fonctionne
        'ascii'            # ASCII avec conversion - dernier recours
    ]
    
    # Supprimer les doublons en gardant l'ordre
    seen = set()
    encoding_priority = [x for x in encoding_priority if not (x in seen or seen.add(x))]
    
    for enc in encoding_priority:
        try:
            if enc == 'ascii':
                # Dernier recours : ASCII avec conversion
                text_converted = convert_french_to_ascii_smart(text)
                return text_converted.encode('ascii', errors='replace')
            else:
                # Essayer l'encodage tel quel
                return text.encode(enc, errors='strict')
                
        except (UnicodeEncodeError, LookupError):
            logger.debug(f"Échec encodage {enc} pour: '{text[:30]}...'")
            continue
    
    # Si vraiment tout échoue, ASCII forcé
    logger.warning(f"Tous les encodages ont échoué pour '{text[:30]}...', utilisation ASCII forcé")
    text_fallback = convert_french_to_ascii_smart(text)
    return text_fallback.encode('ascii', errors='replace')

def print_raw(printer_name, data):
    """Imprime des données brutes sur l'imprimante spécifiée"""
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
        logger.info(f"Impression réussie sur {printer_name}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'impression: {e}")
        return False

def print_test(printer_name):
    """Imprime un ticket de test optimisé selon le type d'imprimante"""
    commands = bytearray()
    commands.extend(ESC_INIT)
    
    # Détection automatique des caractéristiques
    printer_width = detect_printer_width(printer_name)
    encoding = detect_printer_encoding(printer_name)
    
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
    commands.extend(safe_encode_french(f"Encodage: {encoding}", encoding, printer_name))
    commands.extend(b'\n')
    commands.extend(safe_encode_french(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", encoding, printer_name))
    commands.extend(b'\n\n')
    
    # Test spécifique selon l'encodage
    if encoding == 'ascii':
        commands.extend(safe_encode_french("=== TEST FRANÇAIS → ASCII ===", encoding, printer_name))
        commands.extend(b'\n')
        test_phrases = [
            "Café français → Cafe francais",
            "Hôtel de luxe → Hotel de luxe", 
            "Réservation → Reservation",
            "À bientôt → A bientot",
            "François → Francois"
        ]
    else:
        commands.extend(safe_encode_french("=== TEST CARACTÈRES FRANÇAIS ===", encoding, printer_name))
        commands.extend(b'\n')
        test_phrases = [
            "Café français: éèàùç",
            "Hôtel de luxe avec piscine",
            "Réservation confirmée",
            "François et Amélie",
            "Prix: 15,50€ (quinze euros cinquante)"
        ]
    
    for phrase in test_phrases:
        commands.extend(safe_encode_french(phrase, encoding, printer_name))
        commands.extend(b'\n')
    
    commands.extend(b'\n')
    commands.extend(ESC_CENTER)
    commands.extend(safe_encode_french("*** FIN DU TEST ***", encoding, printer_name))
    commands.extend(b'\n\n\n')
    commands.extend(ESC_CUT)
    
    return print_raw(printer_name, commands)

def test_all_encodings_on_printer(printer_name):
    """
    Teste tous les encodages disponibles sur une imprimante spécifique
    Utile pour déterminer le meilleur encodage pour une imprimante
    
    Args:
        printer_name (str): Nom de l'imprimante à tester
        
    Returns:
        dict: Résultats des tests par encodage
    """
    test_phrase = "Café français: éèàùç € 15,50"
    encodings_to_test = ['auto', 'ascii', 'cp1252', 'cp850', 'cp437', 'latin1']
    results = {}
    
    logger.info(f"Test de tous les encodages sur {printer_name}")
    
    for encoding in encodings_to_test:
        try:
            # Tester l'encodage
            if encoding == 'auto':
                actual_encoding = detect_printer_encoding(printer_name)
                encoded_text = safe_encode_french(test_phrase, actual_encoding, printer_name)
                results[encoding] = {
                    'success': True,
                    'actual_encoding': actual_encoding,
                    'encoded_length': len(encoded_text),
                    'sample': encoded_text[:50].decode('ascii', errors='replace')
                }
            else:
                encoded_text = safe_encode_french(test_phrase, encoding, printer_name)
                results[encoding] = {
                    'success': True,
                    'actual_encoding': encoding,
                    'encoded_length': len(encoded_text),
                    'sample': encoded_text[:50].decode('ascii', errors='replace')
                }
                
        except Exception as e:
            results[encoding] = {
                'success': False,
                'error': str(e),
                'actual_encoding': encoding
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
            print(f"✅ {encoding:<8} → {result['actual_encoding']:<8} ({result['encoded_length']} bytes)")
            print(f"   Aperçu: {result['sample']}")
        else:
            print(f"❌ {encoding:<8} → ÉCHEC: {result['error']}")
        print()
    
    # Recommandation
    is_pos58 = is_pos58_printer(printer_name)
    if is_pos58:
        print("🎯 RECOMMANDATION: Cette imprimante POS-58 doit utiliser 'ascii'")
    else:
        print("🎯 RECOMMANDATION: Cette imprimante peut utiliser 'cp1252' ou 'auto'")
    
    return results

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
    
    print("🧪 TEST CONVERSION FRANÇAIS → ASCII")
    print("=" * 50)
    
    for phrase in test_phrases:
        ascii_result = convert_french_to_ascii_smart(phrase)
        print(f"'{phrase}'")
        print(f"→ '{ascii_result}'")
        print()
    
    return True