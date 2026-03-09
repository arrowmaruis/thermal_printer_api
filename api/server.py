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
from printer.printer_utils import get_printers, print_raw, print_smart, print_test, detect_printer_width, detect_printer_encoding
from printer.receipt import format_receipt

def create_static_content():
    """Crée les fichiers statiques nécessaires"""
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # Créer une page d'accueil simple - MISE À JOUR pour ASCII universel
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
        .ascii-highlight {
            background: linear-gradient(45deg, #6c5ce7, #a29bfe);
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border: 2px solid #6c5ce7;
        }
    </style>
</head>
<body>
    <div class="status">🟢 API Active - ASCII Universel</div>
    <h1>🖨️ API d'Impression Thermique</h1>
    <p>Cette API permet d'imprimer sur une imprimante thermique depuis une application web avec <strong>encodage ASCII universel</strong> et conversion française intelligente.</p>
    
    <div class="ascii-highlight">
        <h3>🎯 NOUVEAU: ASCII Universel</h3>
        <p><strong>Toutes les imprimantes</strong> utilisent maintenant l'encodage ASCII par défaut avec conversion française automatique.</p>
        <ul>
            <li>POS-58, Epson, Star, Generic → <strong>ASCII</strong></li>
            <li>Conversion optimisée: café → cafe, hôtel → hotel, €15,50 → EUR15,50</li>
            <li>Compatibilité maximale avec tous les modèles d'imprimantes</li>
        </ul>
    </div>
    
    <div class="feature">
        <h3>✨ Fonctionnalités</h3>
        <ul>
            <li><strong>ASCII universel</strong> : Même encodage pour toutes les imprimantes</li>
            <li><strong>Conversion française optimisée</strong> : café → cafe, hôtel → hotel, 15,50€ → 15,50 EUR</li>
            <li><strong>Fallback intelligent</strong> : Si l'encodage échoue, essaie automatiquement les alternatives</li>
            <li><strong>Support multi-formats</strong> : Reçus standard, hôtel, mixte</li>
            <li><strong>Auto-détection largeur</strong> : 58mm et 80mm détectés automatiquement</li>
        </ul>
    </div>
    
    <div class="endpoints">
        <h2>🔗 Endpoints disponibles</h2>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <span class="path">/health</span>
            <div class="description">Vérifie si l'API est en cours d'exécution et affiche la configuration ASCII</div>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <span class="path">/printers</span>
            <div class="description">Liste toutes les imprimantes avec largeur détectée et encodage ASCII universel</div>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <span class="path">/test-printer/{printer_id}</span>
            <div class="description">Imprime un test ASCII avec conversion française sur l'imprimante spécifiée</div>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <span class="path">/test-immediate-cut/{printer_id}</span>
            <div class="description">🆕 Teste la coupe immédiate (résout le problème de coupe décalée)</div>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span>
            <span class="path">/print</span>
            <div class="description">Imprime les données reçues avec encodage ASCII universel et conversion française</div>
        </div>
    </div>
    
    <div class="feature">
        <h3>🎯 Configuration d'encodage</h3>
        <p><strong>Par défaut :</strong> ASCII (universel) avec conversion française automatique</p>
        <p><strong>Disponibles :</strong> ascii (recommandé) - cp1252 - cp850 - cp437 - latin1</p>
        <p><strong>Spécifiez "encoding": "ascii"</strong> dans vos requêtes pour utiliser l'optimisation par défaut</p>
    </div>
    
    <div class="footer">
        <p><strong>API d'Impression Thermique v1.0.0</strong></p>
        <p>ASCII Universel • Conversion française optimisée • Compatibilité maximale</p>
    </div>
</body>
</html>
"""
    
    with open('static/index.html', 'w', encoding='utf-8') as f:
        f.write(html)

def validate_print_request(data):
    """Valide les données d'une requête d'impression. Retourne une liste d'erreurs (vide si OK)."""
    errors = []
    print_type = data.get('type', 'receipt')

    if print_type == 'receipt':
        receipt_data = data.get('data')
        if receipt_data is None:
            errors.append("Champ 'data' manquant")
            return errors
        if not isinstance(receipt_data, dict):
            errors.append("'data' doit être un objet JSON")
            return errors

        # ── Mode dynamique : valider les sections ──────────────────────────
        if 'sections' in receipt_data:
            sections = receipt_data['sections']
            if not isinstance(sections, list):
                errors.append("'data.sections' doit être une liste")
            else:
                valid_types = {'header', 'text', 'separator', 'keyvalue', 'table', 'feed', 'cut', 'logo'}
                for i, section in enumerate(sections):
                    if not isinstance(section, dict):
                        errors.append(f"Section {i}: doit être un objet JSON")
                        continue
                    sec_type = section.get('type')
                    if sec_type not in valid_types:
                        errors.append(f"Section {i}: type '{sec_type}' inconnu. Types valides: {sorted(valid_types)}")
                    if sec_type == 'table':
                        if 'columns' not in section:
                            errors.append(f"Section {i} (table): 'columns' manquant")
                        if 'rows' not in section:
                            errors.append(f"Section {i} (table): 'rows' manquant")
                    if sec_type == 'keyvalue' and 'rows' not in section:
                        errors.append(f"Section {i} (keyvalue): 'rows' manquant")
                    if sec_type == 'logo' and not section.get('image') and not section.get('path'):
                        errors.append(f"Section {i} (logo): champ 'image' (base64) ou 'path' requis")
            return errors

        # ── Mode classique : valider les items ─────────────────────────────
        items = receipt_data.get('items', [])
        if not isinstance(items, list):
            errors.append("'data.items' doit être une liste")
        else:
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(f"Item {i}: doit être un objet JSON")
                    continue
                if 'name' not in item:
                    errors.append(f"Item {i}: champ 'name' manquant")
                if 'price' not in item:
                    errors.append(f"Item {i}: champ 'price' manquant")
                elif not isinstance(item['price'], (int, float)):
                    errors.append(f"Item {i}: 'price' doit être un nombre")
                if 'quantity' not in item:
                    errors.append(f"Item {i}: champ 'quantity' manquant")
                elif not isinstance(item['quantity'], (int, float)):
                    errors.append(f"Item {i}: 'quantity' doit être un nombre")

    elif print_type == 'raw':
        if not data.get('text'):
            errors.append("Champ 'text' requis pour le type 'raw'")
    else:
        errors.append(f"Type '{print_type}' non supporté. Utiliser 'receipt' ou 'raw'")

    return errors


def create_app():
    """Crée et configure l'application Flask"""
    app = Flask(__name__, static_folder='static')

    # Configuration CORS depuis la config (ou valeurs par défaut)
    configured_origins = config.get('allowed_origins', [])
    origins = configured_origins if configured_origins else [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://hotelia.cloud"
    ]

    CORS(app, resources={r"/*": {"origins": origins}}, supports_credentials=True)

    # Vérification de la clé API sur toutes les routes sauf /health et /
    @app.before_request
    def check_api_key():
        api_key = config.get('api_key', '')
        if not api_key:
            return  # Pas de clé configurée = pas d'authentification
        if request.endpoint in ('index', 'health_check'):
            return  # Ces routes sont publiques
        request_key = request.headers.get('X-API-Key', '')
        if request_key != api_key:
            return jsonify({'status': 'error', 'message': 'Clé API invalide ou manquante'}), 401

    # Créer les fichiers statiques
    create_static_content()
    
    # Routes API
    @app.route('/')
    def index():
        """Page d'accueil"""
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/health')
    def health_check():
        """Vérifie si l'API est en cours d'exécution - MISE À JOUR ASCII"""
        return jsonify({
            'status': 'ok',
            'version': '1.0.0',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'default_printer': config.get('default_printer_name'),
            'default_printer_width': config.get('default_printer_width', '58mm'),
            'default_encoding': 'ascii',  # ASCII universel
            'universal_ascii': True,      # Nouveau flag
            'ascii_support': True,
            'french_conversion': True,    # Conversion française activée
            'all_printers_ascii': config.get('force_ascii_for_all', True),
            'smart_fallback': config.get('smart_fallback', True)
        })

    @app.route('/printers')
    def list_printers():
        """Liste les imprimantes disponibles avec encodage ASCII universel"""
        printers = get_printers()
        return jsonify({
            'status': 'success',
            'printers': printers,
            'default_printer_id': config.get('default_printer_id'),
            'default_printer_width': config.get('default_printer_width', '58mm'),
            'default_encoding': 'ascii',  # ASCII universel
            'count': len(printers),
            'encoding_info': {
                'universal_encoding': 'ascii',              # Nouvel encodage universel
                'pos58_encoding': 'ascii',                  # POS-58 → ASCII (inchangé)
                'standard_encoding': 'ascii',               # Autres imprimantes → ASCII (changé)
                'force_ascii_for_all': True,                # Nouveau flag
                'french_conversion': True,                  # Conversion française activée
                'description': 'ASCII universel avec conversion française automatique'
            }
        })

    @app.route('/test-printer/<int:printer_id>')
    def test_printer_endpoint(printer_id):
        """Imprime un test ASCII avec conversion française sur l'imprimante spécifiée"""
        printers = get_printers()
        
        if printer_id < 0 or printer_id >= len(printers):
            return jsonify({
                'status': 'error',
                'message': f"Imprimante avec ID {printer_id} non trouvée"
            }), 404
        
        printer_name = printers[printer_id]['name']
        # ASCII universel maintenant
        printer_width = printers[printer_id].get('width', detect_printer_width(printer_name))
        printer_encoding = 'ascii'  # ASCII pour toutes les imprimantes
        
        success = print_test(printer_name)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f"Test d'impression ASCII envoyé à {printer_name}",
                'printer_width': printer_width,
                'printer_encoding': printer_encoding,
                'universal_ascii': True,
                'french_conversion': True,
                'test_type': 'ascii_french_conversion'  # Nouveau type de test
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f"Échec du test d'impression sur {printer_name}"
            }), 500

    @app.route('/print', methods=['POST'])
    def print_endpoint():
        """Imprime les données reçues avec encodage ASCII universel"""
        try:
            data = request.json
            logger.info(f"Requête d'impression reçue, type: {data.get('type', 'inconnu')}")
            
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': "Aucune donnée reçue"
                }), 400

            # Validation des données
            validation_errors = validate_print_request(data)
            if validation_errors:
                return jsonify({
                    'status': 'error',
                    'message': "Données invalides",
                    'errors': validation_errors
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
            
            printer_info = printers[printer_id]
            printer_name = printer_info['name']
            conn_type = printer_info.get('connection_type', 'usb')

            # Récupérer ou détecter la largeur de l'imprimante
            printer_width = data.get('printer_width')
            if printer_width is None:
                printer_width = printer_info.get('width',
                                      config.get('default_printer_width', '58mm'))

            encoding = 'ascii'
            logger.info(f"Impression sur {printer_name} ({conn_type}), largeur: {printer_width}")

            # Type d'impression
            print_type = data.get('type', 'receipt')

            if print_type == 'receipt':
                receipt_data = data.get('data', {})
                receipt_type = data.get('receipt_type', 'standard')
                commands = format_receipt(
                    receipt_data,
                    receipt_type,
                    printer_width,
                    encoding,
                    printer_name
                )
                success = print_smart(printer_info, commands)

            elif print_type == 'raw':
                from printer.printer_utils import safe_encode_french
                encoded_text = safe_encode_french(data.get('text', ''), encoding, printer_name)
                success = print_smart(printer_info, encoded_text)

            else:
                return jsonify({
                    'status': 'error',
                    'message': f"Type d'impression '{print_type}' non pris en charge"
                }), 400

            if success:
                return jsonify({
                    'status': 'success',
                    'message': f"Donnees imprimees sur {printer_name}",
                    'printer_width': printer_width,
                    'encoding_used': encoding,
                    'connection_type': conn_type,
                    'universal_ascii': True,
                    'conversion_applied': True,
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
        """Teste tous les encodages sur une imprimante (endpoint de débogage) - MISE À JOUR ASCII"""
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
                'recommended_encoding': 'ascii',  # ASCII universel recommandé
                'universal_ascii': True,
                'note': 'ASCII est maintenant l\'encodage universel recommandé pour toutes les imprimantes'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"Erreur lors du test d'encodage: {str(e)}"
            }), 500

    @app.route('/encoding-info')
    def encoding_info_endpoint():
        """Nouvel endpoint: Informations sur la configuration d'encodage"""
        return jsonify({
            'status': 'success',
            'encoding_configuration': {
                'universal_encoding': 'ascii',
                'description': 'ASCII universel avec conversion française automatique',
                'benefits': [
                    'Compatibilité maximale avec toutes les imprimantes',
                    'Conversion française intelligente: café → cafe',
                    'Symboles monétaires: € → EUR',
                    'Ligatures: œ → oe, æ → ae',
                    'Pas de problèmes de double encodage'
                ],
                'conversion_examples': {
                    'café français': 'cafe francais',
                    'hôtel de luxe': 'hotel de luxe',
                    'réservation': 'reservation',
                    '15,50€': '15,50 EUR',
                    'crème brûlée': 'creme brulee'
                },
                'force_ascii_for_all': config.get('force_ascii_for_all', True),
                'allow_override': config.get('allow_encoding_override', True)
            }
        })

    # -----------------------------------------------------------------------
    # Endpoints Bluetooth
    # -----------------------------------------------------------------------

    @app.route('/bluetooth/ports')
    def bluetooth_ports():
        """Liste tous les ports COM disponibles (Bluetooth et serie)."""
        from printer.bluetooth_utils import get_all_com_ports
        ports = get_all_com_ports()
        bt_ports = [p for p in ports if p['is_bluetooth']]
        return jsonify({
            'status': 'success',
            'bluetooth_ports': bt_ports,
            'all_ports': ports,
            'count_bluetooth': len(bt_ports),
            'count_total': len(ports),
            'note': 'Appairez d\'abord l\'imprimante BT dans les parametres Windows'
        })

    @app.route('/bluetooth/discover')
    def bluetooth_discover():
        """
        Scanne les appareils Bluetooth a portee (necessite pybluez).
        Parametre optionnel: ?duration=8
        """
        from printer.bluetooth_utils import discover_bluetooth_devices
        duration = request.args.get('duration', 8, type=int)
        duration = max(3, min(duration, 30))  # entre 3 et 30 secondes
        result = discover_bluetooth_devices(duration=duration)
        if isinstance(result, dict) and 'error' in result:
            return jsonify({
                'status': 'error',
                'message': result['error'],
                'install': 'pip install pybluez'
            }), 503
        printers = [d for d in result if d.get('is_printer')]
        return jsonify({
            'status': 'success',
            'devices': result,
            'printers': printers,
            'count': len(result),
            'scan_duration': duration,
        })

    @app.route('/bluetooth/print', methods=['POST'])
    def bluetooth_print():
        """
        Imprime via Bluetooth (COM ou socket).

        Body JSON:
          {
            "connection": "com" | "socket",
            "port": "COM3",            // si connection=com
            "address": "AA:BB:CC:...", // si connection=socket
            "rfcomm_port": 1,          // optionnel, defaut 1
            "baudrate": 9600,          // optionnel, defaut 9600
            "type": "receipt" | "raw",
            "data": { ... },           // si type=receipt
            "text": "...",             // si type=raw
            "receipt_type": "standard",
            "printer_width": "58mm"
          }
        """
        from printer.bluetooth_utils import print_via_com_port, print_via_bluetooth_socket

        try:
            data = request.json
            if not data:
                return jsonify({'status': 'error', 'message': 'Aucune donnee recue'}), 400

            connection = data.get('connection', 'com').lower()
            print_type = data.get('type', 'receipt')
            printer_width = data.get('printer_width', config.get('default_printer_width', '58mm'))
            encoding = 'ascii'

            # Construire les bytes a imprimer
            if print_type == 'receipt':
                receipt_data = data.get('data', {})
                receipt_type = data.get('receipt_type', 'standard')
                raw_bytes = format_receipt(receipt_data, receipt_type, printer_width, encoding, None)
            elif print_type == 'raw':
                from printer.printer_utils import safe_encode_french
                raw_bytes = safe_encode_french(data.get('text', ''), encoding)
            else:
                return jsonify({'status': 'error',
                                'message': f"Type '{print_type}' non supporte"}), 400

            # Envoyer selon la methode de connexion
            if connection == 'com':
                port = data.get('port')
                if not port:
                    return jsonify({'status': 'error', 'message': "'port' requis pour connexion COM"}), 400
                baudrate = data.get('baudrate', 9600)
                success = print_via_com_port(port, raw_bytes, baudrate=baudrate)
                target = port
            elif connection == 'socket':
                address = data.get('address')
                if not address:
                    return jsonify({'status': 'error', 'message': "'address' requis pour connexion socket"}), 400
                rfcomm_port = data.get('rfcomm_port', 1)
                success = print_via_bluetooth_socket(address, raw_bytes, rfcomm_port=rfcomm_port)
                target = address
            else:
                return jsonify({'status': 'error',
                                'message': f"Connexion '{connection}' inconnue. Utilisez 'com' ou 'socket'"}), 400

            if success:
                return jsonify({
                    'status': 'success',
                    'message': f"Impression Bluetooth OK vers {target}",
                    'connection': connection,
                    'target': target,
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f"Echec impression Bluetooth vers {target}"
                }), 500

        except Exception as e:
            logger.error(f"Erreur impression Bluetooth: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/bluetooth/test-com/<path:port>')
    def bluetooth_test_com(port):
        """Test d'impression via port COM Bluetooth (ex: /bluetooth/test-com/COM3)."""
        from printer.bluetooth_utils import test_bluetooth_printer_com
        success = test_bluetooth_printer_com(port)
        if success:
            return jsonify({'status': 'success', 'message': f"Test BT COM OK sur {port}", 'port': port})
        return jsonify({'status': 'error', 'message': f"Echec test BT sur {port}"}), 500

    @app.route('/bluetooth/test-socket/<path:address>')
    def bluetooth_test_socket(address):
        """
        Test d'impression via socket Bluetooth (ex: /bluetooth/test-socket/AA:BB:CC:DD:EE:FF).
        Parametre optionnel: ?rfcomm_port=1
        """
        from printer.bluetooth_utils import test_bluetooth_printer_socket
        rfcomm_port = request.args.get('rfcomm_port', 1, type=int)
        success = test_bluetooth_printer_socket(address, rfcomm_port)
        if success:
            return jsonify({'status': 'success', 'message': f"Test BT socket OK vers {address}",
                            'address': address, 'rfcomm_port': rfcomm_port})
        return jsonify({'status': 'error', 'message': f"Echec test BT vers {address}"}), 500

    # -----------------------------------------------------------------------
    # Endpoints impression réseau (WiFi / Ethernet TCP/IP)
    # -----------------------------------------------------------------------

    @app.route('/network/test/<path:ip>')
    def network_test_endpoint(ip):
        """
        Test d'impression TCP direct sur une imprimante réseau (WiFi/Ethernet).
        Exemple: GET /network/test/192.168.10.104
        Parametre optionnel: ?port=9100
        """
        from printer.printer_utils import print_via_network, print_test
        tcp_port = request.args.get('port', 9100, type=int)
        printer_width = request.args.get('width', '58mm')
        printer_name_hint = f"network_{ip}"

        commands = bytearray()
        from printer.printer_utils import get_robust_init_command, get_robust_cut_command, safe_encode_french
        encoding = 'ascii'
        commands.extend(get_robust_init_command(printer_name_hint))
        commands.extend(safe_encode_french(f"=== TEST RESEAU ===\n", encoding))
        commands.extend(safe_encode_french(f"IP: {ip}:{tcp_port}\n", encoding))
        commands.extend(safe_encode_french(f"Cafe francais\n", encoding))
        commands.extend(safe_encode_french(f"Hotel de luxe\n", encoding))
        commands.extend(safe_encode_french(f"15,50 EUR\n", encoding))
        commands.extend(safe_encode_french(f"==================\n", encoding))
        commands.extend(get_robust_cut_command(printer_name_hint))

        success = print_via_network(ip, bytes(commands), tcp_port=tcp_port)
        if success:
            return jsonify({
                'status': 'success',
                'message': f"Test TCP envoye a {ip}:{tcp_port}",
                'ip': ip,
                'tcp_port': tcp_port,
            })
        return jsonify({
            'status': 'error',
            'message': f"Echec connexion TCP vers {ip}:{tcp_port}"
        }), 500

    @app.route('/network/print', methods=['POST'])
    def network_print_endpoint():
        """
        Impression directe via TCP/IP (WiFi/Ethernet).

        Body JSON:
          {
            "ip": "192.168.10.104",
            "port": 9100,           // optionnel, defaut 9100
            "type": "receipt" | "raw",
            "data": { ... },        // si type=receipt
            "text": "...",          // si type=raw
            "receipt_type": "standard",
            "printer_width": "58mm"
          }
        """
        from printer.printer_utils import print_via_network, safe_encode_french
        try:
            data = request.json
            if not data:
                return jsonify({'status': 'error', 'message': 'Aucune donnee recue'}), 400

            ip = data.get('ip')
            if not ip:
                return jsonify({'status': 'error', 'message': "'ip' requis"}), 400

            tcp_port = data.get('port', 9100)
            print_type = data.get('type', 'receipt')
            printer_width = data.get('printer_width', config.get('default_printer_width', '58mm'))
            encoding = 'ascii'

            if print_type == 'receipt':
                receipt_data = data.get('data', {})
                receipt_type = data.get('receipt_type', 'standard')
                raw_bytes = format_receipt(receipt_data, receipt_type, printer_width, encoding, f"network_{ip}")
            elif print_type == 'raw':
                raw_bytes = safe_encode_french(data.get('text', ''), encoding)
            else:
                return jsonify({'status': 'error', 'message': f"Type '{print_type}' non supporte"}), 400

            success = print_via_network(ip, raw_bytes, tcp_port=tcp_port)
            if success:
                return jsonify({
                    'status': 'success',
                    'message': f"Impression TCP OK vers {ip}:{tcp_port}",
                    'ip': ip,
                    'tcp_port': tcp_port,
                })
            return jsonify({
                'status': 'error',
                'message': f"Echec impression TCP vers {ip}:{tcp_port}"
            }), 500

        except Exception as e:
            logger.error(f"Erreur impression reseau: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    # -----------------------------------------------------------------------

    @app.route('/test-immediate-cut/<int:printer_id>')
    def test_immediate_cut_endpoint(printer_id):
        """Teste spécifiquement le problème de coupe décalée"""
        printers = get_printers()
        
        if printer_id < 0 or printer_id >= len(printers):
            return jsonify({
                'status': 'error',
                'message': f"Imprimante avec ID {printer_id} non trouvée"
            }), 404
        
        printer_name = printers[printer_id]['name']
        
        try:
            from printer.printer_utils import test_immediate_cut
            success = test_immediate_cut(printer_name)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': f"Test de coupe immédiate envoyé à {printer_name}",
                    'instructions': [
                        "Vérifiez que le reçu se coupe IMMÉDIATEMENT",
                        "Il ne doit PAS attendre un prochain job d'impression",
                        "Si le problème persiste, vérifiez les paramètres de l'imprimante"
                    ],
                    'test_type': 'immediate_cut_test',
                    'expected_behavior': 'Le reçu doit se couper automatiquement sans délai'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f"Échec du test de coupe immédiate sur {printer_name}"
                }), 500
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"Erreur lors du test de coupe immédiate: {str(e)}"
            }), 500
    
    return app

