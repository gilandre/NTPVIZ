#!/usr/bin/env python3
"""
Script de build corrigé pour NTP Monitor Enterprise
Version simplifiée qui évite les erreurs de dépendances
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_pyinstaller():
    """Vérifier si PyInstaller est installé, sinon l'installer"""
    try:
        import PyInstaller
        print("✅ PyInstaller déjà installé")
        return True
    except ImportError:
        print("📦 Installation de PyInstaller...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], 
                         check=True)
            print("✅ PyInstaller installé avec succès")
            return True
        except subprocess.CalledProcessError:
            print("❌ Échec installation PyInstaller")
            return False

def create_build_directories():
    """Créer les répertoires nécessaires"""
    directories = ['installer', 'installer/data', 'installer/resources']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Répertoire {directory} créé")

def copy_application_files():
    """Copier les fichiers de l'application"""
    print("📋 Copie des fichiers...")
    
    # Répertoires à copier
    source_dirs = ['backend', 'frontend', 'config', 'instance']
    target_dir = Path('installer/data')
    
    for source in source_dirs:
        if os.path.exists(source):
            target = target_dir / source
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
            print(f"✅ {source} → {target}")    
    # Copier les assets vendor (CDN locaux)
    vendor_dirs = ['frontend/static/css/vendor', 'frontend/static/js/vendor', 'frontend/static/fonts']
    for vendor_dir in vendor_dirs:
        if os.path.exists(vendor_dir):
            vendor_target = target_dir / vendor_dir.replace('frontend/', '')
            if vendor_target.exists():
                shutil.rmtree(vendor_target)
            shutil.copytree(vendor_dir, vendor_target)
            print(f"✅ {vendor_dir} → {vendor_target}")
    
    # Fichiers individuels
    files = ['app.py', 'requirements.txt', 'README.md']
    for file in files:
        if os.path.exists(file):
            shutil.copy2(file, target_dir / file)
            print(f"✅ {file} copié")

