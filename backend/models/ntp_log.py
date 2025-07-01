"""
Modèle NTPLog - Version corrigée avec support offset/offset_ms flexible
"""
from datetime import datetime
from backend.database_manager import db

class NTPLog(db.Model):
    """✅ Modèle NTPLog - CORRIGÉ pour support offset/offset_ms"""
    
    __tablename__ = 'ntp_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('ntp_servers.id'), nullable=False, index=True)
    
    # Timestamp et timing
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    local_time = db.Column(db.DateTime, nullable=True)
    server_time = db.Column(db.DateTime, nullable=True)
    
    # Métriques NTP - SUPPORT FLEXIBLE
    offset = db.Column(db.Float, nullable=True)  # Offset en secondes (principal)
    delay = db.Column(db.Float, nullable=True)   # Délai réseau en ms
    latency = db.Column(db.Float, nullable=True) # Latence en ms (alias)
    stratum = db.Column(db.Integer, nullable=True)
    precision = db.Column(db.Float, nullable=True)
    
    # Status et qualité
    status = db.Column(db.String(20), default='unknown')
    quality_indicator = db.Column(db.String(10), nullable=True)
    error_message = db.Column(db.String(500), nullable=True)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, server_id, **kwargs):
        """✅ CONSTRUCTEUR FLEXIBLE - Support offset ET offset_ms"""
        self.server_id = server_id
        
        # Gestion flexible des paramètres offset/offset_ms
        if 'offset_ms' in kwargs:
            # Convertir offset_ms en secondes pour le champ offset
            self.offset = kwargs.pop('offset_ms') / 1000.0
        elif 'offset' in kwargs:
            self.offset = kwargs.pop('offset')
        
        # Gestion flexible delay/latency
        if 'delay' in kwargs:
            self.delay = kwargs.pop('delay')
            if not self.latency:
                self.latency = self.delay  # Alias
        elif 'latency' in kwargs:
            self.latency = kwargs.pop('latency')
            if not self.delay:
                self.delay = self.latency  # Alias
                
        # Autres paramètres
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def offset_ms(self):
        """✅ PROPRIÉTÉ DE COMPATIBILITÉ - Offset en millisecondes"""
        return self.offset * 1000.0 if self.offset is not None else None
    
    @offset_ms.setter
    def offset_ms(self, value):
        """✅ SETTER COMPATIBILITÉ - Convertir ms en secondes"""
        self.offset = value / 1000.0 if value is not None else None
    
    @property
    def offset_seconds(self):
        """Offset en secondes (valeur principale)"""
        return self.offset
    
    @property
    def delay_ms(self):
        """Délai en millisecondes"""
        return self.delay
    
    @property
    def status_color(self):
        """Couleur selon le status"""
        colors = {
            'ok': 'success',
            'warning': 'warning',
            'critical': 'danger',
            'error': 'danger',
            'unknown': 'info'
        }
        return colors.get(self.status, 'info')
    
    def to_dict(self):
        """Convertir en dictionnaire - SUPPORT COMPLET"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'local_time': self.local_time.isoformat() if self.local_time else None,
            'server_time': self.server_time.isoformat() if self.server_time else None,
            'offset': self.offset,
            'offset_ms': self.offset_ms,  # ✅ COMPATIBILITÉ
            'delay': self.delay,
            'latency': self.latency,
            'stratum': self.stratum,
            'precision': self.precision,
            'status': self.status,
            'quality_indicator': self.quality_indicator,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_log(cls, server_id, **kwargs):
        """✅ MÉTHODE FACTORY - Création sécurisée de logs"""
        try:
            log = cls(server_id=server_id, **kwargs)
            db.session.add(log)
            db.session.commit()
            return log
        except Exception as e:
            db.session.rollback()
            print(f"Erreur création NTPLog: {e}")
            return None
    
    def __repr__(self):
        return f'<NTPLog {self.server_id} offset={self.offset}s>'
