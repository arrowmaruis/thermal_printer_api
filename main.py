#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API pour Impression Thermique avec Interface de Configuration
------------------------------------------------------------
Expose une API pour l'impression thermique depuis une application web,
avec une interface graphique pour configurer l'imprimante par défaut.

Commandes:
- Lancement normal (API + GUI): python main.py
- Lancement API uniquement: python main.py --no-gui
- Spécifier un port différent: python main.py --port 8080
"""

import os
import sys
import argparse
import threading

# Ajouter le répertoire parent au path pour les imports entre modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from utils.config import load_config, save_config, config, logger
from api.server import create_app, run_api_server
from gui.config_app import launch_config_gui

def main():
    """Point d'entrée principal de l'application"""
    # Parser les arguments de ligne de commande
    parser = argparse.ArgumentParser(description="API d'impression thermique")
    parser.add_argument('--no-gui', action='store_true', help="Lancer uniquement l'API sans interface graphique")
    parser.add_argument('--port', type=int, help="Port pour l'API (par défaut: 5789)")
    args = parser.parse_args()
    
    # Charger la configuration
    load_config()
    
    # Mettre à jour le port si spécifié
    if args.port:
        config['port'] = args.port
        save_config()
    
    # Créer l'application Flask
    app = create_app()  # La configuration CORS est maintenant dans create_app()
    
    # Démarrer le serveur Flask dans un thread séparé
    server_thread = threading.Thread(target=run_api_server, args=(app,), daemon=True)
    server_thread.start()
    
    # Lancer l'interface graphique si demandé
    if not args.no_gui:
        launch_config_gui()
    else:
        # Garder le thread principal actif en mode sans GUI
        try:
            import time
            print(f"API d'impression thermique démarrée sur http://localhost:{config.get('port', 5789)}")
            print("Appuyez sur Ctrl+C pour arrêter le serveur")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Arrêt du serveur")
            print("Serveur arrêté")
            sys.exit(0)

if __name__ == "__main__":
    main()