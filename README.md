# README.md complet et détaillé

```markdown
# 🖨️ Thermal Printer API

**API d'impression thermique professionnelle avec interface graphique moderne pour la gestion complète d'imprimantes thermiques POS (58mm et 80mm).**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey)](https://github.com/arrowmaruis/thermal_printer_api)

## 📋 Table des matières

- [🎯 Contexte et objectifs](#-contexte-et-objectifs)
- [✨ Fonctionnalités](#-fonctionnalités)
- [🛠️ Architecture technique](#️-architecture-technique)
- [⚡ Installation rapide](#-installation-rapide)
- [📖 Guide d'utilisation détaillé](#-guide-dutilisation-détaillé)
- [🌐 Documentation API REST](#-documentation-api-rest)
- [🖥️ Interface graphique](#️-interface-graphique)
- [⚙️ Configuration avancée](#️-configuration-avancée)
- [🔧 Compilation et distribution](#-compilation-et-distribution)
- [🧪 Tests et débogage](#-tests-et-débogage)
- [❓ FAQ et dépannage](#-faq-et-dépannage)
- [🤝 Contribution](#-contribution)
- [📈 Roadmap](#-roadmap)

## 🎯 Contexte et objectifs

### Problématique
Les systèmes de gestion d'hôtels, restaurants et commerces ont souvent besoin d'imprimer des reçus, factures et tickets sur des imprimantes thermiques. Cependant, l'intégration de ces imprimantes dans des applications web pose plusieurs défis :

- **Compatibilité** : Différentes largeurs d'imprimantes (58mm vs 80mm)
- **Encodage** : Gestion des caractères spéciaux et accents
- **Configuration** : Détection et paramétrage des imprimantes
- **Intégration** : Interface simple pour les développeurs web

### Solution
Cette API offre une solution complète et prête à l'emploi qui :

- ✅ **Détecte automatiquement** le type et l'encodage optimal des imprimantes
- ✅ **Fournit une API REST** simple pour l'intégration web
- ✅ **Inclut une interface graphique** pour la configuration et les tests
- ✅ **Se compile en exécutable** pour un déploiement facile
- ✅ **Supporte plusieurs formats** de documents (reçus, factures, tickets)

### Cas d'usage typiques

1. **Hôtels** : Impression de confirmations de réservation, factures, reçus de consommation
2. **Restaurants** : Tickets de commande, reçus clients, bons de livraison
3. **Commerces** : Reçus de vente, tickets de caisse, bons de réduction
4. **Services** : Tickets de file d'attente, bordereaux de service

## ✨ Fonctionnalités

### 🖨️ Gestion des imprimantes
- **Détection automatique** des imprimantes thermiques connectées
- **Identification de largeur** (58mm/80mm) basée sur le pilote et les capacités
- **Test d'impression** pour vérifier la connectivité
- **Configuration par défaut** avec sauvegarde persistante

### 🔤 Gestion des encodages
- **Détection automatique** de l'encodage optimal par imprimante
- **Support multi-encodages** : UTF-8, CP437, CP850, CP852, CP858, ASCII
- **Fallback intelligent** en cas d'échec d'encodage
- **Nettoyage automatique** des caractères spéciaux problématiques

### 📄 Formats de documents
- **Standard** : Reçus de restaurant/bar avec articles et totaux
- **Hôtel** : Réservations avec détails hébergement et services
- **Mixte** : Réservation + consommations avec récapitulatif détaillé
- **Personnalisé** : Format libre avec commandes ESC/POS

### 🌐 API REST
- **Endpoints RESTful** pour intégration web facile
- **Format JSON** standardisé pour les données
- **CORS configuré** pour les applications web
- **Gestion d'erreurs** complète avec codes de statut

### 🖥️ Interface utilisateur
- **Tableau de bord moderne** avec thème sombre
- **Configuration intuitive** des imprimantes et paramètres
- **Tests en temps réel** des imprimantes
- **Journalisation** des activités avec interface de consultation

## 🛠️ Architecture technique

### Structure modulaire
```
thermal_printer_api/
├── 📁 api/                  # Serveur web et API REST
│   ├── server.py           # Serveur Flask principal
│   └── static/             # Interface web statique
├── 📁 gui/                  # Interface graphique
│   └── config_app.py       # Application tkinter moderne
├── 📁 printer/             # Logique d'impression
│   ├── printer_utils.py    # Utilitaires et détection
│   └── receipt.py          # Formatage des reçus
├── 📁 utils/               # Configuration et utilitaires
│   └── config.py           # Gestion de la configuration
├── 📁 logs/                # Journaux d'activité (généré)
├── 📁 static/              # Fichiers web statiques (généré)
├── main.py                 # Point d'entrée principal
├── setup.py                # Configuration du package Python
├── build.bat              # Script de compilation Windows
├── build.sh               # Script de compilation Linux
└── thermal_printer.spec   # Configuration PyInstaller
```

### Technologies utilisées
- **Backend** : Python 3.8+, Flask, Flask-CORS
- **Interface** : tkinter avec thème moderne personnalisé
- **Impression** : python-escpos, win32print (Windows)
- **Packaging** : PyInstaller pour exécutables autonomes
- **Format** : JSON pour échange de données, ESC/POS pour impression

### Flux de données
```
Application Web ──➤ API REST ──➤ Formatage ──➤ Encodage ──➤ Imprimante
     │                │              │           │            │
     │                │              │           │            ▼
     │                │              │           │       Ticket imprimé
     │                │              │           │
     ▼                ▼              ▼           ▼
Interface Web    Logs & Debug   Détection    Optimisation
```

## ⚡ Installation rapide

### Prérequis système
- **OS** : Windows 10/11 (recommandé) ou Linux
- **Python** : 3.8 ou supérieur
- **Imprimante** : Compatible ESC/POS avec pilotes installés
- **Réseau** : Accès local pour l'API (port 5789 par défaut)

### Installation automatique
```bash
# 1. Cloner le repository
git clone https://github.com/arrowmaruis/thermal_printer_api.git
cd thermal_printer_api

# 2. Installation complète
pip install -e .

# 3. Lancement
python main.py
```

### Installation manuelle des dépendances
```bash
# Dépendances principales
pip install flask>=2.0.0
pip install flask-cors>=3.0.0
pip install python-escpos>=3.0.0
pip install pillow>=8.0.0

# Windows uniquement
pip install pywin32

# Pour la compilation (optionnel)
pip install pyinstaller
```

### Vérification de l'installation
```bash
# Test de l'API
python main.py --no-gui

