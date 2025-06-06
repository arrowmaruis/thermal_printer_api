#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils.config import logger, config
from printer.printer_utils import (
    ESC_INIT, ESC_BOLD_ON, ESC_BOLD_OFF, ESC_DOUBLE_HEIGHT_ON,
    ESC_DOUBLE_HEIGHT_OFF, ESC_CENTER, ESC_LEFT, ESC_RIGHT, ESC_CUT,
    get_codepage_command, safe_encode_french, detect_printer_encoding, is_pos58_printer
)

def format_receipt(receipt_data, receipt_type="standard", printer_width=None, encoding=None, printer_name=None):
    """
    Formate un reçu selon les données reçues et le type spécifié
    Types disponibles:
    - standard: commande restaurant/bar (défaut)
    - hotel: réservation d'hôtel
    - mixed: réservation d'hôtel + consommation restaurant/bar
    
    Args:
        receipt_data (dict): Données du reçu
        receipt_type (str): Type de reçu (standard, hotel, mixed)
        printer_width (str): Largeur d'imprimante (58mm, 80mm)
        encoding (str): Encodage à utiliser
        printer_name (str): Nom de l'imprimante (pour détection auto)
    """
    try:
        # Utiliser la configuration par défaut si non spécifiée
        if printer_width is None:
            printer_width = config.get('default_printer_width', '58mm')
        
        # Détection automatique de l'encodage si nécessaire
        if encoding is None or encoding == 'auto':
            if printer_name:
                if is_pos58_printer(printer_name):
                    encoding = config.get('pos58_encoding', 'ascii')
                else:
                    encoding = config.get('standard_encoding', 'cp1252')
            else:
                encoding = config.get('default_encoding', 'cp1252')
        
        # Log pour le débogage
        logger.info(f"Formatage reçu: type={receipt_type}, largeur={printer_width}, encodage={encoding}")
        if printer_name:
            logger.info(f"Imprimante: {printer_name}")

        # Récupération des données communes
        header = receipt_data.get('header', {})
        footer = receipt_data.get('footer', {})
        change_info = receipt_data.get('change_info')
        currency = 'FCFA'
        
        # Définir les largeurs selon le type d'imprimante
        if printer_width == "80mm":
            MAX_WIDTH = 48
            ARTICLE_WIDTH = 24
        else:
            MAX_WIDTH = 32
            ARTICLE_WIDTH = 14
        
        # Créer les commandes ESC/POS
        commands = bytearray()
        commands.extend(ESC_INIT)
        
        # Définir la page de codes appropriée pour l'encodage choisi
        commands.extend(get_codepage_command(encoding))
        
        # Fonction d'encodage avec nom d'imprimante
        def encode_text(text):
            return safe_encode_french(text, encoding, printer_name)
        
        # Formatage de l'en-tête (commun à tous les types)
        if header:
            # Nom de l'établissement
            if header.get('business_name'):
                commands.extend(ESC_CENTER)
                commands.extend(ESC_BOLD_ON)
                commands.extend(ESC_DOUBLE_HEIGHT_ON)
                business_name = header['business_name']
                if len(business_name) > MAX_WIDTH:
                    business_name = business_name[:MAX_WIDTH-3] + '...'
                commands.extend(encode_text(business_name))
                commands.extend(b'\n')
                commands.extend(ESC_DOUBLE_HEIGHT_OFF)
                commands.extend(ESC_BOLD_OFF)
            
            # Adresse
            if header.get('address'):
                commands.extend(ESC_CENTER)
                address = header['address']
                if len(address) > MAX_WIDTH:
                    address = address[:MAX_WIDTH-3] + '...'
                commands.extend(encode_text(address))
                commands.extend(b'\n')
            
            # Téléphone
            if header.get('phone'):
                commands.extend(ESC_CENTER)
                phone_text = f"Tél: {header['phone']}"
                if len(phone_text) > MAX_WIDTH:
                    phone_text = phone_text[:MAX_WIDTH-3] + '...'
                commands.extend(encode_text(phone_text))
                commands.extend(b'\n')
            
            # Type de document
            commands.extend(ESC_CENTER)
            commands.extend(ESC_BOLD_ON)
            
            # Déterminer le type de reçu à partir du numéro de reçu ou du type spécifié
            type_text = "REÇU"
            if receipt_type == "hotel":
                type_text = "RÉSERVATION"
            elif receipt_type == "mixed":
                type_text = "RÉSERVATION & CONSO"
            elif header.get('order_type'):
                type_text = header['order_type']
            elif header.get('receipt_number'):
                if header['receipt_number'].startswith('RES-'):
                    type_text = "RÉSERVATION"
                elif header['receipt_number'].startswith('ORD-'):
                    type_text = "COMMANDE"
                elif header['receipt_number'].startswith('HTL-'):
                    type_text = "HÔTEL"
                
            commands.extend(encode_text(type_text))
            commands.extend(b'\n')
            commands.extend(ESC_BOLD_OFF)
            
            commands.extend(ESC_LEFT)
            
            # Numéro de reçu
            if header.get('receipt_number'):
                receipt_text = f"Reçu #: {header['receipt_number']}"
                if len(receipt_text) > MAX_WIDTH:
                    receipt_text = receipt_text[:MAX_WIDTH-3] + '...'
                commands.extend(encode_text(receipt_text))
                commands.extend(b'\n')
            
            # Date
            if header.get('date'):
                date_text = f"Date: {header['date']}"
                commands.extend(encode_text(date_text))
                commands.extend(b'\n')
            
            # Informations client si disponibles
            if receipt_data.get('client_info'):
                client_info = receipt_data['client_info']
                if len(client_info) > MAX_WIDTH:
                    client_info = client_info[:MAX_WIDTH-3] + '...'
                commands.extend(encode_text(client_info))
                commands.extend(b'\n')
        
        # Informations chambre si disponibles
        if receipt_data.get('room_info'):
            room_info = receipt_data['room_info']
            
            # Diviser explicitement la chaîne selon les caractères \n
            room_info_lines = room_info.split('\n')
            
            # Imprimer chaque ligne séparément
            for line in room_info_lines:
                if line.strip():  # Éviter les lignes vides
                    commands.extend(encode_text(line.strip()))
                    commands.extend(b'\r\n')  # Utiliser \r\n pour la compatibilité maximale
            
            # Ajouter une ligne de séparation après les infos de chambre
            commands.extend(b'-' * MAX_WIDTH)
            commands.extend(b'\r\n')
        
        # Formatage du contenu selon le type de reçu
        if receipt_type == "standard" or receipt_type == "food" or receipt_type == "drink":
            format_standard_content(commands, receipt_data, MAX_WIDTH, ARTICLE_WIDTH, currency, encode_text)
        elif receipt_type == "hotel":
            format_hotel_content(commands, receipt_data, MAX_WIDTH, ARTICLE_WIDTH, currency, encode_text)
        elif receipt_type == "mixed":
            format_mixed_content(commands, receipt_data, MAX_WIDTH, ARTICLE_WIDTH, currency, encode_text)
        else:
            logger.warning(f"Type de reçu inconnu: {receipt_type}, utilisation du format standard")
            format_standard_content(commands, receipt_data, MAX_WIDTH, ARTICLE_WIDTH, currency, encode_text)
        
        # Formatage du pied de page
        if footer:
            # Méthode de paiement
            if footer.get('payment_method'):
                payment_line = f"Mode: {footer['payment_method']}"
                if len(payment_line) > MAX_WIDTH:
                    payment_line = payment_line[:MAX_WIDTH-3] + '...'
                commands.extend(encode_text(payment_line))
                commands.extend(b'\n')
            
            # Statut du paiement si présent
            if footer.get('payment_status'):
                status_line = footer['payment_status']
                if len(status_line) > MAX_WIDTH:
                    status_line = status_line[:MAX_WIDTH-3] + '...'
                commands.extend(encode_text(status_line))
                commands.extend(b'\n')
        
        # Section dédiée aux informations de monnaie (avant les remerciements)
        if change_info:
            commands.extend(b'\n')
            commands.extend(b'=' * MAX_WIDTH)
            commands.extend(b'\n')
            commands.extend(ESC_BOLD_ON)
            commands.extend(ESC_CENTER)
            commands.extend(encode_text("INFORMATION MONNAIE"))
            commands.extend(b'\n')
            commands.extend(ESC_BOLD_OFF)
            commands.extend(ESC_LEFT)
            commands.extend(b'=' * MAX_WIDTH)
            commands.extend(b'\n')
            
            # Montant de la monnaie due
            if change_info.get('formatted_amount'):
                amount_line = f"Montant: {change_info['formatted_amount']}"
                commands.extend(encode_text(amount_line))
                commands.extend(b'\n')
            
            # Statut de la monnaie
            if change_info.get('status_text'):
                status_line = f"Statut: {change_info['status_text']}"
                commands.extend(ESC_BOLD_ON)
                commands.extend(encode_text(status_line))
                commands.extend(b'\n')
                commands.extend(ESC_BOLD_OFF)
            
            # Date de remise si la monnaie a été rendue
            if change_info.get('change_given') and change_info.get('change_given_at'):
                date_line = f"Rendue le: {change_info['change_given_at']}"
                commands.extend(encode_text(date_line))
                commands.extend(b'\n')
            
            # Message d'attention si la monnaie n'a pas été rendue
            if change_info.get('status') == 'pending':
                commands.extend(b'\n')
                commands.extend(ESC_CENTER)
                commands.extend(ESC_BOLD_ON)
                attention_msg = "!!! ATTENTION !!!"
                commands.extend(encode_text(attention_msg))
                commands.extend(b'\n')
                pending_msg = "MONNAIE À RENDRE"
                commands.extend(encode_text(pending_msg))
                commands.extend(b'\n')
                commands.extend(ESC_BOLD_OFF)
                commands.extend(ESC_LEFT)
            
            commands.extend(b'=' * MAX_WIDTH)
            commands.extend(b'\n')
        
        # Continuer avec le footer
        if footer:
            commands.extend(b'\n')
            commands.extend(ESC_CENTER)
            
            # Message de remerciement
            if footer.get('thank_you_message'):
                thank_you = footer['thank_you_message']
                if len(thank_you) > MAX_WIDTH:
                    thank_you = thank_you[:MAX_WIDTH-3] + '...'
                commands.extend(encode_text(thank_you))
                commands.extend(b'\n')
            
            # Message additionnel
            if footer.get('additional_message'):
                add_msg = footer['additional_message']
                if len(add_msg) > MAX_WIDTH:
                    add_msg = add_msg[:MAX_WIDTH-3] + '...'
                commands.extend(encode_text(add_msg))
                commands.extend(b'\n')
            
            # Site web
            if footer.get('website'):
                website = footer['website']
                if len(website) > MAX_WIDTH:
                    website = website[:MAX_WIDTH-3] + '...'
                commands.extend(encode_text(website))
                commands.extend(b'\n')
        
        # Couper le papier
        commands.extend(b'\n\n\n')
        commands.extend(ESC_CUT)
        
        return commands
    except Exception as e:
        logger.error(f"Erreur lors du formatage du reçu: {e}")
        raise

