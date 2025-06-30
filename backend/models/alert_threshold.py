"""
Modle AlertThreshold - Gestion des seuils d'alertes configurables
"""
from datetime import datetime
from backend.app import db

class AlertThreshold(db.Model):
    """Modle pour les seuils d'alertes configurables"""
    
    __tablename__ = 'alert_thresholds'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(50), nullable=False)  # 'offset', 'latency', 'stratum', 'availability', 'internet'
    server_type = db.Column(db.String(20), default='all')  # 'local', 'pool', 'all'
    warning_threshold = db.Column(db.Float, nullable=False)
    critical_threshold = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # 'ms', 's', 'level', '%', 'bool'
    enabled = db.Column(db.Boolean, default=True)
    
    # Mtadonnes
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    def __init__(self, metric_name, warning_threshold, critical_threshold, unit, **kwargs):
        self.metric_name = metric_name
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.unit = unit
        
        # Paramtres optionnels
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def metric_label(self):
        """Label franais de la mtrique"""
        labels = {
            'offset': 'cart de synchronisation',
            'latency': 'Dlai de rponse',
            'last_sync': 'Dlai depuis dernire sync',
            'stratum': 'Prcision (stratum)',
            'failure_rate': 'Taux d\'chec',
            'availability': 'Disponibilit',
            'internet': 'Connexion internet'
        }
        return labels.get(self.metric_name, self.metric_name)
    
    @property
    def server_type_label(self):
        """Label franais du type de serveur"""
        labels = {
            'local': 'Serveurs locaux',
            'pool': 'Pools NTP',
            'all': 'Tous les serveurs'
        }
        return labels.get(self.server_type, self.server_type)
    
    def check_threshold(self, value: float) -> str:
        """
        Vrifier si une valeur dpasse les seuils
        
        Returns:
            'ok', 'warning', 'critical'
        """
        if value is None:
            return 'ok'
            
        if self.metric_name == 'stratum':
            # Pour le stratum, plus c'est lev, plus c'est mauvais
            if value >= self.critical_threshold:
                return 'critical'
            elif value >= self.warning_threshold:
                return 'warning'
        elif self.metric_name in ['availability']:
            # Pour la disponibilit, moins c'est lev, plus c'est mauvais
            if value <= self.critical_threshold:
                return 'critical'
            elif value <= self.warning_threshold:
                return 'warning'
        else:
            # Pour les autres mtriques (offset, latency, etc.), plus c'est lev, plus c'est mauvais
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