def create_simple_launcher():
    """Créer un lanceur simple"""
    launcher_content = '''#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Configuration pour EXE
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

# Variables d'environnement
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Répertoire de données utilisateur
data_dir = Path.home() / 'NTP_Monitor_Data'
data_dir.mkdir(exist_ok=True)

# Base de données
db_file = data_dir / 'ntp_monitor_prod.db'
os.environ['DATABASE_URL'] = f'sqlite:///{db_file}'

# Logs
logs_dir = data_dir / 'logs'
logs_dir.mkdir(exist_ok=True)

if __name__ == '__main__':
    try:
        print("🌐 Démarrage de NTP Monitor Enterprise...")
        print("📍 Adresse: http://127.0.0.1:5000")
        print("🔑 Connexion: admin / admin123")
        print("❌ Pour arrêter: Ctrl+C")
        print("-" * 50)
        
        # Importer et démarrer
        from app import app
        app.run(host='127.0.0.1', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\\n🛑 Arrêt de l'application")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        input("Appuyez sur Entrée pour fermer...")
'''
    
    with open('installer/launcher.py', 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    
    print("✅ Lanceur créé")

def create_simple_spec():
    """Créer un fichier .spec simplifié"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data/backend', 'backend'),
        ('data/frontend', 'frontend'),
        ('data/config', 'config'),
        ('data/instance', 'instance'),
        ('data/requirements.txt', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask_login',
        'flask_sqlalchemy',
        'sqlalchemy',
        'sqlite3',
        'ntplib',
        'psutil'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NTP_Monitor_Enterprise',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open('installer/simple.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ Fichier .spec simplifié créé")

def build_exe():
    """Construire l'EXE"""
    print("🔨 Construction de l'exécutable...")
    
    os.chdir('installer')
    
    try:
        cmd = [sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', 'simple.spec']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ EXE créé avec succès!")
            if os.path.exists('dist/NTP_Monitor_Enterprise.exe'):
                print(f"📦 Fichier: installer/dist/NTP_Monitor_Enterprise.exe")
                size = os.path.getsize('dist/NTP_Monitor_Enterprise.exe') // (1024*1024)
                print(f"📏 Taille: ~{size}MB")
                return True
        else:
            print(f"❌ Erreur PyInstaller: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur build: {e}")
        return False
    finally:
        os.chdir('..')

def create_installer_script():
    """Créer le script d'installation"""
    print("✅ Script d'installation créé")
    
    installer_script = """@echo off
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
set "INSTALL_DIR=%ProgramFiles%\\NTP_Monitor_Enterprise"
set "DESKTOP_PATH=%PUBLIC%\\Desktop"
set "USER_DESKTOP=%USERPROFILE%\\Desktop"

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
copy "NTP_Monitor_Enterprise.exe" "%INSTALL_DIR%\\" >nul 2>&1
if exist "%INSTALL_DIR%\\NTP_Monitor_Enterprise.exe" (
    echo [✓] Application copiee avec succes
) else (
    echo [X] ERREUR: Echec de la copie
    pause
    exit /B 1
)

echo.
echo [4/4] Creation du raccourci sur le bureau...

:: Créer un script de lancement amélioré
set "LAUNCHER=%INSTALL_DIR%\\Start_NTP_Monitor.bat"
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
set "SHORTCUT_PUBLIC=%DESKTOP_PATH%\\NTP Monitor Enterprise.bat"
set "SHORTCUT_USER=%USER_DESKTOP%\\NTP Monitor Enterprise.bat"

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
set "START_MENU=%ProgramData%\\Microsoft\\Windows\\Start Menu\\Programs"
if exist "%START_MENU%" (
    echo @echo off > "%START_MENU%\\NTP Monitor Enterprise.bat" 2>nul
    if exist "%START_MENU%\\NTP Monitor Enterprise.bat" (
        echo cd /d "%INSTALL_DIR%" >> "%START_MENU%\\NTP Monitor Enterprise.bat"
        echo start Start_NTP_Monitor.bat >> "%START_MENU%\\NTP Monitor Enterprise.bat"
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
if exist "%START_MENU%\\NTP Monitor Enterprise.bat" echo     - Menu Demarrer
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
echo 2. OU ouvrir: %INSTALL_DIR%\\Start_NTP_Monitor.bat
echo 3. L'interface web s'ouvrira automatiquement
echo.
echo Note: L'application fonctionne entierement HORS LIGNE
echo       Aucune connexion internet n'est requise!
echo.
color 0F
echo Appuyez sur une touche pour continuer...
pause >nul
"""
    
    # Écrire le script d'installation
    with open('installer/dist/INSTALLER.bat', 'w', encoding='cp1252') as f:
        f.write(installer_script)

def main():
    """Fonction principale"""
    print("🏗️ BUILD EXE SIMPLIFIÉ - NTP MONITOR ENTERPRISE")
    print("=" * 60)
    
    # Vérifications
    if not check_pyinstaller():
        print("❌ PyInstaller requis pour continuer")
        return False
    
    # Étapes de build
    create_build_directories()
    copy_application_files() 
    create_simple_launcher()
    create_simple_spec()
    
    # Construction
    if build_exe():
        create_installer_script()
        
        print("\n" + "=" * 60)
        print("✅ BUILD TERMINÉ AVEC SUCCÈS!")
        print("=" * 60)
        print("\n📦 FICHIERS CRÉÉS:")
        print("  installer/dist/NTP_Monitor_Enterprise.exe")
        print("  installer/dist/INSTALLER.bat")
        print("\n🚀 POUR INSTALLER:")
        print("  1. Copiez le dossier 'installer/dist' sur la machine cible")
        print("  2. Exécutez 'INSTALLER.bat'")
        print("  3. Utilisez le raccourci créé sur le bureau")
        
        return True
    else:
        print("\n❌ ÉCHEC DU BUILD")
        return False

if __name__ == '__main__':
    success = main()
    if not success:
        input("\nAppuyez sur Entrée pour fermer...")
        sys.exit(1) 