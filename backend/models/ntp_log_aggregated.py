"""
Modles d'agrgation des logs NTP - Optimisation performance BD
Systme automatique d'agrgation par intervalles : 15min, 30min, 1h, 6h, 24h
"""
from datetime import datetime
from backend.app import db
from sqlalchemy.sql import func

class BaseNTPLogAggregated(db.Model):
    """Classe de base pour les logs NTP agrgs"""
    
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('ntp_servers.id'), nullable=False, index=True)
    
    # Priode d'agrgation
    period_start = db.Column(db.DateTime, nullable=False, index=True)
    period_end = db.Column(db.DateTime, nullable=False)
    
    # Statistiques agrges
    query_count = db.Column(db.Integer, default=0)  # Nombre total de requtes
    successful_queries = db.Column(db.Integer, default=0)  # Requtes russies
    failed_queries = db.Column(db.Integer, default=0)  # Requtes choues
    
    # Mtriques d'offset (en millisecondes)
    offset_avg = db.Column(db.Float, nullable=True)  # Offset moyen
    offset_min = db.Column(db.Float, nullable=True)  # Offset minimum
    offset_max = db.Column(db.Float, nullable=True)  # Offset maximum
    offset_std = db.Column(db.Float, nullable=True)  # cart-type de l'offset
    
    # Mtriques de dlai (en millisecondes)
    delay_avg = db.Column(db.Float, nullable=True)  # Dlai moyen
    delay_min = db.Column(db.Float, nullable=True)  # Dlai minimum
    delay_max = db.Column(db.Float, nullable=True)  # Dlai maximum
    
    # Mtriques de stratum
    stratum_avg = db.Column(db.Float, nullable=True)  # Stratum moyen
    stratum_min = db.Column(db.Integer, nullable=True)  # Stratum minimum
    stratum_max = db.Column(db.Integer, nullable=True)  # Stratum maximum
    
    # Taux de succs
    success_rate = db.Column(db.Float, nullable=True)  # % de russite
    
    # Mtadonnes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'query_count': self.query_count,
            'successful_queries': self.successful_queries,
            'failed_queries': self.failed_queries,
            'offset_avg': round(self.offset_avg, 3) if self.offset_avg else None,
            'offset_min': round(self.offset_min, 3) if self.offset_min else None,
            'offset_max': round(self.offset_max, 3) if self.offset_max else None,
            'delay_avg': round(self.delay_avg, 3) if self.delay_avg else None,
            'stratum_avg': round(self.stratum_avg, 1) if self.stratum_avg else None,
            'success_rate': round(self.success_rate, 2) if self.success_rate else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class NTPLog15Min(BaseNTPLogAggregated):
    """Logs NTP agrgs par priode de 15 minutes"""
    __tablename__ = 'ntp_logs_15min'

class NTPLog30Min(BaseNTPLogAggregated):
    """Logs NTP agrgs par priode de 30 minutes"""
    __tablename__ = 'ntp_logs_30min'

class NTPLog1Hour(BaseNTPLogAggregated):
    """Logs NTP agrgs par priode de 1 heure"""
    __tablename__ = 'ntp_logs_1hour'

class NTPLog6Hours(BaseNTPLogAggregated):
    """Logs NTP agrgs par priode de 6 heures"""
    __tablename__ = 'ntp_logs_6hours'

class NTPLog24Hours(BaseNTPLogAggregated):
    """Logs NTP agrgs par priode de 24 heures"""
    __tablename__ = 'ntp_logs_24hours'

class AggregationStatus(db.Model):
    """Table de suivi du statut d'agrgation"""
    
    __tablename__ = 'aggregation_status'
    
    id = db.Column(db.Integer, primary_key=True)
    aggregation_type = db.Column(db.String(20), nullable=False)  # '15min', '30min', '1hour', '6hours', '24hours'
    last_aggregated_at = db.Column(db.DateTime, nullable=True)  # Dernire agrgation effectue
    last_purged_at = db.Column(db.DateTime, nullable=True)  # Dernire purge effectue
    records_aggregated = db.Column(db.Integer, default=0)  # Nombre d'enregistrements agrgs
    records_purged = db.Column(db.Integer, default=0)  # Nombre d'enregistrements purgs
    status = db.Column(db.String(20), default='active')  # 'active', 'running', 'error'
    last_error = db.Column(db.Text, nullable=True)  # Dernire erreur rencontre
    
    # Mtadonnes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_or_create(aggregation_type):
        """Obtenir ou crer un statut d'agrgation"""
        status = AggregationStatus.query.filter_by(aggregation_type=aggregation_type).first()
        if not status:
            status = AggregationStatus(aggregation_type=aggregation_type)
            db.session.add(status)
            db.session.commit()
        return status
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'aggregation_type': self.aggregation_type,
            'last_aggregated_at': self.last_aggregated_at.isoformat() if self.last_aggregated_at else None,
            'last_purged_at': self.last_purged_at.isoformat() if self.last_purged_at else None,
            'records_aggregated': self.records_aggregated,
            'records_purged': self.records_purged,
            'status': self.status,
            'last_error': self.last_error,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 
