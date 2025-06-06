#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de test pour vérifier l'encodage français sur les imprimantes thermiques
Ce script teste différents encodages et imprime des exemples de texte français
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from printer.printer_utils import (
    get_printers, print_raw, safe_encode_french, 
    detect_printer_encoding, test_all_encodings,
    get_codepage_command, ESC_INIT, ESC_BOLD_ON, 
    ESC_BOLD_OFF, ESC_CENTER, ESC_LEFT, ESC_CUT
)
from utils.config import config, logger

def test_french_characters():
    """
    Teste l'impression de caractères français avec différents encodages
    """
    print("=== Test d'encodage des caractères français ===")
    
    # Textes de test français
    test_texts = [
        "Café français",
        "Hôtel de luxe",
        "Réservation confirmée", 
        "Mémoire naïve",
        "Crème brûlée",
        "Cœur généreux",
        "Caractères: éèàùç ÉÈÀÙÇ",
        "Spéciaux: œæ ŒÆÏÔÛ ñ",
        "Prix: 15,50€ - Quantité: 2"
    ]
    
    encodings_to_test = ['cp1252', 'cp850', 'cp437', 'latin1', 'utf-8']
    
    print(f"Textes de test:")
    for i, text in enumerate(test_texts, 1):
        print(f"  {i}. {text}")
    
    print(f"\nEncodages à tester: {encodings_to_test}")
    
    # Tester chaque encodage
    for encoding in encodings_to_test:
        print(f"\n--- Test encodage: {encoding} ---")
        
        for text in test_texts:
            try:
                encoded = safe_encode_french(text, encoding)
                print(f"✓ '{text}' -> {len(encoded)} bytes")
            except Exception as e:
                print(f"✗ '{text}' -> Erreur: {e}")

def create_test_receipt(printer_id=None):
    """
    Crée un reçu de test avec caractères français
    
    Args:
        printer_id (int): ID de l'imprimante (None pour la première trouvée)
    """
    printers = get_printers()
    
    if not printers:
        print("Aucune imprimante trouvée!")
        return False
    
    if printer_id is None:
        printer_id = 0
    
    if printer_id >= len(printers):
        print(f"Imprimante ID {printer_id} non trouvée!")
        return False
    
    printer_name = printers[printer_id]['name']
    encoding = detect_printer_encoding(printer_name)
    
    print(f"Test d'impression sur: {printer_name}")
    print(f"Encodage détecté: {encoding}")
    
    # Créer le reçu de test
    commands = bytearray()
    commands.extend(ESC_INIT)
    commands.extend(get_codepage_command(encoding))
    
    # En-tête
    commands.extend(ESC_CENTER)
    commands.extend(ESC_BOLD_ON)
    commands.extend(safe_encode_french("CAFÉ DE LA PAIX", encoding))
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_OFF)
    commands.extend(safe_encode_french("123 Rue de la République", encoding))
    commands.extend(b'\n')
    commands.extend(safe_encode_french("75001 Paris, France", encoding))
    commands.extend(b'\n')
    commands.extend(safe_encode_french("Tél: +33 1 42 86 87 88", encoding))
    commands.extend(b'\n\n')
    
    commands.extend(ESC_LEFT)
    commands.extend(b'=' * 32)
    commands.extend(b'\n')
    commands.extend(safe_encode_french("Date: 06/06/2025 14:30", encoding))
    commands.extend(b'\n')
    commands.extend(safe_encode_french("Serveur: François", encoding))
    commands.extend(b'\n')
    commands.extend(safe_encode_french("Table: 5 - Terrasse", encoding))
    commands.extend(b'\n')
    commands.extend(b'=' * 32)
    commands.extend(b'\n\n')
    
    # Articles avec caractères français
    articles = [
        ("Café expresso", 1, 2.50),
        ("Thé Earl Grey", 1, 3.00),
        ("Croissant beurré", 2, 1.80),
        ("Crème brûlée", 1, 6.50),
        ("Vin rouge (verre)", 1, 4.20),
        ("Eau minérale gazeuse", 1, 2.80)
    ]
    
    total = 0
    commands.extend(safe_encode_french("DÉTAIL DE LA COMMANDE", encoding))
    commands.extend(b'\n')
    commands.extend(b'-' * 32)
    commands.extend(b'\n')
    
    for nom, qte, prix in articles:
        ligne = f"{nom:<20} {qte:>2} {prix:>6.2f}€"
        if len(ligne) > 32:
            # Raccourcir le nom si nécessaire
            nom_court = nom[:15] + "..."
            ligne = f"{nom_court:<18} {qte:>2} {prix:>6.2f}€"
        
        commands.extend(safe_encode_french(ligne, encoding))
        commands.extend(b'\n')
        total += qte * prix
    
    commands.extend(b'-' * 32)
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_ON)
    commands.extend(safe_encode_french(f"TOTAL: {total:>21.2f}€", encoding))
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_OFF)
    commands.extend(b'\n')
    
    # Pied de page
    commands.extend(safe_encode_french("Mode de paiement: Carte bleue", encoding))
    commands.extend(b'\n')
    commands.extend(safe_encode_french("TVA incluse: 20%", encoding))
    commands.extend(b'\n\n')
    
    commands.extend(ESC_CENTER)
    commands.extend(safe_encode_french("Merci de votre visite!", encoding))
    commands.extend(b'\n')
    commands.extend(safe_encode_french("À bientôt au Café de la Paix", encoding))
    commands.extend(b'\n\n')
    
    # Test spécial caractères accentués
    commands.extend(ESC_BOLD_ON)
    commands.extend(safe_encode_french("TEST CARACTÈRES FRANÇAIS:", encoding))
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_OFF)
    commands.extend(safe_encode_french("àáâãäåæç èéêë ìíîï", encoding))
    commands.extend(b'\n')
    commands.extend(safe_encode_french("ðñòóôõöø ùúûüý þÿ", encoding))
    commands.extend(b'\n')
    commands.extend(safe_encode_french("ÀÁÂÃÄÅÆÇ ÈÉÊË ÌÍÎÏ", encoding))
    commands.extend(b'\n')
    commands.extend(safe_encode_french("ÐÑÒÓÔÕÖØ ÙÚÛÜÝ ÞŸ", encoding))
    commands.extend(b'\n\n')
    
    commands.extend(b'\n\n')
    commands.extend(ESC_CUT)
    
    # Imprimer
    success = print_raw(printer_name, commands)
    
    if success:
        print("✓ Reçu de test imprimé avec succès!")
    else:
        print("✗ Échec de l'impression du reçu de test")
    
    return success

