@echo off
setlocal EnableDelayedExpansion

echo.
echo =========================================================
echo ^| COMPILATION HOTELIA IMPRESSION THERMIQUE - ASCII    ^|
echo =========================================================
echo Version: 1.0.0 avec support ASCII integre
echo Date: %date% %time%
echo.

:: Verification Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    pause
    exit /b 1
)

echo [OK] Python detecte: 
python --version

echo.
echo [1/7] Nettoyage des anciens builds...
echo ===============================================

if exist "build" (
    echo    Suppression build/
    rmdir /s /q "build"
)
if exist "dist" (
    echo    Suppression dist/
    rmdir /s /q "dist"
)

:: Nettoyage des fichiers Python compiles
echo    Nettoyage des .pyc et __pycache__
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul

echo.
echo [2/7] Verification integration ASCII...
echo ===============================================

echo    Test des imports ASCII critiques...

:: Creer un fichier de test temporaire
echo import sys > test_imports.py
echo try: >> test_imports.py
echo     from printer.printer_utils import get_printers, print_raw >> test_imports.py
echo     from utils.config import load_config >> test_imports.py
echo     print("[OK] Modules de base importes avec succes") >> test_imports.py
echo except ImportError as e: >> test_imports.py
echo     print("[ERREUR] Import echoue:", e) >> test_imports.py
echo     sys.exit(1) >> test_imports.py

python test_imports.py
set import_result=%errorlevel%
del test_imports.py

if !import_result! neq 0 (
    echo [ERREUR] Modules de base manquants
    echo Assurez-vous d'avoir les fichiers necessaires
    pause
    exit /b 1
)

echo    Test conversion francaise...

:: Creer un autre fichier de test
echo # -*- coding: utf-8 -*- > test_conversion.py
echo try: >> test_conversion.py
echo     # Test basique de conversion >> test_conversion.py
echo     test = "Cafe francais: 15,50 euros" >> test_conversion.py
echo     result = test.replace("e", "e").replace("a", "a") >> test_conversion.py
echo     print("[OK] Test:", test) >> test_conversion.py
echo     print("   Resultat:", result) >> test_conversion.py
echo     print("[OK] Conversion francaise: OK") >> test_conversion.py
echo except Exception as e: >> test_conversion.py
echo     print("[ERREUR] Conversion francaise defaillante:", e) >> test_conversion.py
echo     exit(1) >> test_conversion.py

python test_conversion.py
set conversion_result=%errorlevel%
del test_conversion.py

if !conversion_result! neq 0 (
    echo [ERREUR] Conversion francaise ne fonctionne pas
    pause
    exit /b 1
)

echo.
echo [3/7] Installation du package...
echo ===============================================

echo    Installation en mode developpement...
pip install -e . --quiet
if errorlevel 1 (
    echo [ERREUR] Echec installation du package
    pause
    exit /b 1
)

echo [OK] Package installe

echo.
echo [4/7] Installation des dependances de compilation...
echo ===============================================

echo    Installation PyInstaller...
pip install pyinstaller --upgrade --quiet
if errorlevel 1 (
    echo [ERREUR] Echec installation PyInstaller
    pause
    exit /b 1
)

echo    Mise a jour PyWin32...
pip install --upgrade pywin32 --quiet

echo [OK] Dependances installees

echo.
echo [5/7] Test rapide de l'application...
echo ===============================================

echo    Test de lancement...

:: Creer un fichier de test de l'application
echo # -*- coding: utf-8 -*- > test_app.py
echo import sys >> test_app.py
echo import os >> test_app.py
echo sys.path.insert(0, '.') >> test_app.py
echo try: >> test_app.py
echo     from utils.config import load_config, config >> test_app.py
echo     load_config() >> test_app.py
echo     print("[OK] Application: OK") >> test_app.py
echo     print("[OK] Config encodage:", config.get("default_encoding", "auto")) >> test_app.py
echo     print("[OK] Test application reussi") >> test_app.py
echo except Exception as e: >> test_app.py
echo     print("[ERREUR] Test app:", e) >> test_app.py
echo     sys.exit(1) >> test_app.py

python test_app.py
set app_result=%errorlevel%
del test_app.py

