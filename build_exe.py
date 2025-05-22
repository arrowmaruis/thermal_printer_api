"""
Module d'entrée pour l'exécutable PyInstaller.
Sert de point d'entrée à l'application.
"""

import sys
import os

# Ajouter le répertoire parent au chemin Python si nécessaire
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

def main():
    """Fonction principale appelée par l'exécutable."""
    from main import main as app_main
    app_main()

if __name__ == "__main__":
    main()