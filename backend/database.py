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
    """Modèle serveur NTP - VERSION COMPLÈTE"""
    
    __tablename__ = 'ntp_servers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False, index=True)
    port = Column(Integer, default=123)
    
    # Type et configuration
    server_type = Column(String(20), nullable=False)  # 'global', 'local'
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)
    
    # Paramètres monitoring
    timeout = Column(Integer, default=10)
    max_offset = Column(Float, default=1.0)
    critical_offset = Column(Float, default=5.0)
    
    # Status et monitoring - ATTRIBUTS COMPLETS
    status = Column(String(20), default='unknown')
    last_sync = Column(DateTime, nullable=True)
    last_offset = Column(Float, nullable=True)
    last_latency = Column(Float, nullable=True)  # En ms
    last_delay = Column(Float, nullable=True)    # Délai réseau
    last_stratum = Column(Integer, nullable=True)
    last_internet_status = Column(Boolean, nullable=True)
    last_error = Column(String(500), nullable=True)
    error_count = Column(Integer, default=0)
    consecutive_errors = Column(Integer, default=0)
    
    # Métadonnées
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Suppression logique
    deleted_at = Column(DateTime, nullable=True, index=True)
    deleted_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    @property
    def is_deleted(self):
        """Vérifier si le serveur est supprimé logiquement"""
        return self.deleted_at is not None and self.deleted_at != ''
    
    @property
    def is_available(self):
        """Vérifier si le serveur est disponible (actif et non supprimé)"""
        return bool(self.is_active) and not self.is_deleted
    
    def soft_delete(self, deleted_by_user_id=None):
        """Suppression logique du serveur"""
        from datetime import datetime
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by_user_id
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def restore(self):
        """Restaurer un serveur supprimé logiquement"""
        from datetime import datetime
        self.deleted_at = None
        self.deleted_by = None
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    @property
    def is_local(self):
        """Propriété is_local pour détecter les serveurs locaux"""
        if not hasattr(self, '_is_local_cache'):
            # Détecter si c'est un serveur local basé sur l'adresse
            local_patterns = [
                '127.', '192.168.', '10.', '172.16.', '172.17.', '172.18.',
                '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
                '172.24.', '172.25.', '172.26.', '172.27.', '172.28.',
                '172.29.', '172.30.', '172.31.', 'localhost'
            ]
            self._is_local_cache = (
                self.server_type == 'local' or 
                any(self.address.startswith(pattern) for pattern in local_patterns)
            )
        return self._is_local_cache
    
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
            'is_local': self.is_local,
            'is_deleted': self.is_deleted,
            'timeout': self.timeout,
            'max_offset': self.max_offset,
            'critical_offset': self.critical_offset,
            'description': self.description,
            'status': self.status,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'last_offset': self.last_offset,
            'last_latency': self.last_latency,
            'last_delay': self.last_delay,
            'last_stratum': self.last_stratum,
            'last_internet_status': self.last_internet_status,
            'last_error': self.last_error,
            'error_count': self.error_count,
            'consecutive_errors': self.consecutive_errors,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'deleted_by': self.deleted_by
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

