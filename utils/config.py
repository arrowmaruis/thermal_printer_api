#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Configuration
PORT = 5789
HOST = '0.0.0.0'  # Accessible depuis n'importe quelle machine du réseau
APP_NAME = "ImprimanteAPI"
VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Dossier de donnees partage — writable par tous les utilisateurs ET par
# le service LocalSystem. Evite les erreurs "Permission denied" quand le GUI
# est lance depuis un raccourci bureau sans droits administrateur.
# ---------------------------------------------------------------------------
_DATA_DIR = Path(os.environ.get('PROGRAMDATA', r'C:\ProgramData')) / 'ThermalPrinterAPI'
_DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = str(_DATA_DIR / "printer_config.json")
_LOG_DIR    = str(_DATA_DIR / "logs")

# Configuration globale optimisée pour ASCII par défaut
config = {
    "default_printer_id": None,
    "default_printer_name": None,
    "default_printer_width": "58mm",
    "autostart": True,
    "port": PORT,
    
    # Encodage principal - ASCII par défaut pour toutes les imprimantes
    "default_encoding": "ascii",              # ASCII par défaut au lieu de 'auto'
    
    # Encodages spécifiques par type d'imprimante - tout en ASCII
    "pos58_encoding": "ascii",                # POS-58 → ASCII (inchangé)
    "standard_encoding": "ascii",             # Autres imprimantes → ASCII (changé de cp1252)
    
    # Configuration avancée
    "force_ascii_for_all": True,              # Force ASCII pour TOUTES les imprimantes
    "force_ascii_for_pos58": True,            # Garde l'option POS-58 pour compatibilité
    "allow_encoding_override": True,          # Permet de forcer un encodage via l'interface
    "smart_fallback": True,                   # Active le fallback intelligent
    
    # Pages de codes et fallbacks - ASCII en priorité
    "printer_codepage": "WPC1252",
    "fallback_encodings": [
        "ascii",           # ASCII en premier (priorité absolue)
        "cp1252",          # Windows-1252 (comme Word) - fallback
        "cp850",           # Europe occidentale - fallback
        "latin1",          # ISO 8859-1 - fallback
        "cp437"            # DOS basique - fallback
    ],
    
    # Options de conversion ASCII
    "ascii_conversion_mode": "smart",         # 'smart', 'basic', 'aggressive'
    "preserve_euro_symbol": True,             # € → EUR
    "preserve_ligatures": True,               # œ → oe, æ → ae
    
    # Devise et format des montants
    "currency": "FCFA",                       # Symbole de devise affiché sur les tickets
    "currency_decimals": 0,                   # 0 pour FCFA, 2 pour EUR/USD

    # Sécurité API
    "api_key": "",                            # Clé API requise (vide = pas d'authentification)
    "allowed_origins": [],                    # Origines CORS autorisées (vide = valeurs par défaut)

    # Logging et débogage
    "log_encoding_decisions": True,           # Log les décisions d'encodage
    "debug_encoding": False                   # Mode debug pour l'encodage
}

def _resolve_log_dir():
    """
    Retourne un dossier de logs accessible en ecriture.
    Priorite : ProgramData → LocalAppData → dossier temporaire.
    """
    candidates = [
        _LOG_DIR,
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'ThermalPrinterAPI', 'logs'),
        os.path.join(os.environ.get('TEMP', ''), 'ThermalPrinterAPI', 'logs'),
    ]
    for d in candidates:
        if not d:
            continue
        try:
            os.makedirs(d, exist_ok=True)
            # Verifier que l'ecriture est possible
            test = os.path.join(d, '.write_test')
            with open(test, 'w') as f:
                f.write('')
            os.unlink(test)
            return d
        except PermissionError:
            continue
    return None  # En dernier recours : log console uniquement


def setup_logging():
    """Configure le systeme de journalisation avec support UTF-8."""
    handlers = []

    # StreamHandler (console) — toujours present sauf si stdout n'existe pas
    try:
        handlers.append(logging.StreamHandler(sys.stdout))
    except Exception:
        pass

    # FileHandler — dans le premier dossier accessible en ecriture
    log_dir = _resolve_log_dir()
    if log_dir:
        log_file = os.path.join(log_dir, f'imprimante_api_{datetime.now().strftime("%Y%m%d")}.log')
        try:
            handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
        except Exception:
            pass

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers or [logging.NullHandler()],
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
    """Migre les anciennes configurations vers le nouveau format ASCII par défaut"""
    global config
    
    # Migration 1: Tout encodage vers ASCII par défaut
    if config.get('default_encoding') in ['utf-8', 'cp1252', 'cp850', 'auto']:
        config['default_encoding'] = 'ascii'
        logger.info(f"Migration: default_encoding → ascii")
    
    if config.get('standard_encoding') in ['cp1252', 'cp850', 'utf-8']:
        config['standard_encoding'] = 'ascii'
        logger.info(f"Migration: standard_encoding → ascii")
    
    # Migration 2: Ajouter les nouvelles propriétés si manquantes
    new_properties = {
        'pos58_encoding': 'ascii',
        'standard_encoding': 'ascii',          # ASCII au lieu de cp1252
        'force_ascii_for_all': True,           # Nouvelle option
        'force_ascii_for_pos58': True,
        'allow_encoding_override': True,
        'smart_fallback': True,
        'ascii_conversion_mode': 'smart',
        'preserve_euro_symbol': True,
        'preserve_ligatures': True,
        'log_encoding_decisions': True,
        'debug_encoding': False,
        'currency': 'FCFA',
        'currency_decimals': 0,
        'api_key': '',
        'allowed_origins': [],
    }
    
    for prop, default_value in new_properties.items():
        if prop not in config:
            config[prop] = default_value
            logger.info(f"Propriété ajoutée: {prop} = {default_value}")