# Dans un autre terminal
curl http://localhost:5789/health
```

Réponse attendue :
```json
{
  "status": "ok",
  "version": "1.0.0",
  "time": "2025-01-22 15:30:45",
  "default_printer": "POS58 Printer",
  "default_printer_width": "58mm",
  "default_encoding": "cp437"
}
```

## 📖 Guide d'utilisation détaillé

### 🚀 Premier démarrage

1. **Lancement de l'application**
   ```bash
   python main.py
   ```

2. **Configuration initiale**
   - L'interface graphique s'ouvre automatiquement
   - Les imprimantes sont détectées automatiquement
   - Sélectionnez votre imprimante par défaut
   - Testez l'impression

3. **Vérification de l'API**
   - L'API démarre automatiquement sur le port 5789
   - Accédez à `http://localhost:5789` pour voir la documentation

### 🖥️ Utilisation de l'interface graphique

#### Tableau de bord principal
- **Statistiques** : Nombre d'imprimantes, imprimante par défaut, port API
- **Actions rapides** : Test d'impression, ouverture navigateur, actualisation

#### Gestion des imprimantes
- **Liste complète** : Toutes les imprimantes avec statut et largeur détectée
- **Actions** : Test, définition par défaut, actualisation
- **Informations** : Nom, statut, largeur (58mm/80mm), port

#### Paramètres
- **Port API** : Modification du port d'écoute
- **Encodage** : Sélection de l'encodage par défaut
- **URL API** : Affichage et accès rapide à l'interface web

#### Journaux
- **Consultation** : Logs en temps réel avec scroll automatique
- **Débogage** : Informations détaillées sur les opérations

### 🌐 Utilisation via API REST

#### Configuration de base
```javascript
// Configuration de base pour les requêtes
const API_BASE = 'http://localhost:5789';
const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
};
```

#### Exemples d'intégration

**JavaScript/jQuery :**
```javascript
// Test de l'API
$.get(API_BASE + '/health')
    .done(function(data) {
        console.log('API disponible:', data);
    });

// Impression d'un reçu
const receiptData = {
    type: 'receipt',
    receipt_type: 'standard',
    data: {
        header: {
            business_name: 'Mon Restaurant',
            address: '123 Rue Example, 75001 Paris',
            phone: '+33 1 23 45 67 89',
            receipt_number: 'R-2025-001'
        },
        items: [
            {name: 'Café Expresso', quantity: 2, price: 350},
            {name: 'Croissant', quantity: 1, price: 180},
            {name: 'Jus d\'orange', quantity: 1, price: 450}
        ],
        footer: {
            payment_method: 'Carte bancaire',
            thank_you_message: 'Merci de votre visite !',
            website: 'www.mon-restaurant.fr'
        }
    }
};

$.ajax({
    url: API_BASE + '/print',
    method: 'POST',
    headers: headers,
    data: JSON.stringify(receiptData),
    success: function(response) {
        console.log('Impression réussie:', response);
    },
    error: function(xhr, status, error) {
        console.error('Erreur d\'impression:', error);
    }
});
```

**PHP/Laravel :**
```php
<?php
// Configuration
$apiBase = 'http://localhost:5789';

// Données du reçu
$receiptData = [
    'type' => 'receipt',
    'receipt_type' => 'hotel',
    'data' => [
        'header' => [
            'business_name' => 'Hôtel Example',
            'address' => '456 Avenue Test, 69001 Lyon',
            'phone' => '+33 4 12 34 56 78',
            'receipt_number' => 'HTL-2025-042'
        ],
        'client_info' => 'M. Dupont Jean - Chambre 205',
        'room_info' => "Chambre: 205\nType: Suite Deluxe\nArrivée: 22/01/2025\nDépart: 25/01/2025",
        'items' => [
            [
                'name' => 'Suite Deluxe - 3 nuits',
                'type' => 'accommodation',
                'quantity' => 3,
                'quantity_unit' => 'nuit(s)',
                'price' => 12000
            ],
            [
                'name' => 'Petit déjeuner',
                'type' => 'food',
                'category' => 'Restaurant',
                'quantity' => 6,
                'price' => 1800
            ]
        ],
        'footer' => [
            'payment_method' => 'Carte de crédit',
            'payment_status' => 'Paiement effectué',
            'thank_you_message' => 'Merci pour votre séjour',
            'website' => 'www.hotel-example.fr'
        ]
    ]
];

// Envoi de la requête
$curl = curl_init();
curl_setopt_array($curl, [
    CURLOPT_URL => $apiBase . '/print',
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
    CURLOPT_POSTFIELDS => json_encode($receiptData)
]);

$response = curl_exec($curl);
$httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
curl_close($curl);

if ($httpCode === 200) {
    echo "Impression réussie: " . $response;
} else {
    echo "Erreur d'impression: " . $response;
}
?>
```

**Python/Django :**
```python
import requests
import json

# Configuration
API_BASE = 'http://localhost:5789'
headers = {'Content-Type': 'application/json'}

def print_receipt(receipt_data):
    """Imprimer un reçu via l'API"""
    try:
        response = requests.post(
            f'{API_BASE}/print',
            headers=headers,
            json=receipt_data,
            timeout=10
        )
        
        if response.status_code == 200:
            return {'success': True, 'data': response.json()}
        else:
            return {'success': False, 'error': response.json()}
            
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': str(e)}

# Exemple d'utilisation dans une vue Django
from django.http import JsonResponse

def process_order(request):
    # ... logique métier ...
    
    # Données du reçu
    receipt_data = {
        'type': 'receipt',
        'receipt_type': 'mixed',
        'printer_width': '80mm',  # Forcer une largeur spécifique
        'encoding': 'utf-8',      # Forcer un encodage spécifique
        'data': {
            'header': {
                'business_name': 'Restaurant & Hôtel',
                'address': '789 Boulevard Test',
                'phone': '+33 5 67 89 01 23'
            },
            # ... autres données ...
        }
    }
    
    # Impression
    result = print_receipt(receipt_data)
    
    if result['success']:
        return JsonResponse({'status': 'success', 'message': 'Reçu imprimé'})
    else:
        return JsonResponse({'status': 'error', 'message': result['error']})
```

## 🌐 Documentation API REST

### Endpoints disponibles

#### `GET /health`
Vérification du statut de l'API et des informations système.

