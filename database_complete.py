"""
Configuration centralisée de la base de données - NTP Monitor Enterprise
Base déclarative SQLAlchemy avec imports des modèles pour compatibilité
"""
from sqlalchemy.ext.declarative import declarative_base

# Base déclarative SQLAlchemy pure (sans Flask-SQLAlchemy)
Base = declarative_base()

# Import des modèles depuis le dossier models/ pour compatibilité
try:
    from backend.models.user import User
except ImportError:
    print("⚠️ Impossible d'importer User depuis backend.models.user")
    User = None

try:
    from backend.models.ntp_server import NTPServer
except ImportError:
    print("⚠️ Impossible d'importer NTPServer depuis backend.models.ntp_server")
    NTPServer = None

try:
    from backend.models.ntp_log import NTPLog
except ImportError:
    print("⚠️ Impossible d'importer NTPLog depuis backend.models.ntp_log")
    NTPLog = None

try:
    from backend.models.alert import Alert
except ImportError:
    print("⚠️ Impossible d'importer Alert depuis backend.models.alert")
    Alert = None

try:
    from backend.models.system_config import SystemConfig
except ImportError:
    print("⚠️ Impossible d'importer SystemConfig depuis backend.models.system_config")
    SystemConfig = None

try:
    from backend.models.alert_threshold import AlertThreshold
except ImportError:
    print("⚠️ Impossible d'importer AlertThreshold depuis backend.models.alert_threshold")
    AlertThreshold = None

try:
    from backend.models.ntp_log_aggregated import BaseNTPLogAggregated, AggregationStatus
except ImportError:
    print("⚠️ Impossible d'importer BaseNTPLogAggregated depuis backend.models.ntp_log_aggregated")
    BaseNTPLogAggregated = None
    AggregationStatus = None

# Tous les modèles importés pour compatibilité descendante
__all__ = [
    'Base', 
    'User', 
    'NTPServer', 
    'NTPLog', 
    'Alert', 
    'SystemConfig', 
    'AlertThreshold',
    'BaseNTPLogAggregated',
    'AggregationStatus'
] 