def validate_config():
    """Valide la configuration et corrige les valeurs invalides"""
    global config
    
    # Validation des encodages - ASCII par défaut
    valid_encodings = ['ascii', 'cp1252', 'cp850', 'latin1', 'cp437', 'utf-8']
    
    # Forcer ASCII si autre chose est configuré et force_ascii_for_all est activé
    if config.get('force_ascii_for_all', True):
        if config.get('default_encoding') != 'ascii':
            logger.info(f"Force ASCII: default_encoding {config.get('default_encoding')} → ascii")
            config['default_encoding'] = 'ascii'
        
        if config.get('standard_encoding') != 'ascii':
            logger.info(f"Force ASCII: standard_encoding {config.get('standard_encoding')} → ascii")
            config['standard_encoding'] = 'ascii'
            
        if config.get('pos58_encoding') != 'ascii':
            logger.info(f"Force ASCII: pos58_encoding {config.get('pos58_encoding')} → ascii")
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
    MAINTENANT: ASCII par défaut pour TOUTES les imprimantes
    """
    if not printer_name:
        return 'ascii'  # ASCII par défaut au lieu de cp1252
    
    # Si force_ascii_for_all est activé, toujours retourner ASCII
    if config.get('force_ascii_for_all', True):
        if config.get('log_encoding_decisions', True):
            logger.info(f"Force ASCII pour toutes imprimantes: {printer_name} → ascii")
        return 'ascii'
    
    # Logique de fallback si force_ascii_for_all est désactivé
    # (mais par défaut maintenant c'est ASCII partout)
    default_encoding = config.get('default_encoding', 'ascii')
    
    if config.get('log_encoding_decisions', True):
        logger.info(f"Encodage pour {printer_name}: {default_encoding}")
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
    valid_encodings = ['ascii', 'cp1252', 'cp850', 'latin1', 'cp437', 'utf-8']
    if encoding not in valid_encodings:
        logger.error(f"Encodage invalide: {encoding}")
        return False
    
    # Si force_ascii_for_all est activé, avertir mais permettre le changement
    if config.get('force_ascii_for_all', True) and encoding != 'ascii':
        logger.warning(f"Attention: Changement d'encodage de ASCII vers {encoding} pour {printer_name}")
    
    # Mise à jour de la configuration
    config['default_encoding'] = encoding
    logger.info(f"Encodage modifié pour {printer_name}: {encoding}")
    
    save_config()
    return True

def get_encoding_info():
    """
    Retourne des informations détaillées sur la configuration d'encodage
    """
    return {
        'default_encoding': config.get('default_encoding', 'ascii'),
        'pos58_encoding': config.get('pos58_encoding', 'ascii'),
        'standard_encoding': config.get('standard_encoding', 'ascii'),
        'force_ascii_for_all': config.get('force_ascii_for_all', True),
        'force_ascii_for_pos58': config.get('force_ascii_for_pos58', True),
        'smart_fallback': config.get('smart_fallback', True),
        'ascii_conversion_mode': config.get('ascii_conversion_mode', 'smart'),
        'available_encodings': ['ascii', 'cp1252', 'cp850', 'latin1', 'cp437'],
        'recommended': {
            'ALL': 'ascii',      # Maintenant ASCII pour tout
            'POS-58': 'ascii',
            'Epson': 'ascii',    # Changé de cp1252
            'Star': 'ascii',     # Changé de cp1252
            'Generic': 'ascii'   # Changé de cp850
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
    
    print("🧪 TEST CONFIGURATION ENCODAGE ASCII PAR DÉFAUT")
    print("=" * 50)
    
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
    
    logger.info("=== Informations encodage système - ASCII par défaut ===")
    logger.info(f"Plateforme: {sys.platform}")
    logger.info(f"Encodage par défaut Python: {sys.getdefaultencoding()}")
    logger.info(f"Encodage système fichiers: {sys.getfilesystemencoding()}")
    
    if hasattr(sys.stdout, 'encoding'):
        logger.info(f"Encodage stdout: {sys.stdout.encoding}")
    
    logger.info("=== Configuration encodage application - ASCII UNIVERSEL ===")
    info = get_encoding_info()
    for key, value in info.items():
        if key not in ['available_encodings', 'recommended']:
            logger.info(f"{key}: {value}")

# Initialisation au chargement du module
if __name__ != "__main__":
    try:
        log_system_encoding_info()
        logger.info("Configuration chargée avec encodage ASCII par défaut pour toutes les imprimantes")
    except:
        pass