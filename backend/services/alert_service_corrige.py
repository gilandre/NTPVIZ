"""
Service d'alertes - Gestion des alertes et notifications
VERSION CORRIGÉE - Problème de session SQLAlchemy résolu
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import or_, and_

from backend.database_manager import db_manager, get_db_session_with_context
from backend.database import Alert, AlertThreshold, NTPServer, SystemConfig

logger = logging.getLogger(__name__)

class AlertService:
    """Service de gestion des alertes avec Database Manager MySQL - VERSION CORRIGÉE"""
    
    def __init__(self):
        self.logger = logger
    
    def check_ntp_threshold(self, server, offset: float, delay: float = None, stratum: int = None):
        """
        Vérifier les seuils NTP et créer des alertes si nécessaire
        VERSION CORRIGÉE - Gestion des sessions améliorée
        
        Args:
            server: Serveur NTP (ID ou objet)
            offset: Décalage temporel (en secondes)
            delay: Délai de réponse (en secondes)
            stratum: Stratum du serveur
        """
        try:
            with get_db_session_with_context() as session:
                # Récupérer l'ID du serveur
                if hasattr(server, 'id'):
                    server_id = server.id
                else:
                    server_id = server
                
                # Récupérer le serveur dans la session courante
                server_obj = session.query(NTPServer).filter(NTPServer.id == server_id).first()
                
                if not server_obj:
                    self.logger.error(f"Serveur NTP introuvable: {server_id}")
                    return
                
                # Récupérer les seuils configurés
                thresholds = session.query(AlertThreshold).filter_by(enabled=True).all()
                
                if not thresholds:
                    self._create_default_thresholds(session)
                    session.commit()
                    thresholds = session.query(AlertThreshold).filter_by(enabled=True).all()
                
                # Vérifier chaque seuil applicable
                for threshold in thresholds:
                    if self._threshold_applies_to_server(threshold, server_obj):
                        self._check_single_threshold(session, server_obj, threshold, offset, delay, stratum)
                    
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des seuils: {e}")
    
    def _threshold_applies_to_server(self, threshold: AlertThreshold, server: NTPServer) -> bool:
        """Vérifier si un seuil s'applique à un serveur donné"""
        if threshold.server_type == 'all':
            return True
        elif threshold.server_type == 'local' and server.is_local:
            return True
        elif threshold.server_type == 'pool' and not server.is_local:
            return True
        return False
    
    def _check_single_threshold(self, session, server: NTPServer, threshold: AlertThreshold, 
                              offset: float, delay: float = None, stratum: int = None):
        """Vérifier un seuil spécifique - VERSION CORRIGÉE"""
        try:
            metric_value = None
            severity = None
            alert_message = ""
            
            severity_labels = {
                'warning': 'Avertissement',
                'critical': 'Critique'
            }
            
            # Vérifier les métriques avec conversion d'unités
            if threshold.metric_name == 'offset' and offset is not None:
                metric_value = abs(offset * 1000)  # Conversion secondes -> millisecondes
                result = threshold.check_threshold(metric_value)
                if result != 'ok':
                    severity = result
                    severity_label = severity_labels.get(result, result)
                    alert_message = f"Décalage temporel {severity_label}: {offset*1000:.1f}ms (seuils: {threshold.warning_threshold}/{threshold.critical_threshold}ms)"
                    
            elif threshold.metric_name == 'latency' and delay is not None:
                metric_value = delay * 1000  # Conversion secondes -> millisecondes
                result = threshold.check_threshold(metric_value)
                if result != 'ok':
                    severity = result
                    severity_label = severity_labels.get(result, result)
                    alert_message = f"Délai de réponse {severity_label}: {delay*1000:.1f}ms (seuils: {threshold.warning_threshold}/{threshold.critical_threshold}ms)"
                    
            elif threshold.metric_name == 'stratum' and stratum is not None:
                metric_value = stratum
                result = threshold.check_threshold(stratum)
                if result != 'ok':
                    severity = result
                    severity_label = severity_labels.get(result, result)
                    alert_message = f"Stratum {severity_label}: {stratum} (seuils: {threshold.warning_threshold}/{threshold.critical_threshold})"
            
            # Créer ou résoudre l'alerte
            if severity:
                self._create_or_update_alert(
                    session=session,
                    server=server,
                    alert_type=threshold.metric_name,
                    severity=severity,
                    message=alert_message,
                    metric_value=metric_value,
                    threshold_value=threshold.critical_threshold if severity == 'critical' else threshold.warning_threshold,
                    threshold_id=threshold.id
                )
            else:
                self._resolve_alert(session, server, threshold.metric_name)
                
        except Exception as e:
            self.logger.error(f"Erreur vérification seuil {threshold.metric_name}: {e}")
    
    def check_server_availability(self, server, is_available: bool, error_message: str = None):
        """Vérifier la disponibilité d'un serveur - VERSION CORRIGÉE"""
        try:
            with get_db_session_with_context() as session:
                # Récupérer l'ID du serveur
                if hasattr(server, 'id'):
                    server_id = server.id
                else:
                    server_id = server
                
                # Récupérer le serveur dans la session courante
                server_obj = session.query(NTPServer).filter(NTPServer.id == server_id).first()
                
                if not server_obj:
                    self.logger.error(f"Serveur NTP introuvable: {server_id}")
                    return
                
                if not is_available:
                    alert_message = f"Serveur indisponible - {server_obj.name}"
                    if error_message:
                        alert_message += f": {error_message}"
                    
                    self._create_or_update_alert(
                        session=session,
                        server=server_obj,
                        alert_type='availability',
                        severity='critical',
                        message=alert_message
                    )
                else:
                    self._resolve_alert(session, server_obj, 'availability')
                    
        except Exception as e:
            self.logger.error(f"Erreur lors de la création d'alerte: {e}")
    
    def _create_or_update_alert(self, session, server: NTPServer, alert_type: str, 
                              severity: str, message: str, metric_value: float = None, 
                              threshold_value: float = None, threshold_id: int = None):
        """Créer une nouvelle alerte ou mettre à jour une existante"""
        try:
            existing_alert = session.query(Alert).filter_by(
                server_id=server.id,
                alert_type=alert_type,
                status='active'
            ).first()
            
            if existing_alert:
                existing_alert.last_occurrence = datetime.utcnow()
                existing_alert.message = message
                existing_alert.metric_value = metric_value
                existing_alert.threshold_value = threshold_value
                existing_alert.occurrence_count += 1
                existing_alert.updated_at = datetime.utcnow()
                
                self.logger.info(f"Alerte mise à jour: {message}")
            else:
                alert_type_labels = {
                    'offset': 'Décalage temporel',
                    'latency': 'Latence',
                    'stratum': 'Stratum',
                    'availability': 'Disponibilité'
                }
                
                alert_type_label = alert_type_labels.get(alert_type, alert_type)
                title = f"Alerte {alert_type_label} - {server.name}"
                
                new_alert = Alert(
                    alert_type=alert_type,
                    title=title,
                    message=message,
                    severity=severity,
                    server_id=server.id,
                    threshold_id=threshold_id,
                    metric_value=metric_value,
                    threshold_value=threshold_value,
                    details={
                        'metric_value': metric_value,
                        'threshold_value': threshold_value,
                        'server_address': server.address
                    }
                )
                
                session.add(new_alert)
                self.logger.info(f"Nouvelle alerte créée: {message}")
            
            session.commit()
            
        except Exception as e:
            self.logger.error(f"Erreur création/mise à jour alerte: {e}")
            session.rollback()
    
    def _resolve_alert(self, session, server: NTPServer, alert_type: str):
        """Résoudre une alerte existante"""
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
            self.logger.error(f"Erreur lors de la résolution des alertes: {e}")
            session.rollback()
    
    def _create_default_thresholds(self, session):
        """Créer les seuils par défaut optimisés"""
        try:
            default_thresholds = [
                {
                    'metric_name': 'offset',
                    'warning_threshold': 50.0,
                    'critical_threshold': 200.0,
                    'unit': 'ms',
                    'description': 'Seuil optimisé pour l'écart de synchronisation'
                },
                {
                    'metric_name': 'latency', 
                    'warning_threshold': 50.0,
                    'critical_threshold': 200.0,
                    'unit': 'ms',
                    'description': 'Seuil optimisé pour le délai de réponse'
                },
                {
                    'metric_name': 'stratum',
                    'warning_threshold': 8.0,
                    'critical_threshold': 15.0,
                    'unit': 'level',
                    'description': 'Seuil optimisé pour le stratum'
                }
            ]
            
            for threshold_config in default_thresholds:
                existing = session.query(AlertThreshold).filter_by(
                    metric_name=threshold_config['metric_name'],
                    server_type='all'
                ).first()
                
                if not existing:
                    threshold = AlertThreshold(
                        metric_name=threshold_config['metric_name'],
                        warning_threshold=threshold_config['warning_threshold'], 
                        critical_threshold=threshold_config['critical_threshold'],
                        unit=threshold_config['unit'],
                        server_type='all',
                        enabled=True,
                        description=threshold_config['description']
                    )
                    session.add(threshold)
            
            self.logger.info("Seuils par défaut optimisés créés")
            
        except Exception as e:
            self.logger.error(f"Erreur création seuils par défaut: {e}")

# Instance globale du service d'alertes
alert_service = AlertService()
