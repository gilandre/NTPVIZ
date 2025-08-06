"""
Service d'alertes - VERSION PRODUCTION ROBUSTE
Gestion complète des alertes avec session SQLAlchemy optimisée
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import or_, and_

from backend.database_manager import db_manager, get_db_session_with_context
from backend.database import Alert, AlertThreshold, NTPServer, SystemConfig

logger = logging.getLogger(__name__)

class AlertService:
    """Service de gestion des alertes - VERSION PRODUCTION"""
    
    def __init__(self):
        self.logger = logger
        self.alertes_cache = {}
        self.derniere_verification = None
    
    def check_ntp_threshold(self, server, offset: float, delay: float = None, stratum: int = None):
        """
        Vérifier les seuils NTP et créer des alertes - VERSION ROBUSTE
        """
        try:
            # Validation des paramètres
            if offset is None and delay is None and stratum is None:
                return
            
            with get_db_session_with_context() as session:
                # Récupération sécurisée du serveur
                server_obj = self._get_server_safe(session, server)
                if not server_obj:
                    return
                
                # Récupération des seuils avec cache
                thresholds = self._get_thresholds_cached(session)
                if not thresholds:
                    return
                
                # Vérification de chaque seuil
                for threshold in thresholds:
                    if self._threshold_applies_to_server(threshold, server_obj):
                        self._check_single_threshold_safe(
                            session, server_obj, threshold, offset, delay, stratum
                        )
                
                # Mise à jour du cache
                self.derniere_verification = datetime.utcnow()
                
        except Exception as e:
            self.logger.error(f"Erreur vérification seuils serveur {server}: {e}")
    
    def _get_server_safe(self, session, server):
        """Récupération sécurisée du serveur"""
        try:
            if hasattr(server, 'id'):
                server_id = server.id
            else:
                server_id = server
            
            return session.query(NTPServer).filter(NTPServer.id == server_id).first()
        except Exception as e:
            self.logger.error(f"Erreur récupération serveur: {e}")
            return None
    
    def _get_thresholds_cached(self, session):
        """Récupération des seuils avec cache"""
        try:
            cache_key = 'thresholds_active'
            now = datetime.utcnow()
            
            # Vérifier le cache (5 minutes)
            if (cache_key in self.alertes_cache and 
                now - self.alertes_cache[cache_key]['timestamp'] < timedelta(minutes=5)):
                return self.alertes_cache[cache_key]['data']
            
            # Récupérer depuis la base
            thresholds = session.query(AlertThreshold).filter_by(enabled=True).all()
            
            if not thresholds:
                self._create_default_thresholds(session)
                session.commit()
                thresholds = session.query(AlertThreshold).filter_by(enabled=True).all()
            
            # Mettre en cache
            self.alertes_cache[cache_key] = {
                'data': thresholds,
                'timestamp': now
            }
            
            return thresholds
            
        except Exception as e:
            self.logger.error(f"Erreur récupération seuils: {e}")
            return []
    
    def _check_single_threshold_safe(self, session, server, threshold, offset, delay, stratum):
        """Vérification sécurisée d'un seuil"""
        try:
            metric_value = None
            severity = None
            alert_message = ""
            
            # Conversion et vérification des métriques
            if threshold.metric_name == 'offset' and offset is not None:
                # Conversion secondes -> millisecondes
                metric_value = abs(offset * 1000)
                result = threshold.check_threshold(metric_value)
                if result != 'ok':
                    severity = result
                    alert_message = f"Décalage temporel {result}: {metric_value:.1f}ms (seuils: {threshold.warning_threshold}/{threshold.critical_threshold}ms)"
            
            elif threshold.metric_name == 'latency' and delay is not None:
                # Conversion secondes -> millisecondes
                metric_value = delay * 1000
                result = threshold.check_threshold(metric_value)
                if result != 'ok':
                    severity = result
                    alert_message = f"Latence {result}: {metric_value:.1f}ms (seuils: {threshold.warning_threshold}/{threshold.critical_threshold}ms)"
            
            elif threshold.metric_name == 'stratum' and stratum is not None:
                metric_value = stratum
                result = threshold.check_threshold(stratum)
                if result != 'ok':
                    severity = result
                    alert_message = f"Stratum {result}: {stratum} (seuils: {threshold.warning_threshold}/{threshold.critical_threshold})"
            
            # Traitement de l'alerte
            if severity:
                self._create_or_update_alert_safe(
                    session, server, threshold.metric_name, severity, 
                    alert_message, metric_value, threshold.id
                )
            else:
                self._resolve_alert_safe(session, server, threshold.metric_name)
                
        except Exception as e:
            self.logger.error(f"Erreur vérification seuil {threshold.metric_name}: {e}")
    
    def _create_or_update_alert_safe(self, session, server, alert_type, severity, message, metric_value, threshold_id):
        """Création/mise à jour sécurisée d'alerte"""
        try:
            # Rechercher alerte existante
            existing_alert = session.query(Alert).filter_by(
                server_id=server.id,
                alert_type=alert_type,
                status='active'
            ).first()
            
            if existing_alert:
                # Mise à jour
                existing_alert.last_occurrence = datetime.utcnow()
                existing_alert.message = message
                existing_alert.metric_value = metric_value
                existing_alert.occurrence_count += 1
                existing_alert.updated_at = datetime.utcnow()
                
                self.logger.info(f"Alerte mise à jour: {message}")
            else:
                # Création
                title = f"Alerte {alert_type.title()} - {server.name}"
                
                new_alert = Alert(
                    alert_type=alert_type,
                    title=title,
                    message=message,
                    severity=severity,
                    server_id=server.id,
                    threshold_id=threshold_id,
                    metric_value=metric_value,
                    first_occurrence=datetime.utcnow(),
                    last_occurrence=datetime.utcnow()
                )
                
                session.add(new_alert)
                self.logger.info(f"Nouvelle alerte créée: {message}")
            
            session.commit()
            
        except Exception as e:
            self.logger.error(f"Erreur création/mise à jour alerte: {e}")
            session.rollback()
    
    def _resolve_alert_safe(self, session, server, alert_type):
        """Résolution sécurisée d'alerte"""
        try:
            active_alerts = session.query(Alert).filter_by(
                server_id=server.id,
                alert_type=alert_type,
                status='active'
            ).all()
            
            for alert in active_alerts:
                alert.status = 'resolved'
                alert.resolved_at = datetime.utcnow()
                alert.updated_at = datetime.utcnow()
                self.logger.info(f"Alerte résolue: {alert.message}")
            
            if active_alerts:
                session.commit()
                
        except Exception as e:
            self.logger.error(f"Erreur résolution alerte: {e}")
            session.rollback()
    
    def _threshold_applies_to_server(self, threshold, server):
        """Vérifier si un seuil s'applique à un serveur"""
        if threshold.server_type == 'all':
            return True
        elif threshold.server_type == 'local' and getattr(server, 'is_local', False):
            return True
        elif threshold.server_type == 'pool' and not getattr(server, 'is_local', True):
            return True
        return False
    
    def _create_default_thresholds(self, session):
        """Créer les seuils par défaut de production"""
        try:
            default_thresholds = [
                {
                    'metric_name': 'offset',
                    'warning_threshold': 50.0,
                    'critical_threshold': 200.0,
                    'unit': 'ms',
                    'description': 'Seuil production offset'
                },
                {
                    'metric_name': 'latency',
                    'warning_threshold': 100.0,
                    'critical_threshold': 500.0,
                    'unit': 'ms',
                    'description': 'Seuil production latency'
                },
                {
                    'metric_name': 'stratum',
                    'warning_threshold': 8.0,
                    'critical_threshold': 15.0,
                    'unit': 'level',
                    'description': 'Seuil production stratum'
                }
            ]
            
            for config in default_thresholds:
                existing = session.query(AlertThreshold).filter_by(
                    metric_name=config['metric_name'],
                    server_type='all'
                ).first()
                
                if not existing:
                    threshold = AlertThreshold(
                        metric_name=config['metric_name'],
                        warning_threshold=config['warning_threshold'],
                        critical_threshold=config['critical_threshold'],
                        unit=config['unit'],
                        server_type='all',
                        enabled=True,
                        description=config['description']
                    )
                    session.add(threshold)
            
            self.logger.info("Seuils par défaut de production créés")
            
        except Exception as e:
            self.logger.error(f"Erreur création seuils par défaut: {e}")
    
    def check_server_availability(self, server, is_available: bool, error_message: str = None):
        """Vérifier la disponibilité d'un serveur"""
        try:
            with get_db_session_with_context() as session:
                server_obj = self._get_server_safe(session, server)
                if not server_obj:
                    return
                
                if not is_available:
                    message = f"Serveur indisponible - {server_obj.name}"
                    if error_message:
                        message += f": {error_message}"
                    
                    self._create_or_update_alert_safe(
                        session, server_obj, 'availability', 'critical',
                        message, None, None
                    )
                else:
                    self._resolve_alert_safe(session, server_obj, 'availability')
                    
        except Exception as e:
            self.logger.error(f"Erreur vérification disponibilité: {e}")
    
    def get_stats(self):
        """Obtenir les statistiques des alertes"""
        try:
            with get_db_session_with_context() as session:
                stats = {
                    'active_alerts': session.query(Alert).filter_by(status='active').count(),
                    'critical_alerts': session.query(Alert).filter_by(status='active', severity='critical').count(),
                    'warning_alerts': session.query(Alert).filter_by(status='active', severity='warning').count(),
                    'resolved_alerts': session.query(Alert).filter_by(status='resolved').count(),
                    'last_check': self.derniere_verification.isoformat() if self.derniere_verification else None
                }
                return stats
        except Exception as e:
            self.logger.error(f"Erreur récupération stats: {e}")
            return {}

# Instance globale du service
alert_service = AlertService()
