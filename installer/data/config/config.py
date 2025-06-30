"""
Configuration principale NTP Monitor Enterprise
"""
import os
from datetime import timedelta

class Config:
    """Configuration de base"""
    
    # Application
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ntp-monitor-enterprise-secret-key-2024'
    DEBUG = False
    TESTING = False
    
    # Base de donnes
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ntp_monitor.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Redis & Cache
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = REDIS_URL
    
    # Celery
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Session
    SESSION_TYPE = 'redis'
    SESSION_REDIS = REDIS_URL
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'ntp-monitor:'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Scurit
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    
    # Logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'false').lower() == 'true'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
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
    
    # WebSocket
    SOCKETIO_LOGGER = True
    SOCKETIO_ENGINEIO_LOGGER = True
    
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
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ntp_monitor_prod.db'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log vers syslog en production
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

# Configuration par environnement
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 