def format_standard_content(commands, receipt_data, max_width, article_width, currency, encode_text):
    """Format pour commande restaurant/bar"""
    items = receipt_data.get('items', [])
    
    if items:
        # En-tête compact des articles
        commands.extend(ESC_BOLD_ON)
        header_line = "Art.  Qté Px    Total"
        commands.extend(encode_text(header_line))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        
        # Affichage des articles
        total = 0
        for item in items:
            name = item.get('name', '')
            if len(name) > article_width:
                name = name[:article_width-1] + '.'
            else:
                name = name.ljust(article_width)
            
            qty = item.get('quantity', 1)
            price = item.get('price', 0)
            item_total = qty * price
            total += item_total
            
            # Format standard pour tous les articles
            line = f"{name} {qty:2d} {price:5.0f} {item_total:7.0f}"
            commands.extend(encode_text(line))
            commands.extend(b'\n')
        
        # Séparateur avant le total
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        
        # Total général
        commands.extend(ESC_BOLD_ON)
        total_line = f"TOTAL:      {total:12,.0f} {currency}"
        commands.extend(encode_text(total_line))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)

def format_hotel_content(commands, receipt_data, max_width, article_width, currency, encode_text):
    """Format pour réservation hôtel"""
    # Voir s'il y a des statistiques spécifiques pour l'hôtel
    stats = receipt_data.get('stats', {})
    items = receipt_data.get('items', [])
    
    # Récupérer les articles par catégorie
    accommodation_items = []
    food_items = []
    other_items = []
    
    for item in items:
        if item.get('type') == 'accommodation':
            accommodation_items.append(item)
        elif item.get('type') == 'food' and item.get('category') == 'Restaurant':
            food_items.append(item)
        else:
            other_items.append(item)
    
    # Afficher les détails de la chambre d'abord
    if accommodation_items:
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text("DÉTAILS HÉBERGEMENT"))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        
        # Affichage des articles d'hébergement
        room_total = 0
        for item in accommodation_items:
            name = item.get('name', '')
            qty = item.get('quantity', 1)
            price = item.get('price', 0)
            item_total = qty * price
            room_total += item_total
            
            # Séparer les lignes si le nom est trop long
            if len(name) > max_width:
                name_parts = []
                current_part = ""
                for word in name.split():
                    if len(current_part + word) + 1 <= max_width:
                        current_part += (word + " ")
                    else:
                        name_parts.append(current_part.strip())
                        current_part = word + " "
                if current_part:
                    name_parts.append(current_part.strip())
                
                for idx, part in enumerate(name_parts):
                    if idx == 0:
                        commands.extend(encode_text(part))
                        commands.extend(b'\n')
                    else:
                        commands.extend(encode_text("  " + part))
                        commands.extend(b'\n')
            else:
                commands.extend(encode_text(name))
                commands.extend(b'\n')
            
            # Afficher le détail du prix
            price_line = f"  {qty} {item.get('quantity_unit', 'nuit(s)')} x {price:,} {currency}/nuit"
            commands.extend(encode_text(price_line))
            commands.extend(b'\n')
        
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        
        # Sous-total pour la chambre
        room_line = f"Sous-total:  {room_total:12,.0f} {currency}"
        commands.extend(encode_text(room_line))
        commands.extend(b'\n\n')
    
    # Afficher les petits déjeuners et autres services
    if food_items:
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text("RESTAURATION"))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        
        food_total = 0
        for item in food_items:
            name = item.get('name', '')
            qty = item.get('quantity', 1)
            price = item.get('price', 0)
            item_total = qty * price
            food_total += item_total
            
            line = f"{name} ({qty}) {item_total:,} {currency}"
            if len(line) > max_width:
                name = name[:max_width - 20] + "..."
                line = f"{name} ({qty}) {item_total:,} {currency}"
            
            commands.extend(encode_text(line))
            commands.extend(b'\n')
        
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        
        # Sous-total nourriture
        food_line = f"Sous-total:  {food_total:12,.0f} {currency}"
        commands.extend(encode_text(food_line))
        commands.extend(b'\n\n')
    
    # Afficher les autres services (extras)
    if other_items:
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text("EXTRAS"))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        
        extras_total = 0
        for item in other_items:
            name = item.get('name', '')
            qty = item.get('quantity', 1)
            price = item.get('price', 0)
            item_total = qty * price
            extras_total += item_total
            
            line = f"{name}: {item_total:,} {currency}"
            if len(line) > max_width:
                name = name[:max_width - 15] + "..."
                line = f"{name}: {item_total:,} {currency}"
            
            commands.extend(encode_text(line))
            commands.extend(b'\n')
        
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        
        # Sous-total extras
        extras_line = f"Sous-total:  {extras_total:12,.0f} {currency}"
        commands.extend(encode_text(extras_line))
        commands.extend(b'\n\n')
    
    # Réduction (si applicable)
    discount = stats.get('discount_amount', 0)
    if discount > 0:
        discount_line = f"Remise:     -{discount:12,.0f} {currency}"
        commands.extend(encode_text(discount_line))
        commands.extend(b'\n')
    
    # Calculer le total général
    total = sum(item.get('quantity', 1) * item.get('price', 0) for item in items)
    
    # Total après remise
    commands.extend(b'-' * max_width)
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_ON)
    total_line = f"TOTAL:      {total:12,.0f} {currency}"
    commands.extend(encode_text(total_line))
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_OFF)

