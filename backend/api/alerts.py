"""
API Alertes - NTP Monitor Enterprise
Gestion des alertes, notifications et configurations
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from backend.database_manager import get_db_session_with_context
# SUPPRIMÉ: Import Flask-SQLAlchemy circulaire
from backend.database import Alert
from backend.database import SystemConfig
from backend.database import NTPServer
from backend.services.alert_service import alert_service

# Crer le blueprint
alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

@alerts_bp.route('', methods=['GET'])
@login_required
def get_alerts():
    """Rcuprer la liste des alertes"""
    try:
        # Paramtres de requte
        status = request.args.get('status', 'active')
        server_id = request.args.get('server_id', type=int)
        severity = request.args.get('severity')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        with get_db_session_with_context() as session:
            # Construire la requte
            query = session.query(Alert)
            
            if status and status != 'all':
                query = query.filter(Alert.status == status)
            
            if server_id:
                query = query.filter(Alert.server_id == server_id)
            
            if severity:
                query = query.filter(Alert.severity == severity)
            
            # Ordonner et paginer
            alerts = query.order_by(Alert.created_at.desc())\
                         .offset(offset)\
                         .limit(limit)\
                         .all()
            
            # Compter le total
            total = query.count()
            
            # Convertir en dictionnaires
            alerts_data = []
            for alert in alerts:
                alerts_data.append({
                    'id': alert.id,
                    'server_id': alert.server_id,
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'title': alert.title,
                    'message': alert.message,
                    'status': alert.status,
                    'created_at': alert.created_at.isoformat() if alert.created_at else None,
                    'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                    'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
                })
        
        return jsonify({
            'success': True,
            'alerts': alerts_data,
            'total': total,
            'count': len(alerts_data),
            'offset': offset,
            'limit': limit
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la rcupration des alertes: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la rcupration des alertes'
        }), 500

@alerts_bp.route('/active', methods=['GET'])
def get_active_alerts():
    """Récupérer les alertes actives (pas de login requis pour les tests)"""
    try:
        from backend.database_manager import get_db_session_with_context
        
        with get_db_session_with_context() as session:
            alerts = session.query(Alert).filter_by(status='active').order_by(Alert.created_at.desc()).limit(20).all()
            
            # Convertir en dictionnaires
            alerts_data = []
            for alert in alerts:
                alert_dict = {
                    'id': alert.id,
                    'server_id': alert.server_id,
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'title': alert.title,
                    'message': alert.message,
                    'status': alert.status,
                    'created_at': alert.created_at.isoformat() if alert.created_at else None
                }
                alerts_data.append(alert_dict)
            
            return jsonify({
                'success': True,
                'alerts': alerts_data,
                'count': len(alerts_data)
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/stats', methods=['GET'])
def get_alerts_stats():
    """Statistiques des alertes (pas de login requis pour les tests)"""
    try:
        from backend.database_manager import get_db_session_with_context
        
        with get_db_session_with_context() as session:
            total_active = session.query(Alert).filter_by(status='active').count()
            total_critical = session.query(Alert).filter_by(status='active', severity='critical').count()
            total_warning = session.query(Alert).filter_by(status='active', severity='warning').count()
            
            return jsonify({
                'success': True,
                'stats': {
                    'active': total_active,
                    'critical': total_critical,
                    'warning': total_warning,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/summary', methods=['GET'])
@login_required
def get_alerts_summary():
    """Rcuprer un rsum des alertes"""
    try:
        from backend.database_manager import get_db_session_with_context
        
        with get_db_session_with_context() as session:
            # Statistiques des alertes
            total_active = session.query(Alert).filter_by(status='active').count()
            total_critical = session.query(Alert).filter_by(status='active', severity='critical').count()
            total_warning = session.query(Alert).filter_by(status='active', severity='warning').count()
            total_info = session.query(Alert).filter_by(status='active', severity='info').count()
            total_unread = session.query(Alert).filter_by(is_read=False).count()
            
            # Alertes rcentes (24h)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_alerts = session.query(Alert).filter(
                Alert.created_at >= recent_cutoff
            ).order_by(Alert.created_at.desc()).limit(10).all()
            
            # Serveurs avec alertes actives
            servers_with_alerts = session.query(NTPServer)\
                .join(Alert, NTPServer.id == Alert.server_id)\
                .filter(Alert.status == 'active')\
                .group_by(NTPServer.id)\
                .all()
            
            # Convertir recent_alerts en dictionnaires
            recent_alerts_data = []
            for alert in recent_alerts:
                alert_dict = {
                    'id': alert.id,
                    'server_id': alert.server_id,
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'title': alert.title,
                    'message': alert.message,
                    'status': alert.status,
                    'created_at': alert.created_at.isoformat() if alert.created_at else None
                }
                recent_alerts_data.append(alert_dict)
        
        return jsonify({
            'success': True,
            'summary': {
                'total_active': total_active,
                'by_severity': {
                    'critical': total_critical,
                    'warning': total_warning,
                    'info': total_info
                },
                'unread_count': total_unread,
                'recent_alerts': recent_alerts_data,
                'affected_servers': len(servers_with_alerts)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors du rsum des alertes: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du rsum des alertes'
        }), 500

@alerts_bp.route('/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    """Acquitter une alerte"""
    try:
        with get_db_session_with_context() as session:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return jsonify({'error': 'Alerte non trouvée'}), 404
            
            # Acquitter l'alerte
            alert.acknowledge(current_user.id)
            session.commit()
            
            alert_data = {
                'id': alert.id,
                'title': alert.title,
                'status': alert.status,
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
            }
        
        return jsonify({
            'success': True,
            'message': f'Alerte "{alert.title}" acquitte',
            'alert': alert_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'acquittement d'alerte: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de l\'acquittement'
        }), 500

@alerts_bp.route('/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    """Rsoudre une alerte"""
    try:
        with get_db_session_with_context() as session:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return jsonify({'error': 'Alerte non trouvée'}), 404
            
            # Rsoudre l'alerte
            alert.resolve(current_user.id)
            session.commit()
            
            alert_data = {
                'id': alert.id,
                'title': alert.title,
                'status': alert.status,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
            }
        
        return jsonify({
            'success': True,
            'message': f'Alerte "{alert.title}" rsolue',
            'alert': alert_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la rsolution d'alerte: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la rsolution'
        }), 500

@alerts_bp.route('/<int:alert_id>/read', methods=['POST'])
@login_required
def mark_alert_read(alert_id):
    """Marquer une alerte comme lue"""
    try:
        with get_db_session_with_context() as session:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return jsonify({'error': 'Alerte non trouvée'}), 404
            
            # Marquer comme lue
            alert.mark_as_read()
            session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Alerte marque comme lue'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors du marquage: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du marquage'
        }), 500

@alerts_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Marquer toutes les alertes comme lues"""
    try:
        with get_db_session_with_context() as session:
            # Marquer toutes les alertes non lues comme lues
            session.query(Alert).filter_by(is_read=False).update({'is_read': True})
            session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Toutes les alertes ont t marques comme lues'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors du marquage global: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du marquage global'
        }), 500

