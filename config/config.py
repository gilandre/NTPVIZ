"""
Configuration principale NTP Monitor Enterprise
"""
import os
from datetime import timedelta
from pathlib import Path

# Répertoire de base du projet
BASE_DIR = Path(__file__).parent.parent

class Config:
    """Configuration de base"""
    
    # Application
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Base de donnes
    # MySQL - RÉSOUT LES PROBLÈMES DE CONCURRENCE (configuration par défaut)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@localhost/ntp_monitor'
    
    # SQLITE - CAUSE DES ERREURS "database is locked" (1032+ erreurs) - DÉSACTIVÉ
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@localhost/ntp_monitor'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }
    
    # Redis & Cache
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = REDIS_URL
    
    # Celery
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Session - UTILISATION SESSIONS FLASK STANDARDS (au lieu de Redis)
    # SESSION_TYPE = 'redis'                #  Redis non disponible  
    # SESSION_REDIS = REDIS_URL             #  Cause le problme d'auth
    # SESSION_USE_SIGNER = True             #  Inutile sans Redis
    # SESSION_KEY_PREFIX = 'ntp-monitor:'   #  Inutile sans Redis
    
    # Configuration sessions Flask standards
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = False
    SESSION_COOKIE_SECURE = False              # HTTP localhost
    SESSION_COOKIE_HTTPONLY = True            # Scurit XSS
    SESSION_COOKIE_SAMESITE = 'Lax'           # Protection CSRF
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Scurit
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    
    # Logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'false').lower() == 'true'
    LOG_LEVEL = 'INFO'
    LOG_FILE = BASE_DIR / 'logs' / 'app.log'
    
    # NTP Configuration - 4 pools NTP + 1 serveur local
    NTP_DEFAULT_SERVERS = [
        {
            'name': 'Pool NTP 0',
            'address': '0.pool.ntp.org',
            'type': 'global',
            'description': 'Pool principal NTP mondial'
        },
        {
            'name': 'Pool NTP 1',
            'address': '1.pool.ntp.org',
            'type': 'global',
            'description': 'Pool secondaire NTP mondial'
        },
        {
            'name': 'Pool NTP 2',
            'address': '2.pool.ntp.org',
            'type': 'global',
            'description': 'Pool tertiaire NTP mondial'
        },
        {
            'name': 'Pool NTP 3',
            'address': '3.pool.ntp.org',
            'type': 'global',
            'description': 'Pool quaternaire NTP mondial'
        },
        {
            'name': 'Serveur Local',
            'address': '192.168.1.1',
            'type': 'local',
            'description': 'Serveur NTP local ( configurer)'
        }
    ]
    
    # Paramtres NTP par dfaut
    NTP_DEFAULT_TIMEOUT = 10
    NTP_DEFAULT_MAX_OFFSET = 1.0  # secondes
    NTP_DEFAULT_CRITICAL_OFFSET = 5.0  # secondes
    NTP_QUERY_INTERVAL = 60  # secondes
    
    # WebSocket -  CORRECTION pour viter les erreurs "Invalid frame header"
    SOCKETIO_LOGGER = False  # Dsactiver les logs verbeux WebSocket
    SOCKETIO_ENGINEIO_LOGGER = False  # Dsactiver les logs EngineIO
    
    # Configuration WebSocket optimise
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_PING_TIMEOUT = 60
    SOCKETIO_PING_INTERVAL = 25
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    
    # Configuration NTP
    NTP_TIMEOUT = 5
    NTP_INTERVAL = 10
    
    # Configuration d'alerte
    ALERT_CHECK_INTERVAL = 30
    
    @staticmethod
    def init_app(app):
        """Initialiser l'application avec cette configuration"""
        pass

class DevelopmentConfig(Config):
    """Configuration de dveloppement"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///ntp_monitor_dev.db'
    LOG_LEVEL = 'DEBUG'

class TestingConfig(Config):
    """Configuration de test"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    REDIS_URL = 'redis://localhost:6379/1'

class ProductionConfig(Config):
    """Configuration de production"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@localhost/ntp_monitor'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log vers syslog en production
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

        # Configuration de sécurité renforcée
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
            'pool_timeout': 30,
            'max_overflow': 10,
            'pool_size': 20
        }

# Configuration par environnement
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 
