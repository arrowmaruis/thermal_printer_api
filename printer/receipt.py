#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils.config import logger, config
from printer.printer_utils import (
    ESC_INIT, ESC_BOLD_ON, ESC_BOLD_OFF, ESC_DOUBLE_HEIGHT_ON,
    ESC_DOUBLE_HEIGHT_OFF, ESC_CENTER, ESC_LEFT, ESC_RIGHT, ESC_CUT,
    get_codepage_command, safe_encode_french, detect_printer_encoding, is_pos58_printer,
    get_robust_cut_command, get_robust_init_command, image_to_escpos
)


# ─────────────────────────────────────────────────────────────────────────────
# MOTEUR DYNAMIQUE — sections
# ─────────────────────────────────────────────────────────────────────────────

def _render_text_section(commands, section, max_width, encode_text):
    """Rend une section 'text' ou 'header'"""
    sec_type = section.get('type', 'text')
    text     = str(section.get('text', ''))
    align    = section.get('align', 'center' if sec_type == 'header' else 'left')
    bold     = section.get('bold',  sec_type == 'header')
    size     = section.get('size',  'double' if sec_type == 'header' else 'normal')

    if align == 'center':
        commands.extend(ESC_CENTER)
    elif align == 'right':
        commands.extend(ESC_RIGHT)
    else:
        commands.extend(ESC_LEFT)

    if bold:
        commands.extend(ESC_BOLD_ON)
    if size == 'double':
        commands.extend(ESC_DOUBLE_HEIGHT_ON)

    for line in (text.splitlines() or [text]):
        if len(line) > max_width:
            line = line[:max_width - 3] + '...'
        commands.extend(encode_text(line))
        commands.extend(b'\n')

    if size == 'double':
        commands.extend(ESC_DOUBLE_HEIGHT_OFF)
    if bold:
        commands.extend(ESC_BOLD_OFF)
    commands.extend(ESC_LEFT)


def _render_keyvalue_section(commands, section, max_width, encode_text):
    """Rend une section 'keyvalue' : clé alignée à gauche, valeur à droite"""
    rows      = section.get('rows', [])
    bold      = section.get('bold', False)
    key_width = int(section.get('key_width', max_width // 2))
    val_width = max_width - key_width - 1

    for row in rows:
        key   = str(row.get('key',   ''))[:key_width].ljust(key_width)
        value = str(row.get('value', ''))
        if len(value) > val_width:
            value = value[:val_width]
        value = value.rjust(val_width)

        if bold:
            commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text(key + ' ' + value))
        commands.extend(b'\n')
        if bold:
            commands.extend(ESC_BOLD_OFF)


def _render_table_section(commands, section, max_width, encode_text, currency, decimals):
    """
    Rend une section 'table' avec colonnes définies dynamiquement.

    Structure attendue :
    {
      "type": "table",
      "show_header": true,
      "columns": [
        { "label": "Article", "width": 14, "align": "left",  "format": "text"  },
        { "label": "Qté",     "width": 3,  "align": "right", "format": "integer" },
        { "label": "Prix",    "width": 7,  "align": "right", "format": "price" },
        { "label": "Total",   "width": 8,  "align": "right", "format": "price" }
      ],
      "rows": [
        ["Burger", 2, 12.50, 25.00],
        ["Coca",   1,  3.00,  3.00]
      ]
    }
    """
    columns     = [dict(c) for c in section.get('columns', [])]   # copie pour ne pas muter
    rows        = section.get('rows', [])
    show_header = section.get('show_header', True)
    separator   = section.get('separator', True)

    if not columns:
        return

    # Réduire les largeurs proportionnellement si ça dépasse la largeur papier
    separators       = len(columns) - 1
    total_col_width  = sum(col.get('width', 10) for col in columns)
    total_width      = total_col_width + separators

    if total_width > max_width:
        available = max_width - separators
        for col in columns:
            col['width'] = max(3, int(col.get('width', 10) * available / total_col_width))

    def format_cell(value, col):
        width = col.get('width', 10)
        align = col.get('align', 'left')
        fmt   = col.get('format', 'text')

        if fmt == 'price':
            try:
                formatted = f"{float(value):,.{decimals}f}"
            except (ValueError, TypeError):
                formatted = str(value)
        elif fmt == 'integer':
            try:
                formatted = str(int(value))
            except (ValueError, TypeError):
                formatted = str(value)
        else:
            formatted = str(value) if value is not None else ''

        if len(formatted) > width:
            formatted = formatted[:width - 1] + '.'

        if align == 'right':
            return formatted.rjust(width)
        elif align == 'center':
            return formatted.center(width)
        else:
            return formatted.ljust(width)

    # En-tête des colonnes
    if show_header:
        header_line = ' '.join(
            format_cell(col.get('label', ''), {**col, 'format': 'text'})
            for col in columns
        )
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text(header_line))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')

    # Lignes de données
    for row in rows:
        line = ' '.join(
            format_cell(row[i] if i < len(row) else '', col)
            for i, col in enumerate(columns)
        )
        commands.extend(encode_text(line))
        commands.extend(b'\n')

    if separator:
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')


