"""
Service de gestion des alertes - NTP Monitor Enterprise
Gère les alertes de seuils, notifications et escalade
"""
import logging
import smtplib
import json
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional, Any

from backend.app import db
from backend.models.alert import Alert
from backend.models.ntp_server import NTPServer
from backend.models.system_config import SystemConfig
from backend.models.user import User

logger = logging.getLogger(__name__)

class AlertService:
    """Service de gestion des alertes"""
    
    def __init__(self):
        self.logger = logger
        
    def check_ntp_threshold(self, server: NTPServer, offset: float, delay: float, 
                          stratum: int = None) -> Optional[Alert]:
        """
        Vérifier les seuils NTP et créer une alerte si nécessaire
        
        Args:
            server: Serveur NTP
            offset: Décalage temporel en secondes
            delay: Délai de réponse en secondes
            stratum: Stratum du serveur (optionnel)
            
        Returns:
            Alert créée ou None
        """
        try:
            alert_created = None
            current_time = datetime.utcnow()
            
            # Récupérer les seuils configurés
            max_offset = float(SystemConfig.get_config('ntp.max_offset_warning', 1.0))
            critical_offset = float(SystemConfig.get_config('ntp.max_offset_critical', 5.0))
            max_delay = float(SystemConfig.get_config('network.connection_timeout', 1.0))
            
            # Vérifier l'offset critique
            if abs(offset) >= critical_offset:
                alert_created = self._create_alert(
                    server=server,
                    alert_type='critical_offset',
                    severity='critical',
                    title=f'Offset critique - {server.name}',
                    message=f'Offset de {offset:.3f}s dépasse le seuil critique de {critical_offset}s',
                    metrics={'offset': offset, 'threshold': critical_offset}
                )
            
            # Vérifier l'offset d'avertissement
            elif abs(offset) >= max_offset:
                alert_created = self._create_alert(
                    server=server,
                    alert_type='high_offset',
                    severity='warning',
                    title=f'Offset élevé - {server.name}',
                    message=f'Offset de {offset:.3f}s dépasse le seuil de {max_offset}s',
                    metrics={'offset': offset, 'threshold': max_offset}
                )
            
            # Vérifier le délai de réponse
            if delay >= max_delay:
                alert_created = self._create_alert(
                    server=server,
                    alert_type='high_delay',
                    severity='warning',
                    title=f'Délai élevé - {server.name}',
                    message=f'Délai de {delay:.3f}s dépasse le seuil de {max_delay}s',
                    metrics={'delay': delay, 'threshold': max_delay}
                )
            
            # Vérifier le stratum
            if stratum and stratum > 15:
                alert_created = self._create_alert(
                    server=server,
                    alert_type='invalid_stratum',
                    severity='error',
                    title=f'Stratum invalide - {server.name}',
                    message=f'Stratum {stratum} invalide (> 15)',
                    metrics={'stratum': stratum}
                )
            
            return alert_created
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des seuils: {e}")
            return None
    
    def check_server_availability(self, server: NTPServer, is_available: bool, 
                                error_message: str = None) -> Optional[Alert]:
        """
        Vérifier la disponibilité d'un serveur NTP
        
        Args:
            server: Serveur NTP
            is_available: État de disponibilité
            error_message: Message d'erreur (optionnel)
            
        Returns:
            Alert créée ou None
        """
        try:
            if not is_available:
                return self._create_alert(
                    server=server,
                    alert_type='server_unreachable',
                    severity='error',
                    title=f'Serveur indisponible - {server.name}',
                    message=f'Impossible de contacter le serveur {server.address}',
                    details=error_message or 'Timeout ou erreur de connexion'
                )
            else:
                # Résoudre les alertes de disponibilité si le serveur est de nouveau disponible
                self._resolve_server_alerts(server, 'server_unreachable')
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification de disponibilité: {e}")
            return None
    
    def _create_alert(self, server: NTPServer, alert_type: str, severity: str,
                     title: str, message: str, details: str = None,
                     metrics: Dict[str, Any] = None) -> Optional[Alert]:
        """
        Créer une nouvelle alerte
        
        Args:
            server: Serveur NTP concerné
            alert_type: Type d'alerte
            severity: Niveau de sévérité
            title: Titre de l'alerte
            message: Message descriptif
            details: Détails supplémentaires
            metrics: Métriques associées
            
        Returns:
            Alert créée ou None
        """
        try:
            # Vérifier s'il existe déjà une alerte active similaire
            existing_alert = Alert.query.filter_by(
                server_id=server.id,
                alert_type=alert_type,
                status='active'
            ).first()
            
            if existing_alert:
                # Mettre à jour l'alerte existante
                existing_alert.message = message
                if details:
                    existing_alert.details = details
                if metrics:
                    existing_alert.details = metrics  # Utiliser details au lieu de metrics
                existing_alert.updated_at = datetime.utcnow()
                
                db.session.commit()
                self.logger.info(f"Alerte mise à jour: {title}")
                
                # Envoyer notification si nécessaire
                self._send_notification(existing_alert)
                
                return existing_alert
            else:
                # Créer une nouvelle alerte
                alert = Alert(
                    alert_type=alert_type,
                    title=title,
                    message=message,
                    severity=severity,
                    server_id=server.id,
                    details=metrics or details,
                    status='active'
                )
                
                db.session.add(alert)
                db.session.commit()
                
                self.logger.warning(f"Nouvelle alerte créée: {title}")
                
                # Envoyer notification
                self._send_notification(alert)
                
                return alert
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la création d'alerte: {e}")
            db.session.rollback()
            return None
    
    def _resolve_server_alerts(self, server: NTPServer, alert_type: str = None):
        """
        Résoudre les alertes actives d'un serveur
        
        Args:
            server: Serveur NTP
            alert_type: Type d'alerte spécifique (optionnel)
        """
        try:
            query = Alert.query.filter_by(server_id=server.id, status='active')
            
            if alert_type:
                query = query.filter_by(alert_type=alert_type)
            
            alerts = query.all()
            
            for alert in alerts:
                alert.status = 'resolved'
                alert.resolved_at = datetime.utcnow()
                alert.updated_at = datetime.utcnow()
                
                self.logger.info(f"Alerte résolue: {alert.title}")
            
            if alerts:
                db.session.commit()
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la résolution d'alertes: {e}")
            db.session.rollback()
    
    def _send_notification(self, alert: Alert):
        """
        Envoyer une notification pour une alerte
        
        Args:
            alert: Alerte à notifier
        """
        try:
            # Vérifier si les notifications sont activées
            email_enabled = SystemConfig.get_config('alerts.email_enabled', False)
            webhook_enabled = SystemConfig.get_config('alerts.webhook_enabled', False)
            
            # Envoyer notification email
            if email_enabled:
                self._send_email_notification(alert)
            
            # Envoyer notification webhook
            if webhook_enabled:
                self._send_webhook_notification(alert)
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi de notification: {e}")
    
    def _send_email_notification(self, alert: Alert):
        """
        Envoyer une notification par email
        
        Args:
            alert: Alerte à notifier
        """
        try:
            # Configuration SMTP
            smtp_server = SystemConfig.get_config('alerts.smtp_server')
            smtp_port = int(SystemConfig.get_config('alerts.smtp_port', 587))
            smtp_username = SystemConfig.get_config('alerts.smtp_username')
            smtp_password = SystemConfig.get_config('alerts.smtp_password')
            smtp_use_tls = SystemConfig.get_config('alerts.smtp_use_tls', True)
            
            if not all([smtp_server, smtp_username, smtp_password]):
                self.logger.warning("Configuration SMTP incomplète")
                return
            
            # Destinataires
            recipients = self._get_notification_recipients(alert.severity)
            if not recipients:
                self.logger.warning("Aucun destinataire configuré pour les alertes")
                return
            
            # Créer le message
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[NTP Monitor] {alert.title}"
            
            # Corps du message
            body = self._create_email_body(alert)
            msg.attach(MIMEText(body, 'html'))
            
            # Envoyer l'email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if smtp_use_tls:
                    server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"Email d'alerte envoyé pour: {alert.title}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi d'email: {e}")
    
    def _send_webhook_notification(self, alert: Alert):
        """
        Envoyer une notification via webhook
        
        Args:
            alert: Alerte à notifier
        """
        try:
            webhook_url = SystemConfig.get_config('alerts.webhook_url')
            webhook_secret = SystemConfig.get_config('alerts.webhook_secret')
            
            if not webhook_url:
                return
            
            # Préparer les données
            payload = {
                'timestamp': alert.created_at.isoformat(),
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'message': alert.message,
                'server': {
                    'name': alert.server.name,
                    'address': alert.server.address,
                    'type': alert.server.server_type
                },
                'details': alert.details
            }
            
            headers = {'Content-Type': 'application/json'}
            
            # Ajouter signature si secret configuré
            if webhook_secret:
                import hmac
                import hashlib
                
                signature = hmac.new(
                    webhook_secret.encode(),
                    json.dumps(payload).encode(),
                    hashlib.sha256
                ).hexdigest()
                headers['X-NTP-Monitor-Signature'] = f'sha256={signature}'
            
            # Envoyer la requête
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            self.logger.info(f"Webhook d'alerte envoyé pour: {alert.title}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi de webhook: {e}")
    
    def _get_notification_recipients(self, severity: str) -> List[str]:
        """
        Obtenir la liste des destinataires selon la sévérité
        
        Args:
            severity: Niveau de sévérité
            
        Returns:
            Liste des emails destinataires
        """
        try:
            # Récupérer les destinataires selon la sévérité
            recipients_str = SystemConfig.get_config('alerts.recipients', '')
            
            if recipients_str:
                return [email.strip() for email in recipients_str.split(',') if email.strip()]
            
            # Fallback sur les admins
            admin_users = User.query.filter_by(role='admin', is_active=True).all()
            return [user.email for user in admin_users if user.email]
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des destinataires: {e}")
            return []
    
    def _create_email_body(self, alert: Alert) -> str:
        """
        Créer le corps du message email
        
        Args:
            alert: Alerte
            
        Returns:
            Corps du message HTML
        """
        severity_colors = {
            'info': '#17a2b8',
            'warning': '#ffc107',
            'error': '#dc3545',
            'critical': '#6f42c1'
        }
        
        color = severity_colors.get(alert.severity, '#6c757d')
        
        details_html = ""
        if alert.details:
            details_html = f"<p><strong>Détails:</strong> {alert.details}</p>"
        
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .alert {{ border-left: 4px solid {color}; padding: 15px; background-color: #f8f9fa; }}
                .header {{ color: {color}; margin-bottom: 10px; }}
                .server-info {{ background-color: #e9ecef; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                .timestamp {{ color: #6c757d; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="alert">
                <h2 class="header">🚨 {alert.title}</h2>
                <p><strong>Sévérité:</strong> {alert.severity.upper()}</p>
                <p><strong>Message:</strong> {alert.message}</p>
                
                <div class="server-info">
                    <h4>Serveur concerné:</h4>
                    <p><strong>Nom:</strong> {alert.server.name}</p>
                    <p><strong>Adresse:</strong> {alert.server.address}:{alert.server.port}</p>
                    <p><strong>Type:</strong> {alert.server.server_type}</p>
                </div>
                
                {details_html}
                
                <p class="timestamp">
                    <strong>Horodatage:</strong> {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
                </p>
            </div>
            
            <p><em>Cet email a été généré automatiquement par NTP Monitor Enterprise.</em></p>
        </body>
        </html>
        """
    
    def get_active_alerts(self, server_id: int = None, severity: str = None) -> List[Alert]:
        """
        Récupérer les alertes actives
        
        Args:
            server_id: ID du serveur (optionnel)
            severity: Niveau de sévérité (optionnel)
            
        Returns:
            Liste des alertes actives
        """
        try:
            query = Alert.query.filter_by(status='active')
            
            if server_id:
                query = query.filter_by(server_id=server_id)
            
            if severity:
                query = query.filter_by(severity=severity)
            
            return query.order_by(Alert.created_at.desc()).all()
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des alertes: {e}")
            return []
    
    def resolve_alert(self, alert_id: int, user_id: int = None) -> bool:
        """
        Résoudre manuellement une alerte
        
        Args:
            alert_id: ID de l'alerte
            user_id: ID de l'utilisateur (optionnel)
            
        Returns:
            True si résolue avec succès
        """
        try:
            alert = Alert.query.get(alert_id)
            if not alert:
                return False
            
            alert.status = 'resolved'
            alert.resolved_at = datetime.utcnow()
            alert.updated_at = datetime.utcnow()
            
            if user_id:
                alert.resolved_by = user_id
            
            db.session.commit()
            
            self.logger.info(f"Alerte résolue manuellement: {alert.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la résolution d'alerte: {e}")
            db.session.rollback()
            return False
    
    def cleanup_old_alerts(self, days: int = 30):
        """
        Nettoyer les anciennes alertes résolues
        
        Args:
            days: Nombre de jours de rétention
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            old_alerts = Alert.query.filter(
                Alert.status == 'resolved',
                Alert.resolved_at < cutoff_date
            ).all()
            
            for alert in old_alerts:
                db.session.delete(alert)
            
            if old_alerts:
                db.session.commit()
                self.logger.info(f"Suppression de {len(old_alerts)} alertes anciennes")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage des alertes: {e}")
            db.session.rollback()

# Instance globale du service
alert_service = AlertService() 