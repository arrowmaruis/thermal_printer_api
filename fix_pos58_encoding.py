#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Solution pour le problème de double encodage UTF-8/ISO sur imprimantes thermiques
Equivalent des balises meta HTML mais pour imprimantes ESC/POS
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from printer.printer_utils import (
    get_printers, print_raw, ESC_INIT, ESC_BOLD_ON, 
    ESC_BOLD_OFF, ESC_CENTER, ESC_LEFT, ESC_CUT
)

def fix_double_encoding_utf8_to_iso(text):
    """
    Corrige le problème de double encodage UTF-8 → ISO-8859-1
    Comme "François" → "Fran絡is" → "François"
    """
    try:
        # Étape 1: Encoder le texte en UTF-8 (comme fait Python)
        utf8_bytes = text.encode('utf-8')
        
        # Étape 2: Décoder ces bytes comme si c'était de l'ISO-8859-1
        # (simulation de ce que fait l'imprimante)
        iso_text = utf8_bytes.decode('iso-8859-1', errors='replace')
        
        # Étape 3: Ré-encoder en ISO-8859-1 pour l'imprimante
        corrected_bytes = iso_text.encode('iso-8859-1', errors='replace')
        
        return corrected_bytes
        
    except Exception as e:
        print(f"Erreur correction double encodage: {e}")
        return text.encode('ascii', errors='replace')

def test_double_encoding_theory():
    """
    Teste la théorie du double encodage avec des exemples concrets
    """
    test_cases = [
        "François",
        "Café",
        "Hôtel", 
        "Réservation",
        "Crème brûlée",
        "À bientôt",
        "Où étaient les péruches ?",
        "Naïveté",
        "Cœur"
    ]
    
    print("🔍 ANALYSE DU PROBLÈME DE DOUBLE ENCODAGE")
    print("=" * 50)
    print("Simulation de ce qui se passe :")
    print("1. Python encode en UTF-8")
    print("2. Imprimante interprète comme ISO-8859-1") 
    print("3. Résultat affiché")
    print("-" * 50)
    
    for text in test_cases:
        try:
            # Étape 1: Encoder en UTF-8 (ce que fait Python)
            utf8_bytes = text.encode('utf-8')
            
            # Étape 2: Voir ce que ça donne si interprété comme ISO-8859-1
            bad_result = utf8_bytes.decode('iso-8859-1', errors='replace')
            
            print(f"'{text}' → UTF-8 → ISO interprétation → '{bad_result}'")
            
        except Exception as e:
            print(f"'{text}' → Erreur: {e}")
    
    print("\n💡 C'est exactement ce qui arrive avec votre imprimante !")

