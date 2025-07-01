"""
Modèle NTPServer - Version corrigée avec tous les attributs requis
"""
from datetime import datetime
from backend.database_manager import db

class NTPServer(db.Model):
    """Modèle serveur NTP - VERSION CORRIGÉE COMPLÈTE"""
    
    __tablename__ = 'ntp_servers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False, index=True)
    port = db.Column(db.Integer, default=123)
    
    # Type et configuration
    server_type = db.Column(db.String(20), nullable=False)  # 'global', 'local'
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=1)
    
    # Paramètres monitoring
    timeout = db.Column(db.Integer, default=10)
    max_offset = db.Column(db.Float, default=1.0)
    critical_offset = db.Column(db.Float, default=5.0)
    
    # Status et monitoring - ATTRIBUTS COMPLETS
    status = db.Column(db.String(20), default='unknown')
    last_sync = db.Column(db.DateTime, nullable=True)
    last_offset = db.Column(db.Float, nullable=True)
    last_latency = db.Column(db.Float, nullable=True)  # En ms
    last_delay = db.Column(db.Float, nullable=True)    # ✅ AJOUTÉ: Résout l'erreur last_delay
    last_stratum = db.Column(db.Integer, nullable=True)
    last_internet_status = db.Column(db.Boolean, nullable=True)
    last_error = db.Column(db.String(500), nullable=True)
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
    
    def update_status(self, offset=None, latency=None, delay=None, stratum=None, internet_status=None, error=False):
        """Mettre à jour le status - VERSION COMPLÈTE"""
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
                
            # ✅ NOUVEAU: Support pour last_delay
            if delay is not None:
                self.last_delay = delay
                
            if stratum is not None:
                self.last_stratum = stratum
                
            if internet_status is not None:
                self.last_internet_status = internet_status
        
        self.updated_at = datetime.utcnow()
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Erreur mise à jour NTPServer: {e}")
    
    @property
    def is_reachable(self):
        """Vérifier si le serveur est accessible"""
        return self.status != 'offline'
    
    @property
    def is_local(self):
        """✅ CORRIGÉ: Propriété is_local - résout l'erreur d'attribut"""
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
    
    @property
    def stratum_quality(self):
        """Qualité de la source selon le stratum"""
        if self.last_stratum is None:
            return 'Inconnu'
        elif self.last_stratum == 0:
            return 'Non synchronisé'
        elif self.last_stratum == 1:
            return 'Référence primaire'
        elif self.last_stratum <= 3:
            return 'Excellent'
        elif self.last_stratum <= 6:
            return 'Bon'
        elif self.last_stratum <= 10:
            return 'Acceptable'
        else:
            return 'Dégradé'
    
    def to_dict(self):
        """Convertir en dictionnaire - VERSION COMPLÈTE"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'port': self.port,
            'server_type': self.server_type,
            'is_active': self.is_active,
            'is_local': self.is_local,  # ✅ AJOUTÉ
            'priority': self.priority,
            'timeout': self.timeout,
            'max_offset': self.max_offset,
            'critical_offset': self.critical_offset,
            'status': self.status,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'last_offset': self.last_offset,
            'last_latency': self.last_latency,
            'last_delay': self.last_delay,  # ✅ AJOUTÉ
            'last_stratum': self.last_stratum,
            'last_internet_status': self.last_internet_status,
            'last_error': self.last_error,
            'error_count': self.error_count,
            'consecutive_errors': self.consecutive_errors,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'stratum_quality': self.stratum_quality
        }
    
    def __repr__(self):
        return f'<NTPServer {self.name} ({self.address})>'
