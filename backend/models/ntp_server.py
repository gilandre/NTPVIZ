"""
Modèle NTPServer - Gestion des serveurs NTP configurables
"""
from datetime import datetime
from backend.app import db

class NTPServer(db.Model):
    """Modèle serveur NTP configurable"""
    
    __tablename__ = 'ntp_servers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False, index=True)
    port = db.Column(db.Integer, default=123)
    
    # Type et configuration
    server_type = db.Column(db.String(20), nullable=False)  # 'global', 'local'
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=1)  # Ordre d'affichage
    
    # Paramètres monitoring
    timeout = db.Column(db.Integer, default=10)  # secondes
    max_offset = db.Column(db.Float, default=1.0)  # Seuil warning en secondes
    critical_offset = db.Column(db.Float, default=5.0)  # Seuil critique en secondes
    
    # Status et monitoring
    status = db.Column(db.String(20), default='unknown')  # 'ok', 'warning', 'critical', 'offline'
    last_sync = db.Column(db.DateTime, nullable=True)
    last_offset = db.Column(db.Float, nullable=True)  # Dernier écart en secondes
    last_latency = db.Column(db.Float, nullable=True)  # Dernière latence en ms
    error_count = db.Column(db.Integer, default=0)
    consecutive_errors = db.Column(db.Integer, default=0)
    
    # Métadonnées
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relations
    logs = db.relationship('NTPLog', backref='server', lazy='dynamic', cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='server', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, name, address, server_type, port=123, **kwargs):
        self.name = name
        self.address = address
        self.server_type = server_type
        self.port = port
        
        # Paramètres optionnels
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def update_status(self, offset=None, latency=None, error=False):
        """Mettre à jour le status du serveur"""
        if error:
            self.consecutive_errors += 1
            self.error_count += 1
            
            if self.consecutive_errors >= 3:
                self.status = 'offline'
            elif self.consecutive_errors >= 1:
                self.status = 'warning'
        else:
            self.consecutive_errors = 0
            self.last_sync = datetime.utcnow()
            
            if offset is not None:
                self.last_offset = offset
                abs_offset = abs(offset)
                
                if abs_offset >= self.critical_offset:
                    self.status = 'critical'
                elif abs_offset >= self.max_offset:
                    self.status = 'warning'
                else:
                    self.status = 'ok'
            
            if latency is not None:
                self.last_latency = latency
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @property
    def is_reachable(self):
        """Vérifier si le serveur est accessible"""
        return self.status != 'offline'
    
    @property
    def status_color(self):
        """Couleur selon le status"""
        colors = {
            'ok': 'success',
            'warning': 'warning', 
            'critical': 'danger',
            'offline': 'secondary',
            'unknown': 'info'
        }
        return colors.get(self.status, 'info')
    
    @property
    def status_label(self):
        """Label français du status"""
        labels = {
            'ok': 'Synchronisé',
            'warning': 'Écart détecté',
            'critical': 'Écart critique',
            'offline': 'Hors ligne',
            'unknown': 'Inconnu'
        }
        return labels.get(self.status, 'Inconnu')
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'port': self.port,
            'server_type': self.server_type,
            'is_active': self.is_active,
            'priority': self.priority,
            'timeout': self.timeout,
            'max_offset': self.max_offset,
            'critical_offset': self.critical_offset,
            'status': self.status,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'last_offset': self.last_offset,
            'last_latency': self.last_latency,
            'error_count': self.error_count,
            'consecutive_errors': self.consecutive_errors,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<NTPServer {self.name} ({self.address})>' 