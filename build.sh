#!/bin/bash
echo "===== Compilation de Hotelia Impression Thermique ====="

echo "1. Nettoyage des anciens builds..."
rm -rf build/
rm -rf dist/

echo "2. Installation du package en mode développement..."
pip install -e .

echo "3. Installation des dépendances pour la compilation..."
pip install pyinstaller

echo "4. Compilation avec PyInstaller..."
pyinstaller thermal_printer.spec --clean

echo "5. Vérification du build..."
if [ -f "dist/HoteliaImpression/HoteliaImpression" ]; then
    echo "Build réussi !"
    echo "===== Résultats ====="
    echo "Exécutable: dist/HoteliaImpression/HoteliaImpression"
    
    echo "Test de l'exécutable..."
    cd dist/HoteliaImpression
    ./HoteliaImpression --help
    cd ../..
else
    echo "ERREUR: Le build a échoué !"
    echo "Vérifiez les erreurs ci-dessus."
fi