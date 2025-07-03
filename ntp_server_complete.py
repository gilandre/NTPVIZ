"""
Modèle NTPServer - Version complète pour MySQL pur SQLAlchemy
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text
from backend.database import Base

class NTPServer(Base):
    """Modèle serveur NTP - VERSION COMPLETE MYSQL PURE SQLALCHEMY"""
    
    __tablename__ = 'ntp_servers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False, index=True)
    port = Column(Integer, default=123)
    
    # Type et configuration
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    description = Column(Text)
    
    # Paramètres de monitoring nécessaires
    timeout = Column(Integer, default=10)
    max_offset = Column(Float, default=1.0)
    critical_offset = Column(Float, default=5.0)
    server_type = Column(String(20), default='global')
    
    # Status et monitoring
    last_offset = Column(Float)
    last_delay = Column(Float)
    last_jitter = Column(Float)
    last_check = Column(DateTime)
    status = Column(String(20), default='unknown')
    
    # Configuration avancée
    polling_interval = Column(Integer, default=60)
    retry_count = Column(Integer, default=3)
    max_retries = Column(Integer, default=5)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<NTPServer {self.name}: {self.address}>'
    
    def to_dict(self):
        """Convertir en dictionnaire pour JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'port': self.port,
            'is_active': self.is_active,
            'priority': self.priority,
            'description': self.description,
            'timeout': self.timeout,
            'max_offset': self.max_offset,
            'critical_offset': self.critical_offset,
            'server_type': self.server_type,
            'last_offset': self.last_offset,
            'last_delay': self.last_delay,
            'last_jitter': self.last_jitter,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'status': self.status,
            'polling_interval': self.polling_interval,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 