def interactive_test():
    """
    Interface interactive pour tester l'encodage
    """
    print("=== TESTEUR D'ENCODAGE FRANÇAIS ===")
    print("Ce script teste l'impression de caractères français")
    print("sur les imprimantes thermiques\n")
    
    # Lister les imprimantes
    printers = get_printers()
    
    if not printers:
        print("❌ Aucune imprimante trouvée!")
        return
    
    print("Imprimantes détectées:")
    for i, printer in enumerate(printers):
        encoding = printer.get('encoding', 'Non détecté')
        width = printer.get('width', 'Non détecté')
        print(f"  {i}: {printer['name']}")
        print(f"     Largeur: {width}, Encodage: {encoding}")
    
    print("\nOptions disponibles:")
    print("1. Tester l'encodage des caractères (sans impression)")
    print("2. Imprimer un reçu de test français")
    print("3. Tester tous les encodages sur une imprimante")
    print("4. Quitter")
    
    while True:
        try:
            choix = input("\nVotre choix (1-4): ").strip()
            
            if choix == '1':
                test_french_characters()
                
            elif choix == '2':
                if len(printers) == 1:
                    printer_id = 0
                else:
                    printer_id = int(input(f"ID de l'imprimante (0-{len(printers)-1}): "))
                create_test_receipt(printer_id)
                
            elif choix == '3':
                if len(printers) == 1:
                    printer_id = 0
                else:
                    printer_id = int(input(f"ID de l'imprimante (0-{len(printers)-1}): "))
                
                if 0 <= printer_id < len(printers):
                    printer_name = printers[printer_id]['name']
                    print(f"\nTest de tous les encodages sur {printer_name}...")
                    results = test_all_encodings(printer_name)
                    
                    print("\nRésultats:")
                    for encoding, result in results.items():
                        status = "✓" if result.get('success', False) else "✗"
                        print(f"  {encoding}: {status}")
                        if 'error' in result:
                            print(f"    Erreur: {result['error']}")
                else:
                    print("ID d'imprimante invalide!")
                    
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
    interactive_test()