class AlertThreshold(Base):
    """Modèle AlertThreshold - Gestion des seuils d'alertes configurables"""
    
    __tablename__ = 'alert_thresholds'
    
    id = Column(Integer, primary_key=True)
    metric_name = Column(String(50), nullable=False)  # 'offset', 'latency', 'stratum', 'availability', 'internet'
    server_type = Column(String(20), default='all')  # 'local', 'pool', 'all'
    warning_threshold = Column(Float, nullable=False)
    critical_threshold = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)  # 'ms', 's', 'level', '%', 'bool'
    enabled = Column(Boolean, default=True)
    
    # Métadonnées
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    def __init__(self, metric_name, warning_threshold, critical_threshold, unit, **kwargs):
        self.metric_name = metric_name
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.unit = unit
        
        # Paramètres optionnels
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def metric_label(self):
        """Label français de la métrique"""
        labels = {
            'offset': 'Écart de synchronisation',
            'latency': 'Délai de réponse',
            'last_sync': 'Délai depuis dernière sync',
            'stratum': 'Précision (stratum)',
            'failure_rate': 'Taux d\'échec',
            'availability': 'Disponibilité',
            'internet': 'Connexion internet'
        }
        return labels.get(self.metric_name, self.metric_name)
    
    @property
    def server_type_label(self):
        """Label français du type de serveur"""
        labels = {
            'local': 'Serveurs locaux',
            'pool': 'Pools NTP',
            'all': 'Tous les serveurs'
        }
        return labels.get(self.server_type, self.server_type)
    
    def check_threshold(self, value: float) -> str:
        """
        Vérifier si une valeur dépasse les seuils
        
        Returns:
            'ok', 'warning', 'critical'
        """
        if value is None:
            return 'ok'
            
        if self.metric_name == 'stratum':
            # Pour le stratum, plus c'est élevé, plus c'est mauvais
            if value >= self.critical_threshold:
                return 'critical'
            elif value >= self.warning_threshold:
                return 'warning'
        elif self.metric_name in ['availability']:
            # Pour la disponibilité, moins c'est élevé, plus c'est mauvais
            if value <= self.critical_threshold:
                return 'critical'
            elif value <= self.warning_threshold:
                return 'warning'
        else:
            # Pour les autres métriques (offset, latency, etc.), plus c'est élevé, plus c'est mauvais
            if abs(value) >= self.critical_threshold:
                return 'critical'
            elif abs(value) >= self.warning_threshold:
                return 'warning'
                
        return 'ok'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'metric_label': self.metric_label,
            'server_type': self.server_type,
            'server_type_label': self.server_type_label,
            'warning_threshold': self.warning_threshold,
            'critical_threshold': self.critical_threshold,
            'unit': self.unit,
            'enabled': self.enabled,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<AlertThreshold {self.metric_name} ({self.warning_threshold}/{self.critical_threshold} {self.unit})>'