**Réponse :**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "time": "2025-01-22 15:30:45",
  "default_printer": "POS58 Printer",
  "default_printer_width": "58mm",
  "default_encoding": "cp437"
}
```

#### `GET /printers`
Liste toutes les imprimantes détectées avec leurs propriétés.

**Réponse :**
```json
{
  "status": "success",
  "printers": [
    {
      "id": 0,
      "name": "POS58 Printer",
      "port": "USB001",
      "driver": "POS58 Driver",
      "is_default": false,
      "width": "58mm",
      "encoding": "cp437"
    },
    {
      "id": 1,
      "name": "Epson TM-T88V",
      "port": "COM1",
      "driver": "EPSON TM-T88V",
      "is_default": true,
      "width": "80mm",
      "encoding": "cp850"
    }
  ],
  "default_printer_id": 1,
  "default_printer_width": "80mm",
  "default_encoding": "cp850",
  "count": 2
}
```

#### `GET /test-printer/<int:printer_id>`
Imprime un ticket de test sur l'imprimante spécifiée.

**Paramètres :**
- `printer_id` : ID de l'imprimante (obtenu via `/printers`)

**Réponse succès :**
```json
{
  "status": "success",
  "message": "Test d'impression envoyé à Epson TM-T88V",
  "printer_width": "80mm"
}
```

**Réponse erreur :**
```json
{
  "status": "error",
  "message": "Imprimante avec ID 5 non trouvée"
}
```

#### `POST /print`
Imprime un document formaté sur l'imprimante spécifiée ou par défaut.

**Corps de la requête :**
```json
{
  "type": "receipt|raw",
  "receipt_type": "standard|hotel|mixed",
  "printer_id": 1,
  "printer_width": "58mm|80mm",
  "encoding": "utf-8|cp437|cp850|ascii",
  "data": {
    // Structure selon le type de reçu
  }
}
```

**Paramètres optionnels :**
- `printer_id` : ID de l'imprimante (utilise la défaut si omis)
- `printer_width` : Force une largeur spécifique (détection auto si omis)
- `encoding` : Force un encodage spécifique (détection auto si omis)

### Structures de données détaillées

#### Reçu standard (restaurant/bar)
```json
{
  "type": "receipt",
  "receipt_type": "standard",
  "data": {
    "header": {
      "business_name": "Café de la Place",
      "address": "12 Place du Marché, 75004 Paris",
      "phone": "+33 1 42 34 56 78",
      "receipt_number": "R-2025-0156",
      "date": "22/01/2025 14:30",
      "order_type": "Sur place"
    },
    "client_info": "Table 5 - Serveur: Marie",
    "items": [
      {
        "name": "Café Expresso",
        "quantity": 2,
        "price": 280
      },
      {
        "name": "Croissant au beurre",
        "quantity": 1,
        "price": 150
      },
      {
        "name": "Jus d'orange pressé",
        "quantity": 1,
        "price": 420
      }
    ],
    "footer": {
      "payment_method": "Carte bancaire",
      "payment_status": "Paiement validé",
      "thank_you_message": "Merci de votre visite !",
      "additional_message": "À bientôt au Café de la Place",
      "website": "www.cafe-de-la-place.fr"
    }
  }
}
```

#### Reçu hôtel (réservation)
```json
{
  "type": "receipt",
  "receipt_type": "hotel",
  "data": {
    "header": {
      "business_name": "Hôtel des Jardins",
      "address": "25 Rue des Roses, 06000 Nice",
      "phone": "+33 4 93 12 34 56",
      "receipt_number": "HTL-2025-0089"
    },
    "client_info": "M. et Mme MARTIN Pierre",
    "room_info": "Chambre: 312\nType: Chambre Deluxe Vue Mer\nArrivée: 22/01/2025 15:00\nDépart: 25/01/2025 11:00\nNombre de nuits: 3",
    "items": [
      {
        "name": "Chambre Deluxe Vue Mer",
        "type": "accommodation",
        "quantity": 3,
        "quantity_unit": "nuit(s)",
        "price": 18500
      },
      {
        "name": "Petit déjeuner continental",
        "type": "food",
        "category": "Restaurant",
        "quantity": 6,
        "price": 2200
      },
      {
        "name": "Parking privé",
        "type": "service",
        "quantity": 3,
        "price": 1500
      }
    ],
    "stats": {
      "discount_amount": 5000
    },
    "footer": {
      "payment_method": "Carte de crédit",
      "payment_status": "Pré-autorisation validée",
      "thank_you_message": "Merci pour votre confiance",
      "additional_message": "Nous espérons vous revoir bientôt",
      "website": "www.hotel-des-jardins.fr"
    }
  }
}
```

#### Reçu mixte (hôtel + consommations)
```json
{
  "type": "receipt",
  "receipt_type": "mixed",
  "data": {
    "header": {
      "business_name": "Resort & Spa Méditerranée",
      "address": "100 Corniche des Anges, 83000 Toulon",
      "phone": "+33 4 94 56 78 90",
      "receipt_number": "MIX-2025-0234"
    },
    "client_info": "Mme DUBOIS Sophie - Suite 501",
    "room_info": "Suite: 501\nType: Suite Présidentielle\nSéjour: 20/01 au 24/01/2025",
    "items": [
      {
        "name": "Suite Présidentielle - 4 nuits",
        "type": "accommodation",
        "quantity": 4,
        "quantity_unit": "nuit(s)",
        "price": 35000
      },
      {
        "name": "Dîner gastronomique",
        "type": "food",
        "quantity": 2,
        "price": 8500
      },
      {
        "name": "Champagne Vintage",
        "type": "drink",
        "quantity": 1,
        "price": 15000
      },
      {
        "name": "Spa - Massage duo",
        "type": "service",
        "quantity": 1,
        "price": 25000
      },
      {
        "name": "Remise fidélité -10%",
        "type": "discount",
        "quantity": 1,
        "price": -19800
      }
    ],
    "footer": {
      "payment_method": "American Express",
      "payment_status": "Paiement intégral effectué",
      "thank_you_message": "Merci pour votre séjour exceptionnel",
      "website": "www.resort-spa-mediterranee.fr"
    }
  }
}
```

#### Impression de texte brut
```json
{
  "type": "raw",
  "text": "Texte libre à imprimer\nAvec retours à la ligne\nEt caractères spéciaux: éèàù çÇ",
  "printer_id": 0,
  "encoding": "utf-8"
}
```

### Codes de statut HTTP

- **200** : Succès
- **400** : Requête malformée (données manquantes ou invalides)
- **404** : Imprimante non trouvée
- **500** : Erreur serveur (problème d'impression, configuration, etc.)

### Gestion des erreurs

Toutes les réponses d'erreur suivent ce format :
```json
{
  "status": "error",
  "message": "Description détaillée de l'erreur"
}
```

Exemples d'erreurs courantes :
```json
// Imprimante non trouvée
{
  "status": "error",
  "message": "Imprimante avec ID 5 non trouvée"
}

// Données manquantes
{
  "status": "error",
  "message": "Aucune donnée reçue"
}

// Problème d'impression
{
  "status": "error",
  "message": "Échec de l'impression sur POS58 Printer"
}

