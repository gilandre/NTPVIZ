#!/usr/bin/env python3
"""
Script de build pour créer un installateur EXE de NTP Monitor Enterprise
Créé un exécutable Windows autonome avec toutes les dépendances
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def install_dependencies():
    """Installer les dépendances nécessaires pour le build"""
    print("📦 Installation des dépendances de build...")
    
    dependencies = [
        'pyinstaller',
        'auto-py-to-exe',  # Interface graphique optionnelle
        'cx-freeze'        # Alternative à PyInstaller
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                         check=True, capture_output=True)
            print(f"✅ {dep} installé")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur installation {dep}: {e}")

def create_build_directories():
    """Créer les répertoires nécessaires pour le build"""
    print("📁 Création des répertoires de build...")
    
    directories = [
        'dist',
        'build', 
        'installer',
        'installer/data',
        'installer/resources'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Répertoire {directory} créé")

def copy_application_files():
    """Copier les fichiers de l'application"""
    print("📋 Copie des fichiers de l'application...")
    
    # Répertoires à copier
    source_dirs = [
        'backend',
        'frontend', 
        'config',
        'instance'
    ]
    
    target_dir = Path('installer/data')
    
    for source in source_dirs:
        if os.path.exists(source):
            target = target_dir / source
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
            print(f"✅ {source} → {target}")
    
    # Fichiers individuels
    files_to_copy = [
        'app.py',
        'requirements.txt',
        'README.md',
        'LICENSE'
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, target_dir / file)
            print(f"✅ {file} copié")

def create_main_launcher():
    """Créer le fichier principal de lancement pour PyInstaller"""
    print("🚀 Création du lanceur principal...")
    
    launcher_content = '''
"""
NTP Monitor Enterprise - Lanceur principal pour Windows
Version EXE standalone avec dépendances intégrées
"""

import os
import sys
import multiprocessing
from pathlib import Path

# Configuration pour l'environnement EXE
if getattr(sys, 'frozen', False):
    # Mode EXE - PyInstaller
    application_path = sys._MEIPASS
else:
    # Mode développement
    application_path = os.path.dirname(os.path.abspath(__file__))

# Ajouter le chemin de l'application au Python path
sys.path.insert(0, application_path)

def setup_environment():
    """Configurer l'environnement pour l'application"""
    
    # Variables d'environnement
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'False'
    
    # Répertoire de données
    data_dir = Path.home() / 'NTP_Monitor_Data'
    data_dir.mkdir(exist_ok=True)
    
    # Base de données
    db_file = data_dir / 'ntp_monitor_prod.db'
    os.environ['DATABASE_URL'] = f'sqlite:///{db_file}'
    
    # Logs
    logs_dir = data_dir / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    print(f"📁 Répertoire de données: {data_dir}")
    print(f"🗄️ Base de données: {db_file}")

def start_application():
    """Démarrer l'application NTP Monitor"""
    try:
        print("🌐 Démarrage de NTP Monitor Enterprise...")
        print("📍 Adresse: http://127.0.0.1:5000")
        print("🔑 Connexion: admin / admin123")
        print("❌ Pour arrêter: Ctrl+C dans cette fenêtre")
        print("-" * 50)
        
        # Importer et démarrer l'application
        from app import create_app, socketio
        
        app = create_app('production')
        socketio.run(app, 
                    host='127.0.0.1', 
                    port=5000, 
                    debug=False,
                    use_reloader=False)
                    
    except KeyboardInterrupt:
        print("\\n🛑 Arrêt de NTP Monitor Enterprise")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        input("Appuyez sur Entrée pour fermer...")

if __name__ == '__main__':
    multiprocessing.freeze_support()  # Nécessaire pour PyInstaller
    setup_environment()
    start_application()
'''
    
    with open('installer/ntp_monitor_launcher.py', 'w', encoding='utf-8') as f:
        f.write(launcher_content.strip())
    
    print("✅ Lanceur principal créé")

