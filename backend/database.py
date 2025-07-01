"""
Configuration centralisée de la base de données - NTP Monitor Enterprise
Élimine les imports circulaires et standardise sur le Database Manager MySQL
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import json

# Base déclarative SQLAlchemy pure (sans Flask-SQLAlchemy)
Base = declarative_base()

class User(UserMixin, Base):
    """Modèle utilisateur avec authentification"""
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profil utilisateur
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    role = Column(String(20), nullable=False, default='viewer')
    
    # Status et dates
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    
    # Paramètres utilisateur
    preferences = Column(JSON, default=lambda: {
        'theme': 'light',
        'language': 'fr',
        'notifications': True,
        'auto_refresh': True,
        'refresh_interval': 30
    })
    
    def __init__(self, username, email, password, role='viewer'):
        self.username = username
        self.email = email
        self.set_password(password)
        self.role = role
    
    def set_password(self, password):
        """Définir le mot de passe haché"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifier le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    def get_current_time(self):
        """Obtenir l'heure actuelle (méthode utilitaire)"""
        return datetime.utcnow()
    
    def update_login_info(self):
        """Mettre à jour les informations de connexion (sans commit automatique)"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        # Pas de commit automatique - sera géré par l'appelant
    
    @property
    def is_admin(self):
        """Vérifier si l'utilisateur est administrateur"""
        return self.role == 'admin'
    
    @property
    def can_configure(self):
        """Vérifier si l'utilisateur peut configurer"""
        return self.role in ['admin', 'operator']
    
    @property
    def full_name(self):
        """Nom complet de l'utilisateur"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def to_dict(self):
        """Convertir en dictionnaire pour API"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'preferences': self.preferences
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class NTPServer(Base):
    """Modèle serveur NTP"""
    
    __tablename__ = 'ntp_servers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False, unique=True)
    port = Column(Integer, default=123)
    server_type = Column(String(50), default='public')
    priority = Column(Integer, default=1)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    timeout = Column(Float, default=5.0)
    max_offset = Column(Float, default=1.0)
    description = Column(Text, nullable=True)
    
    # État actuel
    status = Column(String(20), default='unknown')
    last_sync = Column(DateTime, nullable=True)
    last_offset = Column(Float, nullable=True)
    last_latency = Column(Float, nullable=True)
    last_stratum = Column(Integer, nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convertir en dictionnaire pour API"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'port': self.port,
            'server_type': self.server_type,
            'priority': self.priority,
            'is_active': self.is_active,
            'timeout': self.timeout,
            'max_offset': self.max_offset,
            'description': self.description,
            'status': self.status,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'last_offset': self.last_offset,
            'last_latency': self.last_latency,
            'last_stratum': self.last_stratum,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<NTPServer {self.name} ({self.address})>'

class NTPLog(Base):
    """Modèle log des requêtes NTP"""
    
    __tablename__ = 'ntp_logs'
    
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey('ntp_servers.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Résultats de la requête NTP
    status = Column(String(20), nullable=False)  # success, timeout, error
    offset = Column(Float, nullable=True)
    delay = Column(Float, nullable=True)
    latency = Column(Float, nullable=True)
    stratum = Column(Integer, nullable=True)
    
    # Métadonnées
    error_message = Column(Text, nullable=True)
    response_time = Column(Float, nullable=True)
    
    # Relations
    server = relationship("NTPServer", backref="logs")
    
    def to_dict(self):
        """Convertir en dictionnaire pour API"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'status': self.status,
            'offset': self.offset,
            'delay': self.delay,
            'latency': self.latency,
            'stratum': self.stratum,
            'error_message': self.error_message,
            'response_time': self.response_time
        }
    
    def __repr__(self):
        return f'<NTPLog {self.server_id} {self.timestamp}>'

class Alert(Base):
    """Modèle des alertes"""
    
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey('ntp_servers.id'), nullable=False)
    threshold_id = Column(Integer, nullable=True)
    
    # Contenu de l'alerte
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), default='warning')  # info, warning, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    
    # État
    status = Column(String(20), default='active')  # active, acknowledged, resolved
    is_read = Column(Boolean, default=False)
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Utilisateurs
    created_by = Column(Integer, nullable=True)
    acknowledged_by = Column(Integer, nullable=True)
    resolved_by = Column(Integer, nullable=True)
    
    # Relations
    server = relationship("NTPServer", backref="alerts")
    
    def acknowledge(self, user_id):
        """Acquitter l'alerte"""
        self.status = 'acknowledged'
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.utcnow()
    
    def resolve(self, user_id):
        """Résoudre l'alerte"""
        self.status = 'resolved'
        self.resolved_by = user_id
        self.resolved_at = datetime.utcnow()
    
    def mark_as_read(self):
        """Marquer comme lue"""
        self.is_read = True
    
    def to_dict(self):
        """Convertir en dictionnaire pour API"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'threshold_id': self.threshold_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'details': self.details,
            'status': self.status,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_by': self.created_by,
            'acknowledged_by': self.acknowledged_by,
            'resolved_by': self.resolved_by
        }
    
    def __repr__(self):
        return f'<Alert {self.title} ({self.severity})>'

class SystemConfig(Base):
    """Modèle configuration système COMPLET avec value_type"""
    
    __tablename__ = 'system_config'
    
    id = Column(Integer, primary_key=True)
    key_name = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default='string')  # 'string', 'int', 'float', 'bool', 'json'
    category = Column(String(50), default='general')
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, key=None, value=None, value_type='string', **kwargs):
        """Constructeur avec support value_type"""
        if key:
            self.key_name = key
        if value is not None:
            self.set_value(value, value_type)
        
        # Paramètres optionnels
        for attr, val in kwargs.items():
            if hasattr(self, attr):
                setattr(self, attr, val)
    
    @property
    def key(self):
        """Propriété de compatibilité pour l'ancien nom 'key'"""
        return self.key_name
    
    @key.setter
    def key(self, value):
        """Setter pour la propriété de compatibilité"""
        self.key_name = value
    
    def set_value(self, value, value_type=None):
        """Définir la valeur avec le bon type"""
        if value_type:
            self.value_type = value_type
        
        if self.value_type == 'json':
            self.value = json.dumps(value) if value is not None else None
        else:
            self.value = str(value) if value is not None else None
        
        self.updated_at = datetime.utcnow()
    
    def get_value(self):
        """Récupérer la valeur avec le bon type"""
        if self.value is None:
            return None
        
        if self.value_type == 'int':
            return int(self.value)
        elif self.value_type == 'float':
            return float(self.value)
        elif self.value_type == 'bool':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.value_type == 'json':
            return json.loads(self.value)
        else:
            return self.value
    
    def get_typed_value(self):
        """Alias pour get_value() pour compatibilité"""
        return self.get_value()
    
    def to_dict(self):
        """Convertir en dictionnaire pour API"""
        return {
            'id': self.id,
            'key': self.key_name,
            'value': self.get_value(),
            'value_type': self.value_type,
            'category': self.category,
            'description': self.description,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_config(cls, key, default=None):
        """Récupérer une valeur de configuration"""
        from backend.database_manager import get_db_session_with_context
        try:
            with get_db_session_with_context() as session:
                config = session.query(cls).filter_by(key_name=key).first()
                return config.get_value() if config else default
        except Exception as e:
            print(f"Erreur get_config: {e}")
            return default
    
    @classmethod
    def set_config(cls, key, value, value_type='string', description=None, category='general', user_id=None):
        """Définir une valeur de configuration"""
        from backend.database_manager import get_db_session_with_context
        try:
            with get_db_session_with_context() as session:
                config = session.query(cls).filter_by(key_name=key).first()
                
                if config:
                    config.set_value(value, value_type)
                    if description:
                        config.description = description
                else:
                    config = cls(
                        key=key,
                        value=value,
                        value_type=value_type,
                        description=description,
                        category=category
                    )
                    session.add(config)
                
                session.commit()
                return config
        except Exception as e:
            print(f"Erreur set_config: {e}")
            return None
    
    @classmethod
    def get_category_configs(cls, category):
        """Récupérer toutes les configurations d'une catégorie"""
        from backend.database_manager import get_db_session_with_context
        try:
            with get_db_session_with_context() as session:
                return session.query(cls).filter_by(category=category).all()
        except Exception as e:
            print(f"Erreur get_category_configs: {e}")
            return []
    
    @staticmethod
    def _serialize_value(value, value_type):
        """Sérialiser une valeur selon son type"""
        if value is None:
            return None
        
        if value_type == 'json':
            return json.dumps(value)
        else:
            return str(value)
    
    def __repr__(self):
        return f'<SystemConfig {self.key_name}>' 