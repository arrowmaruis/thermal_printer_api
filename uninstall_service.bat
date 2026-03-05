@echo off
chcp 65001 > nul
title Desinstallation - Thermal Printer API Service

echo.
echo  ============================================
echo   Thermal Printer API - Desinstallation
echo  ============================================
echo.

:: Verifier les droits administrateur
net session > nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERREUR] Ce script doit etre lance en tant qu'Administrateur.
    echo.
    pause
    exit /b 1
)

echo  Arret du service...
net stop "ThermalPrinterAPI" > nul 2>&1

echo  Suppression du service...
sc delete "ThermalPrinterAPI"

if %errorlevel% == 0 (
    echo.
    echo  Service supprime avec succes.
    echo  L'API ne demarrera plus automatiquement.
    echo.
    echo  Pour reinstaller : install_service.bat (admin)
) else (
    echo.
    echo  Le service n'etait pas installe ou deja supprime.
)

echo.
pause