def _render_logo_section(commands, section, max_width, printer_width):
    """
    Rend une section 'logo' — imprime une image en ESC/POS raster.

    Parametres de la section :
      image  (str) : image en base64 OU chemin vers un fichier sur le serveur
      align  (str) : 'left' | 'center' | 'right'  (defaut: 'center')
      width  (int) : largeur cible en pixels (defaut: adapte au papier)
    """
    image_source = section.get('image') or section.get('path')
    if not image_source:
        logger.warning("Section logo : champ 'image' ou 'path' manquant")
        return

    align = section.get('align', 'center')

    # Largeur max selon le papier
    if printer_width == '80mm':
        default_max_px = 512
    else:
        default_max_px = 300  # conservateur pour 58mm

    max_px = int(section.get('width', default_max_px))

    logo_bytes = image_to_escpos(image_source, max_width_px=max_px, align=align)
    if logo_bytes:
        commands.extend(logo_bytes)
    else:
        logger.warning("Conversion logo echouee — section ignoree")


def _render_section(commands, section, max_width, encode_text, currency, decimals,
                    printer_width='58mm'):
    """Dispatch vers le bon renderer selon le type de section"""
    sec_type = section.get('type', 'text')

    if sec_type in ('header', 'text'):
        _render_text_section(commands, section, max_width, encode_text)

    elif sec_type == 'logo':
        _render_logo_section(commands, section, max_width, printer_width)

    elif sec_type == 'separator':
        char = str(section.get('char', '-'))
        commands.extend(encode_text(char * max_width))
        commands.extend(b'\n')

    elif sec_type == 'keyvalue':
        _render_keyvalue_section(commands, section, max_width, encode_text)

    elif sec_type == 'table':
        _render_table_section(commands, section, max_width, encode_text, currency, decimals)

    elif sec_type == 'feed':
        lines = max(1, int(section.get('lines', 1)))
        commands.extend(b'\n' * lines)

    elif sec_type == 'cut':
        pass  # géré dans format_receipt (après toutes les sections)

    else:
        logger.warning(f"Type de section inconnu: {sec_type}")


def format_dynamic_content(commands, receipt_data, max_width, encode_text, currency, decimals,
                           printer_name, printer_width='58mm'):
    """
    Moteur de rendu dynamique.
    Parcourt le tableau 'sections' et rend chaque section dans l'ordre.
    """
    sections = receipt_data.get('sections', [])
    for section in sections:
        try:
            _render_section(commands, section, max_width, encode_text, currency, decimals,
                            printer_width)
        except Exception as e:
            logger.error(f"Erreur section '{section.get('type', '?')}': {e}")


