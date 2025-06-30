"""
Modle Alert - Gestion des alertes et notifications
"""
from datetime import datetime, timedelta
from backend.app import db

class Alert(db.Model):
    """Modle alerte pour notifications et vnements"""
    
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('ntp_servers.id'), nullable=True, index=True)
    
    # Type et niveau d'alerte
    alert_type = db.Column(db.String(50), nullable=False, index=True)  # 'offset', 'timeout', 'offline', 'system'
    severity = db.Column(db.String(20), nullable=False, default='warning')  # 'info', 'warning', 'critical'
    
    # Contenu de l'alerte
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    details = db.Column(db.JSON, nullable=True)  # Donnes supplmentaires JSON
    
    # tat de l'alerte
    status = db.Column(db.String(20), default='active')  # 'active', 'acknowledged', 'resolved'
    is_read = db.Column(db.Boolean, default=False)
    
    # Traitement
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Mtadonnes
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notifications
    notification_sent = db.Column(db.Boolean, default=False)
    notification_methods = db.Column(db.JSON, default=list)  # ['email', 'webhook', 'sms']
    
    def __init__(self, alert_type, title, message, severity='warning', server_id=None, **kwargs):
        self.alert_type = alert_type
        self.title = title
        self.message = message
        self.severity = severity
        self.server_id = server_id
        
        # Paramtres optionnels
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def acknowledge(self, user_id):
        """Acquitter l'alerte"""
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user_id
        self.is_read = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def resolve(self, user_id):
        """Rsoudre l'alerte"""
        self.status = 'resolved'
        self.resolved_at = datetime.utcnow()
        self.resolved_by = user_id
        self.is_read = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def mark_as_read(self):
        """Marquer comme lu"""
        self.is_read = True
        db.session.commit()
    
    @property
    def is_active(self):
        """Vrifier si l'alerte est active"""
        return self.status == 'active'
    
    @property
    def is_critical(self):
        """Vrifier si l'alerte est critique"""
        return self.severity == 'critical'
    
    @property
    def severity_color(self):
        """Couleur selon la svrit"""
        colors = {
            'info': 'info',
            'warning': 'warning',
            'critical': 'danger'
        }
        return colors.get(self.severity, 'info')
    
    @property
    def severity_label(self):
        """Label franais de la svrit"""
        labels = {
            'info': 'Information',
            'warning': 'Avertissement',
            'critical': 'Critique'
        }
        return labels.get(self.severity, 'Inconnu')
    
    @property
    def age_hours(self):
        """ge de l'alerte en heures"""
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
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'age_hours': self.age_hours,
            'notification_sent': self.notification_sent
        }
    
    @classmethod
    def get_active_alerts(cls):
        """Rcuprer les alertes actives"""
        return cls.query.filter_by(status='active').order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_unread_count(cls):
        """Nombre d'alertes non lues"""
        return cls.query.filter_by(is_read=False, status='active').count()
    
    @classmethod
    def create_offset_alert(cls, server, offset):
        """Crer une alerte d'cart de synchronisation"""
        abs_offset = abs(offset)
        severity = 'critical' if abs_offset >= server.critical_offset else 'warning'
        
        alert = cls(
            server_id=server.id,
            alert_type='offset',
            severity=severity,
            title=f'cart de synchronisation - {server.name}',
            message=f'cart de {offset:.3f}s dtect sur le serveur {server.name} ({server.address})',
            details={
                'offset': offset,
                'abs_offset': abs_offset,
                'threshold': server.max_offset,
                'critical_threshold': server.critical_offset
            }
        )
        
        db.session.add(alert)
        db.session.commit()
        return alert
    
    @classmethod
    def create_offline_alert(cls, server):
        """Crer une alerte de serveur hors ligne"""
        alert = cls(
            server_id=server.id,
            alert_type='offline',
            severity='critical',
            title=f'Serveur hors ligne - {server.name}',
            message=f'Le serveur {server.name} ({server.address}) ne rpond plus',
            details={
                'consecutive_errors': server.consecutive_errors,
                'last_sync': server.last_sync.isoformat() if server.last_sync else None
            }
        )
        
        db.session.add(alert)
        db.session.commit()
        return alert
    
    def __repr__(self):
        return f'<Alert {self.title} ({self.severity})>' 
