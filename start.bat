@echo off
chcp 65001 > nul
title Thermal Printer API

echo.
echo  ============================================
echo   Thermal Printer API - Hotelia
echo  ============================================
echo.
echo   [1] Lancer manuellement (cette fenetre)
echo   [2] Installer comme service Windows (admin)
echo   [3] Demarrer le service (si installe)
echo   [4] Arreter le service
echo   [5] Statut du service
echo   [6] Quitter
echo.
set /p choix="Votre choix : "

if "%choix%"=="1" goto :manual
if "%choix%"=="2" goto :install
if "%choix%"=="3" goto :start_svc
if "%choix%"=="4" goto :stop_svc
if "%choix%"=="5" goto :status
if "%choix%"=="6" exit /b 0
goto :manual

:manual
echo.
echo  Lancement manuel (Ctrl+C pour arreter)...
echo  API disponible sur http://localhost:5789
echo.
"C:\Users\ASUS GAMER\AppData\Local\Microsoft\WindowsApps\python3.13.exe" "%~dp0main.py"
pause
exit /b 0

:install
echo.
echo  Ouverture de l'installation du service (droits admin requis)...
powershell -Command "Start-Process '%~dp0install_service.bat' -Verb RunAs"
exit /b 0

:start_svc
echo.
net start "ThermalPrinterAPI"
echo.
pause
exit /b 0

:stop_svc
echo.
net stop "ThermalPrinterAPI"
echo.
pause
exit /b 0

:status
echo.
sc query "ThermalPrinterAPI" | findstr "STATE"
echo.
pause
exit /b 0
