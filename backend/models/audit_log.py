"""
Modèle AuditLog - Persistance des logs d'audit
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from backend.database import Base


class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = Column(Integer, index=True, nullable=True)
    username = Column(String(150), index=True, nullable=True)
    role = Column(String(50), nullable=True)
    action = Column(String(100), index=True, nullable=False)
    resource = Column(String(100), index=True, nullable=True)
    resource_id = Column(String(100), index=True, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    method = Column(String(10), nullable=True)
    endpoint = Column(String(200), nullable=True)
    url = Column(Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role,
            'action': self.action,
            'resource': self.resource,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'method': self.method,
            'endpoint': self.endpoint,
            'url': self.url
        }


