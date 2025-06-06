#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Solution basique et robuste pour imprimante POS-58
Focus sur ASCII pur avec conversion intelligente des caractères français
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from printer.printer_utils import get_printers, print_raw, ESC_INIT, ESC_CUT

def convert_french_to_ascii_readable(text):
    """
    Convertit le français vers ASCII de façon lisible et naturelle
    Optimisé pour que les textes restent compréhensibles
    """
    if not text:
        return text
    
    # Table de conversion optimisée pour la lisibilité française
    french_to_ascii = {
        # Voyelles avec accents - conservation de la lisibilité
        'à': 'a', 'á': 'a', 'â': 'a', 'ä': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e', 
        'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
        'ò': 'o', 'ó': 'o', 'ô': 'o', 'ö': 'o',
        'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
        
        # Majuscules
        'À': 'A', 'Á': 'A', 'Â': 'A', 'Ä': 'A',
        'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
        'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I',
        'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Ö': 'O',
        'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U',
        
        # Caractères spéciaux français
        'ç': 'c', 'Ç': 'C',
        'ñ': 'n', 'Ñ': 'N',
        'ÿ': 'y', 'Ý': 'Y',
        
        # Ligatures
        'œ': 'oe', 'Œ': 'OE',
        'æ': 'ae', 'Æ': 'AE',
        
        # Symboles monétaires et spéciaux
        '€': 'EUR', '£': 'GBP', '¢': 'c',
        '°': 'deg', '²': '2', '³': '3',
        '½': '1/2', '¼': '1/4', '¾': '3/4',
        
        # Guillemets et apostrophes
        '"': '"', '"': '"',
        ''': "'", ''': "'",
        '«': '"', '»': '"',
        
        # Tirets
        '–': '-', '—': '-',
        '…': '...',
    }
    
    # Appliquer les conversions
    result = text
    for french_char, ascii_char in french_to_ascii.items():
        result = result.replace(french_char, ascii_char)
    
    return result