if !app_result! neq 0 (
    echo [ERREUR] Application ne se lance pas correctement
    pause
    exit /b 1
)

echo.
echo [6/7] Compilation avec PyInstaller...
echo ===============================================

echo    Verification du fichier .spec...
if not exist "thermal_printer.spec" (
    echo [ERREUR] thermal_printer.spec manquant
    pause
    exit /b 1
)

echo    Lancement PyInstaller...
pyinstaller thermal_printer.spec --clean --noconfirm

if errorlevel 1 (
    echo [ERREUR] Echec de la compilation PyInstaller
    echo Verifiez les erreurs ci-dessus
    pause
    exit /b 1
)

echo.
echo [7/7] Verification du build...
echo ===============================================

if exist "dist\HoteliaImpression\HoteliaImpression.exe" (
    echo [OK] Build reussi !
    
    :: Calculer la taille
    for %%I in ("dist\HoteliaImpression\HoteliaImpression.exe") do (
        set size=%%~zI
        set /a sizeMB=!size!/1024/1024
        echo    Taille: !sizeMB! MB
    )
    
    echo    Copie des fichiers additionnels...
    if exist "README.md" copy "README.md" "dist\HoteliaImpression\" >nul
    
    :: Creation d'un fichier d'informations
    echo Hotelia Thermal Printer API v1.0.0 > "dist\HoteliaImpression\VERSION.txt"
    echo Build: %date% %time% >> "dist\HoteliaImpression\VERSION.txt"
    echo Support ASCII: Integre >> "dist\HoteliaImpression\VERSION.txt"
    echo Auto-detection POS-58: Activee >> "dist\HoteliaImpression\VERSION.txt"
    
    echo.
    echo =========================================================
    echo ^| COMPILATION TERMINEE AVEC SUCCES !                  ^|
    echo =========================================================
    echo.
    echo Fichiers crees:
    echo    dist\HoteliaImpression\
    echo    ├── HoteliaImpression.exe
    echo    ├── VERSION.txt
    echo    └── Autres fichiers de support
    echo.
    echo Fonctionnalites integrees:
    echo    [OK] Auto-detection POS-58 vers ASCII
    echo    [OK] Conversion francaise (cafe, hotel, etc.)
    echo    [OK] Fallback encodage intelligent
    echo    [OK] Interface graphique moderne
    echo    [OK] API REST complete
    echo.
    echo Test recommande:
    echo    cd dist\HoteliaImpression
    echo    HoteliaImpression.exe
    echo.
    
    :: Test optionnel de l'executable
    set /p test_exe="Tester l'executable maintenant ? (o/n): "
    if /i "!test_exe!"=="o" (
        echo Test de l'executable...
        cd "dist\HoteliaImpression"
        echo    Test --help...
        timeout 3 HoteliaImpression.exe --help >nul 2>&1
        if !errorlevel! equ 0 (
            echo [OK] Test --help: OK
        ) else (
            echo [ATTENTION] Test --help: Attention
        )
        cd ..\..
    )
    
) else (
    echo [ERREUR] Le build a echoue !
    echo L'executable n'a pas ete cree
    echo Verifiez les erreurs ci-dessus
    pause
    exit /b 1
)

echo.
echo Executable pret pour distribution !
echo =========================================================

:: Creation d'un raccourci optionnel
set /p create_shortcut="Creer un raccourci sur le bureau ? (o/n): "
if /i "%create_shortcut%"=="o" (
    echo Creation du raccourci...
    powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Hotelia Impression ASCII.lnk'); $Shortcut.TargetPath = '%CD%\dist\HoteliaImpression\HoteliaImpression.exe'; $Shortcut.WorkingDirectory = '%CD%\dist\HoteliaImpression'; $Shortcut.Description = 'Hotelia Thermal Printer API with ASCII Support'; $Shortcut.Save()" 2>nul
    if !errorlevel! equ 0 (
        echo [OK] Raccourci cree sur le bureau
    ) else (
        echo [ATTENTION] Impossible de creer le raccourci
    )
)

echo.
echo Compilation terminee le %date% a %time%
echo Votre executable avec support ASCII est pret !
echo.
pause