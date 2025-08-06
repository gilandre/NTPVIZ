"""
Service d'agrégation automatique des logs NTP
Optimisation des performances de la base de données
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from backend.app import db
from backend.models.ntp_log import NTPLog
from backend.models.ntp_log_aggregated import (
    NTPLog15Min, NTPLog30Min, NTPLog1Hour, NTPLog6Hours, NTPLog24Hours,
    AggregationStatus
)

logger = logging.getLogger(__name__)

class NTPLogAggregationService:
    """Service d'agrégation automatique des logs NTP"""
    
    def __init__(self):
        self.is_running = False
        self.aggregation_thread = None
        self._app_instance = None
        
        # Configuration des intervalles d'agrégation
        self.aggregation_intervals = {
            '15min': {
                'model': NTPLog15Min,
                'minutes': 15,
                'retention_days': 7,  # Garder 7 jours d'agrégations 15min
                'purge_threshold_hours': 2  # Purger les logs bruts après 2h
            },
            '30min': {
                'model': NTPLog30Min,
                'minutes': 30,
                'retention_days': 14,  # Garder 14 jours d'agrégations 30min
                'purge_threshold_hours': 4
            },
            '1hour': {
                'model': NTPLog1Hour,
                'minutes': 60,
                'retention_days': 30,  # Garder 30 jours d'agrégations 1h
                'purge_threshold_hours': 8
            },
            '6hours': {
                'model': NTPLog6Hours,
                'minutes': 360,
                'retention_days': 90,  # Garder 90 jours d'agrégations 6h
                'purge_threshold_hours': 24
            },
            '24hours': {
                'model': NTPLog24Hours,
                'minutes': 1440,
                'retention_days': 365,  # Garder 1 an d'agrégations 24h
                'purge_threshold_hours': 72
            }
        }

    def start_continuous_aggregation(self, app=None, interval_minutes=30):
        """Démarrer l'agrégation continue en arrière-plan"""
        """Démarrer l'agrégation continue en arrière-plan"""
        if self.is_running:
            logger.warning("Service d'agrégation déjà démarré")
            return
        
        self._app_instance = app
        self.is_running = True
        
        self.aggregation_thread = threading.Thread(
            target=self._aggregation_worker,
            args=(interval_minutes,),
            daemon=True
        )
        self.aggregation_thread.start()
        
        logger.info(f"✅ Service d'agrégation démarré (intervalle: {interval_minutes}min)")

    def stop_continuous_aggregation(self):
        """Arrêter l'agrégation continue"""
        """Arrêter l'agrégation continue"""
        self.is_running = False
        if self.aggregation_thread:
            self.aggregation_thread.join(timeout=30)
        
        logger.info("🛑 Service d'agrégation arrêté")

    def _aggregation_worker(self, interval_minutes):
        """Thread worker pour l'agrégation continue"""
        """Thread worker pour l'agrégation continue"""
        while self.is_running:
            try:
                # Créer le contexte d'application si nécessaire
                if self._app_instance:
                    with self._app_instance.app_context():
                        self._perform_full_aggregation()
                else:
                    # Fallback : créer un nouveau contexte d'application
                    from backend.app import create_app
                    app = create_app()
                    with app.app_context():
                        self._perform_full_aggregation()
                        
            except Exception as e:
                logger.error(f"❌ Erreur dans l'agrégation continue: {e}")
            
            # Attendre l'intervalle spécifié
            time.sleep(interval_minutes * 60)

    def _perform_full_aggregation(self):
        """Effectuer l'agrégation complète pour tous les intervalles"""
        """Effectuer l'agrégation complète pour tous les intervalles"""
        try:
            # Créer le contexte d'application si nécessaire
            if self._app_instance:
                with self._app_instance.app_context():
                    self._aggregate_all_intervals()
            else:
                # Fallback : créer un nouveau contexte d'application
                from backend.app import create_app
                app = create_app()
                with app.app_context():
                    self._aggregate_all_intervals()
                    
        except Exception as e:
            logger.error(f"❌ Erreur dans l'agrégation complète: {e}")

    def _aggregate_all_intervals(self):
        """Agréger tous les intervalles"""
        """Agréger tous les intervalles"""
        for interval_name, config in self.aggregation_intervals.items():
            try:
                self._aggregate_interval(interval_name, config)
            except Exception as e:
                logger.error(f"❌ Erreur agréger {interval_name}: {e}")

    def _aggregate_interval(self, interval_name, config):
        """Agréger un intervalle spécifique"""
        """Agréger un intervalle spécifique"""
        model = config['model']
        minutes = config['minutes']
        
        # Calculer la période d'agrégation
        now = datetime.utcnow()
        period_start = now - timedelta(minutes=minutes)
        
        # Vérifier si l'agrégation a déjà été faite pour cette période
        existing = db.session.query(model).filter(
            model.period_start >= period_start,
            model.period_end <= now
        ).first()
        
        if existing:
            logger.debug(f"⏭️ Agréger {interval_name}: déjà fait pour {period_start}")
            return
        
        # Agréger les données
        aggregated_data = self._calculate_aggregated_data(period_start, now)
        
        if aggregated_data:
            # Créer l'enregistrement agrégé
            aggregated_record = model(
                period_start=period_start,
                period_end=now,
                total_requests=aggregated_data['total_requests'],
                successful_requests=aggregated_data['successful_requests'],
                failed_requests=aggregated_data['failed_requests'],
                avg_offset=aggregated_data['avg_offset'],
                avg_delay=aggregated_data['avg_delay'],
                avg_jitter=aggregated_data['avg_jitter'],
                min_offset=aggregated_data['min_offset'],
                max_offset=aggregated_data['max_offset'],
                min_delay=aggregated_data['min_delay'],
                max_delay=aggregated_data['max_delay'],
                min_jitter=aggregated_data['min_jitter'],
                max_jitter=aggregated_data['max_jitter'],
                std_offset=aggregated_data['std_offset'],
                std_delay=aggregated_data['std_delay'],
                std_jitter=aggregated_data['std_jitter']
            )
            
            db.session.add(aggregated_record)
            db.session.commit()
            
            logger.info(f"✅ Agréger {interval_name}: {aggregated_data['total_requests']} requêtes")
            
            # Purger les anciens logs bruts si nécessaire
            self._purge_old_raw_logs(config['purge_threshold_hours'])
            
            # Purger les anciennes agrégations
            self._purge_old_aggregations(model, config['retention_days'])

    def _calculate_aggregated_data(self, start_time, end_time):
        """Calculer les données agrégées pour une période"""
        """Calculer les données agrégées pour une période"""
        try:
            # Requête pour obtenir les statistiques agrégées
            result = db.session.query(
                func.count(NTPLog.id).label('total_requests'),
                func.sum(func.case((NTPLog.status == 'success', 1), else_=0)).label('successful_requests'),
                func.sum(func.case((NTPLog.status != 'success', 1), else_=0)).label('failed_requests'),
                func.avg(NTPLog.offset).label('avg_offset'),
                func.avg(NTPLog.delay).label('avg_delay'),
                func.avg(NTPLog.jitter).label('avg_jitter'),
                func.min(NTPLog.offset).label('min_offset'),
                func.max(NTPLog.offset).label('max_offset'),
                func.min(NTPLog.delay).label('min_delay'),
                func.max(NTPLog.delay).label('max_delay'),
                func.min(NTPLog.jitter).label('min_jitter'),
                func.max(NTPLog.jitter).label('max_jitter'),
                func.stddev(NTPLog.offset).label('std_offset'),
                func.stddev(NTPLog.delay).label('std_delay'),
                func.stddev(NTPLog.jitter).label('std_jitter')
            ).filter(
                and_(
                    NTPLog.timestamp >= start_time,
                    NTPLog.timestamp <= end_time
                )
            ).first()
            
            if result and result.total_requests > 0:
                return {
                    'total_requests': result.total_requests,
                    'successful_requests': result.successful_requests or 0,
                    'failed_requests': result.failed_requests or 0,
                    'avg_offset': float(result.avg_offset or 0),
                    'avg_delay': float(result.avg_delay or 0),
                    'avg_jitter': float(result.avg_jitter or 0),
                    'min_offset': float(result.min_offset or 0),
                    'max_offset': float(result.max_offset or 0),
                    'min_delay': float(result.min_delay or 0),
                    'max_delay': float(result.max_delay or 0),
                    'min_jitter': float(result.min_jitter or 0),
                    'max_jitter': float(result.max_jitter or 0),
                    'std_offset': float(result.std_offset or 0),
                    'std_delay': float(result.std_delay or 0),
                    'std_jitter': float(result.std_jitter or 0)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul données agrégées: {e}")
            return None

    def _purge_old_raw_logs(self, threshold_hours):
        """Purger les anciens logs bruts"""
        """Purger les anciens logs bruts"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=threshold_hours)
            deleted_count = db.session.query(NTPLog).filter(
                NTPLog.timestamp < cutoff_time
            ).delete()
            
            if deleted_count > 0:
                db.session.commit()
                logger.info(f"🗑️ Purge logs bruts: {deleted_count} enregistrements supprimés")
                
        except Exception as e:
            logger.error(f"❌ Erreur purge logs bruts: {e}")
            db.session.rollback()

    def _purge_old_aggregations(self, model, retention_days):
        """Purger les anciennes agrégations"""
        """Purger les anciennes agrégations"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=retention_days)
            deleted_count = db.session.query(model).filter(
                model.period_end < cutoff_time
            ).delete()
            
            if deleted_count > 0:
                db.session.commit()
                logger.info(f"🗑️ Purge agrégations {model.__name__}: {deleted_count} enregistrements supprimés")
                
        except Exception as e:
            logger.error(f"❌ Erreur purge agrégations {model.__name__}: {e}")
            db.session.rollback()

    def get_aggregation_status(self):
        """Obtenir le statut de l'agrégation"""
        """Obtenir le statut de l'agrégation"""
        try:
            status = db.session.query(AggregationStatus).first()
            if not status:
                status = AggregationStatus(
                    last_15min_aggregation=None,
                    last_30min_aggregation=None,
                    last_1hour_aggregation=None,
                    last_6hours_aggregation=None,
                    last_24hours_aggregation=None,
                    total_aggregated_records=0
                )
                db.session.add(status)
                db.session.commit()
            
            return {
                'is_running': self.is_running,
                'last_15min_aggregation': status.last_15min_aggregation,
                'last_30min_aggregation': status.last_30min_aggregation,
                'last_1hour_aggregation': status.last_1hour_aggregation,
                'last_6hours_aggregation': status.last_6hours_aggregation,
                'last_24hours_aggregation': status.last_24hours_aggregation,
                'total_aggregated_records': status.total_aggregated_records
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur obtenir statut agrégation: {e}")
            return {
                'is_running': self.is_running,
                'error': str(e)
            }

    def get_aggregation_stats(self, interval='24hours', hours=24):
        """Obtenir les statistiques d'agrégation"""
        """Obtenir les statistiques d'agrégation"""
        try:
            if interval not in self.aggregation_intervals:
                return None
            
            model = self.aggregation_intervals[interval]['model']
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            results = db.session.query(model).filter(
                model.period_start >= start_time
            ).order_by(model.period_start.desc()).all()
            
            return [{
                'period_start': result.period_start.isoformat(),
                'period_end': result.period_end.isoformat(),
                'total_requests': result.total_requests,
                'successful_requests': result.successful_requests,
                'failed_requests': result.failed_requests,
                'avg_offset': result.avg_offset,
                'avg_delay': result.avg_delay,
                'avg_jitter': result.avg_jitter,
                'min_offset': result.min_offset,
                'max_offset': result.max_offset,
                'min_delay': result.min_delay,
                'max_delay': result.max_delay,
                'min_jitter': result.min_jitter,
                'max_jitter': result.max_jitter,
                'std_offset': result.std_offset,
                'std_delay': result.std_delay,
                'std_jitter': result.std_jitter
            } for result in results]
            
        except Exception as e:
            logger.error(f"❌ Erreur obtenir stats agrégation {interval}: {e}")
            return None

# Instance globale du service
aggregation_service = NTPLogAggregationService() 