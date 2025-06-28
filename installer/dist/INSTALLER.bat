@echo off
title Installation NTP Monitor Enterprise
cls

echo ========================================
echo   Installation NTP Monitor Enterprise
echo ========================================
echo.

:: Vérifier les privilèges administrateur
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Privileges administrateur detectes.
) else (
    echo ATTENTION: Certaines fonctionnalites necessitent des privileges administrateur.
    echo Vous pouvez continuer sans, mais l'installation sera limitee.
    echo.
)

:: Créer le répertoire d'installation
set INSTALL_DIR=%ProgramFiles%\NTP Monitor Enterprise
echo Creation du repertoire: %INSTALL_DIR%
mkdir "%INSTALL_DIR%" 2>nul

:: Copier les fichiers
echo Copie des fichiers...
copy "NTP_Monitor_Enterprise.exe" "%INSTALL_DIR%\" >nul
copy "start_ntp_monitor.bat" "%INSTALL_DIR%\" >nul

:: Créer un raccourci sur le bureau
echo Creation du raccourci sur le bureau...
set DESKTOP=%USERPROFILE%\Desktop
echo @echo off > "%DESKTOP%\NTP Monitor Enterprise.bat"
echo cd /d "%INSTALL_DIR%" >> "%DESKTOP%\NTP Monitor Enterprise.bat"
echo start start_ntp_monitor.bat >> "%DESKTOP%\NTP Monitor Enterprise.bat"

:: Créer un raccourci dans le menu Démarrer
set START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs
mkdir "%START_MENU%\NTP Monitor Enterprise" 2>nul
copy "%DESKTOP%\NTP Monitor Enterprise.bat" "%START_MENU%\NTP Monitor Enterprise\" >nul

echo.
echo ========================================
echo   Installation terminee avec succes!
echo ========================================
echo.
echo L'application a ete installee dans:
echo %INSTALL_DIR%
echo.
echo Raccourcis crees:
echo - Bureau: NTP Monitor Enterprise.bat
echo - Menu Demarrer: NTP Monitor Enterprise
echo.
echo Pour demarrer l'application:
echo 1. Double-cliquez sur le raccourci du bureau OU
echo 2. Cherchez "NTP Monitor" dans le menu Demarrer
echo.
echo Adresse web: http://127.0.0.1:5000
echo Connexion: admin / admin123
echo.
pause