# ─────────────────────────────────────────────────────────────────────────────
# POINT D'ENTRÉE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def format_receipt(receipt_data, receipt_type="standard", printer_width=None, encoding=None, printer_name=None):
    """
    Formate un reçu selon les données reçues et le type spécifié.

    Modes :
    - Dynamique  : si receipt_data contient une clé 'sections' (tableau de sections)
    - Standard   : receipt_type = 'standard' | 'food' | 'drink'
    - Hôtel      : receipt_type = 'hotel'
    - Mixte      : receipt_type = 'mixed'
    """
    try:
        if printer_width is None:
            printer_width = config.get('default_printer_width', '58mm')

        if encoding is None or encoding == 'auto':
            if printer_name:
                if is_pos58_printer(printer_name):
                    encoding = config.get('pos58_encoding', 'ascii')
                else:
                    encoding = config.get('standard_encoding', 'cp1252')
            else:
                encoding = config.get('default_encoding', 'cp1252')

        logger.info(f"Formatage reçu: type={receipt_type}, largeur={printer_width}, encodage={encoding}")
        if printer_name:
            logger.info(f"Imprimante: {printer_name}")

        header      = receipt_data.get('header', {})
        footer      = receipt_data.get('footer', {})
        change_info = receipt_data.get('change_info')

        currency = receipt_data.get('currency') or config.get('currency', 'FCFA')
        decimals = int(receipt_data.get('currency_decimals', config.get('currency_decimals', 0)))

        if printer_width == "80mm":
            MAX_WIDTH    = 48
            ARTICLE_WIDTH = 24
        else:
            MAX_WIDTH    = 32
            ARTICLE_WIDTH = 14

        commands = bytearray()
        commands.extend(get_robust_init_command(printer_name))
        commands.extend(get_codepage_command(encoding))

        def encode_text(text):
            return safe_encode_french(text, encoding, printer_name)

        # ── Mode dynamique ──────────────────────────────────────────────────
        if 'sections' in receipt_data:
            format_dynamic_content(commands, receipt_data, MAX_WIDTH, encode_text, currency, decimals,
                                   printer_name, printer_width)

            # Coupe finale sauf si une section 'cut' est déjà présente
            has_explicit_cut = any(s.get('type') == 'cut' for s in receipt_data.get('sections', []))
            if not has_explicit_cut:
                commands.extend(b'\n\n\n')
                commands.extend(get_robust_cut_command(printer_name))
            return commands

        # ── Mode classique : en-tête ────────────────────────────────────────
        if header:
            if header.get('business_name'):
                commands.extend(ESC_CENTER)
                commands.extend(ESC_BOLD_ON)
                commands.extend(ESC_DOUBLE_HEIGHT_ON)
                business_name = header['business_name']
                if len(business_name) > MAX_WIDTH:
                    business_name = business_name[:MAX_WIDTH - 3] + '...'
                commands.extend(encode_text(business_name))
                commands.extend(b'\n')
                commands.extend(ESC_DOUBLE_HEIGHT_OFF)
                commands.extend(ESC_BOLD_OFF)

            if header.get('address'):
                commands.extend(ESC_CENTER)
                address = header['address']
                if len(address) > MAX_WIDTH:
                    address = address[:MAX_WIDTH - 3] + '...'
                commands.extend(encode_text(address))
                commands.extend(b'\n')

            if header.get('phone'):
                commands.extend(ESC_CENTER)
                phone_text = f"Tél: {header['phone']}"
                if len(phone_text) > MAX_WIDTH:
                    phone_text = phone_text[:MAX_WIDTH - 3] + '...'
                commands.extend(encode_text(phone_text))
                commands.extend(b'\n')

            commands.extend(ESC_CENTER)
            commands.extend(ESC_BOLD_ON)

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

            if header.get('receipt_number'):
                receipt_text = f"Reçu #: {header['receipt_number']}"
                if len(receipt_text) > MAX_WIDTH:
                    receipt_text = receipt_text[:MAX_WIDTH - 3] + '...'
                commands.extend(encode_text(receipt_text))
                commands.extend(b'\n')

            if header.get('date'):
                commands.extend(encode_text(f"Date: {header['date']}"))
                commands.extend(b'\n')

            if receipt_data.get('client_info'):
                client_info = receipt_data['client_info']
                if len(client_info) > MAX_WIDTH:
                    client_info = client_info[:MAX_WIDTH - 3] + '...'
                commands.extend(encode_text(client_info))
                commands.extend(b'\n')

        if receipt_data.get('room_info'):
            for line in receipt_data['room_info'].splitlines():
                if line.strip():
                    commands.extend(encode_text(line.strip()))
                    commands.extend(b'\r\n')
            commands.extend(b'-' * MAX_WIDTH)
            commands.extend(b'\r\n')

        # ── Contenu selon le type ───────────────────────────────────────────
        if receipt_type in ("standard", "food", "drink"):
            format_standard_content(commands, receipt_data, MAX_WIDTH, ARTICLE_WIDTH, currency, encode_text, decimals)
        elif receipt_type == "hotel":
            format_hotel_content(commands, receipt_data, MAX_WIDTH, ARTICLE_WIDTH, currency, encode_text, decimals)
        elif receipt_type == "mixed":
            format_mixed_content(commands, receipt_data, MAX_WIDTH, ARTICLE_WIDTH, currency, encode_text, decimals)
        else:
            logger.warning(f"Type de reçu inconnu: {receipt_type}, utilisation du format standard")
            format_standard_content(commands, receipt_data, MAX_WIDTH, ARTICLE_WIDTH, currency, encode_text, decimals)

        # ── Pied de page ────────────────────────────────────────────────────
        if footer:
            if footer.get('payment_method'):
                payment_line = f"Mode: {footer['payment_method']}"
                if len(payment_line) > MAX_WIDTH:
                    payment_line = payment_line[:MAX_WIDTH - 3] + '...'
                commands.extend(encode_text(payment_line))
                commands.extend(b'\n')

            if footer.get('payment_status'):
                status_line = footer['payment_status']
                if len(status_line) > MAX_WIDTH:
                    status_line = status_line[:MAX_WIDTH - 3] + '...'
                commands.extend(encode_text(status_line))
                commands.extend(b'\n')

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

            if change_info.get('formatted_amount'):
                commands.extend(encode_text(f"Montant: {change_info['formatted_amount']}"))
                commands.extend(b'\n')

            if change_info.get('status_text'):
                commands.extend(ESC_BOLD_ON)
                commands.extend(encode_text(f"Statut: {change_info['status_text']}"))
                commands.extend(b'\n')
                commands.extend(ESC_BOLD_OFF)

            if change_info.get('change_given') and change_info.get('change_given_at'):
                commands.extend(encode_text(f"Rendue le: {change_info['change_given_at']}"))
                commands.extend(b'\n')

            if change_info.get('status') == 'pending':
                commands.extend(b'\n')
                commands.extend(ESC_CENTER)
                commands.extend(ESC_BOLD_ON)
                commands.extend(encode_text("!!! ATTENTION !!!"))
                commands.extend(b'\n')
                commands.extend(encode_text("MONNAIE À RENDRE"))
                commands.extend(b'\n')
                commands.extend(ESC_BOLD_OFF)
                commands.extend(ESC_LEFT)

            commands.extend(b'=' * MAX_WIDTH)
            commands.extend(b'\n')

        if footer:
            commands.extend(b'\n')
            commands.extend(ESC_CENTER)

            if footer.get('thank_you_message'):
                thank_you = footer['thank_you_message']
                if len(thank_you) > MAX_WIDTH:
                    thank_you = thank_you[:MAX_WIDTH - 3] + '...'
                commands.extend(encode_text(thank_you))
                commands.extend(b'\n')

            if footer.get('additional_message'):
                add_msg = footer['additional_message']
                if len(add_msg) > MAX_WIDTH:
                    add_msg = add_msg[:MAX_WIDTH - 3] + '...'
                commands.extend(encode_text(add_msg))
                commands.extend(b'\n')

            if footer.get('website'):
                website = footer['website']
                if len(website) > MAX_WIDTH:
                    website = website[:MAX_WIDTH - 3] + '...'
                commands.extend(encode_text(website))
                commands.extend(b'\n')

        commands.extend(b'\n\n\n')
        commands.extend(get_robust_cut_command(printer_name))

        return commands
    except Exception as e:
        logger.error(f"Erreur lors du formatage du reçu: {e}")
        raise


