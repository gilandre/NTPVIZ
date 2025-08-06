# Config avec fallback automatique
import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ntp-monitor-2025-secret-key-change-in-production')
    
    # Configuration des sessions
    SESSION_COOKIE_SECURE = False  # True en production avec HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 heure
    SESSION_TYPE = 'filesystem'
    
    # Test MySQL avec utilisateur ntp_user
    try:
        import pymysql
        pymysql.connect(host='localhost', port=3306, user='ntp_user', 
                       password='NTP_Monitor_2025!', connect_timeout=1).close()
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://ntp_user:NTP_Monitor_2025!@localhost:3306/ntp_monitor'
        print("MySQL utilise avec ntp_user")
    except:
        # Fallback SQLite
        db_path = Path(__file__).parent.parent / 'instance' / 'ntp_monitor.db'
        db_path.parent.mkdir(exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        print("SQLite utilise")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

# Configuration par defaut
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig  # Forcer le mode développement par défaut
}
