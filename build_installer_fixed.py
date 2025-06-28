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
    """Créer le script d'installation Windows"""
    installer_script = '''@echo off
title Installation NTP Monitor Enterprise
cls

echo ==========================================
echo    Installation NTP Monitor Enterprise
echo ==========================================
echo.

:: Créer le répertoire d'installation
set INSTALL_DIR=%ProgramFiles%\\NTP Monitor Enterprise
echo Creation du repertoire: %INSTALL_DIR%
mkdir "%INSTALL_DIR%" 2>nul

:: Copier les fichiers
echo Copie de l'application...
copy "NTP_Monitor_Enterprise.exe" "%INSTALL_DIR%\\" >nul

:: Créer raccourci bureau
echo Creation du raccourci sur le bureau...
set DESKTOP=%USERPROFILE%\\Desktop
echo @echo off > "%DESKTOP%\\NTP Monitor Enterprise.bat"
echo cd /d "%INSTALL_DIR%" >> "%DESKTOP%\\NTP Monitor Enterprise.bat"
echo start NTP_Monitor_Enterprise.exe >> "%DESKTOP%\\NTP Monitor Enterprise.bat"

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
'''
    
    with open('installer/dist/INSTALLER.bat', 'w', encoding='utf-8') as f:
        f.write(installer_script)
    
    print("✅ Script d'installation créé")

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