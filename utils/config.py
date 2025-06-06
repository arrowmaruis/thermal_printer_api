#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
from datetime import datetime

# Configuration
PORT = 5789
HOST = '0.0.0.0'  # Accessible depuis n'importe quelle machine du réseau
APP_NAME = "ImprimanteAPI"
VERSION = "1.0.0"
CONFIG_FILE = "printer_config.json"

# Configuration globale optimisée pour le français avec support POS-58
config = {
    "default_printer_id": None,
    "default_printer_name": None,
    "default_printer_width": "58mm",
    "autostart": True,
    "port": PORT,
    
    # Encodage principal (détection automatique par défaut)
    "default_encoding": "auto",           # 'auto' = détection automatique optimale
    
    # Encodages spécifiques par type d'imprimante
    "pos58_encoding": "ascii",            # POS-58 → ASCII (solution qui marche)
    "standard_encoding": "cp1252",        # Autres imprimantes → cp1252 (comme Word)
    
    # Configuration avancée
    "force_ascii_for_pos58": True,        # Force ASCII pour POS-58 (recommandé)
    "allow_encoding_override": True,      # Permet de forcer un encodage via l'interface
    "smart_fallback": True,               # Active le fallback intelligent
    
    # Pages de codes et fallbacks
    "printer_codepage": "WPC1252",
    "fallback_encodings": [
        "cp1252",          # Windows-1252 (comme Word)
        "cp850",           # Europe occidentale
        "latin1",          # ISO 8859-1
        "cp437",           # DOS basique
        "ascii"            # ASCII (dernier recours)
    ],
    
    # Options de conversion ASCII
    "ascii_conversion_mode": "smart",     # 'smart', 'basic', 'aggressive'
    "preserve_euro_symbol": True,         # € → EUR
    "preserve_ligatures": True,           # œ → oe, æ → ae
    
    # Logging et débogage
    "log_encoding_decisions": True,       # Log les décisions d'encodage
    "debug_encoding": False               # Mode debug pour l'encodage
}

def setup_logging():
    """Configure le système de journalisation avec support UTF-8"""
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_file = f'logs/imprimante_api_{datetime.now().strftime("%Y%m%d")}.log'
    
    # Configuration du logging avec encodage UTF-8
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configurer l'encodage de la console pour Windows
    if sys.platform.startswith('win'):
        try:
            os.system('chcp 65001 > nul 2>&1')
        except:
            pass
    
    return logging.getLogger(APP_NAME)

# Initialisation du logger
logger = setup_logging()

def load_config():
    """Charge la configuration depuis le fichier"""
    global config
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                config.update(loaded_config)
                logger.info(f"Configuration chargée")
                
                # Migration automatique des anciennes configs
                migrate_config_if_needed()
                
                # Validation de la configuration
                validate_config()
                
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {e}")
        logger.info("Utilisation de la configuration par défaut")

def migrate_config_if_needed():
    """Migre les anciennes configurations vers le nouveau format"""
    global config
    
    # Migration 1: encodage UTF-8 → auto
    if config.get('default_encoding') == 'utf-8':
        config['default_encoding'] = 'auto'
        logger.info("Migration: default_encoding utf-8 → auto")
    
    # Migration 2: Ajouter les nouvelles propriétés si manquantes
    new_properties = {
        'pos58_encoding': 'ascii',
        'standard_encoding': 'cp1252',
        'force_ascii_for_pos58': True,
        'allow_encoding_override': True,
        'smart_fallback': True,
        'ascii_conversion_mode': 'smart',
        'preserve_euro_symbol': True,
        'preserve_ligatures': True,
        'log_encoding_decisions': True,
        'debug_encoding': False
    }
    
    for prop, default_value in new_properties.items():
        if prop not in config:
            config[prop] = default_value
            logger.info(f"Propriété ajoutée: {prop} = {default_value}")

def validate_config():
    """Valide la configuration et corrige les valeurs invalides"""
    global config
    
    # Validation des encodages
    valid_encodings = ['auto', 'ascii', 'cp1252', 'cp850', 'latin1', 'cp437', 'utf-8']
    
    if config.get('default_encoding') not in valid_encodings:
        logger.warning(f"Encodage par défaut invalide: {config.get('default_encoding')}, correction vers 'auto'")
        config['default_encoding'] = 'auto'
    
    if config.get('pos58_encoding') not in valid_encodings:
        logger.warning(f"Encodage POS-58 invalide: {config.get('pos58_encoding')}, correction vers 'ascii'")
        config['pos58_encoding'] = 'ascii'
    
    # Validation du port
    port = config.get('port', PORT)
    if not isinstance(port, int) or port < 1024 or port > 65535:
        logger.warning(f"Port invalide: {port}, correction vers {PORT}")
        config['port'] = PORT

