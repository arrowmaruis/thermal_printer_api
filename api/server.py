#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Ajouter le répertoire parent au path pour les imports entre modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.config import logger, config, HOST, PORT
from printer.printer_utils import get_printers, print_raw, print_test, detect_printer_width
from printer.receipt import format_receipt

def create_static_content():
    """Crée les fichiers statiques nécessaires"""
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # Créer une page d'accueil simple
    html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API d'Impression Thermique</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #333;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }
        .endpoints {
            background-color: #f5f5f5;
            padding: 20px;
            border-radius: 5px;
        }
        .endpoint {
            margin-bottom: 15px;
        }
        .method {
            display: inline-block;
            padding: 3px 6px;
            background-color: #4CAF50;
            color: white;
            border-radius: 3px;
            font-size: 14px;
            margin-right: 10px;
        }
        .path {
            font-family: monospace;
            font-weight: bold;
        }
        .description {
            margin-top: 5px;
            padding-left: 60px;
        }
        .footer {
            margin-top: 40px;
            color: #666;
            font-size: 14px;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>API d'Impression Thermique</h1>
    <p>Cette API permet d'imprimer sur une imprimante thermique depuis une application web.</p>
    
    <div class="endpoints">
        <h2>Endpoints disponibles</h2>
        
        <div class="endpoint">
            <span class="method">GET</span>
            <span class="path">/health</span>
            <div class="description">Vérifie si l'API est en cours d'exécution</div>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span>
            <span class="path">/printers</span>
            <div class="description">Liste toutes les imprimantes disponibles</div>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span>
            <span class="path">/test-printer/{printer_id}</span>
            <div class="description">Imprime un test sur l'imprimante spécifiée</div>
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span>
            <span class="path">/print</span>
            <div class="description">Imprime les données reçues sur l'imprimante par défaut ou spécifiée</div>
        </div>
    </div>
    
    <div class="footer">
        <p>API d'Impression Thermique v1.0.0</p>
        <p>Pour configurer l'imprimante par défaut, utilisez l'interface de configuration.</p>
    </div>
</body>
</html>
"""
    
    with open('static/index.html', 'w', encoding='utf-8') as f:
        f.write(html)

def create_app():
    """Crée et configure l'application Flask"""
    app = Flask(__name__, static_folder='static')
    
    # Configuration CORS avec liste d'origines spécifiques
    origins = [
        "http://localhost:8000",     # Laravel local (ajustez le port si nécessaire)
        "http://127.0.0.1:8000",     # Alternative pour Laravel local
        "https://hotelia.cloud"      # Votre site Laravel en ligne (remplacez par l'URL réelle)
    ]
    
    CORS(app, resources={r"/*": {"origins": origins}}, supports_credentials=True)
    
    # Créer les fichiers statiques
    create_static_content()
    
    # Routes API
    @app.route('/')
    def index():
        """Page d'accueil"""
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/health')
    def health_check():
        """Vérifie si l'API est en cours d'exécution"""
        return jsonify({
            'status': 'ok',
            'version': '1.0.0',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'default_printer': config.get('default_printer_name'),
            'default_printer_width': config.get('default_printer_width', '58mm'),
            'default_encoding': config.get('default_encoding', 'utf-8')
        })

    @app.route('/printers')
    def list_printers():
        """Liste les imprimantes disponibles"""
        printers = get_printers()
        return jsonify({
            'status': 'success',
            'printers': printers,
            'default_printer_id': config.get('default_printer_id'),
            'default_printer_width': config.get('default_printer_width', '58mm'),
            'default_encoding': config.get('default_encoding', 'utf-8'),
            'count': len(printers)
        })

    @app.route('/test-printer/<int:printer_id>')
    def test_printer_endpoint(printer_id):
        """Imprime un test sur l'imprimante spécifiée"""
        printers = get_printers()
        
        if printer_id < 0 or printer_id >= len(printers):
            return jsonify({
                'status': 'error',
                'message': f"Imprimante avec ID {printer_id} non trouvée"
            }), 404
        
        printer_name = printers[printer_id]['name']
        # Détection automatique de la largeur d'imprimante si non déjà détectée
        printer_width = printers[printer_id].get('width', detect_printer_width(printer_name))
        
        success = print_test(printer_name)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f"Test d'impression envoyé à {printer_name}",
                'printer_width': printer_width
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f"Échec du test d'impression sur {printer_name}"
            }), 500

    @app.route('/print', methods=['POST'])
    def print_endpoint():
        """Imprime les données reçues sur l'imprimante par défaut ou spécifiée"""
        try:
            data = request.json
            logger.info(f"Requête d'impression reçue, type: {data.get('type', 'inconnu')}")
            
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': "Aucune donnée reçue"
                }), 400
            
            # Utiliser l'imprimante spécifiée ou l'imprimante par défaut
            printer_id = data.get('printer_id', config.get('default_printer_id'))
            
            if printer_id is None:
                return jsonify({
                    'status': 'error',
                    'message': "Aucune imprimante par défaut configurée et aucun ID d'imprimante spécifié"
                }), 400
            
            printers = get_printers()
            
            if printer_id < 0 or printer_id >= len(printers):
                return jsonify({
                    'status': 'error',
                    'message': f"Imprimante avec ID {printer_id} non trouvée"
                }), 404
            
            printer_name = printers[printer_id]['name']
            
            # Récupérer ou détecter la largeur de l'imprimante
            printer_width = data.get('printer_width')
            if printer_width is None:
                printer_width = printers[printer_id].get('width', 
                                      config.get('default_printer_width', '58mm'))
            
            # Récupérer l'encodage souhaité
            encoding = data.get('encoding')
            if encoding is None:
                encoding = config.get('default_encoding', 'utf-8')
            
            # Type d'impression
            print_type = data.get('type', 'receipt')
            
            if print_type == 'receipt':
                # Impression d'un reçu formaté avec paramètres supplémentaires
                receipt_data = data.get('data', {})
                receipt_type = data.get('receipt_type', 'standard')  # Types: standard, hotel, mixed
                
                logger.info(f"Formatage d'un reçu de type {receipt_type}, largeur: {printer_width}, encodage: {encoding}")
                commands = format_receipt(receipt_data, receipt_type, printer_width, encoding)
                success = print_raw(printer_name, commands)
            elif print_type == 'raw':
                # Impression de texte brut avec encodage spécifié
                raw_text = data.get('text', '')
                try:
                    # Essayer d'encoder avec l'encodage demandé
                    encoded_text = raw_text.encode(encoding, errors='replace')
                except LookupError:
                    # Si l'encodage n'est pas reconnu, utiliser utf-8
                    logger.warning(f"Encodage {encoding} non reconnu, utilisation de utf-8")
                    encoded_text = raw_text.encode('utf-8', errors='replace')
                
                success = print_raw(printer_name, encoded_text)
            else:
                return jsonify({
                    'status': 'error',
                    'message': f"Type d'impression '{print_type}' non pris en charge"
                }), 400
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': f"Données imprimées sur {printer_name}",
                    'printer_width': printer_width,
                    'encoding': encoding
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f"Échec de l'impression sur {printer_name}"
                }), 500
                
        except Exception as e:
            logger.error(f"Erreur lors de l'impression: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    return app

def run_api_server(app=None):
    """Démarre le serveur Flask"""
    if app is None:
        app = create_app()
    
    logger.info(f"Démarrage de l'API d'impression thermique sur {HOST}:{PORT}")
    print(f"API d'impression thermique démarrée sur http://{HOST}:{PORT}")
    print(f"Utilisez les endpoints suivants:")
    print(f"- GET /health : Vérifier si le serveur est en cours d'exécution")
    print(f"- GET /printers : Lister toutes les imprimantes disponibles")
    print(f"- GET /test-printer/<printer_id> : Imprimer un test sur l'imprimante choisie")
    print(f"- POST /print : Imprimer les données reçues")
    
    app.run(host=HOST, port=config.get('port', PORT))