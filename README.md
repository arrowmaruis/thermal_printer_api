# Thermal Printer API

API d'impression thermique pour la gestion d'imprimantes POS (58mm et 80mm) connectees en **USB**, **Bluetooth** ou **reseau**, avec conversion française automatique vers ASCII.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)](https://github.com/arrowmaruis/thermal_printer_api)
[![Flask](https://img.shields.io/badge/flask-3.x-green.svg)](https://flask.palletsprojects.com/)

---

## Sommaire

- [Fonctionnalites](#fonctionnalites)
- [Architecture](#architecture)
- [Installation](#installation)
- [Demarrage](#demarrage)
- [Connexion Bluetooth](#connexion-bluetooth)
- [API REST](#api-rest)
- [Format des requetes](#format-des-requetes)
- [Configuration](#configuration)
- [Depannage](#depannage)

---

## Fonctionnalites

- Detection automatique des imprimantes USB, Bluetooth et reseau
- Support Bluetooth via **port COM** (methode principale) et **socket RFCOMM** (adresse MAC)
- Encodage **ASCII universel** avec conversion française intelligente (`café → cafe`, `15,50€ → 15,50 EUR`)
- Detection automatique de la largeur de papier (58mm / 80mm)
- Moteur de recu dynamique (sections : header, text, table, keyvalue, separator, feed, cut)
- Coupe papier immediate et robuste
- Authentification par cle API (optionnelle)
- CORS configurable

---

## Architecture

```
thermal_printer_api/
├── main.py                     # Point d'entree principal
├── run.py                      # Lancement alternatif
├── start.bat                   # Lancement Windows (double-clic)
├── printer_config.json         # Configuration sauvegardee (auto-genere)
├── requirements.txt
│
├── api/
│   └── server.py               # Serveur Flask + tous les endpoints
│
├── printer/
│   ├── printer_utils.py        # Detection, encodage, impression (USB/BT/COM)
│   ├── bluetooth_utils.py      # Utilitaires Bluetooth (COM + socket RFCOMM)
│   └── receipt.py              # Moteur de formatage des recus
│
├── utils/
│   └── config.py               # Configuration globale et logging
│
├── gui/
│   └── config_app.py           # Interface graphique (optionnelle)
│
└── static/
    └── index.html              # Page d'accueil auto-generee
```

---

## Installation

### Prerequis

- Python 3.8+ (teste sur Python 3.13)
- Windows 10/11
- Imprimante thermique compatible ESC/POS

### Installer les dependances

```bash
pip install -r requirements.txt
```

**Dependances principales :**

| Package | Usage |
|---|---|
| `flask` | Serveur HTTP |
| `flask-cors` | Gestion CORS |
| `pywin32` | Impression via spouleur Windows |
| `pyserial` | Impression via port COM (Bluetooth SPP) |
| `pillow` | Traitement image (optionnel) |

**Optionnel — scan Bluetooth radio :**

```bash
pip install pybluez
```

> Necessite uniquement pour l'endpoint `/bluetooth/discover` (scan actif des appareils a portee).

---

## Demarrage

### Methode 1 — double-clic

Lancer `start.bat`

### Methode 2 — terminal

```bash
python main.py
```

L'API demarre sur `http://0.0.0.0:5789`

---

## Connexion Bluetooth

### Methode recommandee : Port COM

1. **Appairez** l'imprimante dans **Parametres Windows > Bluetooth**
2. Windows lui assigne un port COM (ex: `COM4`)
3. Appelez `GET /bluetooth/ports` pour identifier le port
4. Utilisez `POST /print` avec `printer_id` (l'imprimante apparait dans `/printers`) **OU** `POST /bluetooth/print` avec `"port": "COM4"`

### Methode alternative : Socket RFCOMM (adresse MAC)

Connexion directe sans driver Windows. Necessite `pybluez` ou le stack Bluetooth Windows.

```bash
GET /bluetooth/test-socket/AA:BB:CC:DD:EE:FF
```

### Detection automatique dans /printers

L'endpoint `/printers` retourne maintenant **toutes** les imprimantes, quel que soit le type de connexion :

| `connection_type` | Description |
|---|---|
| `usb` | Imprimante USB classique |
| `bluetooth_spooler` | BT appairee avec driver Windows installe |
| `bluetooth_com` | BT sur port COM sans driver (detection pyserial) |
| `network` | Imprimante reseau (IP, WSD) |

L'endpoint `/print` route automatiquement selon le type — **pas besoin de changer le code client**.

---

## API REST

### Sante et infos

| Methode | Endpoint | Description |
|---|---|---|
| GET | `/` | Page d'accueil HTML |
| GET | `/health` | Statut de l'API |
| GET | `/encoding-info` | Configuration encodage ASCII |

### Imprimantes

| Methode | Endpoint | Description |
|---|---|---|
| GET | `/printers` | Liste toutes les imprimantes (USB + BT + reseau) |
| GET | `/test-printer/<id>` | Ticket de test sur l'imprimante id |
| GET | `/test-immediate-cut/<id>` | Test de coupe papier immediate |
| GET | `/encoding-test/<id>` | Test des encodages sur l'imprimante id |

### Impression

| Methode | Endpoint | Description |
|---|---|---|
| POST | `/print` | Impression (USB, BT, reseau) — routing automatique |

### Bluetooth (avance)

| Methode | Endpoint | Description |
|---|---|---|
| GET | `/bluetooth/ports` | Liste les ports COM disponibles (BT detectes) |
| GET | `/bluetooth/discover` | Scan radio BT (`?duration=8`) — necessite pybluez |
| POST | `/bluetooth/print` | Impression BT directe (COM ou socket) |
| GET | `/bluetooth/test-com/<port>` | Test impression via `COM3` par exemple |
| GET | `/bluetooth/test-socket/<adresse>` | Test impression via adresse MAC |

---

## Format des requetes

### Authentification (si cle configuree)

```
X-API-Key: votre_cle_api
```

---

### POST /print — Impression standard

```json
{
  "printer_id": 0,
  "type": "receipt",
  "receipt_type": "standard",
  "printer_width": "58mm",
  "data": {
    "sections": [
      { "type": "header", "text": "Hotel Luxe" },
      { "type": "separator" },
      {
        "type": "keyvalue",
        "rows": [
          { "key": "Chambre", "value": "101" },
          { "key": "Client",  "value": "Dupont" }
        ]
      },
      { "type": "separator" },
      {
        "type": "table",
        "columns": ["Article", "Qte", "Prix"],
        "rows": [
          ["Petit-dejeuner", "2", "5000 FCFA"],
          ["Cafe",           "1", "1500 FCFA"]
        ]
      },
      { "type": "separator" },
      { "type": "text", "text": "TOTAL : 11500 FCFA", "bold": true, "align": "right" },
      { "type": "feed", "lines": 3 },
      { "type": "cut" }
    ]
  }
}
```

**Types de sections disponibles :**

| Type | Parametres |
|---|---|
| `header` | `text`, `align` |
| `text` | `text`, `align`, `bold`, `size` (`normal`/`double`) |
| `separator` | *(aucun)* |
| `keyvalue` | `rows: [{key, value}]` |
| `table` | `columns: [...]`, `rows: [[...]]` |
| `feed` | `lines` (nombre de lignes a avancer) |
| `cut` | *(aucun)* |

---

### POST /print — Texte brut

```json
{
  "printer_id": 0,
  "type": "raw",
  "text": "Bonjour depuis l'API !\nMerci de votre visite."
}
```

---

### POST /bluetooth/print — Impression BT directe (port COM)

```json
{
  "connection": "com",
  "port": "COM4",
  "baudrate": 9600,
  "type": "receipt",
  "printer_width": "58mm",
  "data": { "sections": [...] }
}
```

### POST /bluetooth/print — Impression BT directe (socket)

```json
{
  "connection": "socket",
  "address": "AA:BB:CC:DD:EE:FF",
  "rfcomm_port": 1,
  "type": "raw",
  "text": "Test impression BT"
}
```

---

## Configuration

La configuration est sauvegardee dans `printer_config.json` (cree automatiquement).

| Cle | Defaut | Description |
|---|---|---|
| `port` | `5789` | Port HTTP de l'API |
| `default_printer_id` | `null` | ID de l'imprimante par defaut |
| `default_printer_width` | `"58mm"` | Largeur par defaut |
| `force_ascii_for_all` | `true` | Force ASCII pour toutes les imprimantes |
| `currency` | `"FCFA"` | Devise affichee sur les tickets |
| `currency_decimals` | `0` | Decimales (0 pour FCFA, 2 pour EUR) |
| `api_key` | `""` | Cle API (vide = pas d'auth) |
| `allowed_origins` | `[]` | Origines CORS (vide = valeurs par defaut) |

**Origines CORS par defaut** (si `allowed_origins` est vide) :
- `http://localhost:8000`
- `http://127.0.0.1:8000`
- `https://hotelia.cloud`

---

## Depannage

### L'imprimante BT n'apparait pas dans /printers

1. Verifiez qu'elle est bien **appairee** dans Parametres Windows > Bluetooth
2. Allez dans **Peripheriques et imprimantes** et ajoutez-la comme imprimante
3. Sinon elle apparaitra quand meme via `/bluetooth/ports` comme port COM

### Coupe papier decalee (coupe le recu suivant)

Utilisez l'endpoint de diagnostic :
```
GET /test-immediate-cut/<id>
```

### Caracteres corrompus a l'impression

L'API utilise l'ASCII universel — tous les accents sont convertis automatiquement. Si le probleme persiste :
```
GET /encoding-test/<id>
```

### Erreur port COM (Access denied / port busy)

- Verifiez qu'aucune autre application n'utilise le port
- Fermez le moniteur serie si ouvert
- Redemarrez le service Bluetooth Windows

### Module flask / pyserial manquant

```bash
pip install -r requirements.txt
```
