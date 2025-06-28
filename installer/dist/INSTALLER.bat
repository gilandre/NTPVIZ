@echo off
title Installation NTP Monitor Enterprise
cls

echo ==========================================
echo    Installation NTP Monitor Enterprise
echo ==========================================
echo.

:: Créer le répertoire d'installation
set INSTALL_DIR=%ProgramFiles%\NTP Monitor Enterprise
echo Creation du repertoire: %INSTALL_DIR%
mkdir "%INSTALL_DIR%" 2>nul

:: Copier les fichiers
echo Copie de l'application...
copy "NTP_Monitor_Enterprise.exe" "%INSTALL_DIR%\" >nul

:: Créer raccourci bureau
echo Creation du raccourci sur le bureau...
set DESKTOP=%USERPROFILE%\Desktop
echo @echo off > "%DESKTOP%\NTP Monitor Enterprise.bat"
echo cd /d "%INSTALL_DIR%" >> "%DESKTOP%\NTP Monitor Enterprise.bat"
echo start NTP_Monitor_Enterprise.exe >> "%DESKTOP%\NTP Monitor Enterprise.bat"

echo.
echo ==========================================
echo    Installation terminee avec succes!
echo ==========================================
echo.
echo L'application sera accessible via:
echo - Raccourci sur le bureau
echo - Dossier: %INSTALL_DIR%
echo.
echo Pour demarrer: Double-clic sur le raccourci
echo Adresse web: http://127.0.0.1:5000
echo Connexion: admin / admin123
echo.
pause
