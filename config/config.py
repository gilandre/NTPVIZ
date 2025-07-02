# Config avec fallback automatique
import os
from pathlib import Path

class Config:
    SECRET_KEY = 'ntp-monitor-2025'
    
    # Test MySQL
    try:
        import pymysql
        pymysql.connect(host='localhost', port=3306, user='root', 
                       password='', connect_timeout=1).close()
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost:3306/ntp_monitor'
        print("MySQL utilise")
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
    'default': ProductionConfig
}