@alerts_bp.route('/bulk-action', methods=['POST'])
@login_required
def bulk_action():
    """Actions en lot sur les alertes"""
    try:
        data = request.get_json()
        alert_ids = data.get('alert_ids', [])
        action = data.get('action')
        
        if not alert_ids or not action:
            return jsonify({
                'success': False,
                'error': 'IDs d\'alertes et action requis'
            }), 400
        
        with get_db_session_with_context() as session:
            alerts = session.query(Alert).filter(Alert.id.in_(alert_ids)).all()
            
            if not alerts:
                return jsonify({
                    'success': False,
                    'error': 'Aucune alerte trouve'
                }), 404
            
            processed = 0
            
            for alert in alerts:
                if action == 'acknowledge':
                    alert.acknowledge(current_user.id)
                    processed += 1
                elif action == 'resolve':
                    alert.resolve(current_user.id)
                    processed += 1
                elif action == 'read':
                    alert.mark_as_read()
                    processed += 1
            
            session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{processed} alertes traites',
            'processed_count': processed
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'action en lot: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de l\'action en lot'
        }), 500

@alerts_bp.route('/test-notification', methods=['POST'])
@login_required
def test_notification():
    """Tester l'envoi de notifications"""
    try:
        # Vrifier les permissions admin
        if current_user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Permissions administrateur requises'
            }), 403
        
        data = request.get_json()
        notification_type = data.get('type', 'email')  # email ou webhook
        
        # Crer une alerte de test
        with get_db_session_with_context() as session:
            test_server = session.query(NTPServer).first()
            if not test_server:
                return jsonify({
                    'success': False,
                    'error': 'Aucun serveur NTP configur pour le test'
                }), 400
        
        # Crer une alerte temporaire pour le test
        test_alert = Alert(
            server_id=test_server.id,
            alert_type='test',
            severity='info',
            title='Test de notification NTP Monitor',
            message='Ceci est un test de notification automatique.',
            details={'test': True, 'timestamp': datetime.utcnow().isoformat()}
        )
        
        # Ne pas sauvegarder en base, juste tester la notification
        if notification_type == 'email':
            alert_service._send_email_notification(test_alert)
            message = 'Email de test envoy'
        elif notification_type == 'webhook':
            alert_service._send_webhook_notification(test_alert)
            message = 'Webhook de test envoy'
        else:
            return jsonify({
                'success': False,
                'error': 'Type de notification non support'
            }), 400
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors du test de notification: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@alerts_bp.route('/config', methods=['GET'])
@login_required
def get_alert_config():
    """Rcuprer la configuration des alertes"""
    try:
        config = {
            # Notifications gnrales
            'email_enabled': SystemConfig.get_value('alert_email_enabled', 'false').lower() == 'true',
            'webhook_enabled': SystemConfig.get_value('alert_webhook_enabled', 'false').lower() == 'true',
            
            # Configuration email
            'smtp_server': SystemConfig.get_value('smtp_server', ''),
            'smtp_port': SystemConfig.get_value('smtp_port', '587'),
            'smtp_username': SystemConfig.get_value('smtp_username', ''),
            'smtp_use_tls': SystemConfig.get_value('smtp_use_tls', 'true').lower() == 'true',
            
            # Configuration webhook
            'webhook_url': SystemConfig.get_value('webhook_url', ''),
            
            # Destinataires
            'alert_recipients': SystemConfig.get_value('alert_recipients', ''),
            'alert_critical_recipients': SystemConfig.get_value('alert_critical_recipients', ''),
            'alert_error_recipients': SystemConfig.get_value('alert_error_recipients', ''),
            'alert_warning_recipients': SystemConfig.get_value('alert_warning_recipients', ''),
            
            # Seuils d'alerte
            'max_offset_threshold': float(SystemConfig.get_value('max_offset_threshold', '1.0')),
            'critical_offset_threshold': float(SystemConfig.get_value('critical_offset_threshold', '5.0')),
            'max_delay_threshold': float(SystemConfig.get_value('max_delay_threshold', '1.0')),
            
            # Rtention
            'alert_retention_days': int(SystemConfig.get_value('alert_retention_days', '30'))
        }
        
        return jsonify({
            'success': True,
            'config': config
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la rcupration de config: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la rcupration de la configuration'
        }), 500