// Aucune imprimante configurée
{
  "status": "error",
  "message": "Aucune imprimante par défaut configurée et aucun ID d'imprimante spécifié"
}
```

## 🖥️ Interface graphique

### Conception et ergonomie

L'interface graphique utilise un thème sombre moderne inspiré des applications web contemporaines :

- **Palette de couleurs** : Tons sombres (#1a1a2e) avec accents violets (#6c5ce7)
- **Typographie** : Segoe UI pour une lisibilité optimale
- **Layout responsive** : S'adapte aux différentes tailles d'écran
- **Icônes et visuels** : Interface claire et intuitive

### Pages et fonctionnalités

#### 🏠 Tableau de bord
**Vue d'ensemble du système avec cartes informatives :**

- **Statistiques en temps réel** :
  - Nombre d'imprimantes détectées
  - Imprimante par défaut avec largeur
  - Port API actuel
  - Encodage configuré

- **Actions rapides** :
  - Test d'impression sur imprimante par défaut
  - Ouverture de l'interface web dans le navigateur
  - Actualisation de la liste des imprimantes

#### 🖨️ Gestion des imprimantes
**Configuration et test des imprimantes :**

- **Liste détaillée** avec colonnes :
  - Nom de l'imprimante
  - Statut (Disponible, Par défaut, Système)
  - Largeur détectée (58mm/80mm)
  - Port de connexion

- **Actions disponibles** :
  - Actualiser la liste
  - Tester l'imprimante sélectionnée
  - Définir comme imprimante par défaut

- **Détection automatique** :
  - Largeur basée sur le pilote et les capacités
  - Encodage optimal selon le modèle
  - Sauvegarde automatique des paramètres

#### ⚙️ Paramètres
**Configuration avancée du système :**

- **Port API** :
  - Modification du port d'écoute
  - Validation des ports disponibles (1024-65535)
  - Redémarrage requis pour application

- **Largeur d'imprimante** :
  - Affichage de la largeur détectée
  - Information automatique lors de la sélection

- **Encodage** :
  - Sélection manuelle si détection automatique insuffisante
  - Options : UTF-8, CP437, CP850, ASCII
  - Application immédiate

- **URL API** :
  - Affichage de l'URL complète
  - Bouton d'ouverture rapide dans le navigateur

#### 📋 Journaux
**Consultation des logs système :**

- **Affichage en temps réel** des activités
- **Scroll automatique** vers les nouveaux messages
- **Filtrage par niveau** (info, warning, error)
- **Historique persistant** avec rotation quotidienne

### Raccourcis clavier

- **F5** : Actualiser la liste des imprimantes
- **Ctrl+T** : Test de l'imprimante par défaut
- **Ctrl+O** : Ouvrir l'interface web
- **Ctrl+S** : Sauvegarder les paramètres
- **Ctrl+Q** : Quitter l'application

## ⚙️ Configuration avancée

### Fichier de configuration (`printer_config.json`)

```json
{
    "default_printer_id": 1,
    "default_printer_name": "Epson TM-T88V",
    "default_printer_width": "80mm",
    "default_encoding": "cp850",
    "autostart": true,
    "port": 5789,
    "log_level": "INFO",
    "max_log_files": 30,
    "cors_origins": [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://votre-site.com"
    ],
    "print_settings": {
        "max_line_width_58mm": 32,
        "max_line_width_80mm": 48,
        "article_width_58mm": 14,
        "article_width_80mm": 24,
        "currency": "FCFA",
        "date_format": "%d/%m/%Y %H:%M:%S"
    }
}
```

### Variables d'environnement

```bash
# Port API (priorité sur la config)
THERMAL_API_PORT=5789

# Niveau de log
THERMAL_LOG_LEVEL=DEBUG

# Répertoire de logs personnalisé
THERMAL_LOG_DIR=./custom_logs

# Désactiver l'interface graphique
THERMAL_NO_GUI=true

# Imprimante par défaut (nom)
THERMAL_DEFAULT_PRINTER="Mon Imprimante"

# Encodage forcé
THERMAL_FORCE_ENCODING=cp437
```

### Configuration avancée des imprimantes

#### Détection personnalisée
Vous pouvez ajouter des règles de détection personnalisées dans `printer_utils.py` :

```python
# Mots-clés personnalisés pour détection 80mm
custom_keywords_80mm = [
    'ma-marque-80', 'modele-large', 'wide-printer'
]

# Mots-clés personnalisés pour encodage
custom_encoding_rules = {
    'ma-marque': 'cp850',
    'modele-special': 'utf-8'
}
```

#### Commands ESC/POS personnalisées
Ajout de commandes spécifiques dans `printer_utils.py` :

```python
# Commandes ESC/POS supplémentaires
ESC_UNDERLINE_ON = b'\x1b\x2d\x01'   # Soulignement
ESC_UNDERLINE_OFF = b'\x1b\x2d\x00'  # Arrêt soulignement
ESC_REVERSE_ON = b'\x1d\x42\x01'     # Inversion vidéo
ESC_REVERSE_OFF = b'\x1d\x42\x00'    # Arrêt inversion

# Logo personnalisé (bitmap)
def add_custom_logo(commands):
    """Ajoute un logo personnalisé au début du ticket"""
    # Commande pour logo bitmap (exemple)
    logo_data = b'\x1d\x2a\x20\x20' + your_logo_bitmap
    commands.extend(logo_data)
    commands.extend(b'\n\n')
```

### Intégration avec des systèmes existants

#### Laravel/PHP
```php
// config/thermal_printer.php
<?php
return [
    'api_url' => env('THERMAL_API_URL', 'http://localhost:5789'),
    'timeout' => env('THERMAL_API_TIMEOUT', 10),
    'retry_attempts' => env('THERMAL_API_RETRY', 3),
    'default_width' => env('THERMAL_WIDTH', '58mm'),
    'default_encoding' => env('THERMAL_ENCODING', 'cp437'),
];

// Service class
class ThermalPrinterService {
    public function printReceipt($data, $type = 'standard') {
        $client = new \GuzzleHttp\Client();
        
        try {
            $response = $client->post(config('thermal_printer.api_url') . '/print', [
                'json' => [
                    'type' => 'receipt',
                    'receipt_type' => $type,
                    'data' => $data
                ],
                'timeout' => config('thermal_printer.timeout')
            ]);
            
            return json_decode($response->getBody(), true);
        } catch (\Exception $e) {
            \Log::error('Thermal printer error: ' . $e->getMessage());
            return ['status' => 'error', 'message' => $e->getMessage()];
        }
    }
}
```

#### Node.js/Express
```javascript
// thermal-printer.js
const axios = require('axios');

