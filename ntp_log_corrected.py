"""
Modèle NTPLog - Version alignée avec la structure MySQL réelle
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from backend.database import Base

class NTPLog(Base):
    """Modèle NTPLog - ALIGNÉ AVEC LA STRUCTURE MYSQL RÉELLE"""
    
    __tablename__ = 'ntp_logs'
    
    # Colonnes existantes dans la table MySQL réelle
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey('ntp_servers.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Colonne address requise par le service NTP
    address = Column(String(255), nullable=True)
    
    # Métriques NTP - NOMS EXACTS DE LA TABLE
    offset_ms = Column(Float, nullable=True)    # Table a 'offset_ms' pas 'offset'
    delay_ms = Column(Float, nullable=True)     # Table a 'delay_ms' pas 'delay'  
    jitter_ms = Column(Float, nullable=True)    # Table a 'jitter_ms'
    stratum = Column(Integer, nullable=True)    # ✅ Même nom
    status = Column(String(20), nullable=True)  # ✅ Même nom
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Nouvelles colonnes ajoutées
    local_time = Column(DateTime, nullable=True)
    server_time = Column(DateTime, nullable=True)
    latency = Column(Float, nullable=True)
    quality_indicator = Column(String(10), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Colonnes NTP supplémentaires requises par le service
    poll = Column(Integer, nullable=True)
    reach = Column(Integer, nullable=True)
    response_time = Column(Float, nullable=True)
    query_timestamp = Column(DateTime, nullable=True)
    
    # Méthodes de compatibilité pour l'ancien code
    @property
    def offset(self):
        """Compatibilité: renvoie offset_ms converti en secondes"""
        return self.offset_ms / 1000.0 if self.offset_ms is not None else None
    
    @offset.setter
    def offset(self, value):
        """Compatibilité: stocke en ms dans offset_ms"""
        self.offset_ms = value * 1000.0 if value is not None else None
    
    @property
    def delay(self):
        """Compatibilité: renvoie delay_ms"""
        return self.delay_ms
    
    @delay.setter
    def delay(self, value):
        """Compatibilité: stocke en delay_ms"""
        self.delay_ms = value
    
    @property
    def jitter(self):
        """Compatibilité: renvoie jitter_ms"""
        return self.jitter_ms
    
    @jitter.setter
    def jitter(self, value):
        """Compatibilité: stocke en jitter_ms"""
        self.jitter_ms = value
    
    def __repr__(self):
        return f'<NTPLog {self.server_id} {self.timestamp}>'
    
    def to_dict(self):
        """Convertir en dictionnaire pour API"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'offset': self.offset,  # Utilise la propriété de compatibilité
            'delay': self.delay,
            'jitter': self.jitter,
            'stratum': self.stratum,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 