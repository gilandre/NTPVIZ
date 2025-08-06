"""
Modèle NTPServer - Version avec suppression logique
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class NTPServer(Base):
    """Modèle serveur NTP avec suppression logique"""
    
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
    # ❌ SUPPRIMÉ: max_offset et critical_offset redondants avec alert_thresholds
    # # max_offset = Column(Float, default=1.0)
    # # critical_offset = Column(Float, default=5.0)
    
    # Status et monitoring
    status = Column(String(20), default='unknown')
    last_sync = Column(DateTime, nullable=True)
    last_offset = Column(Float, nullable=True)
    last_latency = Column(Float, nullable=True)
    last_delay = Column(Float, nullable=True)
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
    
    # Relations
    logs = relationship("NTPLog", backref="server", lazy='dynamic', cascade='all, delete-orphan')
    alerts = relationship("Alert", backref="server", lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def is_deleted(self):
        """Vérifier si le serveur est supprimé logiquement"""
        return self.deleted_at is not None
    
    @property
    def is_available(self):
        """Vérifier si le serveur est disponible (actif et non supprimé)"""
        return self.is_active and not self.is_deleted
    
    def soft_delete(self, deleted_by_user_id=None):
        """Suppression logique du serveur"""
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by_user_id
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def restore(self):
        """Restaurer un serveur supprimé logiquement"""
        self.deleted_at = None
        self.deleted_by = None
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        status = "DELETED" if self.is_deleted else "ACTIVE" if self.is_active else "INACTIVE"
        return f'<NTPServer {self.name} ({self.address}) - {status}>'
