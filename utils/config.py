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

# Configuration globale
config = {
    "default_printer_id": None,
    "default_printer_name": None,
    "default_printer_width": "58mm",  # Nouvelle propriété pour le type d'imprimante
    "autostart": True,
    "port": PORT,
    "default_encoding": "CP437"       # Utiliser UTF-8 par défaut pour une meilleure compatibilité
}

def setup_logging():
    """Configure le système de journalisation"""
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_file = f'logs/imprimante_api_{datetime.now().strftime("%Y%m%d")}.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(APP_NAME)

# Initialisation du logger
logger = setup_logging()

def load_config():
    """Charge la configuration depuis le fichier"""
    global config
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                loaded_config = json.load(f)
                config.update(loaded_config)
                logger.info(f"Configuration chargée: {config}")
                
                # S'assurer que les nouvelles propriétés existent dans la configuration
                if "default_printer_width" not in config:
                    config["default_printer_width"] = "58mm"
                    logger.info("Propriété 'default_printer_width' ajoutée avec valeur par défaut: 58mm")
                
                if "default_encoding" not in config:
                    config["default_encoding"] = "utf-8"
                    logger.info("Propriété 'default_encoding' ajoutée avec valeur par défaut: utf-8")
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {e}")

def save_config():
    """Sauvegarde la configuration dans le fichier"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info(f"Configuration sauvegardée: {config}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")