def create_simple_receipt_pos58():
    """
    Crée un reçu simple en ASCII pur, optimisé pour POS-58
    """
    printers = get_printers()
    
    # Trouver l'imprimante POS-58
    pos58_printer = None
    for printer in printers:
        if 'POS-58' in printer['name'] or 'POS58' in printer['name']:
            pos58_printer = printer['name']
            break
    
    if not pos58_printer:
        print("❌ Imprimante POS-58 non trouvée!")
        return False
    
    print(f"🧪 Reçu ASCII optimisé sur {pos58_printer}")
    
    # Données du reçu avec caractères français
    business_name = "Café de la Paix"
    address = "123 Rue de la République"
    city = "75001 Paris, France"
    phone = "Tél: +33 1 42 86 87 88"
    
    server = "Serveur: François"
    table = "Table: 5 - Terrasse"
    
    items = [
        ("Café expresso", 1, 2.50),
        ("Thé Earl Grey", 1, 3.00), 
        ("Croissant beurré", 2, 1.80),
        ("Crème brûlée", 1, 6.50),
        ("Vin rouge (verre)", 1, 4.20),
        ("Eau minérale gazeuse", 1, 2.80)
    ]
    
    thank_you = "Merci de votre visite!"
    goodbye = "À bientôt au Café de la Paix"
    
    # Convertir tout en ASCII
    business_ascii = convert_french_to_ascii_readable(business_name)
    address_ascii = convert_french_to_ascii_readable(address)
    phone_ascii = convert_french_to_ascii_readable(phone)
    server_ascii = convert_french_to_ascii_readable(server)
    thank_you_ascii = convert_french_to_ascii_readable(thank_you)
    goodbye_ascii = convert_french_to_ascii_readable(goodbye)
    
    # Construire les commandes - MINIMALISTE
    commands = bytearray()
    commands.extend(ESC_INIT)  # Seulement l'initialisation
    
    # En-tête - centré
    commands.extend(b'\x1b\x61\x01')  # ESC a 1 - Centrer
    commands.extend(b'\x1b\x45\x01')  # ESC E 1 - Gras ON
    commands.extend(business_ascii.encode('ascii', errors='replace'))
    commands.extend(b'\n')
    commands.extend(b'\x1b\x45\x00')  # ESC E 0 - Gras OFF
    commands.extend(address_ascii.encode('ascii', errors='replace'))
    commands.extend(b'\n')
    commands.extend(city.encode('ascii', errors='replace'))
    commands.extend(b'\n')
    commands.extend(phone_ascii.encode('ascii', errors='replace'))
    commands.extend(b'\n\n')
    
    # Retour à gauche
    commands.extend(b'\x1b\x61\x00')  # ESC a 0 - Gauche
    commands.extend(b'=' * 32)
    commands.extend(b'\n')
    commands.extend(b'Date: 06/06/2025 14:30\n')
    commands.extend(server_ascii.encode('ascii', errors='replace'))
    commands.extend(b'\n')
    commands.extend(table.encode('ascii', errors='replace'))
    commands.extend(b'\n')
    commands.extend(b'=' * 32)
    commands.extend(b'\n\n')
    
    # Articles
    commands.extend(b'DETAIL DE LA COMMANDE\n')
    commands.extend(b'-' * 32)
    commands.extend(b'\n')
    
    total = 0
    for name, qty, price in items:
        name_ascii = convert_french_to_ascii_readable(name)
        item_total = qty * price
        total += item_total
        
        # Format simple: nom (qty) prix
        line = f"{name_ascii[:18]:<18} {qty} {price:>5.2f}E"
        if len(line) > 32:
            line = line[:32]
        
        commands.extend(line.encode('ascii', errors='replace'))
        commands.extend(b'\n')
    
    commands.extend(b'-' * 32)
    commands.extend(b'\n')
    commands.extend(b'\x1b\x45\x01')  # Gras ON
    total_line = f"TOTAL: {total:>19.2f}E"
    commands.extend(total_line.encode('ascii', errors='replace'))
    commands.extend(b'\n')
    commands.extend(b'\x1b\x45\x00')  # Gras OFF
    commands.extend(b'\n')
    
    # Pied de page
    commands.extend(b'Mode de paiement: Carte bleue\n')
    commands.extend(b'TVA incluse: 20%\n\n')
    
    commands.extend(b'\x1b\x61\x01')  # Centrer
    commands.extend(thank_you_ascii.encode('ascii', errors='replace'))
    commands.extend(b'\n')
    commands.extend(goodbye_ascii.encode('ascii', errors='replace'))
    commands.extend(b'\n\n\n')
    
    commands.extend(ESC_CUT)
    
    # Imprimer
    success = print_raw(pos58_printer, commands)
    
    if success:
        print("✅ Reçu ASCII optimisé imprimé avec succès!")
        print("📋 Vérifiez si les caractères s'affichent correctement")
        print("    (même sans accents, le texte doit être lisible)")
    else:
        print("❌ Échec de l'impression")
    
    return success

def test_individual_chars_pos58():
    """
    Test des caractères français un par un avec conversion ASCII
    """
    printers = get_printers()
    
    # Trouver l'imprimante POS-58
    pos58_printer = None
    for printer in printers:
        if 'POS-58' in printer['name'] or 'POS58' in printer['name']:
            pos58_printer = printer['name']
            break
    
    if not pos58_printer:
        print("❌ Imprimante POS-58 non trouvée!")
        return
    
    print(f"🧪 Test caractères individuels sur {pos58_printer}")
    
    # Caractères problématiques avec leur version ASCII
    test_chars = [
        ('é', 'e'), ('è', 'e'), ('à', 'a'), ('ç', 'c'), 
        ('ù', 'u'), ('ô', 'o'), ('î', 'i'), ('â', 'a'),
        ('É', 'E'), ('È', 'E'), ('À', 'A'), ('Ç', 'C'),
        ('œ', 'oe'), ('Œ', 'OE'), ('€', 'EUR')
    ]
    
    commands = bytearray()
    commands.extend(ESC_INIT)
    
    commands.extend(b'TEST CARACTERES FRANCAIS\n')
    commands.extend(b'Original -> ASCII\n')
    commands.extend(b'-' * 32)
    commands.extend(b'\n')
    
    for original, ascii_version in test_chars:
        line = f"{original} -> {ascii_version}"
        line_ascii = convert_french_to_ascii_readable(line)
        commands.extend(line_ascii.encode('ascii', errors='replace'))
        commands.extend(b'\n')
    
    commands.extend(b'-' * 32)
    commands.extend(b'\n')
    commands.extend(b'Phrases test:\n')
    
    test_phrases = [
        "Cafe francais",
        "Hotel de luxe", 
        "Reservation confirmee",
        "Creme brulee",
        "A bientot"
    ]
    
    for phrase in test_phrases:
        phrase_ascii = convert_french_to_ascii_readable(phrase)
        commands.extend(phrase_ascii.encode('ascii', errors='replace'))
        commands.extend(b'\n')
    
    commands.extend(b'\n\n')
    commands.extend(ESC_CUT)
    
    success = print_raw(pos58_printer, commands)
    
    if success:
        print("✅ Test caractères envoyé avec succès!")
    else:
        print("❌ Échec du test caractères")

