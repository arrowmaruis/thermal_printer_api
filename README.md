# Thermal Printer API

API d'impression thermique pour la gestion d'imprimantes POS (58mm et 80mm) connectees en **USB**, **Bluetooth** ou **reseau**, avec conversion française automatique vers ASCII.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)](https://github.com/arrowmaruis/thermal_printer_api)
[![Flask](https://img.shields.io/badge/flask-3.x-green.svg)](https://flask.palletsprojects.com/)

---

## Sommaire

- [Fonctionnalites](#fonctionnalites)
- [Architecture](#architecture)
- [Installation client (Setup.exe)](#installation-client-setupexe)
- [Installation developpeur](#installation-developpeur)
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
- **Service Windows** : demarre automatiquement au boot, aucune action manuelle
- **Installateur .exe** : une seule installation, tout est configure automatiquement
- Authentification par cle API (optionnelle)
- CORS configurable

---

## Architecture

```
thermal_printer_api/
├── installer_main.py           # Logique de l'installateur graphique
├── build.py                    # Genere ThermalPrinterAPI_Setup.exe (PyInstaller)
├── service.py                  # Service Windows (demarrage automatique)
├── main.py                     # Point d'entree (lancement manuel)
├── start.bat                   # Menu interactif (manuel / service)
├── install_service.bat         # Installation service seule (admin)
├── uninstall_service.bat       # Desinstallation du service (admin)
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
└── gui/
    └── config_app.py           # Interface graphique (optionnelle)
```

---

## Installation client (Setup.exe)

> Pour les clients finaux — aucune connaissance technique requise.

### Methode recommandee

1. Telecharger `ThermalPrinterAPI_Setup.exe`
2. Double-cliquer dessus
3. Cliquer **Installer** dans la fenetre qui s'ouvre
4. C'est tout

L'installateur effectue automatiquement :
- Copie des fichiers dans `C:\Program Files\ThermalPrinterAPI\`
- Installation des dependances Python
- Enregistrement du **service Windows** (demarrage auto)
- Demarrage immediat du service
- Creation d'un raccourci dans le menu Demarrer

**Des ce moment, l'API demarre a chaque demarrage Windows — sans rien faire.**

API accessible sur : `http://localhost:5789`

### Desinstallation

Executer `C:\Program Files\ThermalPrinterAPI\uninstall.bat` en tant qu'administrateur.

---

## Installation developpeur

### Prerequis

- Python 3.8+ (teste sur Python 3.13)
- Windows 10/11

### Installer les dependances

```bash
pip install -r requirements.txt
```

### Lancement manuel

```bash
python main.py
# ou
start.bat  (menu interactif)
```

### Generer le Setup.exe a distribuer

```bash
pip install pyinstaller
python build.py
# -> dist/ThermalPrinterAPI_Setup.exe
```

### Gestion du service (ligne de commande, admin)

```bash
python service.py install    # Installer le service
python service.py start      # Demarrer
python service.py stop       # Arreter
python service.py restart    # Redemarrer
python service.py status     # Statut
python service.py remove     # Desinstaller
python service.py debug      # Mode debug (fenetre visible)
```

---

## Connexion Bluetooth

### Methode recommandee : Port COM

1. **Appairez** l'imprimante dans **Parametres Windows > Bluetooth**
2. Windows lui assigne un port COM (ex: `COM4`)
3. Appelez `GET /bluetooth/ports` pour identifier le port
4. L'imprimante apparait automatiquement dans `GET /printers` avec `connection_type: "bluetooth_com"`
5. Utilisez `POST /print` avec le `printer_id` correspondant — le routage est automatique

### Methode alternative : Socket RFCOMM (adresse MAC)

Connexion directe sans driver Windows. Necessite `pybluez` ou le stack Bluetooth Windows.

```
GET /bluetooth/test-socket/AA:BB:CC:DD:EE:FF
```

### Detection automatique dans /printers

`GET /printers` retourne toutes les imprimantes, quel que soit le type de connexion :

| `connection_type` | Description |
|---|---|
| `usb` | Imprimante USB classique |
| `bluetooth_spooler` | BT appairee avec driver Windows installe |
| `bluetooth_com` | BT sur port COM sans driver (detection pyserial) |
| `network` | Imprimante reseau (IP, WSD) |

`POST /print` route automatiquement selon le type — **le code client ne change pas**.

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
| `logo` | `image` (base64), `path` (chemin serveur), `align`, `width` |
| `header` | `text`, `align` |
| `text` | `text`, `align`, `bold`, `size` (`normal`/`double`) |
| `separator` | `char` (defaut: `-`) |
| `keyvalue` | `rows: [{key, value}]`, `bold`, `key_width` |
| `table` | `columns: [...]`, `rows: [[...]]`, `show_header`, `separator` |
| `feed` | `lines` (nombre de lignes a avancer) |
| `cut` | *(aucun)* |

---

### POST /print — Impression avec logo

Le logo doit etre envoye en **base64** ou via un chemin de fichier sur le serveur.

```json
{
  "printer_id": 0,
  "type": "receipt",
  "printer_width": "58mm",
  "data": {
    "sections": [
      {
        "type": "logo",
        "image": "iVBORw0KGgoAAAANSUhEUgAA...",
        "align": "center",
        "width": 250
      },
      { "type": "feed", "lines": 1 },
      { "type": "header", "text": "Hotel Luxe" },
      { "type": "separator" },
      { "type": "text", "text": "Merci de votre visite", "align": "center" },
      { "type": "cut" }
    ]
  }
}
```

**Parametres de la section `logo` :**

| Champ | Requis | Description |
|---|---|---|
| `image` | Oui* | Image encodee en **base64** (PNG, JPG, BMP) |
| `path` | Oui* | OU chemin fichier sur le serveur (`logo.png`) |
| `align` | Non | `center` (defaut), `left`, `right` |
| `width` | Non | Largeur cible en pixels (defaut: 300px pour 58mm, 512px pour 80mm) |

*`image` ou `path` — l'un des deux est requis.

**Convertir une image en base64 (JavaScript) :**
```js
// Depuis un fichier input
const file = document.querySelector('input[type=file]').files[0];
const reader = new FileReader();
reader.onload = e => {
  const base64 = e.target.result.split(',')[1]; // supprimer le prefixe data:image/...
  // envoyer base64 dans le champ "image"
};
reader.readAsDataURL(file);
```

**Convertir une image en base64 (Python) :**
```python
import base64
with open('logo.png', 'rb') as f:
    base64_logo = base64.b64encode(f.read()).decode('utf-8')
```

**Conseils pour un bon rendu :**
- Utiliser un logo en **noir et blanc** ou avec fort contraste
- Format **PNG avec fond transparent** : ideal (le fond devient blanc automatiquement)
- Largeur recommandee : **200-300px** pour 58mm, **300-500px** pour 80mm
- Eviter les logos trop fins (traits fins peuvent disparaitre apres conversion 1-bit)

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
3. Sinon elle apparaitra via `/bluetooth/ports` comme port COM

### Le service ne demarre pas apres installation

```bash
python service.py debug
```
Lance l'API en mode visible pour voir l'erreur exacte.

### Coupe papier decalee (coupe le recu suivant)

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

### Dependances manquantes

```bash
pip install -r requirements.txt
```