def create_pyinstaller_spec():
    """Créer le fichier .spec pour PyInstaller"""
    print("⚙️ Création du fichier de configuration PyInstaller...")
    
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['ntp_monitor_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data/backend', 'backend'),
        ('data/frontend', 'frontend'),
        ('data/config', 'config'),
        ('data/instance', 'instance'),
        ('data/requirements.txt', '.'),
        ('data/README.md', '.'),
    ],
    hiddenimports=[
        'engineio.async_drivers.threading',
        'socketio',
        'eventlet.hubs.epolls',
        'eventlet.hubs.kqueue', 
        'eventlet.hubs.selects',
        'flask_login',
        'flask_sqlalchemy',
        'flask_migrate',
        'ntplib',
        'email.mime.text',
        'email.mime.multipart',
        'smtplib',
        'sqlite3',
        'threading',
        'multiprocessing',
        'concurrent.futures',
        'datetime',
        'json',
        'requests'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',
    version_file='resources/version_info.txt'
)
'''
    
    with open('installer/ntp_monitor.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content.strip())
    
    print("✅ Fichier .spec créé")

def create_resources():
    """Créer les ressources pour l'installateur"""
    print("🎨 Création des ressources...")
    
    # Version info pour Windows
    version_info = '''
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'NTP Monitor Enterprise'),
         StringStruct(u'FileDescription', u'Monitoring et surveillance de serveurs NTP'),
         StringStruct(u'FileVersion', u'1.0.0.0'),
         StringStruct(u'InternalName', u'ntp_monitor'),
         StringStruct(u'LegalCopyright', u'© 2025 NTP Monitor Enterprise'),
         StringStruct(u'OriginalFilename', u'NTP_Monitor_Enterprise.exe'),
         StringStruct(u'ProductName', u'NTP Monitor Enterprise'),
         StringStruct(u'ProductVersion', u'1.0.0.0')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('installer/resources/version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info.strip())
    
    # Script de démarrage Windows
    startup_script = '''@echo off
title NTP Monitor Enterprise
cls
echo ================================
echo   NTP Monitor Enterprise v1.0
echo ================================
echo.
echo Demarrage de l'application...
echo Adresse: http://127.0.0.1:5000
echo Connexion: admin / admin123
echo.
echo Pour arreter: Fermez cette fenetre ou Ctrl+C
echo.
NTP_Monitor_Enterprise.exe
pause
'''
    
    with open('installer/resources/start_ntp_monitor.bat', 'w', encoding='utf-8') as f:
        f.write(startup_script.strip())
    
    print("✅ Ressources créées")

def build_executable():
    """Construire l'exécutable avec PyInstaller"""
    print("🔨 Construction de l'exécutable...")
    
    os.chdir('installer')
    
    try:
        # Commande PyInstaller
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm', 
            'ntp_monitor.spec'
        ]
        
        subprocess.run(cmd, check=True)
        print("✅ Exécutable créé avec succès!")
        
        # Copier le fichier de démarrage
        shutil.copy2('resources/start_ntp_monitor.bat', 'dist/')
        
        print("📦 Fichiers de distribution:")
        print(f"  - dist/NTP_Monitor_Enterprise.exe")
        print(f"  - dist/start_ntp_monitor.bat")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la construction: {e}")
    
    os.chdir('..')

def create_installer_script():
    """Créer un script d'installation pour Windows"""
    print("📋 Création du script d'installation...")
    
    installer_script = '''
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
set INSTALL_DIR=%ProgramFiles%\\NTP Monitor Enterprise
echo Creation du repertoire: %INSTALL_DIR%
mkdir "%INSTALL_DIR%" 2>nul

:: Copier les fichiers
echo Copie des fichiers...
copy "NTP_Monitor_Enterprise.exe" "%INSTALL_DIR%\\" >nul
copy "start_ntp_monitor.bat" "%INSTALL_DIR%\\" >nul

:: Créer un raccourci sur le bureau
echo Creation du raccourci sur le bureau...
set DESKTOP=%USERPROFILE%\\Desktop
echo @echo off > "%DESKTOP%\\NTP Monitor Enterprise.bat"
echo cd /d "%INSTALL_DIR%" >> "%DESKTOP%\\NTP Monitor Enterprise.bat"
echo start start_ntp_monitor.bat >> "%DESKTOP%\\NTP Monitor Enterprise.bat"

:: Créer un raccourci dans le menu Démarrer
set START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs
mkdir "%START_MENU%\\NTP Monitor Enterprise" 2>nul
copy "%DESKTOP%\\NTP Monitor Enterprise.bat" "%START_MENU%\\NTP Monitor Enterprise\\" >nul

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
'''
    
    with open('installer/dist/INSTALLER.bat', 'w', encoding='utf-8') as f:
        f.write(installer_script.strip())
    
    print("✅ Script d'installation créé")

def main():
    """Fonction principale de build"""
    print("🏗️ CONSTRUCTION DE L'INSTALLATEUR NTP MONITOR ENTERPRISE")
    print("=" * 60)
    
    try:
        install_dependencies()
        create_build_directories()
        copy_application_files()
        create_main_launcher()
        create_pyinstaller_spec()
        create_resources()
        build_executable()
        create_installer_script()
        
        print("\n" + "=" * 60)
        print("✅ CONSTRUCTION TERMINÉE AVEC SUCCÈS!")
        print("=" * 60)
        print("\n📦 FICHIERS CRÉÉS:")
        print("  installer/dist/NTP_Monitor_Enterprise.exe  - Application principale")
        print("  installer/dist/start_ntp_monitor.bat       - Script de démarrage")
        print("  installer/dist/INSTALLER.bat               - Installateur Windows")
        print("\n🚀 POUR INSTALLER SUR UNE MACHINE WINDOWS 11:")
        print("  1. Copiez le dossier 'installer/dist' sur la machine cible")
        print("  2. Exécutez 'INSTALLER.bat' en tant qu'administrateur")
        print("  3. Lancez l'application via le raccourci créé")
        print("\n🌐 ACCÈS À L'APPLICATION:")
        print("  URL: http://127.0.0.1:5000")
        print("  Login: admin")
        print("  Password: admin123")
        
    except Exception as e:
        print(f"\n❌ ERREUR DURANT LA CONSTRUCTION: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    
    if not success:
        input("\nAppuyez sur Entrée pour fermer...")
        sys.exit(1) 