def update_printer_utils_for_pos58():
    """
    Génère le code pour modifier printer_utils.py pour POS-58
    """
    print("📝 CODE À AJOUTER DANS VOTRE printer_utils.py")
    print("=" * 50)
    
    code = '''
# AJOUTEZ cette fonction dans printer_utils.py :

def is_pos58_printer(printer_name):
    """Vérifie si c'est une imprimante POS-58"""
    return 'POS-58' in printer_name.upper() or 'POS58' in printer_name.upper()

def convert_french_to_ascii_readable(text):
    """Convertit le français vers ASCII de façon lisible"""
    if not text:
        return text
    
    french_to_ascii = {
        'à': 'a', 'á': 'a', 'â': 'a', 'ä': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
        'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
        'ò': 'o', 'ó': 'o', 'ô': 'o', 'ö': 'o',
        'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
        'À': 'A', 'Á': 'A', 'Â': 'A', 'Ä': 'A',
        'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
        'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I',
        'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Ö': 'O',
        'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U',
        'ç': 'c', 'Ç': 'C', 'ñ': 'n', 'Ñ': 'N',
        'œ': 'oe', 'Œ': 'OE', 'æ': 'ae', 'Æ': 'AE',
        '€': 'EUR', '°': 'deg', '"': '"', '"': '"',
    }
    
    result = text
    for french_char, ascii_char in french_to_ascii.items():
        result = result.replace(french_char, ascii_char)
    
    return result

# MODIFIEZ votre fonction safe_encode_french :

def safe_encode_french(text, encoding='ascii'):
    """Encode sécurisé optimisé pour POS-58"""
    if not text:
        return b''
    
    # Pour POS-58, toujours convertir en ASCII lisible
    if encoding == 'ascii' or is_pos58_printer(printer_name if 'printer_name' in locals() else ''):
        text_ascii = convert_french_to_ascii_readable(text)
        return text_ascii.encode('ascii', errors='replace')
    
    # Pour autres imprimantes, votre code existant...
    return text.encode(encoding, errors='replace')
'''
    
    print(code)
    print("=" * 50)
    print("💾 Copiez ce code dans votre printer_utils.py")

def main_menu():
    """Menu principal pour solution POS-58"""
    print("🔧 SOLUTION FINALE POUR POS-58")
    print("=" * 35)
    print("1. Tester reçu ASCII optimisé (RECOMMANDÉ)")
    print("2. Tester caractères individuels") 
    print("3. Voir le code pour modifier printer_utils.py")
    print("4. Quitter")
    
    while True:
        try:
            choix = input("\nVotre choix (1-4): ").strip()
            
            if choix == '1':
                create_simple_receipt_pos58()
                
            elif choix == '2':
                test_individual_chars_pos58()
                
            elif choix == '3':
                update_printer_utils_for_pos58()
                
            elif choix == '4':
                break
                
            else:
                print("Choix invalide!")
                
        except (ValueError, KeyboardInterrupt):
            print("\nAu revoir!")
            break
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    main_menu()