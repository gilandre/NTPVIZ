"""
Configuration principale NTP Monitor Enterprise - VERSION CORRIGÉE
"""
import os
from datetime import timedelta
from pathlib import Path

# Répertoire de base du projet
BASE_DIR = Path(__file__).parent.parent

class Config:
    """Configuration de base - CORRIGÉE HOLISTIQUE"""
    
    # Application - SECRET KEY SÉCURISÉE
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ntp-monitor-enterprise-secure-key-2024-v2'
    DEBUG = False
    TESTING = False
    
    # Base de données MySQL - OPTIMISÉE
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@localhost/ntp_monitor'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 1800,      # 30 minutes
        'pool_timeout': 20,
        'max_overflow': 5,
        'pool_size': 10
    }
    
    # Sessions Flask - CONFIGURATION CORRIGÉE POUR AUTHENTIFICATION
    SESSION_PERMANENT = True
    SESSION_COOKIE_SECURE = False              # HTTP localhost
    SESSION_COOKIE_HTTPONLY = True             # Sécurité XSS
    SESSION_COOKIE_SAMESITE = 'Lax'            # Protection CSRF
    SESSION_COOKIE_NAME = 'ntp_monitor_session'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    
    # Authentification - CONFIGURATION ROBUSTE
    LOGIN_DISABLED = False
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Sécurité CSRF - CONFIGURATION OPTIMISÉE
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 7200  # 2 heures
    WTF_CSRF_SECRET_KEY = SECRET_KEY
    
    # WebSocket - CONFIGURATION CORRIGÉE
    SOCKETIO_LOGGER = False              # Désactiver les logs verbeux
    SOCKETIO_ENGINEIO_LOGGER = False     # Désactiver les logs EngineIO
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_PING_TIMEOUT = 60
    SOCKETIO_PING_INTERVAL = 25
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    
    # Logging optimisé
    LOG_LEVEL = 'INFO'
    LOG_FILE = BASE_DIR / 'logs' / 'app.log'
    
    @staticmethod
    def init_app(app):
        """Initialiser l'application avec cette configuration"""
        pass

class DevelopmentConfig(Config):
    """Configuration de développement - OPTIMISÉE"""
    DEBUG = True
    WTF_CSRF_ENABLED = False  # Désactiver CSRF en développement pour faciliter les tests
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Configuration de production - SÉCURISÉE"""
    DEBUG = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True  # HTTPS uniquement en production
    REMEMBER_COOKIE_SECURE = True

# Configuration par environnement
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
