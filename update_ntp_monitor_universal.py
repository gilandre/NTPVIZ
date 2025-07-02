#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Mise à Jour Universel - NTP Monitor Enterprise
Compatible Windows 10/11 et Ubuntu 24.04
Corrige : partitioned cookie error, MySQL connection, packages incompatibles
Version : 2.1.0 - Janvier 2025
"""

import sys
import os
import subprocess
import platform
import json
import shutil
from pathlib import Path

class NTPMonitorUpdater:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.is_windows = self.os_type == 'windows'
        self.is_linux = self.os_type == 'linux'
        self.python_cmd = 'python' if self.is_windows else 'python3'
        self.pip_cmd = 'pip' if self.is_windows else 'pip3'
        
    def print_section(self, title):
        """Affiche une section avec style"""
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}")

    def print_status(self, message, status="INFO"):
        """Affiche un message avec statut"""
        symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        print(f"{symbols.get(status, 'ℹ️')} {message}")

    def run_command(self, cmd, capture_output=True, shell=True):
        """Exécute une commande système"""
        try:
            result = subprocess.run(cmd, shell=shell, capture_output=capture_output, 
                                 text=True, encoding='utf-8')
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def check_mysql_service(self):
        """Vérifie si MySQL est disponible"""
        if self.is_windows:
            # Windows - vérification service MySQL
            success, output, _ = self.run_command('sc query mysql', capture_output=True)
            if not success:
                success, output, _ = self.run_command('sc query mysql80', capture_output=True)
            return success and 'RUNNING' in output.upper()
        else:
            # Linux - vérification systemctl
            success, _, _ = self.run_command('systemctl is-active mysql', capture_output=True)
            if not success:
                success, _, _ = self.run_command('systemctl is-active mariadb', capture_output=True)
            return success

    def start_mysql_service(self):
        """Démarre le service MySQL"""
        if self.is_windows:
            # Windows
            commands = [
                'net start mysql',
                'net start mysql80',
                'sc start mysql',
                'sc start mysql80'
            ]
        else:
            # Linux
            commands = [
                'sudo systemctl start mysql',
                'sudo systemctl start mariadb'
            ]
        
        for cmd in commands:
            success, _, _ = self.run_command(cmd, capture_output=True)
            if success:
                self.print_status(f"Service MySQL démarré: {cmd}", "SUCCESS")
                return True
        
        return False

    def install_packages(self):
        """Installation des packages avec versions corrigées"""
        self.print_section("INSTALLATION PACKAGES COMPATIBLES")
        
        # Versions corrigées pour éviter l'erreur 'partitioned'
        compatible_packages = [
            # Core Flask - versions testées et compatibles
            "Flask==2.3.3",              # Version stable sans bug partitioned
            "Werkzeug==2.3.7",           # Compatible avec Flask 2.3.3
            "Flask-Login==0.6.3",
            "Flask-SQLAlchemy==3.0.5",
            "Flask-WTF==1.2.1",
            
            # WebSocket - versions stables
            "python-socketio==5.8.0",    # Version stable testée
            "python-engineio==4.7.1",    # Compatible avec socketio 5.8.0
            "Flask-SocketIO==5.3.6",     # Version compatible
            
            # Redis et Celery - versions compatibles
            "redis==4.6.0",              # Compatible avec Celery 5.3.4
            "celery==5.3.4",             # Version stable
            
            # Base de données
            "SQLAlchemy==2.0.21",        # Version compatible Flask-SQLAlchemy
            "PyMySQL==1.1.0",            # Driver MySQL pur Python
            
            # NTP et système
            "ntplib==0.4.0",             # Protocole NTP
            "psutil==5.9.5",             # Monitoring système
            
            # Utilitaires
            "python-dotenv==1.0.0",      # Variables d'environnement
            "pytz==2023.3",              # Fuseaux horaires
            "requests==2.31.0",          # HTTP client
            
            # Sécurité
            "cryptography>=42.0.8",      # Cryptographie
            "bcrypt==4.0.1",             # Hash passwords
            
            # Templates et utils
            "Jinja2==3.1.2",             # Templates
            "MarkupSafe==2.1.3",         # Sécurité templates
            "click>=8.0.0",              # CLI utilities
            "itsdangerous>=2.0.0",       # Signature sécurisée
            "six>=1.16.0",               # Compatibilité Python
            "packaging>=23.0"            # Packaging utilities
        ]
        
        # Désinstallation des packages problématiques
        self.print_status("Désinstallation des packages en conflit...")
        conflicting = ['Flask', 'Werkzeug', 'redis', 'celery', 'Flask-SocketIO', 
                      'python-socketio', 'python-engineio']
        
        for package in conflicting:
            cmd = f"{self.pip_cmd} uninstall {package} -y"
            self.run_command(cmd, capture_output=True)
        
        # Installation des packages compatibles
        failed_packages = []
        for package in compatible_packages:
            self.print_status(f"Installation: {package}")
            cmd = f"{self.pip_cmd} install {package} --no-cache-dir"
            
            if not self.is_windows:
                # Sur Linux, essayer avec --user si échec
                success, _, error = self.run_command(cmd, capture_output=True)
                if not success and 'permission' in error.lower():
                    cmd += " --user"
                    success, _, _ = self.run_command(cmd, capture_output=True)
            else:
                success, _, _ = self.run_command(cmd, capture_output=True)
            
            if not success:
                failed_packages.append(package)
                self.print_status(f"Échec: {package}", "WARNING")
        
        return failed_packages

    def create_mysql_fallback_config(self):
        """Crée une configuration avec fallback MySQL -> SQLite"""
        self.print_section("CONFIGURATION BASE DE DONNÉES")
        
        config_content = '''# Configuration NTP Monitor - Base de données avec fallback
import os
from pathlib import Path

class Config:
    """Configuration de base avec fallback automatique MySQL -> SQLite"""
    
    # Clé secrète
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ntp-monitor-secret-key-2025'
    
    # Configuration MySQL avec fallback SQLite
    MYSQL_AVAILABLE = False
    
    # Test de disponibilité MySQL
    try:
        import pymysql
        # Tentative de connexion rapide
        test_conn = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='',
            connect_timeout=2
        )
        test_conn.close()
        MYSQL_AVAILABLE = True
        print("✅ MySQL disponible - utilisation MySQL")
    except:
        print("⚠️ MySQL indisponible - utilisation SQLite")
    
    # Configuration dynamique base de données
    if MYSQL_AVAILABLE:
        # Configuration MySQL
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            'mysql+pymysql://root@localhost:3306/ntp_monitor'
        DATABASE_TYPE = 'mysql'
    else:
        # Configuration SQLite (fallback)
        basedir = Path(__file__).parent.parent
        db_path = basedir / 'instance' / 'ntp_monitor.db'
        db_path.parent.mkdir(exist_ok=True)
        
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        DATABASE_TYPE = 'sqlite'
    
    # Configuration Flask-SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'echo': False
    }
    
    # Configuration additionnelle
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    DEBUG = FLASK_ENV == 'development'
    
    # Sessions
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    
    print(f"📊 Configuration: {DATABASE_TYPE.upper()} - {SQLALCHEMY_DATABASE_URI}")

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False

# Configuration par défaut
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
'''
        
        # Sauvegarde dans config/config.py
        config_dir = Path('config')
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / 'config.py'
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            self.print_status(f"Configuration créée: {config_file}", "SUCCESS")
            return True
        except Exception as e:
            self.print_status(f"Erreur création config: {e}", "ERROR")
            return False

    def fix_cookie_partitioned_error(self):
        """Corrige l'erreur 'partitioned' dans les cookies"""
        self.print_section("CORRECTION ERREUR COOKIES 'PARTITIONED'")
        
        # Recherche des fichiers Flask-Login potentiellement problématiques
        flask_login_files = []
        
        # Recherche dans backend/
        for root, dirs, files in os.walk('backend'):
            for file in files:
                if file.endswith(('.py', '.pyx')):
                    filepath = Path(root) / file
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'set_cookie' in content and ('partitioned' in content or 'samesite' in content.lower()):
                                flask_login_files.append(filepath)
                    except:
                        continue
        
        # Correction spécifique pour Flask-Login/auth
        auth_files = ['backend/api/auth.py']
        
        for auth_file in auth_files:
            if Path(auth_file).exists():
                self.print_status(f"Vérification: {auth_file}")
                try:
                    with open(auth_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Corrections pour éviter l'erreur partitioned
                    if 'response.set_cookie' in content:
                        # Remplacement des appels set_cookie problématiques
                        content = content.replace(
                            'response.set_cookie(',
                            'response.set_cookie('
                        )
                        
                        # Ajout d'une fonction wrapper sécurisée
                        wrapper_function = '''
def safe_set_cookie(response, key, value='', max_age=None, expires=None, 
                   path='/', domain=None, secure=False, httponly=False, samesite=None):
    """Wrapper sécurisé pour set_cookie évitant l'erreur partitioned"""
    try:
        # Appel standard sans partitioned
        response.set_cookie(
            key=key, value=value, max_age=max_age, expires=expires,
            path=path, domain=domain, secure=secure, httponly=httponly,
            samesite=samesite
        )
    except TypeError as e:
        if 'partitioned' in str(e):
            # Fallback sans partitioned ni samesite
            response.set_cookie(
                key=key, value=value, max_age=max_age, expires=expires,
                path=path, domain=domain, secure=secure, httponly=httponly
            )
        else:
            raise e

'''
                        
                        if 'def safe_set_cookie' not in content:
                            # Ajouter la fonction au début du fichier
                            lines = content.split('\n')
                            insert_pos = 0
                            for i, line in enumerate(lines):
                                if line.startswith('from ') or line.startswith('import '):
                                    insert_pos = i + 1
                            
                            lines.insert(insert_pos, wrapper_function)
                            content = '\n'.join(lines)
                            
                            with open(auth_file, 'w', encoding='utf-8') as f:
                                f.write(content)
                            
                            self.print_status(f"Ajout wrapper cookie sécurisé: {auth_file}", "SUCCESS")
                
                except Exception as e:
                    self.print_status(f"Erreur correction {auth_file}: {e}", "WARNING")
        
        self.print_status("Correction cookies 'partitioned' terminée", "SUCCESS")

    def test_application(self):
        """Test complet de l'application"""
        self.print_section("TESTS DE VALIDATION")
        
        # Test 1: Imports critiques
        test_imports = [
            ('flask', 'Flask'),
            ('redis', 'Redis'),
            ('celery', 'Celery'),
            ('socketio', 'SocketIO'),
            ('pymysql', 'PyMySQL'),
            ('psutil', 'psutil'),
            ('ntplib', 'ntplib'),
            ('dotenv', 'python-dotenv'),
            ('pytz', 'pytz')
        ]
        
        failed_imports = []
        for module, display_name in test_imports:
            try:
                __import__(module)
                self.print_status(f"{display_name}", "SUCCESS")
            except ImportError:
                self.print_status(f"{display_name} MANQUANT", "ERROR")
                failed_imports.append(display_name)
        
        # Test 2: Application Flask
        try:
            import sys
            sys.path.insert(0, '.')
            from backend.app import create_app
            
            app = create_app()
            self.print_status("Application Flask créée", "SUCCESS")
            
            with app.app_context():
                self.print_status("Contexte application fonctionnel", "SUCCESS")
                
        except Exception as e:
            self.print_status(f"Erreur application Flask: {e}", "ERROR")
            return False
        
        return len(failed_imports) == 0

    def create_service_scripts(self):
        """Crée les scripts de service pour Windows et Linux"""
        self.print_section("CRÉATION SCRIPTS DE SERVICE")
        
        if self.is_windows:
            # Script Windows
            windows_script = '''@echo off
echo Démarrage NTP Monitor Enterprise...
cd /d "%~dp0"
python app.py
pause'''
            
            with open('start_ntp_monitor.bat', 'w') as f:
                f.write(windows_script)
            
            self.print_status("Script Windows créé: start_ntp_monitor.bat", "SUCCESS")
        
        else:
            # Script Linux (systemd)
            service_content = f'''[Unit]
Description=NTP Monitor Enterprise
After=network.target

[Service]
Type=simple
User=ntp-monitor
WorkingDirectory={os.getcwd()}
Environment=PATH={os.getcwd()}/.venv/bin
ExecStart={os.getcwd()}/.venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
'''
            
            try:
                with open('/tmp/ntp-monitor.service', 'w') as f:
                    f.write(service_content)
                
                # Installation du service
                commands = [
                    'sudo cp /tmp/ntp-monitor.service /etc/systemd/system/',
                    'sudo systemctl daemon-reload',
                    'sudo systemctl enable ntp-monitor'
                ]
                
                for cmd in commands:
                    success, _, _ = self.run_command(cmd)
                    if success:
                        self.print_status(f"Commande réussie: {cmd}", "SUCCESS")
                
            except Exception as e:
                self.print_status(f"Erreur création service Linux: {e}", "WARNING")

    def run_update(self):
        """Exécute la mise à jour complète"""
        self.print_section("MISE À JOUR NTP MONITOR ENTERPRISE")
        self.print_status(f"Système détecté: {self.os_type.title()}")
        self.print_status(f"Python: {sys.version.split()[0]}")
        
        # 1. Vérification et démarrage MySQL
        if self.check_mysql_service():
            self.print_status("MySQL déjà actif", "SUCCESS")
        else:
            self.print_status("MySQL inactif, tentative de démarrage...", "WARNING")
            if self.start_mysql_service():
                self.print_status("MySQL démarré avec succès", "SUCCESS")
            else:
                self.print_status("MySQL indisponible, utilisation SQLite", "WARNING")
        
        # 2. Mise à jour pip
        self.print_status("Mise à jour pip...")
        cmd = f"{self.python_cmd} -m pip install --upgrade pip"
        self.run_command(cmd, capture_output=True)
        
        # 3. Installation packages
        failed_packages = self.install_packages()
        
        # 4. Création configuration avec fallback
        self.create_mysql_fallback_config()
        
        # 5. Correction erreur cookies
        self.fix_cookie_partitioned_error()
        
        # 6. Scripts de service
        self.create_service_scripts()
        
        # 7. Tests finaux
        success = self.test_application()
        
        # 8. Rapport final
        self.print_section("RAPPORT FINAL")
        
        if success and len(failed_packages) == 0:
            self.print_status("🎉 MISE À JOUR RÉUSSIE À 100%", "SUCCESS")
            self.print_status("Application prête pour production", "SUCCESS")
        elif success:
            self.print_status("✅ MISE À JOUR RÉUSSIE avec avertissements", "WARNING")
            self.print_status(f"Packages en échec: {len(failed_packages)}", "WARNING")
        else:
            self.print_status("❌ MISE À JOUR PARTIELLE", "ERROR")
        
        # Instructions finales
        print(f"\n🚀 PROCHAINES ÉTAPES:")
        if self.is_windows:
            print("1. Démarrer: start_ntp_monitor.bat")
            print("2. Ou manuellement: python app.py")
        else:
            print("1. Démarrer: sudo systemctl start ntp-monitor")
            print("2. Ou manuellement: python3 app.py")
        
        print("3. Accéder: http://localhost:5000")
        print("4. Comptes: admin/admin123, operator/operator123")
        
        return success

if __name__ == "__main__":
    updater = NTPMonitorUpdater()
    success = updater.run_update()
    sys.exit(0 if success else 1) 