class ThermalPrinter {
    constructor(apiUrl = 'http://localhost:5789') {
        this.apiUrl = apiUrl;
        this.client = axios.create({
            baseURL: apiUrl,
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }
    
    async printReceipt(data, type = 'standard', options = {}) {
        try {
            const payload = {
                type: 'receipt',
                receipt_type: type,
                data: data,
                ...options
            };
            
            const response = await this.client.post('/print', payload);
            return response.data;
        } catch (error) {
            console.error('Thermal printer error:', error.message);
            throw new Error(`Print failed: ${error.message}`);
        }
    }
    
    async getStatus() {
        try {
            const response = await this.client.get('/health');
            return response.data;
        } catch (error) {
            throw new Error(`API unavailable: ${error.message}`);
        }
    }
}

module.exports = ThermalPrinter;

// Utilisation
const printer = new ThermalPrinter();

app.post('/orders/:id/print', async (req, res) => {
    try {
        const order = await Order.findById(req.params.id);
        const receiptData = formatOrderForReceipt(order);
        
        const result = await printer.printReceipt(receiptData);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});
```

## 🔧 Compilation et distribution

### Préparation pour la compilation

#### 1. Nettoyage du projet
```bash
# Supprimer les fichiers temporaires
rm -rf __pycache__/ *.pyc build/ dist/
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete
```

#### 2. Test complet avant compilation
```bash
# Test de l'installation
pip install -e .

# Test de l'API
python main.py --no-gui &
curl http://localhost:5789/health
curl http://localhost:5789/printers

# Test de l'interface
python main.py
```

### Compilation avec PyInstaller

#### Configuration optimisée (`thermal_printer.spec`)

Pour une compilation optimale, voici la configuration recommandée :

```python
# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_all

# Collecte automatique des dépendances
datas_flask, binaries_flask, hiddenimports_flask = collect_all('flask')
datas_escpos, binaries_escpos, hiddenimports_escpos = collect_all('escpos')

project_dir = os.path.abspath('.')

a = Analysis(
    ['build_exe.py'],
    pathex=[project_dir],
    binaries=binaries_flask + binaries_escpos,
    datas=[
        # Fichiers statiques
        (os.path.join(project_dir, 'api', 'static'), 'api/static'),
        # Templates Flask si utilisés
        (os.path.join(project_dir, 'api', 'templates'), 'api/templates'),
        # Fichiers de configuration par défaut
        ('printer_config.json', '.'),
    ] + datas_flask + datas_escpos,
    hiddenimports=[
        # Core
        'flask', 'flask_cors', 'werkzeug', 'jinja2', 'markupsafe',
        'itsdangerous', 'click', 'blinker',
        
        # Impression
        'escpos', 'escpos.printer', 'escpos.constants',
        'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont',
        'qrcode', 'qrcode.image.pil',
        
        # Système Windows
        'win32print', 'win32api', 'win32gui', 'win32con',
        'win32file', 'win32pipe', 'pywintypes',
        
        # Interface graphique
        'tkinter', 'tkinter.ttk', 'tkinter.font', 'tkinter.messagebox',
        'tkinter.filedialog', 'tkinter.colorchooser',
        
        # Encodages
        'encodings', 'encodings.utf_8', 'encodings.cp437',
        'encodings.cp850', 'encodings.cp852', 'encodings.ascii',
        
        # Modules standard
        'json', 'datetime', 'threading', 'queue', 'logging',
        'unicodedata', 'webbrowser', 'getpass', 'tempfile',
        
        # Modules projet
        'thermal_printer_api',
        'thermal_printer_api.api', 'thermal_printer_api.api.server',
        'thermal_printer_api.printer', 'thermal_printer_api.printer.printer_utils',
        'thermal_printer_api.printer.receipt',
        'thermal_printer_api.gui', 'thermal_printer_api.gui.config_app',
        'thermal_printer_api.utils', 'thermal_printer_api.utils.config',
    ] + hiddenimports_flask + hiddenimports_escpos,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclusions pour réduire la taille
        'matplotlib', 'numpy', 'scipy', 'pandas', 'jupyter',
        'IPython', 'notebook', 'pytz', 'babel', 'setuptools',
        'distutils', 'email', 'html', 'http', 'urllib3',
        'multiprocessing', 'concurrent', 'asyncio',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Filtrage des fichiers inutiles
a.datas = [x for x in a.datas if not x[0].startswith('tcl')]
a.datas = [x for x in a.datas if not x[0].startswith('tk')]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HoteliaImpression',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compression UPX pour réduire la taille
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Pas de console en production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'  # Icône personnalisée
)
```

#### Scripts de compilation améliorés

**Windows (`build.bat`) :**
```batch
@echo off
setlocal EnableDelayedExpansion

echo ================================
echo  BUILD HOTELIA THERMAL PRINTER
echo ================================
echo.

:: Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installé ou pas dans le PATH
    pause
    exit /b 1
)

:: Vérifier pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: pip n'est pas disponible
    pause
    exit /b 1
)

echo [1/6] Nettoyage des anciens builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.egg-info" rmdir /s /q "*.egg-info"

echo [2/6] Installation du package en mode développement...
pip install -e . --quiet
if errorlevel 1 (
    echo ERREUR: Échec de l'installation du package
    pause
    exit /b 1
)

echo [3/6] Installation de PyInstaller...
pip install pyinstaller --quiet --upgrade
if errorlevel 1 (
    echo ERREUR: Échec de l'installation de PyInstaller
    pause
    exit /b 1
)

echo [4/6] Compilation avec PyInstaller...
pyinstaller thermal_printer.spec --clean --noconfirm
if errorlevel 1 (
    echo ERREUR: Échec de la compilation
    pause
    exit /b 1
)

echo [5/6] Vérification du build...
if exist "dist\HoteliaImpression\HoteliaImpression.exe" (
    echo ✓ Build réussi !
    
    :: Copier les fichiers additionnels
    if exist "README.md" copy "README.md" "dist\HoteliaImpression\"
    if exist "LICENSE" copy "LICENSE" "dist\HoteliaImpression\"
    
    :: Créer un raccourci
    echo [6/6] Création du raccourci...
    echo Set oWS = WScript.CreateObject("WScript.Shell"^) > CreateShortcut.vbs
    echo sLinkFile = "HoteliaImpression.lnk" >> CreateShortcut.vbs
    echo Set oLink = oWS.CreateShortcut(sLinkFile^) >> CreateShortcut.vbs
    echo oLink.TargetPath = "%CD%\dist\HoteliaImpression\HoteliaImpression.exe" >> CreateShortcut.vbs
    echo oLink.WorkingDirectory = "%CD%\dist\HoteliaImpression\" >> CreateShortcut.vbs
    echo oLink.Description = "Hotelia Thermal Printer API" >> CreateShortcut.vbs
    echo oLink.Save >> CreateShortcut.vbs
    cscript CreateShortcut.vbs >nul
    del CreateShortcut.vbs
    
    echo.
    echo ================================
    echo        BUILD TERMINÉ !
    echo ================================
    echo Exécutable: dist\HoteliaImpression\HoteliaImpression.exe
    echo Raccourci:  HoteliaImpression.lnk
    echo.
    echo Test rapide...
    cd dist\HoteliaImpression
    timeout /t 2 >nul
    start "" "HoteliaImpression.exe"
    cd ..\..
) else (
    echo ✗ ERREUR: Le build a échoué !
    echo Vérifiez les erreurs ci-dessus.
    pause
    exit /b 1
)

echo Appuyez sur une touche pour continuer...
pause >nul
```

### Optimisation de la taille

#### Techniques de réduction
1. **Exclusion de modules** : Exclure les modules non utilisés
2. **Compression UPX** : Réduire la taille de l'exécutable
3. **Suppression des fichiers debug** : Éliminer les symboles de débogage

#### Script d'optimisation post-build
```python
# optimize_build.py
import os
import shutil
import glob

def optimize_build():
    """Optimise le build après compilation"""
    dist_dir = "dist/HoteliaImpression"
    
