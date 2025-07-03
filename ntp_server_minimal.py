"""
Modèle NTPServer - Version minimale compatible avec la base de données actuelle
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text
from backend.database import Base

class NTPServer(Base):
    """Modèle serveur NTP - VERSION MINIMALE COMPATIBLE"""
    
    __tablename__ = 'ntp_servers'
    
    # Colonnes qui existent réellement dans la base de données
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False, index=True)
    port = Column(Integer, default=123)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Colonnes ajoutées récemment
    timeout = Column(Integer, default=10)
    max_offset = Column(Float, default=1.0)
    critical_offset = Column(Float, default=5.0)
    
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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 