class Alert(Base):
    """Modèle Alert - VERSION COMPLÈTE COHÉRENTE"""
    
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey('ntp_servers.id'), nullable=True, index=True)
    threshold_id = Column(Integer, ForeignKey('alert_thresholds.id'), nullable=True)
    
    # Type et niveau d'alerte
    alert_type = Column(String(50), nullable=False, index=True)  # 'offset', 'timeout', 'offline', 'system'
    severity = Column(String(20), nullable=False, default='warning')  # 'info', 'warning', 'critical'
    
    # Contenu de l'alerte
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)  # Données supplémentaires JSON
    
    # État de l'alerte
    status = Column(String(20), default='active')  # 'active', 'acknowledged', 'resolved'
    is_read = Column(Boolean, default=False)
    
    # Traitement
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notifications
    notification_sent = Column(Boolean, default=False)
    notification_methods = Column(JSON, default=list)
    
    # Champs pour la gestion des occurrences multiples
    first_occurrence = Column(DateTime, default=datetime.utcnow)
    last_occurrence = Column(DateTime, default=datetime.utcnow)
    occurrence_count = Column(Integer, default=1)
    
    # Valeurs métriques pour le suivi
    metric_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    
    # Relations
    server = relationship("NTPServer", backref="alerts")
    threshold = relationship("AlertThreshold", backref="alerts")
    
    def __init__(self, alert_type, title, message, severity='warning', server_id=None, **kwargs):
        self.alert_type = alert_type
        self.title = title
        self.message = message
        self.severity = severity
        self.server_id = server_id
        self.first_occurrence = datetime.utcnow()
        self.last_occurrence = datetime.utcnow()
        
        # Paramètres optionnels
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def acknowledge(self, user_id):
        """Acquitter l'alerte"""
        self.status = 'acknowledged'
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user_id
        self.is_read = True
        self.updated_at = datetime.utcnow()
    
    def resolve(self, user_id):
        """Résoudre l'alerte"""
        self.status = 'resolved'
        self.resolved_at = datetime.utcnow()
        self.resolved_by = user_id
        self.is_read = True
        self.updated_at = datetime.utcnow()
    
    def mark_as_read(self):
        """Marquer comme lu"""
        self.is_read = True
    
    @property
    def is_active(self):
        """Vérifier si l'alerte est active"""
        return self.status == 'active'
    
    @property
    def is_critical(self):
        """Vérifier si l'alerte est critique"""
        return self.severity == 'critical'
    
    @property
    def severity_color(self):
        """Couleur selon la sévérité"""
        colors = {
            'info': 'info',
            'warning': 'warning',
            'critical': 'danger'
        }
        return colors.get(self.severity, 'info')
    
    @property
    def severity_label(self):
        """Label français de la sévérité"""
        labels = {
            'info': 'Information',
            'warning': 'Avertissement',
            'critical': 'Critique'
        }
        return labels.get(self.severity, 'Inconnu')
    
    @property
    def age_hours(self):
        """Âge de l'alerte en heures"""
        if self.created_at:
            delta = datetime.utcnow() - self.created_at
            return delta.total_seconds() / 3600
        return 0
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'server_name': self.server.name if self.server else None,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'severity_label': self.severity_label,
            'severity_color': self.severity_color,
            'title': self.title,
            'message': self.message,
            'details': self.details,
            'status': self.status,
            'is_read': self.is_read,
            'is_active': self.is_active,
            'is_critical': self.is_critical,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'age_hours': self.age_hours,
            'notification_sent': self.notification_sent,
            'first_occurrence': self.first_occurrence.isoformat() if self.first_occurrence else None,
            'last_occurrence': self.last_occurrence.isoformat() if self.last_occurrence else None,
            'occurrence_count': self.occurrence_count,
            'metric_value': self.metric_value,
            'threshold_value': self.threshold_value
        }
    
    @classmethod
    def get_active_alerts(cls, session):
        """Récupérer les alertes actives"""
        return session.query(cls).filter_by(status='active').order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_unread_count(cls, session):
        """Nombre d'alertes non lues"""
        return session.query(cls).filter_by(is_read=False, status='active').count()
    
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
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    def __init__(self, key=None, value=None, value_type='string', **kwargs):
        if key:
            self.key_name = key
        if value is not None:
            self.set_value(value, value_type)
        self.value_type = value_type
        
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
        """Définir la valeur avec sérialisation selon le type"""
        if value_type:
            self.value_type = value_type
        
        if value is None:
            self.value = None
        else:
            self.value = self._serialize_value(value, self.value_type)
    
    def get_value(self):
        """Récupérer la valeur brute (string)"""
        return self.value
    
    def get_typed_value(self):
        """Récupérer la valeur avec le bon type"""
        if self.value is None:
            return None
            
        try:
            if self.value_type == 'int':
                return int(self.value)
            elif self.value_type == 'float':
                return float(self.value)
            elif self.value_type == 'bool':
                return self.value.lower() in ('true', '1', 'yes', 'on')
            elif self.value_type == 'json':
                return json.loads(self.value)
            else:  # string
                return self.value
        except (ValueError, json.JSONDecodeError):
            return self.value
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'key': self.key_name,
            'value': self.get_typed_value(),
            'value_type': self.value_type,
            'category': self.category,
            'description': self.description,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_config(cls, session, key, default=None):
        """Récupérer une configuration par clé"""
        try:
            config = session.query(cls).filter_by(key_name=key).first()
            if config:
                return config.get_typed_value()
            return default
        except Exception:
            return default
    
    @classmethod
    def set_config(cls, session, key, value, value_type='string', description=None, category='general', user_id=None):
        """Définir une configuration"""
        try:
            config = session.query(cls).filter_by(key_name=key).first()
            
            if config:
                # Mettre à jour la configuration existante
                config.set_value(value, value_type)
                config.updated_at = datetime.utcnow()
                if user_id:
                    config.updated_by = user_id
            else:
                # Créer une nouvelle configuration
                config = cls(
                    key=key,
                    value=value,
                    value_type=value_type,
                    description=description,
                    category=category
                )
                session.add(config)
            
            return config
        except Exception as e:
            print(f"Erreur lors de la définition de la configuration {key}: {e}")
            return None
    
    @classmethod
    def get_category_configs(cls, session, category):
        """Récupérer toutes les configurations d'une catégorie"""
        try:
            configs = session.query(cls).filter_by(category=category).all()
            return {config.key_name: config.get_typed_value() for config in configs}
        except Exception:
            return {}
    
    @staticmethod
    def _serialize_value(value, value_type):
        """Sérialiser une valeur selon son type"""
        if value is None:
            return None
        elif value_type == 'json':
            return json.dumps(value)
        else:
            return str(value)
    
    def __repr__(self):
        return f'<SystemConfig {self.key_name}={self.value}>' 