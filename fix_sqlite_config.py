#!/usr/bin/env python3
"""
Script de correction de configuration pour forcer SQLite
"""

config_content = '''"""
Configuration forcée SQLite pour NTP Monitor - Version corrigée
"""
import os
from pathlib import Path

class Config:
    """Configuration de base avec SQLite forcé"""
    SECRET_KEY = 'ntp-monitor-2025-sqlite-forced'
    
    # Force SQLite uniquement - PAS DE TEST MYSQL
    db_path = Path(__file__).parent.parent / 'instance' / 'ntp_monitor.db'
    db_path.parent.mkdir(exist_ok=True)
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuration Flask-Login
    SESSION_PROTECTION = 'strong'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 heure
    
    # Configuration de l'application
    APP_NAME = 'EmaraudeNTP VIZ V1.0.0'
    APP_VERSION = '1.0.0'
    APP_EDITOR = '© Quantinnum EA'
    
    # Configuration NTP
    NTP_DEFAULT_SERVERS = [
        {
            'name': 'Pool FR 0',
            'address': '0.fr.pool.ntp.org',
            'type': 'pool',
            'description': 'Serveur NTP Pool France 0'
        },
        {
            'name': 'Pool FR 1', 
            'address': '1.fr.pool.ntp.org',
            'type': 'pool',
            'description': 'Serveur NTP Pool France 1'
        },
        {
            'name': 'Pool Europe',
            'address': 'europe.pool.ntp.org', 
            'type': 'pool',
            'description': 'Serveur NTP Pool Europe'
        },
        {
            'name': 'Cloudflare Time',
            'address': 'time.cloudflare.com',
            'type': 'public',
            'description': 'Service de temps Cloudflare'
        },
        {
            'name': 'Google Time',
            'address': 'time.google.com',
            'type': 'public', 
            'description': 'Service de temps Google'
        }
    ]
    
    print(f"✅ Configuration SQLite forcée active")

class DevelopmentConfig(Config):
    """Configuration de développement"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuration de production"""
    DEBUG = False

class TestingConfig(Config):
    """Configuration de test"""
    TESTING = True
    DEBUG = True

# Configuration par défaut
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig
}

def get_config(config_name=None):
    """Récupérer la configuration"""
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'production')
    
    return config_map.get(config_name, ProductionConfig)
'''

# Écrire le fichier de configuration sur le serveur
with open('/opt/NTPVIZ/config/config.py', 'w') as f:
    f.write(config_content)

print("✅ Configuration SQLite forcée installée")
print("🔄 Redémarrez le service ntp-monitor pour appliquer les changements") 