@alerts_bp.route('/config', methods=['POST'])
@login_required
def update_alert_config():
    """Mettre  jour la configuration des alertes"""
    try:
        # Vrifier les permissions admin
        if current_user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Permissions administrateur requises'
            }), 403
        
        data = request.get_json()
        
        # Configurations  mettre  jour
        config_mapping = {
            'email_enabled': 'alert_email_enabled',
            'webhook_enabled': 'alert_webhook_enabled',
            'smtp_server': 'smtp_server',
            'smtp_port': 'smtp_port',
            'smtp_username': 'smtp_username',
            'smtp_password': 'smtp_password',
            'smtp_use_tls': 'smtp_use_tls',
            'webhook_url': 'webhook_url',
            'webhook_secret': 'webhook_secret',
            'alert_recipients': 'alert_recipients',
            'alert_critical_recipients': 'alert_critical_recipients',
            'alert_error_recipients': 'alert_error_recipients',
            'alert_warning_recipients': 'alert_warning_recipients',
            'max_offset_threshold': 'max_offset_threshold',
            'critical_offset_threshold': 'critical_offset_threshold',
            'max_delay_threshold': 'max_delay_threshold',
            'alert_retention_days': 'alert_retention_days'
        }
        
        updated = []
        
        for frontend_key, config_key in config_mapping.items():
            if frontend_key in data:
                value = data[frontend_key]
                
                # Convertir les boolens en string
                if isinstance(value, bool):
                    value = 'true' if value else 'false'
                else:
                    value = str(value)
                
                # Mettre  jour ou crer la configuration
                config = session.query(SystemConfig).filter_by(key_name=config_key).first()
                if config:
                    config.value = value
                    config.updated_at = datetime.utcnow()
                else:
                    config = SystemConfig(
                        key=config_key,
                        value=value,
                        description=f'Configuration automatique pour {frontend_key}'
                    )
                    db.session.add(config)
                
                updated.append(config_key)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Configuration mise  jour ({len(updated)} paramtres)'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la mise  jour de config: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la mise  jour de la configuration'
        }), 500

@alerts_bp.route('/cleanup', methods=['POST'])
@login_required
def cleanup_alerts():
    """Nettoyer les anciennes alertes"""
    try:
        # Vrifier les permissions admin
        if current_user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Permissions administrateur requises'
            }), 403
        
        data = request.get_json()
        days = data.get('days', 30)
        
        # Nettoyer via le service
        alert_service.cleanup_old_alerts(days)
        
        return jsonify({
            'success': True,
            'message': f'Nettoyage des alertes de plus de {days} jours effectu'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors du nettoyage: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du nettoyage'
        }), 500 
