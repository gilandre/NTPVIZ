# Configuration SQLite forcée pour NTP Monitor
import os
from pathlib import Path

class Config:
    SECRET_KEY = 'ntp-monitor-2025-sqlite'
    db_path = Path(__file__).parent.parent / 'instance' / 'ntp_monitor.db'
    db_path.parent.mkdir(exist_ok=True)
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
} 