def format_mixed_content(commands, receipt_data, max_width, article_width, currency, encode_text):
    """Format pour réservation hôtel + consommation restaurant/bar"""
    # Voir s'il y a des statistiques spécifiques
    stats = receipt_data.get('stats', {})
    items = receipt_data.get('items', [])
    
    # Récupérer les articles par catégorie
    accommodation_items = []
    food_items = []
    drink_items = []
    other_items = []
    
    for item in items:
        if item.get('type') == 'accommodation':
            accommodation_items.append(item)
        elif item.get('type') == 'food':
            food_items.append(item)
        elif item.get('type') == 'drink':
            drink_items.append(item)
        elif item.get('type') == 'discount':
            # Traiter séparément les remises
            pass
        else:
            other_items.append(item)
    
    # Partie 1: Afficher les détails de l'hébergement
    if accommodation_items:
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text("HÉBERGEMENT"))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        
        # Affichage des articles d'hébergement
        room_total = 0
        for item in accommodation_items:
            name = item.get('name', '')
            qty = item.get('quantity', 1)
            price = item.get('price', 0)
            item_total = qty * price
            room_total += item_total
            
            # Séparer les lignes si le nom est trop long
            if len(name) > max_width:
                name_parts = []
                current_part = ""
                for word in name.split():
                    if len(current_part + word) + 1 <= max_width:
                        current_part += (word + " ")
                    else:
                        name_parts.append(current_part.strip())
                        current_part = word + " "
                if current_part:
                    name_parts.append(current_part.strip())
                
                for idx, part in enumerate(name_parts):
                    if idx == 0:
                        commands.extend(encode_text(part))
                        commands.extend(b'\n')
                    else:
                        commands.extend(encode_text("  " + part))
                        commands.extend(b'\n')
            else:
                commands.extend(encode_text(name))
                commands.extend(b'\n')
            
            # Afficher le détail du prix
            price_line = f"  {qty} {item.get('quantity_unit', 'nuit(s)')} x {price:,} {currency}/nuit"
            commands.extend(encode_text(price_line))
            commands.extend(b'\n')
        
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        
        # Sous-total pour la chambre
        room_line = f"Hébergement: {room_total:12,.0f} {currency}"
        commands.extend(encode_text(room_line))
        commands.extend(b'\n\n')
    
    # Partie 2: Afficher les consommations (nourriture et boissons)
    if food_items or drink_items:
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text("CONSOMMATIONS"))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        
        # En-tête compact des articles (pour food et drink)
        commands.extend(ESC_BOLD_ON)
        header_line = "Art.  Qté Px    Total"
        commands.extend(encode_text(header_line))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        
        # Affichage des articles nourriture
        food_total = 0
        for item in food_items:
            name = item.get('name', '')
            if len(name) > article_width:
                name = name[:article_width-1] + '.'
            else:
                name = name.ljust(article_width)
            
            qty = item.get('quantity', 1)
            price = item.get('price', 0)
            item_total = qty * price
            food_total += item_total
            
            # Format standard pour tous les articles
            line = f"{name} {qty:2d} {price:5.0f} {item_total:7.0f}"
            commands.extend(encode_text(line))
            commands.extend(b'\n')
        
        # Affichage des articles boissons
        drink_total = 0
        for item in drink_items:
            name = item.get('name', '')
            if len(name) > article_width:
                name = name[:article_width-1] + '.'
            else:
                name = name.ljust(article_width)
            
            qty = item.get('quantity', 1)
            price = item.get('price', 0)
            item_total = qty * price
            drink_total += item_total
            
            # Format standard pour tous les articles
            line = f"{name} {qty:2d} {price:5.0f} {item_total:7.0f}"
            commands.extend(encode_text(line))
            commands.extend(b'\n')
        
        # Sous-total consommations
        if food_items or drink_items:
            commands.extend(b'-' * max_width)
            commands.extend(b'\n')
            
            consumption_total = food_total + drink_total
            consumption_line = f"Consommation:{consumption_total:12,.0f} {currency}"
            commands.extend(encode_text(consumption_line))
            commands.extend(b'\n\n')
    
    # Partie 3: Détails extras et réductions
    # Extras (autres services)
    if other_items:
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text("EXTRAS"))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        
        extras_total = 0
        for item in other_items:
            name = item.get('name', '')
            qty = item.get('quantity', 1)
            price = item.get('price', 0)
            item_total = qty * price
            extras_total += item_total
            
            line = f"{name}: {item_total:,} {currency}"
            if len(line) > max_width:
                name = name[:max_width - 15] + "..."
                line = f"{name}: {item_total:,} {currency}"
            
            commands.extend(encode_text(line))
            commands.extend(b'\n')
        
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        
        # Sous-total extras
        extras_line = f"Extras:      {extras_total:12,.0f} {currency}"
        commands.extend(encode_text(extras_line))
        commands.extend(b'\n\n')
    
    # Réduction (si applicable)
    discount_items = [item for item in items if item.get('type') == 'discount']
    discount_total = 0
    
    for item in discount_items:
        discount_total += item.get('price', 0)
    
    if discount_total != 0:  # La réduction peut être positive ou négative
        discount_line = f"Remise:     {discount_total:12,.0f} {currency}"
        commands.extend(encode_text(discount_line))
        commands.extend(b'\n')
    
    # Récapitulatif et total
    commands.extend(ESC_BOLD_ON)
    commands.extend(encode_text("RÉCAPITULATIF"))
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_OFF)
    commands.extend(b'-' * max_width)
    commands.extend(b'\n')
    
    # Calculer les différents sous-totaux
    room_total = sum(item.get('quantity', 1) * item.get('price', 0) 
                     for item in accommodation_items)
    
    food_total = sum(item.get('quantity', 1) * item.get('price', 0) 
                    for item in food_items)
    
    drink_total = sum(item.get('quantity', 1) * item.get('price', 0) 
                     for item in drink_items)
    
    extras_total = sum(item.get('quantity', 1) * item.get('price', 0) 
                      for item in other_items)
    
    # Calculer le grand total (y compris la réduction)
    grand_total = room_total + food_total + drink_total + extras_total + discount_total
    
    # Afficher le total par catégorie si présente
    if room_total > 0:
        commands.extend(encode_text(f"Hébergement: {room_total:12,.0f} {currency}"))
        commands.extend(b'\n')
    
    if food_total > 0 or drink_total > 0:
        consumption_total = food_total + drink_total
        commands.extend(encode_text(f"Consommation:{consumption_total:12,.0f} {currency}"))
        commands.extend(b'\n')
    
    if extras_total > 0:
        commands.extend(encode_text(f"Extras:      {extras_total:12,.0f} {currency}"))
        commands.extend(b'\n')
    
    if discount_total != 0:
        commands.extend(encode_text(f"Remise:      {discount_total:12,.0f} {currency}"))
        commands.extend(b'\n')
    
    # Total général
    commands.extend(b'-' * max_width)
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_ON)
    total_line = f"TOTAL:      {grand_total:12,.0f} {currency}"
    commands.extend(encode_text(total_line))
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_OFF)