def run_api_server(app=None):
    """Démarre le serveur Flask"""
    if app is None:
        app = create_app()
    
    logger.info(f"Démarrage de l'API d'impression thermique sur {HOST}:{PORT}")
    print(f"🖨️  API d'impression thermique démarrée sur http://{HOST}:{PORT}")
    print(f"🎯 NOUVEAU: ASCII UNIVERSEL pour toutes les imprimantes")
    print(f"📋 Endpoints disponibles:")
    print(f"   • GET  /health : Vérifier le statut de l'API (ASCII universel)")
    print(f"   • GET  /printers : Lister les imprimantes avec encodage ASCII")
    print(f"   • GET  /test-printer/<id> : Test d'impression ASCII avec conversion française") 
    print(f"   • GET  /test-immediate-cut/<id> : 🆕 Test coupe immédiate (problème coupe décalée)")
    print(f"   • POST /print : Impression ASCII avec conversion française automatique")
    print(f"   • GET  /encoding-test/<id> : Test de tous les encodages (ASCII recommandé)")
    print(f"   • GET  /encoding-info : Informations sur la configuration ASCII")
    print(f"   • GET  /network/test/<ip> : 🆕 Test impression WiFi/Ethernet direct (TCP port 9100)")
    print(f"   • POST /network/print : 🆕 Impression WiFi/Ethernet direct (TCP)")
    print(f"")
    print(f"🎯 ASCII universel activé pour TOUTES les imprimantes")
    print(f"🔧 Conversion française automatique: café → cafe, hôtel → hotel, €15,50 → EUR15,50")
    print(f"✅ Compatibilité maximale avec tous les modèles d'imprimantes")
    
    app.run(host=HOST, port=config.get('port', PORT))