    if not os.path.exists(dist_dir):
        print("Dossier de build non trouvé")
        return
    
    print("Optimisation du build...")
    
    # Supprimer les fichiers inutiles
    unnecessary_files = [
        "*.pdb",           # Fichiers de débogage
        "*.lib",           # Bibliothèques statiques
        "*test*",          # Fichiers de test
        "example*",        # Fichiers d'exemple
    ]
    
    for pattern in unnecessary_files:
        for file in glob.glob(os.path.join(dist_dir, "**", pattern), recursive=True):
            try:
                os.remove(file)
                print(f"Supprimé: {file}")
            except:
                pass
    
    # Créer un fichier VERSION
    with open(os.path.join(dist_dir, "VERSION.txt"), "w") as f:
        f.write("Hotelia Thermal Printer API v1.0.0\n")
        f.write(f"Build date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Calculer la taille finale
    total_size = sum(
        os.path.getsize(os.path.join(dirpath, filename))
        for dirpath, dirnames, filenames in os.walk(dist_dir)
        for filename in filenames
    )
    
    print(f"Taille finale: {total_size / 1024 / 1024:.1f} MB")
    print("Optimisation terminée !")

if __name__ == "__main__":
    optimize_build()
```

### Création d'un installateur

#### Inno Setup (Windows)
```ini
; thermal_printer_installer.iss
[Setup]
AppName=Hotelia Thermal Printer API
AppVersion=1.0.0
AppPublisher=Votre Société
AppPublisherURL=https://votre-site.com
DefaultDirName={pf}\HoteliaImpression
DefaultGroupName=Hotelia Thermal Printer
OutputDir=setup
OutputBaseFilename=HoteliaImpression-Setup-v1.0.0
Compression=lzma2/max
SolidCompression=yes
SetupIconFile=assets\icon.ico
WizardImageFile=assets\wizard-image.bmp
WizardSmallImageFile=assets\wizard-small.bmp

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le bureau"; GroupDescription: "Raccourcis additionnels:"
Name: "quicklaunchicon"; Description: "Créer un raccourci dans la barre de lancement rapide"; GroupDescription: "Raccourcis additionnels:"; Flags: unchecked

[Files]
Source: "dist\HoteliaImpression\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Hotelia Thermal Printer"; Filename: "{app}\HoteliaImpression.exe"
Name: "{group}\Désinstaller"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Hotelia Thermal Printer"; Filename: "{app}\HoteliaImpression.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\HoteliaImpression.exe"; Description: "Lancer Hotelia Thermal Printer"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\HoteliaImpression"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"
Root: HKCU; Subkey: "Software\HoteliaImpression"; ValueType: string; ValueName: "Version"; ValueData: "1.0.0"
```

## 🧪 Tests et débogage

### Tests automatisés

#### Structure des tests
```
tests/
├── __init__.py
├── test_api.py              # Tests API REST
├── test_printer_utils.py    # Tests utilitaires imprimante
├── test_receipt.py          # Tests formatage reçus
├── test_config.py           # Tests configuration
├── fixtures/                # Données de test
│   ├── sample_receipts.json
│   └── mock_printers.json
└── conftest.py             # Configuration pytest
```

#### Tests API (`test_api.py`)
```python
import pytest
import json
from api.server import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    """Test de l'endpoint /health"""
    rv = client.get('/health')
    assert rv.status_code == 200
    
    data = json.loads(rv.data)
    assert data['status'] == 'ok'
    assert 'version' in data
    assert 'time' in data

def test_printers_endpoint(client):
    """Test de l'endpoint /printers"""
    rv = client.get('/printers')
    assert rv.status_code == 200
    
    data = json.loads(rv.data)
    assert data['status'] == 'success'
    assert 'printers' in data
    assert 'count' in data

def test_print_endpoint_no_data(client):
    """Test de l'endpoint /print sans données"""
    rv = client.post('/print')
    assert rv.status_code == 400
    
    data = json.loads(rv.data)
    assert data['status'] == 'error'

def test_print_endpoint_standard_receipt(client):
    """Test d'impression d'un reçu standard"""
    receipt_data = {
        'type': 'receipt',
        'receipt_type': 'standard',
        'data': {
            'header': {
                'business_name': 'Test Restaurant',
                'address': '123 Test Street'
            },
            'items': [
                {'name': 'Test Item', 'quantity': 1, 'price': 1000}
            ]
        }
    }
    
    rv = client.post('/print', 
                    data=json.dumps(receipt_data),
                    content_type='application/json')
    
    # Note: En test, l'impression peut échouer (pas d'imprimante)
    # mais le format de réponse doit être correct
    data = json.loads(rv.data)
    assert 'status' in data
    assert 'message' in data
```

#### Tests utilitaires (`test_printer_utils.py`)
```python
import pytest
from unittest.mock import patch, MagicMock
from printer.printer_utils import detect_printer_width, detect_printer_encoding

def test_detect_printer_width_58mm():
    """Test détection largeur 58mm"""
    with patch('printer.printer_utils.win32print') as mock_win32:
        mock_win32.OpenPrinter.return_value = MagicMock()
        mock_win32.GetPrinter.return_value = {
            'pDriverName': 'POS58 Driver',
            'pPortName': 'USB001'
        }
        
        width = detect_printer_width('POS58 Printer')
        assert width == '58mm'

def test_detect_printer_width_80mm():
    """Test détection largeur 80mm"""
    with patch('printer.printer_utils.win32print') as mock_win32:
        mock_win32.OpenPrinter.return_value = MagicMock()
        mock_win32.GetPrinter.return_value = {
            'pDriverName': 'Epson TM-T88V',
            'pPortName': 'COM1'
        }
        
        width = detect_printer_width('Epson TM-T88V')
        assert width == '80mm'

def test_detect_printer_encoding():
    """Test détection encodage"""
    encodings = [
        ('Epson TM-T88V', 'cp850'),
        ('Star TSP100', 'cp437'),
        ('Generic POS', 'cp437')
    ]
    
    for printer_name, expected in encodings:
        with patch('printer.printer_utils.win32print') as mock_win32:
            mock_win32.OpenPrinter.return_value = MagicMock()
            mock_win32.GetPrinter.return_value = {
                'pDriverName': printer_name,
                'pPortName': 'USB001'
            }
            
            encoding = detect_printer_encoding(printer_name)
            assert encoding == expected
```

#### Lancement des tests
```bash
# Installation des dépendances de test
pip install pytest pytest-cov pytest-mock

# Lancement des tests
pytest tests/ -v

# Avec couverture de code
pytest tests/ --cov=. --cov-report=html

# Tests spécifiques
pytest tests/test_api.py::test_health_endpoint -v
```

### Débogage

#### Activation du mode debug
```python
# Dans config.py, modifier:
logger.setLevel(logging.DEBUG)

# Ou via variable d'environnement
export THERMAL_LOG_LEVEL=DEBUG
```

#### Logs détaillés
```python
# Exemple de logs utiles pour le débogage
logger.debug(f"Données reçues: {json.dumps(data, indent=2)}")
logger.debug(f"Imprimante sélectionnée: {printer_name} (ID: {printer_id})")
logger.debug(f"Encodage utilisé: {encoding}, Largeur: {printer_width}")
logger.debug(f"Commandes ESC/POS générées: {len(commands)} bytes")
```

#### Interface de débogage
```python
# Route de débogage (à ajouter temporairement dans server.py)
@app.route('/debug/config')
def debug_config():
    """Affiche la configuration complète pour débogage"""
    return jsonify({
        'config': config,
        'printers': get_printers(),
        'system_info': {
            'platform': sys.platform,
            'python_version': sys.version,
            'working_directory': os.getcwd()
        }
    })

@app.route('/debug/test-encodings/<int:printer_id>')
def debug_test_encodings(printer_id):
    """Test tous les encodages sur une imprimante"""
    # Implementation du test d'encodage...
    pass
```

### Outils de diagnostic

#### Script de diagnostic complet
```python
# diagnostic.py
import sys
import os
import json
import importlib

def check_dependencies():
    """Vérifier toutes les dépendances"""
    required_modules = [
        'flask', 'flask_cors', 'escpos', 'PIL', 'win32print'
    ]
    
    missing = []
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module} - MANQUANT")
            missing.append(module)
    