def test_encoding_corrections():
    """
    Teste différentes méthodes de correction d'encodage
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
    
    test_text = "Café français: éèàùç"
    
    print(f"🧪 Test des corrections d'encodage sur {pos58_printer}")
    print("=" * 55)
    
    # Méthodes à tester
    methods = [
        {
            'name': 'Méthode 1: Force ISO-8859-1 direct',
            'function': lambda text: text.encode('iso-8859-1', errors='replace'),
            'esc_command': b'\x1b\x74\x03'  # ESC t 3
        },
        {
            'name': 'Méthode 2: Correction double encodage UTF-8→ISO',
            'function': fix_double_encoding_utf8_to_iso,
            'esc_command': b'\x1b\x74\x03'  # ESC t 3
        },
        {
            'name': 'Méthode 3: Force CP850 avec commande',
            'function': lambda text: text.encode('cp850', errors='replace'),
            'esc_command': b'\x1b\x74\x02'  # ESC t 2
        },
        {
            'name': 'Méthode 4: UTF-8 avec commande UTF-8',
            'function': lambda text: text.encode('utf-8', errors='replace'),
            'esc_command': b'\x1b\x74\x16'  # ESC t 22 (UTF-8)
        },
        {
            'name': 'Méthode 5: Pre-correction puis ASCII',
            'function': lambda text: fix_utf8_to_ascii_smart(text),
            'esc_command': None
        },
        {
            'name': 'Méthode 6: Latin-1 natif',
            'function': lambda text: text.encode('latin-1', errors='replace'), 
            'esc_command': b'\x1b\x74\x19'  # ESC t 25
        }
    ]
    
    for i, method in enumerate(methods, 1):
        print(f"\n[{i}/{len(methods)}] {method['name']}")
        
        try:
            commands = bytearray()
            commands.extend(ESC_INIT)
            
            # Ajouter la commande ESC/POS si spécifiée
            if method['esc_command']:
                commands.extend(method['esc_command'])
            
            commands.extend(ESC_CENTER)
            commands.extend(ESC_BOLD_ON)
            
            # Appliquer la méthode d'encodage
            encoded_text = method['function'](test_text)
            commands.extend(encoded_text)
            
            commands.extend(b'\n')
            commands.extend(ESC_BOLD_OFF)
            commands.extend(f"({method['name'][:20]}...)".encode('ascii', errors='replace'))
            commands.extend(b'\n\n')
            commands.extend(ESC_CUT)
            
            # Imprimer
            success = print_raw(pos58_printer, commands)
            
            if success:
                print(f"✅ Méthode {i} envoyée avec succès")
            else:
                print(f"❌ Méthode {i} a échoué à l'impression")
                
        except Exception as e:
            print(f"❌ Méthode {i} erreur: {e}")
        
        input("Appuyez sur Entrée pour la méthode suivante...")

def fix_utf8_to_ascii_smart(text):
    """
    Correction intelligente UTF-8 vers ASCII en préservant la lisibilité française
    """
    # D'abord essayer de corriger le double encodage
    try:
        utf8_bytes = text.encode('utf-8')
        # Essayer différentes interprétations
        for encoding in ['iso-8859-1', 'cp1252', 'cp850']:
            try:
                decoded = utf8_bytes.decode(encoding, errors='strict')
                # Si ça marche, re-encoder en ASCII en supprimant les accents
                return remove_accents_complete(decoded).encode('ascii', errors='replace')
            except:
                continue
    except:
        pass
    
    # Fallback: suppression directe des accents
    return remove_accents_complete(text).encode('ascii', errors='replace')

def remove_accents_complete(text):
    """
    Suppression complète des accents avec mapping détaillé
    """
    import unicodedata
    
    # Mapping manuel pour les cas spéciaux
    manual_replacements = {
        'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
        'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
        'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'ñ': 'n',
        'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A', 'Å': 'A',
        'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
        'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I',
        'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O',
        'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U',
        'Ç': 'C', 'Ñ': 'N',
        'œ': 'oe', 'Œ': 'OE', 'æ': 'ae', 'Æ': 'AE'
    }
    
    # Appliquer les remplacements manuels
    for accented, plain in manual_replacements.items():
        text = text.replace(accented, plain)
    
    # Utiliser unicodedata pour le reste
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    
    return text

def create_diagnostic_receipt():
    """
    Crée un reçu de diagnostic complet pour identifier le problème
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
    
    print(f"🔬 Création d'un reçu de diagnostic sur {pos58_printer}")
    
    commands = bytearray()
    commands.extend(ESC_INIT)
    
    # Test 1: ASCII pur
    commands.extend(ESC_CENTER)
    commands.extend(ESC_BOLD_ON)
    commands.extend(b"DIAGNOSTIC ENCODAGE")
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_OFF)
    commands.extend(ESC_LEFT)
    commands.extend(b"=" * 32)
    commands.extend(b'\n')
    
    # Test 2: Caractères problématiques un par un
    problem_chars = ['é', 'è', 'à', 'ç', 'ù', 'ô']
    
    commands.extend(b"Test caracteres un par un:\n")
    for char in problem_chars:
        try:
            # Méthode 1: UTF-8 direct
            utf8_version = char.encode('utf-8')
            commands.extend(f"UTF8-{char}: ".encode('ascii'))
            commands.extend(utf8_version)
            commands.extend(b'\n')
            
            # Méthode 2: ISO-8859-1
            iso_version = char.encode('iso-8859-1', errors='replace')
            commands.extend(f"ISO-{char}: ".encode('ascii'))
            commands.extend(iso_version)
            commands.extend(b'\n')
            
            # Méthode 3: Correction double encodage
            corrected = fix_double_encoding_utf8_to_iso(char)
            commands.extend(f"CORR-{char}: ".encode('ascii'))
            commands.extend(corrected)
            commands.extend(b'\n')
            
        except Exception as e:
            commands.extend(f"ERR-{char}: {str(e)[:10]}".encode('ascii', errors='replace'))
            commands.extend(b'\n')
    
    commands.extend(b"=" * 32)
    commands.extend(b'\n')
    commands.extend(b"Fin diagnostic")
    commands.extend(b'\n\n\n')
    commands.extend(ESC_CUT)
    
    success = print_raw(pos58_printer, commands)
    
    if success:
        print("✅ Reçu de diagnostic imprimé !")
        print("📋 Examinez les résultats pour voir quelle méthode fonctionne")
    else:
        print("❌ Échec de l'impression du diagnostic")

def main_menu():
    """
    Menu principal pour les tests de correction d'encodage
    """
    print("🔧 CORRECTEUR DE DOUBLE ENCODAGE UTF-8/ISO")
    print("=" * 45)
    print("1. Analyser le problème (simulation)")
    print("2. Créer un reçu de diagnostic")
    print("3. Tester toutes les méthodes de correction")
    print("4. Quitter")
    
    while True:
        try:
            choix = input("\nVotre choix (1-4): ").strip()
            
            if choix == '1':
                test_double_encoding_theory()
                
            elif choix == '2':
                create_diagnostic_receipt()
                
            elif choix == '3':
                test_encoding_corrections()
                
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