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
from printer.printer_utils import get_printers, print_raw, print_test, detect_printer_width, detect_printer_encoding
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
            background: #1a1a2e;
            color: #ffffff;
        }
        h1 {
            color: #6c5ce7;
            border-bottom: 1px solid #6c5ce7;
            padding-bottom: 10px;
        }
        .endpoints {
            background-color: #252541;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .endpoint {
            margin-bottom: 15px;
        }
        .method {
            display: inline-block;
            padding: 3px 8px;
            background-color: #6c5ce7;
            color: white;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 10px;
            font-weight: bold;
        }
        .method.get { background-color: #00b894; }
        .method.post { background-color: #6c5ce7; }
        .path {
            font-family: 'Courier New', monospace;
            font-weight: bold;
            color: #a29bfe;
        }
        .description {
            margin-top: 5px;
            padding-left: 60px;
            color: #a0a0a0;
        }
        .footer {
            margin-top: 40px;
            color: #666;
            font-size: 14px;
            text-align: center;
            border-top: 1px solid #444;
            padding-top: 20px;
        }
        .feature {
            background: #2f2f50;
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
            border-left: 4px solid #6c5ce7;
        }
        .status {
            background: #00b894;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            display: inline-block;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="status">🟢 API Active</div>
    <h1>🖨️ API d'Impression Thermique</h1>
    <p>Cette API permet d'imprimer sur une imprimante thermique depuis une application web avec support ASCII intelligent pour les imprimantes POS-58.</p>
    
    <div class="feature">
        <h3>✨ Fonctionnalités</h3>
        <ul>
            <li><strong>Auto-détection intelligente</strong> : POS-58 → ASCII, autres → cp1252</li>
            <li><strong>Conversion française optimisée</strong> : café → cafe, hôtel → hotel, 15,50€ → 15,50 EUR</li>
            <li><strong>Fallback intelligent</strong> : Si l'encodage échoue, essaie automatiquement les alternatives</li>
            <li><strong>Support multi-formats</strong> : Reçus standard, hôtel, mixte</li>
        </ul>
    </div>
    
    <div class="endpoints">
        <h2>🔗 Endpoints disponibles</h2>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <span class="path">/health</span>
            <div class="description">Vérifie si l'API est en cours d'exécution et affiche la configuration</div>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <span class="path">/printers</span>
            <div class="description">Liste toutes les imprimantes avec largeur et encodage détectés automatiquement</div>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <span class="path">/test-printer/{printer_id}</span>
            <div class="description">Imprime un test sur l'imprimante spécifiée avec test d'encodage adapté</div>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span>
            <span class="path">/print</span>
            <div class="description">Imprime les données reçues avec auto-détection d'encodage optimal</div>
        </div>
    </div>
    
    <div class="feature">
        <h3>🎯 Encodages supportés</h3>
        <p><strong>auto</strong> (recommandé) - <strong>ascii</strong> - <strong>cp1252</strong> - <strong>cp850</strong> - <strong>cp437</strong> - <strong>latin1</strong></p>
    </div>
    
    <div class="footer">
        <p><strong>API d'Impression Thermique v1.0.0</strong></p>
        <p>Support ASCII intelligent • Conversion française optimisée • Auto-détection POS-58</p>
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
            'default_encoding': config.get('default_encoding', 'auto'),
            'ascii_support': True,
            'pos58_auto_detection': config.get('force_ascii_for_pos58', True),
            'smart_fallback': config.get('smart_fallback', True)
        })

    @app.route('/printers')
    def list_printers():
        """Liste les imprimantes disponibles avec détection automatique"""
        printers = get_printers()
        return jsonify({
            'status': 'success',
            'printers': printers,
            'default_printer_id': config.get('default_printer_id'),
            'default_printer_width': config.get('default_printer_width', '58mm'),
            'default_encoding': config.get('default_encoding', 'auto'),
            'count': len(printers),
            'encoding_info': {
                'pos58_encoding': config.get('pos58_encoding', 'ascii'),
                'standard_encoding': config.get('standard_encoding', 'cp1252'),
                'force_ascii_for_pos58': config.get('force_ascii_for_pos58', True)
            }
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
        # Détection automatique de la largeur et encodage
        printer_width = printers[printer_id].get('width', detect_printer_width(printer_name))
        printer_encoding = printers[printer_id].get('encoding', detect_printer_encoding(printer_name))
        
        success = print_test(printer_name)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f"Test d'impression envoyé à {printer_name}",
                'printer_width': printer_width,
                'printer_encoding': printer_encoding,
                'test_type': 'ascii_conversion' if printer_encoding == 'ascii' else 'unicode_support'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f"Échec du test d'impression sur {printer_name}"
            }), 500

    @app.route('/print', methods=['POST'])
    def print_endpoint():
        """Imprime les données reçues avec auto-détection d'encodage optimal"""
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
            
            # Récupérer l'encodage souhaité avec auto-détection intelligente
            encoding = data.get('encoding')
            if encoding is None:
                # Auto-détection basée sur le type d'imprimante
                detected_encoding = printers[printer_id].get('encoding')
                if detected_encoding:
                    encoding = detected_encoding
                else:
                    # Fallback sur la configuration
                    encoding = config.get('default_encoding', 'auto')
            
            # Type d'impression
            print_type = data.get('type', 'receipt')
            
            if print_type == 'receipt':
                # Impression d'un reçu formaté avec paramètres supplémentaires
                receipt_data = data.get('data', {})
                receipt_type = data.get('receipt_type', 'standard')  # Types: standard, hotel, mixed
                
                logger.info(f"Formatage d'un reçu de type {receipt_type}")
                logger.info(f"Imprimante: {printer_name}, largeur: {printer_width}, encodage: {encoding}")
                
                # Passer le nom de l'imprimante pour l'auto-détection d'encodage
                commands = format_receipt(
                    receipt_data, 
                    receipt_type, 
                    printer_width, 
                    encoding,
                    printer_name  # ← Ajout important pour l'auto-détection
                )
                success = print_raw(printer_name, commands)
                
            elif print_type == 'raw':
                # Impression de texte brut avec encodage intelligent
                raw_text = data.get('text', '')
                
                # Utiliser la fonction d'encodage intelligent
                from printer.printer_utils import safe_encode_french
                encoded_text = safe_encode_french(raw_text, encoding, printer_name)
                
                success = print_raw(printer_name, encoded_text)
                
            else:
                return jsonify({
                    'status': 'error',
                    'message': f"Type d'impression '{print_type}' non pris en charge"
                }), 400
            
            if success:
                # Récupérer l'encodage réellement utilisé pour le retour
                final_encoding = encoding
                if encoding == 'auto':
                    final_encoding = detect_printer_encoding(printer_name)
                
                return jsonify({
                    'status': 'success',
                    'message': f"Données imprimées sur {printer_name}",
                    'printer_width': printer_width,
                    'encoding_used': final_encoding,
                    'ascii_conversion': final_encoding == 'ascii',
                    'printer_type': 'POS-58' if 'pos-58' in printer_name.lower() or 'pos58' in printer_name.lower() else 'Standard'
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

    @app.route('/encoding-test/<int:printer_id>')
    def encoding_test_endpoint(printer_id):
        """Teste tous les encodages sur une imprimante (endpoint de débogage)"""
        printers = get_printers()
        
        if printer_id < 0 or printer_id >= len(printers):
            return jsonify({
                'status': 'error',
                'message': f"Imprimante avec ID {printer_id} non trouvée"
            }), 404
        
        printer_name = printers[printer_id]['name']
        
        try:
            from printer.printer_utils import test_all_encodings_on_printer
            results = test_all_encodings_on_printer(printer_name)
            
            return jsonify({
                'status': 'success',
                'printer_name': printer_name,
                'encoding_test_results': results,
                'recommended_encoding': detect_printer_encoding(printer_name)
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"Erreur lors du test d'encodage: {str(e)}"
            }), 500
    
    return app

def run_api_server(app=None):
    """Démarre le serveur Flask"""
    if app is None:
        app = create_app()
    
    logger.info(f"Démarrage de l'API d'impression thermique sur {HOST}:{PORT}")
    print(f"🖨️  API d'impression thermique démarrée sur http://{HOST}:{PORT}")
    print(f"📋 Endpoints disponibles:")
    print(f"   • GET  /health : Vérifier le statut de l'API")
    print(f"   • GET  /printers : Lister les imprimantes avec auto-détection")
    print(f"   • GET  /test-printer/<id> : Test d'impression avec encodage adapté") 
    print(f"   • POST /print : Impression avec auto-détection ASCII/Unicode")
    print(f"   • GET  /encoding-test/<id> : Test de tous les encodages (debug)")
    print(f"")
    print(f"🎯 Support ASCII intelligent activé pour les imprimantes POS-58")
    print(f"🔧 Conversion française automatique: café → cafe, hôtel → hotel")
    
    app.run(host=HOST, port=config.get('port', PORT))