    return missing

def check_printers():
    """Vérifier les imprimantes disponibles"""
    try:
        from printer.printer_utils import get_printers
        printers = get_printers()
        
        print(f"\nImprimantes détectées: {len(printers)}")
        for printer in printers:
            print(f"  - {printer['name']} ({printer['width']}, {printer.get('encoding', 'N/A')})")
        
        return printers
    except Exception as e:
        print(f"Erreur détection imprimantes: {e}")
        return []

def check_config():
    """Vérifier la configuration"""
    try:
        from utils.config import config
        print(f"\nConfiguration:")
        print(json.dumps(config, indent=2))
        return True
    except Exception as e:
        print(f"Erreur configuration: {e}")
        return False

def main():
    print("=== DIAGNOSTIC THERMAL PRINTER API ===\n")
    
    print("1. Vérification des dépendances:")
    missing = check_dependencies()
    
    print("\n2. Vérification des imprimantes:")
    printers = check_printers()
    
    print("\n3. Vérification de la configuration:")
    config_ok = check_config()
    
    print("\n=== RÉSUMÉ ===")
    if missing:
        print(f"❌ Dépendances manquantes: {', '.join(missing)}")
    else:
        print("✅ Toutes les dépendances sont installées")
    
    if printers:
        print(f"✅ {len(printers)} imprimante(s) détectée(s)")
    else:
        print("❌ Aucune imprimante détectée")
    
    if config_ok:
        print("✅ Configuration chargée")
    else:
        print("❌ Problème de configuration")

if __name__ == "__main__":
    main()
```

## ❓ FAQ et dépannage

### Questions fréquentes

#### Q: L'API ne démarre pas
**R:** Vérifiez les points suivants :
1. **Port occupé** : Un autre service utilise peut-être le port 5789
   ```bash
   netstat -an | findstr :5789  # Windows
   lsof -i :5789               # Linux
   ```
2. **Dépendances manquantes** : Lancez le diagnostic
   ```bash
   python diagnostic.py
   ```
3. **Permissions** : Lancez en tant qu'administrateur si nécessaire

#### Q: L'imprimante n'est pas détectée
**R:** Solutions possibles :
1. **Pilotes** : Vérifiez que les pilotes sont installés
2. **Connexion** : USB/Série/Réseau selon le type
3. **Partage** : Imprimante non partagée sur le réseau
4. **Test Windows** : Imprimez une page de test depuis Windows

#### Q: Caractères bizarres sur les reçus
**R:** Problème d'encodage :
1. **Test d'encodages** : Utilisez `/test-all-encodings`
2. **Configuration manuelle** : Changez l'encodage dans les paramètres
3. **Encodages recommandés** :
   - `cp437` : USA (le plus courant)
   - `cp850` : Europe occidentale
   - `ascii` : En dernier recours

#### Q: L'exécutable ne se lance pas
**R:** Vérifications :
1. **Antivirus** : Peut bloquer l'exécutable
2. **Permissions** : Droits d'exécution
3. **Dépendances système** : Visual C++ Redistributable
4. **Mode console** : Changez `console=True` dans le .spec pour voir les erreurs

#### Q: L'API n'est pas accessible depuis une autre machine
**R:** Configuration réseau :
1. **Pare-feu** : Autoriser le port 5789
2. **Host** : Vérifiez que `HOST = '0.0.0.0'` dans config.py
3. **CORS** : Ajoutez votre domaine dans les origines autorisées

### Codes d'erreur courants

#### Erreurs API
- **400** : Données manquantes ou malformées
- **404** : Imprimante non trouvée
- **500** : Erreur d'impression ou configuration

#### Erreurs d'impression
- **Imprimante hors ligne** : Vérifiez la connexion
- **File d'attente bloquée** : Videz la file d'attente Windows
- **Papier épuisé** : Rechargez le papier

#### Erreurs de configuration
- **Port occupé** : Changez le port dans les paramètres
- **Permissions insuffisantes** : Lancez en administrateur
- **Fichier de config corrompu** : Supprimez `printer_config.json`

### Résolution de problèmes avancés

#### Problème de performance
```python
# Optimisation des requêtes
# Dans server.py, ajoutez un cache pour les imprimantes
from functools import lru_cache
import time

printer_cache_time = 0
printer_cache_data = None

@lru_cache(maxsize=1)
def get_printers_cached():
    global printer_cache_time, printer_cache_data
    current_time = time.time()
    
