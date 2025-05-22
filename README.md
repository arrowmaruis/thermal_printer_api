# Thermal Printer API

API d'impression thermique avec interface graphique pour la gestion d'imprimantes thermiques (58mm et 80mm).

## Fonctionnalités

- 🖨️ **Support multi-largeurs**: Détection automatique des imprimantes 58mm et 80mm
- 🔤 **Gestion des encodages**: Support UTF-8, CP850, CP437, ASCII avec détection automatique
- 🖥️ **Interface graphique moderne**: Tableau de bord pour configuration et test
- 🌐 **API REST**: Endpoints pour impression depuis applications web
- 📄 **Formats de reçus**: Standard, hôtel, mixte avec formatage automatique
- ⚙️ **Configuration automatique**: Détection et configuration automatique des imprimantes

## Installation

### Prérequis
- Windows 10/11
- Python 3.8+
- Imprimante thermique compatible ESC/POS

### Installation rapide
```bash
# Cloner le repository
git clone https://github.com/arrowmaruis/thermal_printer_api.git
cd thermal_printer_api

# Installer les dépendances
pip install -e .

# Lancer l'application
python main.py