def save_config():
    """Sauvegarde la configuration dans le fichier avec encodage UTF-8"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info("Configuration sauvegardée")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")

def get_optimal_encoding_for_printer(printer_name):
    """
    Retourne l'encodage optimal pour une imprimante spécifique
    Prend en compte la configuration et les spécificités du matériel
    """
    if not printer_name:
        return config.get('standard_encoding', 'cp1252')
    
    # Vérification POS-58 avec option de forçage
    if config.get('force_ascii_for_pos58', True):
        if 'POS-58' in printer_name.upper() or 'POS58' in printer_name.upper():
            encoding = config.get('pos58_encoding', 'ascii')
            if config.get('log_encoding_decisions', True):
                logger.info(f"POS-58 détectée: {printer_name} → encodage {encoding}")
            return encoding
    
    # Pour les autres imprimantes
    default_encoding = config.get('default_encoding', 'auto')
    
    if default_encoding == 'auto':
        # Détection automatique intelligente
        return config.get('standard_encoding', 'cp1252')
    else:
        # Encodage forcé par l'utilisateur
        if config.get('log_encoding_decisions', True):
            logger.info(f"Encodage forcé pour {printer_name}: {default_encoding}")
        return default_encoding

def set_printer_encoding(printer_name, encoding):
    """
    Définit l'encodage pour une imprimante spécifique
    Permet de forcer un encodage via l'interface utilisateur
    """
    if not config.get('allow_encoding_override', True):
        logger.warning("Modification d'encodage désactivée dans la configuration")
        return False
    
    # Vérifier que l'encodage est valide
    valid_encodings = ['auto', 'ascii', 'cp1252', 'cp850', 'latin1', 'cp437', 'utf-8']
    if encoding not in valid_encodings:
        logger.error(f"Encodage invalide: {encoding}")
        return False
    
    # Cas spécial POS-58
    if 'POS-58' in printer_name.upper() or 'POS58' in printer_name.upper():
        config['pos58_encoding'] = encoding
        logger.info(f"Encodage POS-58 modifié: {encoding}")
    else:
        # Pour les autres imprimantes, modifier l'encodage par défaut
        config['default_encoding'] = encoding
        logger.info(f"Encodage par défaut modifié: {encoding}")
    
    save_config()
    return True

def get_encoding_info():
    """
    Retourne des informations détaillées sur la configuration d'encodage
    """
    return {
        'default_encoding': config.get('default_encoding', 'auto'),
        'pos58_encoding': config.get('pos58_encoding', 'ascii'),
        'standard_encoding': config.get('standard_encoding', 'cp1252'),
        'force_ascii_for_pos58': config.get('force_ascii_for_pos58', True),
        'smart_fallback': config.get('smart_fallback', True),
        'ascii_conversion_mode': config.get('ascii_conversion_mode', 'smart'),
        'available_encodings': ['auto', 'ascii', 'cp1252', 'cp850', 'latin1', 'cp437'],
        'recommended': {
            'POS-58': 'ascii',
            'Epson': 'cp1252',
            'Star': 'cp1252',
            'Generic': 'cp850'
        }
    }

def test_encoding_configuration():
    """
    Teste la configuration d'encodage avec différents cas
    """
    test_cases = [
        ('POS-58', 'Test POS-58'),
        ('POS58 Printer', 'Test POS58'),
        ('Epson TM-T88V', 'Test Epson'),
        ('Star TSP100', 'Test Star'),
        ('Generic Printer', 'Test Generic')
    ]
    
    print("🧪 TEST CONFIGURATION ENCODAGE")
    print("=" * 40)
    
    for printer_name, description in test_cases:
        encoding = get_optimal_encoding_for_printer(printer_name)
        print(f"{description:<15} → {encoding}")
    
    print(f"\nConfiguration actuelle:")
    info = get_encoding_info()
    for key, value in info.items():
        if key != 'available_encodings' and key != 'recommended':
            print(f"  {key}: {value}")

def log_system_encoding_info():
    """Log des informations système pour le débogage d'encodage"""
    if not config.get('debug_encoding', False):
        return
    
    logger.info("=== Informations encodage système ===")
    logger.info(f"Plateforme: {sys.platform}")
    logger.info(f"Encodage par défaut Python: {sys.getdefaultencoding()}")
    logger.info(f"Encodage système fichiers: {sys.getfilesystemencoding()}")
    
    if hasattr(sys.stdout, 'encoding'):
        logger.info(f"Encodage stdout: {sys.stdout.encoding}")
    
    logger.info("=== Configuration encodage application ===")
    info = get_encoding_info()
    for key, value in info.items():
        if key not in ['available_encodings', 'recommended']:
            logger.info(f"{key}: {value}")

# Initialisation au chargement du module
if __name__ != "__main__":
    try:
        log_system_encoding_info()
    except:
        pass