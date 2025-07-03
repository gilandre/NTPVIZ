# Configuration MySQL pour NTP Monitor - Production avec utilisateur ntpmonitor
import os
from pathlib import Path

class Config:
    """Configuration de base avec MySQL"""
    SECRET_KEY = 'ntp-monitor-2025-mysql-production'
    
    # Configuration MySQL avec utilisateur dédié
    MYSQL_HOST = 'localhost'
    MYSQL_PORT = 3306
    MYSQL_USER = 'ntpmonitor'
    MYSQL_PASSWORD = 'ntp2025secure'
    MYSQL_DATABASE = 'ntp_monitor'
    
    # URL de connexion MySQL
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }
    
    # Configuration Flask-Login
    SESSION_PROTECTION = 'strong'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 heure
    
    # Configuration de l'application
    APP_NAME = 'EmaraudeNTP VIZ V1.0.0'
    APP_VERSION = '1.0.0'
    APP_EDITOR = '© Quantinnum EA'
    
    # Configuration NTP
    NTP_DEFAULT_SERVERS = [
        '0.pool.ntp.org',
        '1.pool.ntp.org', 
        '2.pool.ntp.org',
        '3.pool.ntp.org',
        'pool.ntp.org'
    ]
    
    # Configuration des logs
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/app.log'
    
    print(f"✅ Configuration MySQL Production: mysql+pymysql://{MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = 'INFO'

config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
} 