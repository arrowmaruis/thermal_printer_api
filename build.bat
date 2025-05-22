@echo off
echo ===== Compilation de Hotelia Impression Thermique =====

echo 1. Nettoyage des anciens builds...
if exist "build" (
    rmdir /s /q "build"
)
if exist "dist" (
    rmdir /s /q "dist"
)

echo 2. Installation du package en mode développement...
pip install -e .

echo 3. Installation des dépendances pour la compilation...
pip install pyinstaller
pip install --upgrade pywin32

echo 4. Compilation avec PyInstaller...
pyinstaller thermal_printer.spec --clean

echo 5. Vérification du build...
if exist "dist\HoteliaImpression\HoteliaImpression.exe" (
    echo Build réussi !
    echo ===== Résultats =====
    echo Exécutable: dist\HoteliaImpression\HoteliaImpression.exe
    echo.
    echo Test de l'exécutable...
    cd dist\HoteliaImpression
    HoteliaImpression.exe --help
    cd ..\..
) else (
    echo ERREUR: Le build a échoué !
    echo Vérifiez les erreurs ci-dessus.
)

pause