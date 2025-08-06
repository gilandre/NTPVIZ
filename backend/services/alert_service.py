"""
Service d'alertes - VERSION UNIFIÉE AVEC THRESHOLDMANAGER
Gestion complète des alertes avec seuils centralisés
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import or_, and_

from backend.database_manager import db_manager, get_db_session_with_context
from backend.database import Alert, AlertThreshold, NTPServer, SystemConfig
from backend.services.threshold_manager import threshold_manager

logger = logging.getLogger(__name__)

class AlertService:
    """Service de gestion des alertes - VERSION UNIFIÉE"""
    
    def __init__(self):
        self.logger = logger
        self.alertes_cache = {}
        self.derniere_verification = None
    
    def check_ntp_threshold(self, server, offset: float, delay: float = None, stratum: int = None):
        """
        Vérifier les seuils NTP et créer des alertes - VERSION UNIFIÉE
        Utilise le ThresholdManager centralisé
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
                
                # Déterminer le type de serveur pour les seuils
                server_type = self._get_server_type(server_obj)
                
                # Vérification des seuils avec ThresholdManager
                self._check_offset_threshold(session, server_obj, offset, server_type)
                self._check_latency_threshold(session, server_obj, delay, server_type)
                self._check_stratum_threshold(session, server_obj, stratum, server_type)
                
                # Mise à jour du cache
                self.derniere_verification = datetime.utcnow()
                
        except Exception as e:
            self.logger.error(f"Erreur vérification seuils serveur {server}: {e}")
    
    def _check_offset_threshold(self, session, server: NTPServer, offset: float, server_type: str):
        """Vérifier le seuil d'offset avec ThresholdManager"""
        if offset is None:
            return
        
        # Convertir en millisecondes pour la comparaison
        offset_ms = abs(offset * 1000)
        severity, threshold = threshold_manager.check_threshold('offset', offset_ms, server_type)
        
        if severity != 'ok' and threshold:
            # Créer l'alerte
            alert_message = f"Offset {severity}: {offset_ms:.2f}ms (seuils: {threshold['warning_threshold']}/{threshold['critical_threshold']}ms)"
            
            self._create_or_update_alert_safe(
                session, server, 'offset', severity, 
                alert_message, offset_ms, threshold['id']
            )
        else:
            # Résoudre l'alerte si elle existe
            self._resolve_alert_safe(session, server, 'offset')
    
    def _check_latency_threshold(self, session, server: NTPServer, delay: float, server_type: str):
        """Vérifier le seuil de latence avec ThresholdManager"""
        if delay is None:
            return
        
        # Convertir en millisecondes pour la comparaison
        delay_ms = abs(delay * 1000)
        severity, threshold = threshold_manager.check_threshold('latency', delay_ms, server_type)
        
        if severity != 'ok' and threshold:
            # Créer l'alerte
            alert_message = f"Latence {severity}: {delay_ms:.2f}ms (seuils: {threshold['warning_threshold']}/{threshold['critical_threshold']}ms)"
            
            self._create_or_update_alert_safe(
                session, server, 'latency', severity, 
                alert_message, delay_ms, threshold['id']
            )
        else:
            # Résoudre l'alerte si elle existe
            self._resolve_alert_safe(session, server, 'latency')
    
    def _check_stratum_threshold(self, session, server: NTPServer, stratum: int, server_type: str):
        """Vérifier le seuil de stratum avec ThresholdManager"""
        if stratum is None:
            return
        
        severity, threshold = threshold_manager.check_threshold('stratum', stratum, server_type)
        
        if severity != 'ok' and threshold:
            # Créer l'alerte
            alert_message = f"Stratum {severity}: {stratum} (seuils: {threshold['warning_threshold']}/{threshold['critical_threshold']})"
            
            self._create_or_update_alert_safe(
                session, server, 'stratum', severity, 
                alert_message, stratum, threshold['id']
            )
        else:
            # Résoudre l'alerte si elle existe
            self._resolve_alert_safe(session, server, 'stratum')
    
    def _get_server_safe(self, session, server) -> Optional[NTPServer]:
        """Récupération sécurisée du serveur"""
        try:
            if isinstance(server, NTPServer):
                return server
            elif isinstance(server, int):
                return session.query(NTPServer).filter_by(id=server).first()
            elif isinstance(server, str):
                return session.query(NTPServer).filter_by(address=server).first()
            else:
                self.logger.warning(f"Type de serveur non reconnu: {type(server)}")
                return None
        except Exception as e:
            self.logger.error(f"Erreur récupération serveur: {e}")
            return None
    
    def _get_server_type(self, server: NTPServer) -> str:
        """Déterminer le type de serveur pour les seuils"""
        if hasattr(server, 'is_local') and server.is_local:
            return 'local'
        elif hasattr(server, 'server_type'):
            if server.server_type in ['pool', 'public']:
                return 'pool'
            elif server.server_type in ['local', 'internal']:
                return 'local'
        return 'all'
    
    def _create_or_update_alert_safe(self, session, server: NTPServer, alert_type: str, 
                                   severity: str, message: str, metric_value: float, threshold_id: int):
        """Créer ou mettre à jour une alerte de manière sécurisée"""
        try:
            # Chercher une alerte active existante
            existing_alert = session.query(Alert).filter_by(
                server_id=server.id,
                alert_type=alert_type,
                status='active'
            ).first()
            
            if existing_alert:
                # Mettre à jour l'alerte existante
                existing_alert.severity = severity
                existing_alert.message = message
                existing_alert.metric_value = metric_value
                existing_alert.threshold_value = threshold_id
                existing_alert.occurrence_count += 1
                existing_alert.updated_at = datetime.utcnow()
                existing_alert.is_read = False
                
                self.logger.info(f"Alerte mise à jour: {message}")
            else:
                # Créer une nouvelle alerte
                new_alert = Alert(
                    server_id=server.id,
                    alert_type=alert_type,
                    severity=severity,
                    title=f"Alerte {severity.upper()} - {alert_type}",
                    message=message,
                    status='active',
                    is_read=False,
                    occurrence_count=1,
                    metric_value=metric_value,
                    threshold_value=threshold_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(new_alert)
                
                self.logger.info(f"Nouvelle alerte créée: {message}")
            
            session.commit()
            
        except Exception as e:
            self.logger.error(f"Erreur création/mise à jour alerte: {e}")
            session.rollback()
    
    def _resolve_alert_safe(self, session, server: NTPServer, alert_type: str):
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
    
    def check_server_availability(self, server, is_available: bool, error_message: str = None):
        """
        Vérifier la disponibilité d'un serveur et créer des alertes si nécessaire
        
        Args:
            server: Serveur NTP (ID ou objet)
            is_available: True si le serveur est disponible
            error_message: Message d'erreur si indisponible
        """
        try:
            with get_db_session_with_context() as session:
                server_obj = self._get_server_safe(session, server)
                if not server_obj:
                    return
                
                if not is_available:
                    # Créer une alerte de disponibilité
                    message = f"Serveur {server_obj.name} indisponible"
                    if error_message:
                        message += f": {error_message}"
                    
                    self._create_or_update_alert_safe(
                        session, server_obj, 'availability', 'critical',
                        message, 0, 0
                    )
                else:
                    # Résoudre les alertes de disponibilité
                    self._resolve_alert_safe(session, server_obj, 'availability')
                    
        except Exception as e:
            self.logger.error(f"Erreur vérification disponibilité serveur {server}: {e}")
    
    def get_active_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupérer les alertes actives avec informations complètes"""
        try:
            with get_db_session_with_context() as session:
                alerts = session.query(Alert).filter_by(status='active').order_by(
                    Alert.created_at.desc()
                ).limit(limit).all()
                
                result = []
                for alert in alerts:
                    alert_dict = {
                        'id': alert.id,
                        'server_id': alert.server_id,
                        'alert_type': alert.alert_type,
                        'severity': alert.severity,
                        'title': alert.title,
                        'message': alert.message,
                        'status': alert.status,
                        'is_read': alert.is_read,
                        'created_at': alert.created_at.isoformat() if alert.created_at else None,
                        'updated_at': alert.updated_at.isoformat() if alert.updated_at else None,
                        'occurrence_count': alert.occurrence_count,
                        'metric_value': alert.metric_value,
                        'threshold_value': alert.threshold_value
                    }
                    
                    # Ajouter les informations du serveur
                    if alert.server_id:
                        server = session.query(NTPServer).filter_by(id=alert.server_id).first()
                        if server:
                            alert_dict['server'] = {
                                'id': server.id,
                                'name': server.name,
                                'address': server.address
                            }
                    
                    result.append(alert_dict)
                
                return result
                
        except Exception as e:
            self.logger.error(f"Erreur récupération alertes actives: {e}")
            return []
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Récupérer un résumé des alertes"""
        try:
            with get_db_session_with_context() as session:
                total_active = session.query(Alert).filter_by(status='active').count()
                total_unread = session.query(Alert).filter_by(status='active', is_read=False).count()
                
                # Par sévérité
                critical_count = session.query(Alert).filter(
                    and_(Alert.status == 'active', Alert.severity == 'critical')
                ).count()
                
                warning_count = session.query(Alert).filter(
                    and_(Alert.status == 'active', Alert.severity == 'warning')
                ).count()
                
                # Par type
                offset_count = session.query(Alert).filter(
                    and_(Alert.status == 'active', Alert.alert_type == 'offset')
                ).count()
                
                latency_count = session.query(Alert).filter(
                    and_(Alert.status == 'active', Alert.alert_type == 'latency')
                ).count()
                
                stratum_count = session.query(Alert).filter(
                    and_(Alert.status == 'active', Alert.alert_type == 'stratum')
                ).count()
                
                return {
                    'total_active': total_active,
                    'total_unread': total_unread,
                    'by_severity': {
                        'critical': critical_count,
                        'warning': warning_count
                    },
                    'by_type': {
                        'offset': offset_count,
                        'latency': latency_count,
                        'stratum': stratum_count
                    },
                    'last_update': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Erreur récupération résumé alertes: {e}")
            return {
                'total_active': 0,
                'total_unread': 0,
                'by_severity': {'critical': 0, 'warning': 0},
                'by_type': {'offset': 0, 'latency': 0, 'stratum': 0},
                'last_update': datetime.utcnow().isoformat()
            }

# Instance globale
alert_service = AlertService()
