"""
Service d'alertes unifié - VERSION CORRIGÉE
Gestion complète des alertes avec seuils centralisés et métriques dynamiques
Élimination des redondances et standardisation des unités
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import or_, and_

from backend.database_manager import get_db_session_with_context
from backend.database import Alert, AlertThreshold, NTPServer, SystemConfig
from backend.services.threshold_manager import threshold_manager
from backend.config.alert_metrics import (
    ALERT_METRICS, convert_to_standard_unit, validate_metric_value,
    format_alert_message, get_metric_config
)

logger = logging.getLogger(__name__)

class AlertServiceUnified:
    """Service unifié de gestion des alertes - VERSION CORRIGÉE"""
    
    def __init__(self):
        self.logger = logger
        self.alertes_cache = {}
        self.derniere_verification = None
    
    def check_ntp_threshold(self, server, metrics_data: Dict[str, Any]):
        """
        Vérifier toutes les métriques avec seuils centralisés - VERSION UNIFIÉE
        Utilise la configuration centralisée et les métriques dynamiques
        """
        try:
            # Validation des paramètres
            if not metrics_data or not any(metrics_data.values()):
                return
            
            with get_db_session_with_context() as session:
                # Récupération sécurisée du serveur
                server_obj = self._get_server_safe(session, server)
                if not server_obj:
                    return
                
                # Déterminer le type de serveur pour les seuils
                server_type = self._get_server_type(server_obj)
                
                # Vérification dynamique de toutes les métriques
                for metric_name, value in metrics_data.items():
                    if value is not None and metric_name in ALERT_METRICS:
                        self._check_metric_threshold(session, server_obj, metric_name, value, server_type)
                
                # Mise à jour du cache
                self.derniere_verification = datetime.utcnow()
                
        except Exception as e:
            self.logger.error(f"Erreur vérification seuils serveur {server}: {e}")
    
    def _check_metric_threshold(self, session, server: NTPServer, metric_name: str, value: Any, server_type: str):
        """Vérifier une métrique spécifique avec configuration centralisée"""
        
        # Validation de la valeur
        if not validate_metric_value(value, metric_name):
            self.logger.warning(f"Valeur invalide pour {metric_name}: {value}")
            return
        
        # Conversion vers l'unité standard
        converted_value = convert_to_standard_unit(value, metric_name)
        
        # Vérification avec ThresholdManager
        severity, threshold = threshold_manager.check_threshold(metric_name, converted_value, server_type)
        
        if severity != 'ok' and threshold:
            # Créer l'alerte avec message formaté
            alert_message = format_alert_message(metric_name, converted_value, severity, threshold)
            
            self._create_or_update_alert_safe(
                session, server, metric_name, severity, 
                alert_message, converted_value, threshold['id']
            )
        else:
            # Résoudre l'alerte si elle existe
            self._resolve_alert_safe(session, server, metric_name)
    
    def check_server_availability(self, server, is_available: bool, error_message: str = None):
        """Vérifier la disponibilité du serveur"""
        try:
            with get_db_session_with_context() as session:
                server_obj = self._get_server_safe(session, server)
                if not server_obj:
                    return
                
                server_type = self._get_server_type(server_obj)
                
                if not is_available:
                    # Créer une alerte de disponibilité
                    alert_message = f"Serveur {server_obj.name} ({server_obj.address}) hors ligne"
                    if error_message:
                        alert_message += f" - {error_message}"
                    
                    self._create_or_update_alert_safe(
                        session, server_obj, 'availability', 'critical',
                        alert_message, 0, None  # 0 = 0% de disponibilité
                    )
                else:
                    # Résoudre l'alerte de disponibilité si elle existe
                    self._resolve_alert_safe(session, server_obj, 'availability')
                    
        except Exception as e:
            self.logger.error(f"Erreur vérification disponibilité serveur {server}: {e}")
    
    def _get_server_safe(self, session, server) -> Optional[NTPServer]:
        """Récupération sécurisée du serveur"""
        try:
            if isinstance(server, int):
                return session.query(NTPServer).filter_by(id=server).first()
            elif isinstance(server, NTPServer):
                return session.query(NTPServer).filter_by(id=server.id).first()
            elif hasattr(server, 'id'):
                return session.query(NTPServer).filter_by(id=server.id).first()
            else:
                self.logger.warning(f"Type de serveur non reconnu: {type(server)}")
                return None
        except Exception as e:
            self.logger.error(f"Erreur récupération serveur: {e}")
            return None
    
    def _get_server_type(self, server: NTPServer) -> str:
        """Déterminer le type de serveur pour les seuils"""
        if not server:
            return 'all'
        
        # Logique de détermination du type de serveur
        if hasattr(server, 'server_type') and server.server_type:
            return server.server_type
        
        # Détermination basée sur l'adresse
        address = server.address.lower()
        if 'pool' in address or 'ntp.org' in address:
            return 'pool'
        elif 'local' in address or '192.168' in address or '10.' in address:
            return 'local'
        elif 'internet' in address or 'public' in address:
            return 'internet'
        else:
            return 'all'
    
    def _create_or_update_alert_safe(self, session, server: NTPServer, alert_type: str, 
                                    severity: str, message: str, metric_value: float, threshold_id: int = None):
        """Créer ou mettre à jour une alerte de manière sécurisée"""
        try:
            # Rechercher une alerte existante du même type pour ce serveur
            existing_alert = session.query(Alert).filter_by(
                server_id=server.id,
                alert_type=alert_type,
                status='active'
            ).first()
            
            if existing_alert:
                # Mettre à jour l'alerte existante
                existing_alert.occurrence_count += 1
                existing_alert.last_occurrence = datetime.utcnow()
                existing_alert.message = message
                existing_alert.details = {
                    'metric_value': metric_value,
                    'threshold_id': threshold_id,
                    'severity': severity
                }
                existing_alert.updated_at = datetime.utcnow()
                
                self.logger.info(f"🔄 Alerte mise à jour: {alert_type} pour {server.name}")
            else:
                # Créer une nouvelle alerte
                alert = Alert(
                    server_id=server.id,
                    alert_type=alert_type,
                    severity=severity,
                    title=f"Alerte {alert_type} - {server.name}",
                    message=message,
                    details={
                        'metric_value': metric_value,
                        'threshold_id': threshold_id,
                        'severity': severity
                    },
                    status='active',
                    is_read=False,
                    occurrence_count=1,
                    first_occurrence=datetime.utcnow(),
                    last_occurrence=datetime.utcnow()
                )
                
                session.add(alert)
                self.logger.info(f"🆕 Nouvelle alerte créée: {alert_type} pour {server.name}")
            
            session.commit()
            
        except Exception as e:
            self.logger.error(f"Erreur création/mise à jour alerte: {e}")
            session.rollback()
    
    def _resolve_alert_safe(self, session, server: NTPServer, alert_type: str):
        """Résoudre une alerte de manière sécurisée"""
        try:
            # Rechercher les alertes actives du même type pour ce serveur
            active_alerts = session.query(Alert).filter_by(
                server_id=server.id,
                alert_type=alert_type,
                status='active'
            ).all()
            
            for alert in active_alerts:
                alert.status = 'resolved'
                alert.resolved_at = datetime.utcnow()
                alert.auto_resolved = True
                alert.updated_at = datetime.utcnow()
                
                self.logger.info(f"✅ Alerte résolue: {alert_type} pour {server.name}")
            
            session.commit()
            
        except Exception as e:
            self.logger.error(f"Erreur résolution alerte: {e}")
            session.rollback()
    
    def get_active_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupérer les alertes actives"""
        try:
            with get_db_session_with_context() as session:
                alerts = session.query(Alert).filter_by(status='active').order_by(
                    Alert.created_at.desc()
                ).limit(limit).all()
                
                return [alert.to_dict() for alert in alerts]
                
        except Exception as e:
            self.logger.error(f"Erreur récupération alertes actives: {e}")
            return []
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Récupérer un résumé des alertes"""
        try:
            with get_db_session_with_context() as session:
                total_alerts = session.query(Alert).filter_by(status='active').count()
                critical_alerts = session.query(Alert).filter_by(status='active', severity='critical').count()
                warning_alerts = session.query(Alert).filter_by(status='active', severity='warning').count()
                unread_alerts = session.query(Alert).filter_by(status='active', is_read=False).count()
                
                return {
                    'total_alerts': total_alerts,
                    'critical_alerts': critical_alerts,
                    'warning_alerts': warning_alerts,
                    'unread_alerts': unread_alerts,
                    'last_check': self.derniere_verification.isoformat() if self.derniere_verification else None
                }
                
        except Exception as e:
            self.logger.error(f"Erreur récupération résumé alertes: {e}")
            return {
                'total_alerts': 0,
                'critical_alerts': 0,
                'warning_alerts': 0,
                'unread_alerts': 0,
                'last_check': None
            }
    
    def acknowledge_alert(self, alert_id: int, user_id: int) -> bool:
        """Acquitter une alerte"""
        try:
            with get_db_session_with_context() as session:
                alert = session.query(Alert).filter_by(id=alert_id).first()
                if alert:
                    alert.acknowledge(user_id)
                    session.commit()
                    self.logger.info(f"✅ Alerte acquittée: {alert_id}")
                    return True
                else:
                    self.logger.warning(f"⚠️ Alerte non trouvée: {alert_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Erreur acquittement alerte: {e}")
            return False
    
    def resolve_alert(self, alert_id: int, user_id: int) -> bool:
        """Résoudre une alerte"""
        try:
            with get_db_session_with_context() as session:
                alert = session.query(Alert).filter_by(id=alert_id).first()
                if alert:
                    alert.resolve(user_id)
                    session.commit()
                    self.logger.info(f"✅ Alerte résolue: {alert_id}")
                    return True
                else:
                    self.logger.warning(f"⚠️ Alerte non trouvée: {alert_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Erreur résolution alerte: {e}")
            return False

# Instance globale du service unifié
alert_service_unified = AlertServiceUnified() 