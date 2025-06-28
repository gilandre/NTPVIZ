"""
Modèle NTPLog - Historique des requêtes NTP
"""
from datetime import datetime, timedelta
from backend.app import db
from sqlalchemy import func

class NTPLog(db.Model):
    """Log des requêtes NTP pour historique et analyse"""
    
    __tablename__ = 'ntp_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('ntp_servers.id'), nullable=False, index=True)
    
    # Données de la requête
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    offset = db.Column(db.Float, nullable=True)  # Écart en secondes
    latency = db.Column(db.Float, nullable=True)  # Latence en ms
    stratum = db.Column(db.Integer, nullable=True)  # Niveau hiérarchique NTP
    
    # Détails techniques
    precision = db.Column(db.Float, nullable=True)  # Précision du serveur
    root_delay = db.Column(db.Float, nullable=True)  # Délai racine
    root_dispersion = db.Column(db.Float, nullable=True)  # Dispersion racine
    reference_id = db.Column(db.String(50), nullable=True)  # ID de référence
    
    # Horodatage
    local_time = db.Column(db.DateTime, nullable=True)  # Heure locale lors de la requête
    server_time = db.Column(db.DateTime, nullable=True)  # Heure du serveur NTP
    
    # État de la requête
    status = db.Column(db.String(20), default='success')  # 'success', 'timeout', 'error', etc.
    error_message = db.Column(db.Text, nullable=True)
    
    def __init__(self, server_id, status='success', **kwargs):
        self.server_id = server_id
        self.status = status
        
        # Paramètres optionnels
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def offset_ms(self):
        """Écart en millisecondes"""
        return self.offset * 1000 if self.offset is not None else None
    
    @property
    def is_synchronized(self):
        """Vérifier si la synchronisation est correcte"""
        return self.status == 'success' and self.offset is not None
    
    @property
    def status_label(self):
        """Label français du status"""
        labels = {
            'success': 'Succès',
            'timeout': 'Timeout',
            'error': 'Erreur'
        }
        return labels.get(self.status, 'Inconnu')
    
    @classmethod
    def get_recent_logs(cls, server_id, hours=24):
        """Récupérer les logs récents d'un serveur"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return cls.query.filter(
            cls.server_id == server_id,
            cls.timestamp >= since
        ).order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_server_stats(cls, server_id, hours=24):
        """Calculer les statistiques d'un serveur"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Requêtes réussies
        successful_logs = cls.query.filter(
            cls.server_id == server_id,
            cls.timestamp >= since,
            cls.status == 'success',
            cls.offset.isnot(None)
        ).all()
        
        if not successful_logs:
            return None
        
        # Statistiques
        offsets = [abs(log.offset) for log in successful_logs]
        latencies = [log.latency for log in successful_logs if log.latency is not None]
        
        total_queries = cls.query.filter(
            cls.server_id == server_id,
            cls.timestamp >= since
        ).count()
        
        successful_queries = len(successful_logs)
        
        stats = {
            'period_hours': hours,
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'success_rate': (successful_queries / total_queries * 100) if total_queries > 0 else 0,
            'avg_offset': sum(offsets) / len(offsets) if offsets else 0,
            'max_offset': max(offsets) if offsets else 0,
            'min_offset': min(offsets) if offsets else 0,
            'avg_latency': sum(latencies) / len(latencies) if latencies else 0,
            'max_latency': max(latencies) if latencies else 0,
            'min_latency': min(latencies) if latencies else 0,
            'last_sync': successful_logs[0].timestamp if successful_logs else None
        }
        
        return stats
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'timestamp': self.timestamp.isoformat(),
            'offset': self.offset,
            'latency': self.latency,
            'stratum': self.stratum,
            'precision': self.precision,
            'root_delay': self.root_delay,
            'root_dispersion': self.root_dispersion,
            'reference_id': self.reference_id,
            'local_time': self.local_time.isoformat() if self.local_time else None,
            'server_time': self.server_time.isoformat() if self.server_time else None,
            'status': self.status,
            'error_message': self.error_message
        }
    
    def __repr__(self):
        return f'<NTPLog {self.server_id} {self.timestamp} {self.status}>' 