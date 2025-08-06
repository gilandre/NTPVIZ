"""
Modèle NTPLog - Logs détaillés des requêtes NTP
"""
from datetime import datetime
from backend.database_manager import db

class NTPLog(db.Model):
    """Modèle log NTP - Logs détaillés des requêtes NTP"""
    
    __tablename__ = 'ntp_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('ntp_servers.id'), nullable=False, index=True)
    
    # Données de la requête NTP
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    offset = db.Column(db.Float, nullable=True)  # Offset en millisecondes
    delay = db.Column(db.Float, nullable=True)   # Délai en millisecondes
    jitter = db.Column(db.Float, nullable=True)  # Jitter en millisecondes
    stratum = db.Column(db.Integer, nullable=True)  # Niveau stratum
    
    # Statut de la requête
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.String(500), nullable=True)
    
    # Métadonnées
    client_ip = db.Column(db.String(45), nullable=True)  # IP du client
    user_agent = db.Column(db.String(255), nullable=True)  # User agent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, server_id, timestamp, **kwargs):
        self.server_id = server_id
        self.timestamp = timestamp
        
        # Paramètres optionnels
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def offset_abs(self):
        """Offset absolu en millisecondes"""
        return abs(self.offset) if self.offset is not None else None
    
    @property
    def is_successful(self):
        """Vérifier si la requête a réussi"""
        return self.success and self.offset is not None
    
    @property
    def quality_level(self):
        """Niveau de qualité basé sur l'offset"""
        if not self.is_successful:
            return 'error'
        
        abs_offset = abs(self.offset)
        if abs_offset <= 1.0:
            return 'excellent'
        elif abs_offset <= 5.0:
            return 'good'
        elif abs_offset <= 10.0:
            return 'acceptable'
        else:
            return 'poor'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'offset': round(self.offset, 3) if self.offset else None,
            'delay': round(self.delay, 3) if self.delay else None,
            'jitter': round(self.jitter, 3) if self.jitter else None,
            'stratum': self.stratum,
            'success': self.success,
            'error_message': self.error_message,
            'client_ip': self.client_ip,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'offset_abs': round(self.offset_abs, 3) if self.offset_abs else None,
            'quality_level': self.quality_level
        }
    
    def __repr__(self):
        return f'<NTPLog(id={self.id}, server_id={self.server_id}, timestamp={self.timestamp}, offset={self.offset})>' 