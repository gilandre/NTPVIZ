"""
Configuration centralisée de la base de données - NTP Monitor Enterprise
Base déclarative SQLAlchemy pure pour éviter les conflits de métadonnées
"""
from sqlalchemy.ext.declarative import declarative_base

# Base déclarative SQLAlchemy pure (sans Flask-SQLAlchemy)
# Les modèles sont définis dans le dossier backend/models/
Base = declarative_base() 