@echo off
title Construction NTP Monitor Enterprise EXE
cls

echo ========================================
echo   NTP Monitor Enterprise - Build EXE
echo ========================================
echo.
echo Construction d'un installateur Windows 11 autonome...
echo Toutes les dependances seront integrees dans l'EXE
echo.

:: Vérifier Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERREUR: Python n'est pas installe ou pas dans le PATH
    echo Veuillez installer Python 3.8+ depuis python.org
    pause
    exit /b 1
)

echo Python detecte, construction en cours...
echo.

:: Lancer le script de build
python build_installer.py

echo.
echo Construction terminee!
echo Verifiez le dossier 'installer/dist' pour les fichiers de distribution.
echo.
pause 