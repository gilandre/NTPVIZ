@echo off
title Installation NTP Monitor Enterprise
cls
color 0A

echo ==========================================
echo    Installation NTP Monitor Enterprise
echo ==========================================
echo.

:: Vérifier les droits admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [✓] Droits administrateur detectes
) else (
    echo [X] ERREUR: Droits administrateur requis!
    echo     Clic droit sur ce fichier ^> "Executer en tant qu'administrateur"
    echo.
    pause
    exit /B 1
)

:: Définir les chemins
set "INSTALL_DIR=%ProgramFiles%\NTP_Monitor_Enterprise"
set "DESKTOP_PATH=%PUBLIC%\Desktop"
set "USER_DESKTOP=%USERPROFILE%\Desktop"

echo [1/4] Verification de l'executable...
if not exist "NTP_Monitor_Enterprise.exe" (
    echo [X] ERREUR: NTP_Monitor_Enterprise.exe non trouve!
    echo     Assurez-vous que ce script est dans le meme dossier que l'EXE
    pause
    exit /B 1
)
echo [✓] Executable trouve

echo.
echo [2/4] Creation du repertoire d'installation...
echo     Repertoire: %INSTALL_DIR%
if exist "%INSTALL_DIR%" (
    echo [!] Repertoire existe deja, mise a jour...
    rmdir /S /Q "%INSTALL_DIR%" >nul 2>&1
)
mkdir "%INSTALL_DIR%" 2>nul
if exist "%INSTALL_DIR%" (
    echo [✓] Repertoire cree avec succes
) else (
    echo [X] ERREUR: Impossible de creer le repertoire
    pause
    exit /B 1
)

echo.
echo [3/4] Copie de l'application...
copy "NTP_Monitor_Enterprise.exe" "%INSTALL_DIR%\" >nul 2>&1
if exist "%INSTALL_DIR%\NTP_Monitor_Enterprise.exe" (
    echo [✓] Application copiee avec succes
) else (
    echo [X] ERREUR: Echec de la copie
    pause
    exit /B 1
)

echo.
echo [4/4] Creation du raccourci sur le bureau...

:: Créer un script de lancement amélioré
set "LAUNCHER=%INSTALL_DIR%\Start_NTP_Monitor.bat"
echo @echo off > "%LAUNCHER%"
echo title NTP Monitor Enterprise >> "%LAUNCHER%"
echo cd /d "%INSTALL_DIR%" >> "%LAUNCHER%"
echo echo Demarrage de NTP Monitor Enterprise... >> "%LAUNCHER%"
echo echo. >> "%LAUNCHER%"
echo echo Interface web: http://127.0.0.1:5000 >> "%LAUNCHER%"
echo echo Connexion: admin / admin123 >> "%LAUNCHER%"
echo echo. >> "%LAUNCHER%"
echo echo Fermer cette fenetre arretera l'application. >> "%LAUNCHER%"
echo echo. >> "%LAUNCHER%"
echo start /min cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:5000" >> "%LAUNCHER%"
echo NTP_Monitor_Enterprise.exe >> "%LAUNCHER%"

:: Créer raccourci bureau (Public Desktop pour tous les utilisateurs)
set "SHORTCUT_PUBLIC=%DESKTOP_PATH%\NTP Monitor Enterprise.bat"
set "SHORTCUT_USER=%USER_DESKTOP%\NTP Monitor Enterprise.bat"

:: Raccourci public
echo @echo off > "%SHORTCUT_PUBLIC%" 2>nul
if exist "%SHORTCUT_PUBLIC%" (
    echo cd /d "%INSTALL_DIR%" >> "%SHORTCUT_PUBLIC%"
    echo start Start_NTP_Monitor.bat >> "%SHORTCUT_PUBLIC%"
    echo [✓] Raccourci public cree
) else (
    echo [!] Raccourci public non cree (normal sur certains systemes)
)

:: Raccourci utilisateur actuel
echo @echo off > "%SHORTCUT_USER%" 2>nul
if exist "%SHORTCUT_USER%" (
    echo cd /d "%INSTALL_DIR%" >> "%SHORTCUT_USER%"
    echo start Start_NTP_Monitor.bat >> "%SHORTCUT_USER%"
    echo [✓] Raccourci utilisateur cree
) else (
    echo [!] Raccourci utilisateur non cree
)

:: Ajouter au menu Démarrer (optionnel)
set "START_MENU=%ProgramData%\Microsoft\Windows\Start Menu\Programs"
if exist "%START_MENU%" (
    echo @echo off > "%START_MENU%\NTP Monitor Enterprise.bat" 2>nul
    if exist "%START_MENU%\NTP Monitor Enterprise.bat" (
        echo cd /d "%INSTALL_DIR%" >> "%START_MENU%\NTP Monitor Enterprise.bat"
        echo start Start_NTP_Monitor.bat >> "%START_MENU%\NTP Monitor Enterprise.bat"
        echo [✓] Raccourci menu Demarrer cree
    )
)

echo.
echo ==========================================
echo    Installation terminee avec succes!
echo ==========================================
echo.
echo [✓] Application installee dans: 
echo     %INSTALL_DIR%
echo.
echo [✓] Raccourcis crees sur:
if exist "%SHORTCUT_PUBLIC%" echo     - Bureau (tous utilisateurs)
if exist "%SHORTCUT_USER%" echo     - Bureau (utilisateur actuel)
if exist "%START_MENU%\NTP Monitor Enterprise.bat" echo     - Menu Demarrer
echo.
echo ==========================================
echo    INFORMATIONS DE CONNEXION
echo ==========================================
echo.
echo Interface web: http://127.0.0.1:5000
echo Utilisateur:   admin
echo Mot de passe:  admin123
echo.
echo ==========================================
echo    DEMARRAGE
echo ==========================================
echo.
echo Pour demarrer l'application:
echo 1. Double-clic sur le raccourci bureau "NTP Monitor Enterprise"
echo 2. OU ouvrir: %INSTALL_DIR%\Start_NTP_Monitor.bat
echo 3. L'interface web s'ouvrira automatiquement
echo.
echo Note: L'application fonctionne entierement HORS LIGNE
echo       Aucune connexion internet n'est requise!
echo.
color 0F
echo Appuyez sur une touche pour continuer...
pause >nul 