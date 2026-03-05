@echo off
chcp 65001 > nul
title Installation - Thermal Printer API Service

echo.
echo  ============================================
echo   Thermal Printer API - Installation Service
echo  ============================================
echo.

:: Verifier les droits administrateur
net session > nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERREUR] Ce script doit etre lance en tant qu'Administrateur.
    echo.
    echo  Faites un clic droit sur install_service.bat
    echo  puis choisissez "Executer en tant qu'administrateur"
    echo.
    pause
    exit /b 1
)

:: Trouver Python
set PYTHON=
for %%p in (python python3 py) do (
    %%p --version > nul 2>&1
    if !errorlevel! == 0 (
        set PYTHON=%%p
        goto :found_python
    )
)

:: Chercher Python 3.13 (Microsoft Store)
set STORE_PYTHON=%LOCALAPPDATA%\Microsoft\WindowsApps\python3.13.exe
if exist "%STORE_PYTHON%" (
    set PYTHON="%STORE_PYTHON%"
    goto :found_python
)

echo  [ERREUR] Python introuvable. Installez Python 3.8+
pause
exit /b 1

:found_python
setlocal enabledelayedexpansion
set SCRIPT_DIR=%~dp0
set SERVICE_SCRIPT=%SCRIPT_DIR%service.py

echo  Python trouve : %PYTHON%
echo  Repertoire   : %SCRIPT_DIR%
echo.

:: Installer les dependances si besoin
echo  [1/3] Verification des dependances...
%PYTHON% -m pip install -r "%SCRIPT_DIR%requirements.txt" -q
if %errorlevel% neq 0 (
    echo  [AVERTISSEMENT] Certaines dependances n'ont pas pu etre installees.
)
echo  OK
echo.

:: Supprimer l'ancien service si existant
echo  [2/3] Nettoyage de l'ancienne installation...
sc query "ThermalPrinterAPI" > nul 2>&1
if %errorlevel% == 0 (
    net stop "ThermalPrinterAPI" > nul 2>&1
    sc delete "ThermalPrinterAPI" > nul 2>&1
    timeout /t 2 /nobreak > nul
    echo  Ancien service supprime.
) else (
    echo  Aucun service existant.
)
echo.

:: Installer le nouveau service
echo  [3/3] Installation du service Windows...
%PYTHON% "%SERVICE_SCRIPT%" install
if %errorlevel% neq 0 (
    echo.
    echo  [ERREUR] Installation echouee.
    pause
    exit /b 1
)
echo.

:: Demarrer le service
echo  Demarrage du service...
net start "ThermalPrinterAPI"
if %errorlevel% == 0 (
    echo.
    echo  ============================================
    echo   Installation reussie !
    echo  ============================================
    echo.
    echo   L'API demarre automatiquement avec Windows.
    echo   Accessible sur : http://localhost:5789
    echo.
    echo   Gestion du service :
    echo   - Arreter  : net stop ThermalPrinterAPI
    echo   - Demarrer : net start ThermalPrinterAPI
    echo   - Statut   : sc query ThermalPrinterAPI
    echo   - Supprimer: uninstall_service.bat (admin)
    echo.
) else (
    echo.
    echo  [AVERTISSEMENT] Service installe mais non demarre.
    echo  Verifiez les logs dans le dossier 'logs\'
    echo  ou lancez : python service.py debug
    echo.
)

pause