# ─────────────────────────────────────────────────────────────────────────────
# FORMATS CLASSIQUES (rétrocompatibilité)
# ─────────────────────────────────────────────────────────────────────────────

def format_standard_content(commands, receipt_data, max_width, article_width, currency, encode_text, decimals=0):
    """Format pour commande restaurant/bar"""
    items = receipt_data.get('items', [])
    eff_art_width = article_width - decimals

    if items:
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text("Art.  Qté Px    Total"))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')

        total = 0
        for item in items:
            name = item.get('name', '')
            if len(name) > eff_art_width:
                name = name[:eff_art_width - 1] + '.'
            else:
                name = name.ljust(eff_art_width)

            qty        = item.get('quantity', 1)
            price      = float(item.get('price', 0))
            item_total = qty * price
            total     += item_total

            line = f"{name} {qty:2d} {price:6.{decimals}f} {item_total:{7+decimals}.{decimals}f}"
            commands.extend(encode_text(line))
            commands.extend(b'\n')

        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text(f"TOTAL:      {total:12,.{decimals}f} {currency}"))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)


def format_hotel_content(commands, receipt_data, max_width, article_width, currency, encode_text, decimals=0):
    """Format pour réservation hôtel"""
    stats  = receipt_data.get('stats', {})
    items  = receipt_data.get('items', [])

    accommodation_items = []
    food_items          = []
    other_items         = []

    for item in items:
        if item.get('type') == 'accommodation':
            accommodation_items.append(item)
        elif item.get('type') == 'food' and item.get('category') == 'Restaurant':
            food_items.append(item)
        else:
            other_items.append(item)

    if accommodation_items:
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text("DÉTAILS HÉBERGEMENT"))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')

        room_total = 0
        for item in accommodation_items:
            name       = item.get('name', '')
            qty        = item.get('quantity', 1)
            price      = float(item.get('price', 0))
            item_total = qty * price
            room_total += item_total

            if len(name) > max_width:
                name_parts   = []
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
                    commands.extend(encode_text(("  " if idx > 0 else "") + part))
                    commands.extend(b'\n')
            else:
                commands.extend(encode_text(name))
                commands.extend(b'\n')

            price_line = f"  {qty} {item.get('quantity_unit', 'nuit(s)')} x {price:,.{decimals}f} {currency}/nuit"
            commands.extend(encode_text(price_line))
            commands.extend(b'\n')

        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        commands.extend(encode_text(f"Sous-total:  {room_total:12,.{decimals}f} {currency}"))
        commands.extend(b'\n\n')

    if food_items:
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text("RESTAURATION"))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')

        food_total = 0
        for item in food_items:
            name       = item.get('name', '')
            qty        = item.get('quantity', 1)
            price      = float(item.get('price', 0))
            item_total = qty * price
            food_total += item_total

            line = f"{name} ({qty}) {item_total:,.{decimals}f} {currency}"
            if len(line) > max_width:
                name = name[:max_width - 20] + "..."
                line = f"{name} ({qty}) {item_total:,.{decimals}f} {currency}"
            commands.extend(encode_text(line))
            commands.extend(b'\n')

        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        commands.extend(encode_text(f"Sous-total:  {food_total:12,.{decimals}f} {currency}"))
        commands.extend(b'\n\n')

    if other_items:
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text("EXTRAS"))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')

        extras_total = 0
        for item in other_items:
            name       = item.get('name', '')
            qty        = item.get('quantity', 1)
            price      = float(item.get('price', 0))
            item_total = qty * price
            extras_total += item_total

            line = f"{name}: {item_total:,.{decimals}f} {currency}"
            if len(line) > max_width:
                name = name[:max_width - 15] + "..."
                line = f"{name}: {item_total:,.{decimals}f} {currency}"
            commands.extend(encode_text(line))
            commands.extend(b'\n')

        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        commands.extend(encode_text(f"Sous-total:  {extras_total:12,.{decimals}f} {currency}"))
        commands.extend(b'\n\n')

    discount = stats.get('discount_amount', 0)
    if discount > 0:
        commands.extend(encode_text(f"Remise:     -{float(discount):12,.{decimals}f} {currency}"))
        commands.extend(b'\n')

    total = sum(item.get('quantity', 1) * float(item.get('price', 0)) for item in items)
    commands.extend(b'-' * max_width)
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_ON)
    commands.extend(encode_text(f"TOTAL:      {total:12,.{decimals}f} {currency}"))
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_OFF)


