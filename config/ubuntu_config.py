"""
Configuration spécifique pour Ubuntu 24.04
Optimisée pour le déploiement en production
"""

import os
from pathlib import Path

class UbuntuConfig:
    """Configuration pour Ubuntu 24.04"""
    
    # Clé secrète pour Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ntp-monitor-ubuntu-2025')
    
    # Configuration de la base de données
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'ntp_user')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'NTP_Monitor_2025!')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'ntp_monitor')
    
    # Test de connexion MySQL avec fallback SQLite
    try:
        import pymysql
        pymysql.connect(
            host=MYSQL_HOST, 
            port=MYSQL_PORT, 
            user=MYSQL_USER, 
            password=MYSQL_PASSWORD, 
            database=MYSQL_DATABASE,
            connect_timeout=5
        ).close()
        
        SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
        print(f"✅ MySQL utilisé: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
        
    except Exception as e:
        print(f"⚠️ MySQL non disponible ({e}), utilisation de SQLite")
        # Fallback SQLite
        db_path = Path(__file__).parent.parent / 'instance' / 'ntp_monitor.db'
        db_path.parent.mkdir(exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    
    # Configuration SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }
    
    # Configuration de l'application
    DEBUG = False
    TESTING = False
    
    # Configuration des logs
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', '/var/log/ntp-monitor/app.log')
    
    # Configuration du serveur
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5001))
    
    # Configuration des services NTP pour Ubuntu
    NTP_SERVICES = ['ntpsec', 'ntp', 'chronyd', 'systemd-timesyncd']
    
    # Configuration des alertes
    ALERT_CHECK_INTERVAL = int(os.environ.get('ALERT_CHECK_INTERVAL', 60))  # secondes
    ALERT_RETENTION_DAYS = int(os.environ.get('ALERT_RETENTION_DAYS', 30))
    
    # Configuration du monitoring
    MONITORING_INTERVAL = int(os.environ.get('MONITORING_INTERVAL', 30))  # secondes
    CLIENT_MONITORING_ENABLED = os.environ.get('CLIENT_MONITORING_ENABLED', 'true').lower() == 'true'
    
    # Configuration de sécurité
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 heure
    
    # Configuration des fichiers statiques
    STATIC_FOLDER = 'frontend/static'
    TEMPLATE_FOLDER = 'frontend/templates'

# Configuration par défaut
config = UbuntuConfig() 