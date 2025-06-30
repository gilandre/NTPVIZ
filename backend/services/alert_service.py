"""
Service d'alertes - Gestion des alertes et notifications
VERSION MYSQL - Utilise le Database Manager centralisé
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import or_, and_

from backend.database_manager import db_manager, get_db_session_with_context
from backend.models.alert import Alert
from backend.models.alert_threshold import AlertThreshold
from backend.models.ntp_server import NTPServer
from backend.models.system_config import SystemConfig

logger = logging.getLogger(__name__)

class AlertService:
    """Service de gestion des alertes avec Database Manager MySQL"""
    
    def __init__(self):
        self.logger = logger
    
    def check_ntp_threshold(self, server: NTPServer, offset: float, delay: float = None, stratum: int = None):
        """
        Vérifier les seuils NTP et créer des alertes si nécessaire
        
        Args:
            server: Serveur NTP
            offset: Décalage temporel
            delay: Délai de réponse
            stratum: Stratum du serveur
        """
        try:
            with get_db_session_with_context() as session:
                # Récupérer les seuils configurés
                thresholds = session.query(AlertThreshold).filter_by(
                    server_id=server.id,
                    is_active=True
                ).all()
                
                if not thresholds:
                    # Utiliser les seuils par défaut
                    self._create_default_thresholds(session, server.id)
                    thresholds = session.query(AlertThreshold).filter_by(
                        server_id=server.id,
                        is_active=True
                    ).all()
                
                # Vérifier chaque seuil
                for threshold in thresholds:
                    self._check_single_threshold(session, server, threshold, offset, delay, stratum)
                    
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des seuils: {e}")
    
    def _check_single_threshold(self, session, server: NTPServer, threshold: AlertThreshold, 
                              offset: float, delay: float = None, stratum: int = None):
        """
        Vérifier un seuil spécifique
        
        Args:
            session: Session MySQL
            server: Serveur NTP
            threshold: Seuil à vérifier
            offset: Décalage temporel
            delay: Délai de réponse
            stratum: Stratum du serveur
        """
        try:
            alert_needed = False
            alert_message = ""
            metric_value = None
            
            # Déterminer quelle métrique vérifier
            if threshold.threshold_type == 'offset':
                metric_value = abs(offset) if offset is not None else None
                if metric_value is not None and metric_value > threshold.threshold_value:
                    alert_needed = True
                    alert_message = f"Décalage temporel élevé: {offset:.3f}s (seuil: {threshold.threshold_value}s)"
                    
            elif threshold.threshold_type == 'delay' and delay is not None:
                metric_value = delay
                if delay > threshold.threshold_value:
                    alert_needed = True
                    alert_message = f"Délai de réponse élevé: {delay:.3f}s (seuil: {threshold.threshold_value}s)"
                    
            elif threshold.threshold_type == 'stratum' and stratum is not None:
                metric_value = stratum
                if stratum > threshold.threshold_value:
                    alert_needed = True
                    alert_message = f"Stratum élevé: {stratum} (seuil: {threshold.threshold_value})"
            
            # Créer ou résoudre l'alerte
            if alert_needed:
                self._create_or_update_alert(
                    session=session,
                    server=server,
                    alert_type=threshold.threshold_type,
                    severity=threshold.severity,
                    message=alert_message,
                    metric_value=metric_value,
                    threshold_value=threshold.threshold_value
                )
            else:
                # Résoudre l'alerte si elle existe
                self._resolve_alert(session, server, threshold.threshold_type)
                
        except Exception as e:
            self.logger.error(f"Erreur vérification seuil {threshold.threshold_type}: {e}")
    
    def check_server_availability(self, server: NTPServer, is_available: bool, error_message: str = None):
        """
        Vérifier la disponibilité d'un serveur et créer des alertes
        
        Args:
            server: Serveur NTP
            is_available: Serveur disponible ou non
            error_message: Message d'erreur si indisponible
        """
        try:
            with get_db_session_with_context() as session:
                if not is_available:
                    # Créer une alerte de disponibilité
                    alert_message = f"Serveur indisponible - {server.name}"
                    if error_message:
                        alert_message += f": {error_message}"
                    
                    self._create_or_update_alert(
                        session=session,
                        server=server,
                        alert_type='availability',
                        severity='critical',
                        message=alert_message
                    )
                else:
                    # Résoudre l'alerte de disponibilité
                    self._resolve_alert(session, server, 'availability')
                    
        except Exception as e:
            self.logger.error(f"Erreur lors de la création d'alerte: {e}")
    
    def _create_or_update_alert(self, session, server: NTPServer, alert_type: str, 
                              severity: str, message: str, metric_value: float = None, 
                              threshold_value: float = None):
        """
        Créer une nouvelle alerte ou mettre à jour une existante
        
        Args:
            session: Session MySQL
            server: Serveur NTP
            alert_type: Type d'alerte
            severity: Sévérité
            message: Message d'alerte
            metric_value: Valeur de la métrique
            threshold_value: Valeur du seuil
        """
        try:
            # Chercher une alerte existante
            existing_alert = session.query(Alert).filter_by(
                server_id=server.id,
                alert_type=alert_type,
                status='active'
            ).first()
            
            if existing_alert:
                # Mettre à jour l'alerte existante
                existing_alert.last_occurrence = datetime.utcnow()
                existing_alert.message = message
                existing_alert.metric_value = metric_value
                existing_alert.threshold_value = threshold_value
                existing_alert.occurrence_count += 1
                
                self.logger.info(f"Alerte mise à jour: {message}")
            else:
                # Créer une nouvelle alerte
                new_alert = Alert(
                    server_id=server.id,
                    alert_type=alert_type,
                    severity=severity,
                    status='active',
                    message=message,
                    metric_value=metric_value,
                    threshold_value=threshold_value,
                    first_occurrence=datetime.utcnow(),
                    last_occurrence=datetime.utcnow(),
                    occurrence_count=1
                )
                
                session.add(new_alert)
                self.logger.info(f"Nouvelle alerte créée: {message}")
            
        except Exception as e:
            self.logger.error(f"Erreur création/mise à jour alerte: {e}")
    
    def _resolve_alert(self, session, server: NTPServer, alert_type: str):
        """
        Résoudre une alerte existante
        
        Args:
            session: Session MySQL
            server: Serveur NTP
            alert_type: Type d'alerte à résoudre
        """
        try:
            # Chercher les alertes actives à résoudre
            active_alerts = session.query(Alert).filter_by(
                server_id=server.id,
                alert_type=alert_type,
                status='active'
            ).all()
            
            for alert in active_alerts:
                alert.status = 'resolved'
                alert.resolved_at = datetime.utcnow()
                self.logger.info(f"Alerte résolue: {alert.message}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la résolution des alertes: {e}")
    
    def _create_default_thresholds(self, session, server_id: int):
        """
        Créer les seuils par défaut pour un serveur
        
        Args:
            session: Session MySQL
            server_id: ID du serveur
        """
        try:
            default_thresholds = [
                {
                    'threshold_type': 'offset',
                    'threshold_value': 1.0,  # 1 seconde
                    'severity': 'warning'
                },
                {
                    'threshold_type': 'offset',
                    'threshold_value': 5.0,  # 5 secondes
                    'severity': 'critical'
                },
                {
                    'threshold_type': 'delay',
                    'threshold_value': 2.0,  # 2 secondes
                    'severity': 'warning'
                },
                {
                    'threshold_type': 'stratum',
                    'threshold_value': 10,
                    'severity': 'warning'
                }
            ]
            
            for threshold_config in default_thresholds:
                threshold = AlertThreshold(
                    server_id=server_id,
                    threshold_type=threshold_config['threshold_type'],
                    threshold_value=threshold_config['threshold_value'],
                    severity=threshold_config['severity'],
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                session.add(threshold)
            
            self.logger.info(f"Seuils par défaut créés pour le serveur {server_id}")
            
        except Exception as e:
            self.logger.error(f"Erreur création seuils par défaut: {e}")
    
    def get_active_alerts(self, server_id: int = None, severity: str = None) -> List[Dict]:
        """
        Récupérer les alertes actives
        
        Args:
            server_id: ID du serveur (optionnel)
            severity: Sévérité des alertes (optionnel)
            
        Returns:
            Liste des alertes actives
        """
        try:
            with get_db_session_with_context() as session:
                query = session.query(Alert).filter_by(status='active')
                
                if server_id:
                    query = query.filter_by(server_id=server_id)
                    
                if severity:
                    query = query.filter_by(severity=severity)
                
                alerts = query.order_by(Alert.last_occurrence.desc()).all()
                
                # Convertir en dictionnaires
                result = []
                for alert in alerts:
                    alert_dict = {
                        'id': alert.id,
                        'server_id': alert.server_id,
                        'server_name': alert.server.name if alert.server else 'Serveur inconnu',
                        'alert_type': alert.alert_type,
                        'severity': alert.severity,
                        'status': alert.status,
                        'message': alert.message,
                        'metric_value': alert.metric_value,
                        'threshold_value': alert.threshold_value,
                        'first_occurrence': alert.first_occurrence.isoformat() if alert.first_occurrence else None,
                        'last_occurrence': alert.last_occurrence.isoformat() if alert.last_occurrence else None,
                        'occurrence_count': alert.occurrence_count
                    }
                    result.append(alert_dict)
                
                return result
                
        except Exception as e:
            self.logger.error(f"Erreur récupération alertes actives: {e}")
            return []
    
    def acknowledge_alert(self, alert_id: int, user_id: int = None) -> bool:
        """
        Acquitter une alerte
        
        Args:
            alert_id: ID de l'alerte
            user_id: ID de l'utilisateur (optionnel)
            
        Returns:
            True si succès, False sinon
        """
        try:
            with get_db_session_with_context() as session:
                alert = session.get(Alert, alert_id)
                if not alert:
                    return False
                
                alert.status = 'acknowledged'
                alert.acknowledged_at = datetime.utcnow()
                if user_id:
                    alert.acknowledged_by = user_id
                
                self.logger.info(f"Alerte {alert_id} acquittée")
                return True
                
        except Exception as e:
            self.logger.error(f"Erreur acquittement alerte {alert_id}: {e}")
            return False
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """
        Obtenir les statistiques des alertes
        
        Returns:
            Dictionnaire avec les statistiques
        """
        try:
            with get_db_session_with_context() as session:
                # Compter les alertes par statut
                active_count = session.query(Alert).filter_by(status='active').count()
                acknowledged_count = session.query(Alert).filter_by(status='acknowledged').count()
                resolved_count = session.query(Alert).filter_by(status='resolved').count()
                
                # Compter par sévérité (alertes actives)
                critical_count = session.query(Alert).filter_by(
                    status='active', severity='critical'
                ).count()
                warning_count = session.query(Alert).filter_by(
                    status='active', severity='warning'
                ).count()
                info_count = session.query(Alert).filter_by(
                    status='active', severity='info'
                ).count()
                
                # Alertes récentes (dernières 24h)
                yesterday = datetime.utcnow() - timedelta(days=1)
                recent_count = session.query(Alert).filter(
                    Alert.first_occurrence >= yesterday
                ).count()
                
                return {
                    'active_alerts': active_count,
                    'acknowledged_alerts': acknowledged_count,
                    'resolved_alerts': resolved_count,
                    'critical_alerts': critical_count,
                    'warning_alerts': warning_count,
                    'info_alerts': info_count,
                    'recent_alerts_24h': recent_count,
                    'total_alerts': active_count + acknowledged_count + resolved_count
                }
                
        except Exception as e:
            self.logger.error(f"Erreur récupération statistiques alertes: {e}")
            return {
                'active_alerts': 0,
                'acknowledged_alerts': 0,
                'resolved_alerts': 0,
                'critical_alerts': 0,
                'warning_alerts': 0,
                'info_alerts': 0,
                'recent_alerts_24h': 0,
                'total_alerts': 0
            }

# Instance globale du service d'alertes
alert_service = AlertService() 