def format_mixed_content(commands, receipt_data, max_width, article_width, currency, encode_text, decimals=0):
    """Format pour réservation hôtel + consommation restaurant/bar"""
    items = receipt_data.get('items', [])

    accommodation_items = []
    food_items          = []
    drink_items         = []
    other_items         = []

    for item in items:
        if item.get('type') == 'accommodation':
            accommodation_items.append(item)
        elif item.get('type') == 'food':
            food_items.append(item)
        elif item.get('type') == 'drink':
            drink_items.append(item)
        elif item.get('type') == 'discount':
            pass
        else:
            other_items.append(item)

    eff_art_width = article_width - decimals

    if accommodation_items:
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text("HÉBERGEMENT"))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')

        room_total = 0
        for item in accommodation_items:
            name       = item.get('name', '')
            qty        = item.get('quantity', 1)
            price      = float(item.get('price', 0))
            item_total = qty * price
            room_total += item_total

            if len(name) > max_width:
                name_parts   = []
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
                    commands.extend(encode_text(("  " if idx > 0 else "") + part))
                    commands.extend(b'\n')
            else:
                commands.extend(encode_text(name))
                commands.extend(b'\n')

            price_line = f"  {qty} {item.get('quantity_unit', 'nuit(s)')} x {price:,.{decimals}f} {currency}/nuit"
            commands.extend(encode_text(price_line))
            commands.extend(b'\n')

        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        commands.extend(encode_text(f"Hébergement: {room_total:12,.{decimals}f} {currency}"))
        commands.extend(b'\n\n')

    if food_items or drink_items:
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text("CONSOMMATIONS"))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text("Art.  Qté Px    Total"))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')

        food_total = 0
        for item in food_items:
            name = item.get('name', '')
            name = (name[:eff_art_width - 1] + '.') if len(name) > eff_art_width else name.ljust(eff_art_width)
            qty        = item.get('quantity', 1)
            price      = float(item.get('price', 0))
            item_total = qty * price
            food_total += item_total
            commands.extend(encode_text(f"{name} {qty:2d} {price:6.{decimals}f} {item_total:{7+decimals}.{decimals}f}"))
            commands.extend(b'\n')

        drink_total = 0
        for item in drink_items:
            name = item.get('name', '')
            name = (name[:eff_art_width - 1] + '.') if len(name) > eff_art_width else name.ljust(eff_art_width)
            qty         = item.get('quantity', 1)
            price       = float(item.get('price', 0))
            item_total  = qty * price
            drink_total += item_total
            commands.extend(encode_text(f"{name} {qty:2d} {price:6.{decimals}f} {item_total:{7+decimals}.{decimals}f}"))
            commands.extend(b'\n')

        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        consumption_total = food_total + drink_total
        commands.extend(encode_text(f"Consommation:{consumption_total:12,.{decimals}f} {currency}"))
        commands.extend(b'\n\n')

    if other_items:
        commands.extend(ESC_BOLD_ON)
        commands.extend(encode_text("EXTRAS"))
        commands.extend(b'\n')
        commands.extend(ESC_BOLD_OFF)
        commands.extend(b'-' * max_width)
        commands.extend(b'\n')

        extras_total = 0
        for item in other_items:
            name       = item.get('name', '')
            price      = float(item.get('price', 0))
            item_total = item.get('quantity', 1) * price
            extras_total += item_total

            line = f"{name}: {item_total:,.{decimals}f} {currency}"
            if len(line) > max_width:
                name = name[:max_width - 15] + "..."
                line = f"{name}: {item_total:,.{decimals}f} {currency}"
            commands.extend(encode_text(line))
            commands.extend(b'\n')

        commands.extend(b'-' * max_width)
        commands.extend(b'\n')
        commands.extend(encode_text(f"Extras:      {extras_total:12,.{decimals}f} {currency}"))
        commands.extend(b'\n\n')

    discount_items = [item for item in items if item.get('type') == 'discount']
    discount_total = sum(float(item.get('price', 0)) for item in discount_items)
    if discount_total != 0:
        commands.extend(encode_text(f"Remise:     {discount_total:12,.{decimals}f} {currency}"))
        commands.extend(b'\n')

    room_total        = sum(i.get('quantity', 1) * float(i.get('price', 0)) for i in accommodation_items)
    food_total        = sum(i.get('quantity', 1) * float(i.get('price', 0)) for i in food_items)
    drink_total       = sum(i.get('quantity', 1) * float(i.get('price', 0)) for i in drink_items)
    extras_total      = sum(i.get('quantity', 1) * float(i.get('price', 0)) for i in other_items)
    grand_total       = room_total + food_total + drink_total + extras_total + discount_total

    commands.extend(ESC_BOLD_ON)
    commands.extend(encode_text("RÉCAPITULATIF"))
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_OFF)
    commands.extend(b'-' * max_width)
    commands.extend(b'\n')

    if room_total > 0:
        commands.extend(encode_text(f"Hébergement: {room_total:12,.{decimals}f} {currency}"))
        commands.extend(b'\n')
    if food_total > 0 or drink_total > 0:
        commands.extend(encode_text(f"Consommation:{food_total+drink_total:12,.{decimals}f} {currency}"))
        commands.extend(b'\n')
    if extras_total > 0:
        commands.extend(encode_text(f"Extras:      {extras_total:12,.{decimals}f} {currency}"))
        commands.extend(b'\n')
    if discount_total != 0:
        commands.extend(encode_text(f"Remise:      {discount_total:12,.{decimals}f} {currency}"))
        commands.extend(b'\n')

    commands.extend(b'-' * max_width)
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_ON)
    commands.extend(encode_text(f"TOTAL:      {grand_total:12,.{decimals}f} {currency}"))
    commands.extend(b'\n')
    commands.extend(ESC_BOLD_OFF)
