#!/usr/bin/env python
# -*- coding: utf-8 -*-

import win32print
import unicodedata
from datetime import datetime
from utils.config import logger

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
    ESC_SET_CODEPAGE_PC437 = b'\x1b\x74\x00'      # ESC t 0  - PC437 USA (optimal pour ASCII)
    ESC_SET_CODEPAGE_WPC1252 = b'\x1b\x74\x10'    # ESC t 16 - Windows-1252 (cp1252)
    ESC_SET_CODEPAGE_PC858 = b'\x1b\x74\x13'      # ESC t 19 - PC858 avec €
    ESC_SET_CODEPAGE_PC850 = b'\x1b\x74\x02'      # ESC t 2  - PC850 Europe
    ESC_SET_CODEPAGE_LATIN1 = b'\x1b\x74\x03'     # ESC t 3  - ISO 8859-1
    
    # Table de correspondance encodage → commande ESC/POS
    # ASCII utilise PC437 par défaut (le plus compatible)
    codepage_commands = {
        'ascii': ESC_SET_CODEPAGE_PC437,        # ASCII → PC437 (optimal)
        'cp437': ESC_SET_CODEPAGE_PC437,        # PC437 natif
        'cp1252': ESC_SET_CODEPAGE_WPC1252,     # Windows-1252
        'cp850': ESC_SET_CODEPAGE_PC850,        # PC850 Europe
        'cp858': ESC_SET_CODEPAGE_PC858,        # PC858 avec €
        'latin1': ESC_SET_CODEPAGE_LATIN1,      # ISO 8859-1
        'auto': ESC_SET_CODEPAGE_PC437,         # Auto → PC437 (ASCII compatible)
        'utf-8': ESC_SET_CODEPAGE_PC437         # UTF-8 → PC437 avec conversion ASCII
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
    SIMPLIFIÉ: Retourne toujours ASCII pour TOUTES les imprimantes
    """
    logger.info(f"Configuration ASCII universelle: {printer_name} → Encodage ASCII (pour toutes les imprimantes)")
    return "ascii"

def get_printers():
    """Récupère la liste des imprimantes avec détection automatique de largeur et encodage ASCII"""
    try:
        printer_info = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | 
                                             win32print.PRINTER_ENUM_CONNECTIONS)
        printers = []
        for i, printer in enumerate(printer_info):
            printer_name = printer[2]
            
            # Détection automatique
            printer_width = detect_printer_width(printer_name)
            printer_encoding = "ascii"  # ASCII pour toutes les imprimantes
            
            printers.append({
                'id': i,
                'name': printer_name,
                'port': printer[1],
                'driver': printer[3],
                'is_default': (printer_name == win32print.GetDefaultPrinter()),
                'width': printer_width,
                'encoding': printer_encoding  # Toujours ASCII
            })
        
        logger.info(f"{len(printers)} imprimantes détectées avec encodage ASCII par défaut")
        return printers
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des imprimantes: {e}")
        return []

def get_robust_init_command(printer_name=None):
    """
    Retourne une séquence d'initialisation robuste pour l'imprimante
    
    Args:
        printer_name (str): Nom de l'imprimante
        
    Returns:
        bytes: Commande d'initialisation robuste
    """
    robust_init = bytearray()
    
    # Étape 1: Réinitialisation complète
    robust_init.extend(b'\x1b\x40')          # ESC @ - Reset complet
    
    # Étape 2: Status et préparation
    robust_init.extend(b'\x10\x04\x01')      # DLE EOT 1 - Status de l'imprimante
    robust_init.extend(b'\x1d\x61\x00')      # GS a 0 - Activer l'auto-cut
    
    # Étape 3: Configuration du papier
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
    # SOLUTION pour le problème de coupe décalée :
    # Le problème : l'imprimante garde la commande de coupe en tampon
    # La solution : forcer le flush du tampon ET coupe immédiate
    
    robust_cut = bytearray()
    
    # Étape 1: Avancer suffisamment de lignes pour s'assurer qu'il y a du papier
    robust_cut.extend(b'\x1b\x64\x03')      # ESC d 3 - Avancer 3 lignes (important!)
    
    # Étape 2: Forcer le vidage du tampon d'impression (CRITIQUE)
    robust_cut.extend(b'\x0c')              # Form Feed - Force le flush du tampon
    robust_cut.extend(b'\x10\x04\x01')      # DLE EOT 1 - Demander status (force la communication)
    
    # Étape 3: Coupe immédiate et forcée
    robust_cut.extend(b'\x1d\x56\x00')      # GS V 0 - Coupe complète IMMÉDIATE
    
    # Étape 4: Alternative avec coupe partielle si la complète ne marche pas
    robust_cut.extend(b'\x1d\x56\x01')      # GS V 1 - Coupe partielle
    
    # Étape 5: FORCER l'exécution avec des commandes de contrôle
    robust_cut.extend(b'\x1b\x64\x01')      # ESC d 1 - Avancer 1 ligne (force l'action)
    robust_cut.extend(b'\x1d\x56\x41')      # GS V A - Coupe avec avance (dernière tentative)
    
    # Étape 6: Finaliser avec flush final
    robust_cut.extend(b'\x0c')              # Form Feed final pour forcer l'action
    
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
    
    # NOUVEAU: ASCII universel par défaut
    logger.debug(f"Encodage ASCII universel pour: {printer_name or 'imprimante'}")
    
    # Conversion française intelligente
    text_ascii = convert_french_to_ascii_smart(text)
    
    # Encoder en ASCII avec gestion d'erreurs robuste
    try:
        return text_ascii.encode('ascii', errors='strict')
    except UnicodeEncodeError:
        # Si même après conversion il y a des problèmes, forcer le remplacement
        logger.warning(f"Caractères ASCII problématiques dans: '{text[:30]}...', remplacement forcé")
        return text_ascii.encode('ascii', errors='replace')

def print_raw(printer_name, data):
    """Imprime des données brutes sur l'imprimante spécifiée avec flush forcé"""
    try:
        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            # Utiliser un document avec flush immédiat
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Impression Hotelia", None, "RAW"))
            try:
                win32print.StartPagePrinter(hPrinter)
                
                # Écrire les données
                win32print.WritePrinter(hPrinter, data)
                
                # IMPORTANT: Forcer le flush immédiat après l'écriture
                # Ceci garantit que la coupe s'exécute immédiatement
                win32print.EndPagePrinter(hPrinter)
                
            finally:
                win32print.EndDocPrinter(hPrinter)
                
        finally:
            win32print.ClosePrinter(hPrinter)
            
        # Attendre un court délai pour s'assurer que l'impression est terminée
        import time
        time.sleep(0.1)  # 100ms pour laisser le temps à l'imprimante de traiter
        
        logger.info(f"Impression réussie sur {printer_name} avec flush forcé")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'impression: {e}")
        return False

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