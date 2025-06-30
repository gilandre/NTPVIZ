"""
Modle SystemConfig - Configuration systme
"""
import json
from datetime import datetime
from backend.app import db

class SystemConfig(db.Model):
    """Configuration systme key-value"""
    
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(20), default='string')  # 'string', 'int', 'float', 'bool', 'json'
    
    # Mtadonnes
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), default='general')  # 'general', 'ntp', 'alerts', 'network'
    is_public = db.Column(db.Boolean, default=True)  # Visible aux utilisateurs non-admin
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    def __init__(self, key, value, value_type='string', **kwargs):
        self.key = key
        self.set_value(value, value_type)
        
        # Paramtres optionnels
        for attr, val in kwargs.items():
            if hasattr(self, attr):
                setattr(self, attr, val)
    
    def set_value(self, value, value_type=None):
        """Dfinir la valeur avec le bon type"""
        if value_type:
            self.value_type = value_type
        
        if self.value_type == 'json':
            import json
            self.value = json.dumps(value) if value is not None else None
        else:
            self.value = str(value) if value is not None else None
        
        self.updated_at = datetime.utcnow()
    
    def get_value(self):
        """Rcuprer la valeur avec le bon type"""
        if self.value is None:
            return None
        
        if self.value_type == 'int':
            return int(self.value)
        elif self.value_type == 'float':
            return float(self.value)
        elif self.value_type == 'bool':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.value_type == 'json':
            import json
            return json.loads(self.value)
        else:
            return self.value
    
    def to_dict(self):
        """Convertir en dictionnaire pour API"""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.get_value(),
            'value_type': self.value_type,
            'description': self.description,
            'category': self.category,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_config(cls, key, default=None):
        """Rcuprer une valeur de configuration"""
        config = cls.query.filter_by(key=key).first()
        if not config:
            return default
        
        return config.get_typed_value()
    
    @classmethod
    def set_config(cls, key, value, value_type='string', description=None, category='general', user_id=None):
        """Dfinir une valeur de configuration"""
        config = cls.query.filter_by(key=key).first()
        
        if config:
            config.value = cls._serialize_value(value, value_type)
            config.value_type = value_type
            config.updated_at = datetime.utcnow()
            config.updated_by = user_id
            if description:
                config.description = description
        else:
            config = cls(
                key=key,
                value=cls._serialize_value(value, value_type),
                value_type=value_type,
                description=description,
                category=category,
                updated_by=user_id
            )
            db.session.add(config)
        
        db.session.commit()
        return config
    
    @classmethod
    def get_category_configs(cls, category):
        """Rcuprer toutes les configurations d'une catgorie"""
        return cls.query.filter_by(category=category).all()
    
    @classmethod
    def init_default_configs(cls):
        """Initialiser les configurations par dfaut"""
        defaults = [
            # Configuration systme
            ('system.app_name', 'NTP Monitor Enterprise', 'string', 'Nom de l\'application', 'system'),
            ('system.version', '1.0.0', 'string', 'Version de l\'application', 'system'),
            ('system.timezone', 'Europe/Paris', 'string', 'Fuseau horaire', 'system'),
            
            # Configuration NTP
            ('ntp.query_interval', 60, 'int', 'Intervalle entre les requtes NTP (secondes)', 'ntp'),
            ('ntp.default_timeout', 10, 'int', 'Timeout par dfaut pour les requtes NTP (secondes)', 'ntp'),
            ('ntp.max_offset_warning', 1.0, 'float', 'Seuil d\'alerte pour l\'cart (secondes)', 'ntp'),
            ('ntp.max_offset_critical', 5.0, 'float', 'Seuil critique pour l\'cart (secondes)', 'ntp'),
            
            # Configuration alertes
            ('alerts.retention_days', 30, 'int', 'Dure de conservation des alertes (jours)', 'alerts'),
            ('alerts.email_enabled', False, 'bool', 'Activer les notifications par email', 'alerts'),
            ('alerts.webhook_enabled', False, 'bool', 'Activer les webhooks', 'alerts'),
            
            # Configuration rseau
            ('network.max_connections', 100, 'int', 'Nombre maximum de connexions simultanes', 'network'),
            ('network.connection_timeout', 30, 'int', 'Timeout de connexion rseau (secondes)', 'network'),
            
            # Configuration monitoring
            ('monitoring.log_retention_days', 7, 'int', 'Dure de conservation des logs (jours)', 'monitoring'),
            ('monitoring.stats_interval', 300, 'int', 'Intervalle de calcul des statistiques (secondes)', 'monitoring')
        ]
        
        for key, value, value_type, description, category in defaults:
            if not cls.query.filter_by(key=key).first():
                cls.set_config(key, value, value_type, description, category)
    
    def get_typed_value(self):
        """Rcuprer la valeur avec le bon type"""
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
        else:  # string
            return self.value
    
    @staticmethod
    def _serialize_value(value, value_type):
        """Srialiser une valeur selon son type"""
        if value is None:
            return None
        
        if value_type == 'json':
            return json.dumps(value)
        else:
            return str(value)
    
    def __repr__(self):
        return f'<SystemConfig {self.key}={self.value}>' 