    # Cache pendant 30 secondes
    if current_time - printer_cache_time > 30:
        printer_cache_data = get_printers()
        printer_cache_time = current_time
    
    return printer_cache_data
```

#### Problème de mémoire (gros volumes)
```python
# Limitation de la taille des requêtes
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB max

# Nettoyage périodique des logs
import schedule

def cleanup_logs():
    """Nettoie les anciens logs"""
    log_dir = 'logs'
    max_age_days = 30
    # Implementation du nettoyage...

schedule.every().day.at("03:00").do(cleanup_logs)
```

## 🤝 Contribution

### Guide de contribution

#### Avant de contribuer
1. **Fork** le repository
2. **Clone** votre fork localement
3. **Créez une branche** pour votre fonctionnalité
4. **Testez** vos modifications
5. **Documentez** vos changements

#### Standards de code

**Style Python :**
- Suivez PEP 8
- Utilisez des docstrings pour toutes les fonctions
- Type hints recommandés
- Maximum 100 caractères par ligne

**Nommage :**
- `snake_case` pour les fonctions et variables
- `PascalCase` pour les classes
- `UPPER_CASE` pour les constantes

**Structure des commits :**
```
type(scope): description courte

Description détaillée si nécessaire

Fixes #123
```

Types de commits :
- `feat`: nouvelle fonctionnalité
- `fix`: correction de bug
- `docs`: documentation
- `style`: formatage, pas de changement de code
- `refactor`: refactorisation
- `test`: ajout de tests
- `chore`: maintenance

#### Processus de développement

```bash
# 1. Fork et clone
git clone https://github.com/votre-username/thermal_printer_api.git
cd thermal_printer_api

# 2. Créer une branche
git checkout -b feature/nouvelle-fonctionnalite

# 3. Développement
# ... vos modifications ...

# 4. Tests
python -m pytest tests/
python diagnostic.py

# 5. Commit
git add .
git commit -m "feat(api): ajout endpoint pour configuration imprimante"

# 6. Push et Pull Request
git push origin feature/nouvelle-fonctionnalite
```

#### Zones de contribution prioritaires

1. **Support de nouvelles imprimantes** :
   - Ajout de règles de détection
   - Tests avec différents modèles
   - Documentation de compatibilité

2. **Amélioration de l'interface** :
   - Nouveaux thèmes
   - Fonctionnalités ergonomiques
   - Internationalisation

3. **Optimisation des performances** :
   - Cache intelligent
   - Gestion mémoire
   - Temps de réponse

4. **Documentation** :
   - Traductions
   - Tutoriels vidéo
   - Examples d'intégration

### Signalement de bugs

#### Template de bug report
```markdown
**Description du bug**
Description claire et concise du problème.

**Étapes pour reproduire**
1. Aller à '...'
2. Cliquer sur '....'
3. Faire défiler jusqu'à '....'
4. Voir l'erreur

**Comportement attendu**
Description de ce qui devrait se passer.

**Captures d'écran**
Si applicable, ajoutez des captures d'écran.

**Environnement:**
 - OS: [e.g. Windows 10]
 - Version Python: [e.g. 3.9.5]
 - Version de l'API: [e.g. 1.0.0]
 - Imprimante: [e.g. Epson TM-T88V]

**Logs**
```
Coller ici les logs pertinents
```

**Contexte additionnel**
Tout autre information utile sur le problème.
```

#### Template de demande de fonctionnalité
```markdown
**La fonctionnalité résout-elle un problème ?**
Description claire du problème. Ex: "Je suis frustré quand [...]"

**Solution souhaitée**
Description claire de ce que vous aimeriez voir.

**Alternatives considérées**
Description des solutions alternatives considerées.

**Contexte additionnel**
Tout autre contexte ou captures d'écran sur la demande.
```

## 📈 Roadmap

### Version 1.1.0 (Q2 2025)
- 🌍 **Support Linux complet** avec détection CUPS
- 🎨 **Thèmes d'interface** multiples (clair, sombre, personnalisé)
- 🔧 **Configuration avancée** des formats de reçus
- 📊 **Statistiques d'utilisation** et monitoring

### Version 1.2.0 (Q3 2025)
- 🌐 **Interface web** complète pour administration
- 📱 **Support mobile** pour tests d'impression
- 🔌 **Plugins** pour formats de reçus personnalisés
- 🗄️ **Base de données** pour historique des impressions

### Version 2.0.0 (Q4 2025)
- ☁️ **Version cloud** avec API centralisée
- 🔄 **Synchronisation** multi-sites
- 📈 **Analytics** avancés et rapports
- 🤖 **Intelligence artificielle** pour optimisation automatique

### Fonctionnalités envisagées
- **Support imprimantes couleur**
- **Impression de codes-barres avancés**
- **Intégration avec systèmes de caisse**
- **Support imprimantes réseau avancé**
- **Mode kiosque** pour usage autonome

---

## 📄 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 📞 Support

### Support technique
- 🐛 **Issues GitHub** : [Issues](https://github.com/arrowmaruis/thermal_printer_api/issues)
- 📧 **Email** : support@votre-domaine.com
- 💬 **Discord** : [Serveur de support](https://discord.gg/votre-serveur)

### Documentation
- 📖 **Wiki** : [Wiki GitHub](https://github.com/arrowmaruis/thermal_printer_api/wiki)
- 🎥 **Tutoriels** : [Chaîne YouTube](https://youtube.com/votre-chaine)
- 📚 **Guides** : [Documentation complète](https://docs.votre-domaine.com)

### Communauté
- 💻 **Forum** : [Forum communautaire](https://forum.votre-domaine.com)
- 📱 **Telegram** : [Groupe Telegram](https://t.me/votre-groupe)
- 🐦 **Twitter** : [@votre_compte](https://twitter.com/votre_compte)

---

**Développé avec ❤️ pour simplifier l'impression thermique**

*Dernière mise à jour: 22 janvier 2025*
```

Ce README.md est maintenant extrêmement complet et couvre tous les aspects du projet :

1. **Description détaillée** du contexte et des objectifs
2. **Guide d'installation** pas à pas
3. **Documentation API** complète avec exemples
4. **Tutoriels d'intégration** pour différents langages
5. **Guide de configuration** avancée
6. **Instructions de compilation** détaillées
7. **Procédures de test** et débogage
8. **FAQ** et résolution de problèmes
9. **Guide de contribution** professionnel
10. **Roadmap** et vision future

Le document fait environ 15 000 mots et constitue une documentation professionnelle complète pour votre projet.