"""
API Alertes - NTP Monitor Enterprise
Gestion des alertes, notifications et configurations
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from backend.database_manager import get_db_session_with_context
# Imports corrects des modèles
from backend.models.alert import Alert
from backend.models.system_config import SystemConfig
from backend.models.ntp_server import NTPServer
from backend.services.alert_service import alert_service
from sqlalchemy import func, or_

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
    """Récupérer uniquement les alertes réellement actives (non auto-résolues)"""
    try:
        with get_db_session_with_context() as session:
            # Filtrer UNIQUEMENT les alertes actives (non acquittées ET non résolues ET non auto-résolues)
            alerts = session.query(Alert).filter(
                Alert.status == 'active',
                Alert.acknowledged_at == None,
                Alert.resolved_at == None
            ).order_by(Alert.created_at.desc()).all()
            
            alerts_data = []
            for alert in alerts:
                # Récupérer le nom du serveur
                server_name = 'Système'
                if alert.server_id:
                    server = session.query(NTPServer).filter_by(id=alert.server_id).first()
                    if server:
                        server_name = server.name
                
                alert_data = {
                    'id': alert.id,
                    'title': alert.title,
                    'message': alert.message,
                    'severity': alert.severity,
                    'alert_type': alert.alert_type,
                    'status': alert.status,
                    'server_name': server_name,
                    'server_id': alert.server_id,
                    'created_at': alert.created_at.isoformat() if alert.created_at else None,
                    'updated_at': alert.updated_at.isoformat() if alert.updated_at else None,
                    'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                    'is_read': alert.is_read,
                    'occurrence_count': getattr(alert, 'occurrence_count', 1),
                    'first_occurrence': getattr(alert, 'first_occurrence', alert.created_at).isoformat() if getattr(alert, 'first_occurrence', alert.created_at) else None,
                    'last_occurrence': getattr(alert, 'last_occurrence', alert.updated_at).isoformat() if getattr(alert, 'last_occurrence', alert.updated_at) else None,
                    'auto_resolved': getattr(alert, 'auto_resolved', False)
                }
                alerts_data.append(alert_data)
            
            return jsonify({
                'success': True,
                'alerts': alerts_data,
                'count': len(alerts_data)
            })
            
    except Exception as e:
        current_app.logger.error(f"Erreur récupération alertes actives: {e}")
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
def get_alerts_summary():
    """Récupérer le résumé des alertes avec comptage correct"""
    try:
        with get_db_session_with_context() as session:
            # Compter toutes les alertes par sévérité
            total_query = session.query(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
            
            # Compter les alertes actives (non acquittées, non résolues)
            active_query = session.query(Alert.severity, func.count(Alert.id)).filter(
                Alert.status == 'active',
                Alert.acknowledged_at == None,
                Alert.resolved_at == None
            ).group_by(Alert.severity)
            
            # Compter les alertes non lues (actives uniquement)
            unread_query = session.query(func.count(Alert.id)).filter(
                Alert.is_read == False,
                Alert.status == 'active',
                Alert.acknowledged_at == None,
                Alert.resolved_at == None
            )
            
            # Traitement des résultats
            total_counts = {row[0]: row[1] for row in total_query.all()}
            active_counts = {row[0]: row[1] for row in active_query.all()}
            unread_count = unread_query.scalar() or 0
            
            # Calculer les totaux
            total_alerts = sum(total_counts.values())
            active_alerts = sum(active_counts.values())
            
            summary = {
                'total_alerts': total_alerts,
                'active_alerts': active_alerts,
                'unread_count': unread_count,
                'by_severity': {
                    'critical': {
                        'total': total_counts.get('critical', 0),
                        'active': active_counts.get('critical', 0)
                    },
                    'warning': {
                        'total': total_counts.get('warning', 0),
                        'active': active_counts.get('warning', 0)
                    },
                    'info': {
                        'total': total_counts.get('info', 0),
                        'active': active_counts.get('info', 0)
                    }
                }
            }
            
            return jsonify({
                'success': True,
                'summary': summary
            })
            
    except Exception as e:
        current_app.logger.error(f"Erreur récupération résumé alertes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/acknowledge/<int:alert_id>', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    """Acquitter une alerte - la retire de la liste active"""
    try:
        # Vérifier les permissions admin/operator
        if current_user.role not in ['admin', 'operator']:
            return jsonify({
                'success': False,
                'error': 'Permissions insuffisantes'
            }), 403
        
        with get_db_session_with_context() as session:
            alert = session.query(Alert).filter_by(id=alert_id).first()
            if not alert:
                return jsonify({'success': False, 'error': 'Alerte non trouvée'}), 404
            
            # Acquitter l'alerte - change le statut
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = current_user.id
            alert.status = 'acknowledged'  # Nouveau statut pour la retirer des actives
            alert.updated_at = datetime.utcnow()
            
            session.commit()
            
            current_app.logger.info(f"Alerte {alert_id} acquittée par {current_user.username}")
            
            return jsonify({
                'success': True,
                'message': 'Alerte acquittée avec succès'
            })
            
    except Exception as e:
        current_app.logger.error(f"Erreur acquittement alerte {alert_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/resolve/<int:alert_id>', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    """Résoudre une alerte - la retire définitivement de la liste active"""
    try:
        # Vérifier les permissions admin/operator
        if current_user.role not in ['admin', 'operator']:
            return jsonify({
                'success': False,
                'error': 'Permissions insuffisantes'
            }), 403
        
        with get_db_session_with_context() as session:
            alert = session.query(Alert).filter_by(id=alert_id).first()
            if not alert:
                return jsonify({'success': False, 'error': 'Alerte non trouvée'}), 404
            
            # Résoudre l'alerte
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = current_user.id
            alert.status = 'resolved'
            alert.updated_at = datetime.utcnow()
            
            session.commit()
            
            current_app.logger.info(f"Alerte {alert_id} résolue par {current_user.username}")
            
            return jsonify({
                'success': True,
                'message': 'Alerte résolue avec succès'
            })
            
    except Exception as e:
        current_app.logger.error(f"Erreur résolution alerte {alert_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/mark-read/<int:alert_id>', methods=['POST'])
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
    """Récupérer la configuration des alertes"""
    try:
        with get_db_session_with_context() as session:
            # Récupérer les configurations depuis la base de données
            configs = session.query(SystemConfig).filter_by(category='alerts').all()
            
            # Créer un dictionnaire de configuration
            config = {
                # Notifications générales
                'email_enabled': False,
                'webhook_enabled': False,
                
                # Configuration email
                'smtp_server': '',
                'smtp_port': '587',
                'smtp_username': '',
                'smtp_use_tls': True,
                
                # Configuration webhook
                'webhook_url': '',
                
                # Destinataires
                'alert_recipients': '',
                'alert_critical_recipients': '',
                'alert_error_recipients': '',
                'alert_warning_recipients': '',
                
                # Seuils d'alerte
                'max_offset_threshold': 1.0,
                'critical_offset_threshold': 5.0,
                'max_delay_threshold': 1.0,
                
                # Rétention
                'alert_retention_days': 30
            }
            
            # Mettre à jour avec les valeurs de la base de données
            for config_item in configs:
                key = config_item.key_name.replace('alerts.', '')
                if key in config:
                    if config_item.value_type == 'bool':
                        config[key] = config_item.value.lower() == 'true'
                    elif config_item.value_type == 'int':
                        config[key] = int(config_item.value)
                    elif config_item.value_type == 'float':
                        config[key] = float(config_item.value)
                    else:
                        config[key] = config_item.value
        
        return jsonify({
            'success': True,
            'config': config
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération de config: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la récupération de la configuration'
        }), 500

@alerts_bp.route('/config', methods=['POST'])
@login_required
def update_alert_config():
    """Mettre à jour la configuration des alertes"""
    try:
        # Vérifier les permissions admin
        if current_user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Permissions administrateur requises'
            }), 403
        
        data = request.get_json()
        
        # Configurations à mettre à jour
        config_mapping = {
            'email_enabled': 'alerts.email_enabled',
            'webhook_enabled': 'alerts.webhook_enabled',
            'smtp_server': 'alerts.smtp_server',
            'smtp_port': 'alerts.smtp_port',
            'smtp_username': 'alerts.smtp_username',
            'smtp_password': 'alerts.smtp_password',
            'smtp_use_tls': 'alerts.smtp_use_tls',
            'webhook_url': 'alerts.webhook_url',
            'webhook_secret': 'alerts.webhook_secret',
            'alert_recipients': 'alerts.alert_recipients',
            'alert_critical_recipients': 'alerts.alert_critical_recipients',
            'alert_error_recipients': 'alerts.alert_error_recipients',
            'alert_warning_recipients': 'alerts.alert_warning_recipients',
            'max_offset_threshold': 'alerts.max_offset_threshold',
            'critical_offset_threshold': 'alerts.critical_offset_threshold',
            'max_delay_threshold': 'alerts.max_delay_threshold',
            'alert_retention_days': 'alerts.alert_retention_days'
        }
        
        updated = []
        
        with get_db_session_with_context() as session:
            for frontend_key, config_key in config_mapping.items():
                if frontend_key in data:
                    value = data[frontend_key]
                    
                    # Convertir les booléens en string
                    if isinstance(value, bool):
                        value = 'true' if value else 'false'
                    else:
                        value = str(value)
                    
                    # Mettre à jour ou créer la configuration
                    config = session.query(SystemConfig).filter_by(key_name=config_key).first()
                    if config:
                        config.value = value
                        config.updated_at = datetime.utcnow()
                    else:
                        config = SystemConfig(
                            key_name=config_key,
                            value=value,
                            value_type='string',
                            description=f'Configuration automatique pour {frontend_key}',
                            category='alerts',
                            created_by=current_user.id,
                            updated_by=current_user.id
                        )
                        session.add(config)
                    
                    updated.append(config_key)
            
            session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Configuration mise à jour ({len(updated)} paramètres)'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la mise à jour de config: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la mise à jour de la configuration'
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

@alerts_bp.route('/<int:alert_id>', methods=['GET'])
@login_required
def get_alert_details(alert_id):
    """Récupérer les détails complets d'une alerte spécifique"""
    try:
        with get_db_session_with_context() as session:
            # Récupérer l'alerte
            alert = session.query(Alert).filter_by(id=alert_id).first()
            
            if not alert:
                return jsonify({
                    'success': False,
                    'error': 'Alerte non trouvée'
                }), 404
            
            # Récupérer le serveur associé si disponible
            server_info = None
            if alert.server_id:
                server = session.query(NTPServer).filter_by(id=alert.server_id).first()
                if server:
                    server_info = {
                        'id': server.id,
                        'name': server.name,
                        'address': server.address,
                        'status': server.status
                    }
            
            # Récupérer les alertes similaires pour statistiques
            similar_alerts = session.query(Alert).filter(
                Alert.alert_type == alert.alert_type,
                Alert.server_id == alert.server_id,
                Alert.id != alert.id
            ).order_by(Alert.created_at.desc()).limit(5).all()
            
            # Compter les occurrences
            total_occurrences = session.query(Alert).filter(
                Alert.alert_type == alert.alert_type,
                Alert.server_id == alert.server_id
            ).count()
            
            # Calculer la fréquence
            first_occurrence = session.query(Alert.created_at).filter(
                Alert.alert_type == alert.alert_type,
                Alert.server_id == alert.server_id
            ).order_by(Alert.created_at.asc()).first()
            
            frequency_days = 0
            if first_occurrence and first_occurrence[0]:
                frequency_days = (datetime.utcnow() - first_occurrence[0]).days
            
            # Construire la réponse
            alert_data = {
                'id': alert.id,
                'server_id': alert.server_id,
                'server_name': server_info['name'] if server_info else None,
                'server_info': server_info,
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'message': alert.message,
                'status': alert.status,
                'details': alert.details,
                'created_at': alert.created_at.isoformat() if alert.created_at else None,
                'updated_at': alert.updated_at.isoformat() if alert.updated_at else None,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                'is_read': alert.is_read,
                'statistics': {
                    'total_occurrences': total_occurrences,
                    'frequency_days': frequency_days,
                    'similar_alerts_count': len(similar_alerts),
                    'first_occurrence': first_occurrence[0].isoformat() if first_occurrence and first_occurrence[0] else None
                },
                'similar_alerts': [
                    {
                        'id': sa.id,
                        'created_at': sa.created_at.isoformat() if sa.created_at else None,
                        'status': sa.status,
                        'severity': sa.severity
                    } for sa in similar_alerts
                ]
            }
            
            return jsonify({
                'success': True,
                'alert': alert_data
            })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des détails de l'alerte {alert_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la récupération des détails'
        }), 500 

@alerts_bp.route('/history', methods=['GET'])
@login_required
def get_alert_history():
    """Récupérer l'historique des alertes résolues et inactives"""
    try:
        # Paramètres de pagination et de filtrage
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status', 'all')
        severity = request.args.get('severity', 'all')
        server_id = request.args.get('server_id', 'all')
        date_range = request.args.get('date_range', '7d')
        
        with get_db_session_with_context() as session:
            # Construire la requête de base pour les alertes historiques
            query = session.query(Alert).filter(Alert.status.in_(['resolved', 'acknowledged']))
            
            # Filtrer par statut
            if status != 'all':
                query = query.filter_by(status=status)
            
            # Filtrer par sévérité
            if severity != 'all':
                query = query.filter_by(severity=severity)
            
            # Filtrer par serveur
            if server_id != 'all':
                query = query.filter_by(server_id=int(server_id))
            
            # Filtrer par plage de dates
            if date_range != 'all':
                cutoff_date = datetime.utcnow()
                if date_range == '1d':
                    cutoff_date -= timedelta(days=1)
                elif date_range == '7d':
                    cutoff_date -= timedelta(days=7)
                elif date_range == '30d':
                    cutoff_date -= timedelta(days=30)
                elif date_range == '90d':
                    cutoff_date -= timedelta(days=90)
                
                query = query.filter(Alert.created_at >= cutoff_date)
            
            # Ordonner par date de résolution (plus récent en premier)
            query = query.order_by(Alert.resolved_at.desc(), Alert.created_at.desc())
            
            # Récupérer le total pour la pagination
            total = query.count()
            
            # Appliquer la pagination
            offset = (page - 1) * per_page
            alerts = query.offset(offset).limit(per_page).all()
            
            # Convertir en dictionnaires avec informations du serveur
            alerts_data = []
            for alert in alerts:
                # Récupérer le nom du serveur si disponible
                server_name = None
                if alert.server_id:
                    server = session.query(NTPServer).filter_by(id=alert.server_id).first()
                    if server:
                        server_name = server.name
                
                alert_dict = {
                    'id': alert.id,
                    'server_id': alert.server_id,
                    'server_name': server_name,
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'title': alert.title,
                    'message': alert.message,
                    'status': alert.status,
                    'created_at': alert.created_at.isoformat() if alert.created_at else None,
                    'updated_at': alert.updated_at.isoformat() if alert.updated_at else None,
                    'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                    'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    'occurrence_count': getattr(alert, 'occurrence_count', 1),
                    'first_occurrence': alert.created_at.isoformat() if alert.created_at else None,
                    'last_occurrence': alert.updated_at.isoformat() if alert.updated_at else None
                }
                alerts_data.append(alert_dict)
            
            # Statistiques pour l'historique
            stats = {
                'total': total,
                'resolved': session.query(Alert).filter_by(status='resolved').count(),
                'acknowledged': session.query(Alert).filter_by(status='acknowledged').count(),
                'deleted': 0  # Placeholder pour les alertes supprimées si implémenté
            }
            
            return jsonify({
                'success': True,
                'alerts': alerts_data,
                'pagination': {
                    'page': page,
                    'pages': (total + per_page - 1) // per_page,
                    'per_page': per_page,
                    'total': total
                },
                'stats': stats,
                'filters': {
                    'status': status,
                    'severity': severity,
                    'server_id': server_id,
                    'date_range': date_range
                }
            })
            
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération de l'historique des alertes: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la récupération de l\'historique'
        }), 500

@alerts_bp.route('/history/export', methods=['GET'])
@login_required
def export_alert_history():
    """Exporter l'historique des alertes en CSV"""
    try:
        # Récupérer les mêmes filtres que pour l'historique
        status = request.args.get('status', 'all')
        severity = request.args.get('severity', 'all')
        server_id = request.args.get('server_id', 'all')
        date_range = request.args.get('date_range', '7d')
        
        with get_db_session_with_context() as session:
            # Construire la requête (même logique que get_alert_history)
            query = session.query(Alert).filter(Alert.status.in_(['resolved', 'acknowledged']))
            
            if status != 'all':
                query = query.filter_by(status=status)
            
            if severity != 'all':
                query = query.filter_by(severity=severity)
            
            if server_id != 'all':
                query = query.filter_by(server_id=int(server_id))
            
            if date_range != 'all':
                cutoff_date = datetime.utcnow()
                if date_range == '1d':
                    cutoff_date -= timedelta(days=1)
                elif date_range == '7d':
                    cutoff_date -= timedelta(days=7)
                elif date_range == '30d':
                    cutoff_date -= timedelta(days=30)
                elif date_range == '90d':
                    cutoff_date -= timedelta(days=90)
                
                query = query.filter(Alert.created_at >= cutoff_date)
            
            # Limiter à 1000 entrées pour l'export
            alerts = query.order_by(Alert.resolved_at.desc(), Alert.created_at.desc()).limit(1000).all()
            
            # Créer le CSV
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # En-têtes
            writer.writerow([
                'ID', 'Serveur', 'Type', 'Sévérité', 'Titre', 'Message', 'Statut',
                'Créée le', 'Résolue le', 'Durée (minutes)', 'Occurrences'
            ])
            
            # Données
            for alert in alerts:
                # Récupérer le nom du serveur
                server_name = 'Système'
                if alert.server_id:
                    server = session.query(NTPServer).filter_by(id=alert.server_id).first()
                    if server:
                        server_name = server.name
                
                # Calculer la durée
                duration_minutes = 0
                if alert.created_at and alert.resolved_at:
                    duration_minutes = int((alert.resolved_at - alert.created_at).total_seconds() / 60)
                
                writer.writerow([
                    alert.id,
                    server_name,
                    alert.alert_type or '',
                    alert.severity or '',
                    alert.title or '',
                    alert.message or '',
                    alert.status or '',
                    alert.created_at.strftime('%Y-%m-%d %H:%M:%S') if alert.created_at else '',
                    alert.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if alert.resolved_at else '',
                    duration_minutes,
                    getattr(alert, 'occurrence_count', 1)
                ])
            
            # Préparer la réponse
            from flask import make_response
            
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=alert-history-{datetime.now().strftime("%Y%m%d")}.csv'
            
            return response
            
    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'export de l'historique: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de l\'export'
        }), 500 


# ================== CONFIGURATION ALERTTHRESHOLD ==================

@alerts_bp.route('/thresholds', methods=['GET'])
@login_required
def get_alert_thresholds():
    """Récupérer la configuration des seuils d'alertes"""
    try:
        from backend.services.threshold_manager import threshold_manager
        
        # Utiliser le ThresholdManager pour récupérer les seuils
        thresholds = threshold_manager.get_all_thresholds()
        
        thresholds_data = []
        for threshold in thresholds:
            thresholds_data.append({
                'id': threshold['id'],
                'metric_name': threshold['metric_name'],
                'server_type': threshold['server_type'],
                'warning_threshold': threshold['warning_threshold'],
                'critical_threshold': threshold['critical_threshold'],
                'unit': threshold['unit'],
                'enabled': threshold['enabled'],
                'description': threshold['description']
            })
        
        return jsonify({
            'success': True,
            'thresholds': thresholds_data,
            'count': len(thresholds_data)
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur récupération seuils: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/thresholds/<int:threshold_id>', methods=['PUT'])
@login_required
def update_alert_threshold(threshold_id):
    """Mettre à jour un seuil d'alerte"""
    try:
        # Vérifier les permissions admin
        if current_user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Permissions administrateur requises'
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Données manquantes'}), 400
        
        with get_db_session_with_context() as session:
            threshold = session.query(AlertThreshold).filter_by(id=threshold_id).first()
            if not threshold:
                return jsonify({'success': False, 'error': 'Seuil non trouvé'}), 404
            
            # Validation des données
            warning_threshold = data.get('warning_threshold')
            critical_threshold = data.get('critical_threshold')
            
            if warning_threshold is not None and critical_threshold is not None:
                if warning_threshold >= critical_threshold:
                    return jsonify({
                        'success': False,
                        'error': 'Le seuil d\'avertissement doit être inférieur au seuil critique'
                    }), 400
            
            # Mettre à jour les champs
            if warning_threshold is not None:
                threshold.warning_threshold = float(warning_threshold)
            if critical_threshold is not None:
                threshold.critical_threshold = float(critical_threshold)
            if 'enabled' in data:
                threshold.enabled = bool(data['enabled'])
            if 'description' in data:
                threshold.description = data['description']
            
            threshold.updated_at = datetime.utcnow()
            session.commit()
            
            # Synchroniser SystemConfig si nécessaire
            sync_systemconfig_with_alertthreshold(session, threshold)
            
            current_app.logger.info(f"Seuil {threshold.metric_name} mis à jour par {current_user.username}")
            
            return jsonify({
                'success': True,
                'message': f'Seuil {threshold.metric_name} mis à jour',
                'threshold': {
                    'id': threshold.id,
                    'metric_name': threshold.metric_name,
                    'warning_threshold': threshold.warning_threshold,
                    'critical_threshold': threshold.critical_threshold,
                    'enabled': threshold.enabled
                }
            })
            
    except Exception as e:
        current_app.logger.error(f"Erreur mise à jour seuil: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def sync_systemconfig_with_alertthreshold(session, threshold):
    """Synchroniser SystemConfig avec AlertThreshold"""
    try:
        # Mapping des métriques vers les clés SystemConfig
        config_mapping = {
            'offset': {
                'warning': 'alerts.offset_warning_threshold',
                'critical': 'alerts.offset_critical_threshold'
            },
            'latency': {
                'warning': 'alerts.latency_warning_threshold',
                'critical': 'alerts.latency_critical_threshold'
            },
            'stratum': {
                'warning': 'alerts.stratum_max_threshold',
                'critical': 'alerts.stratum_critical_threshold'
            }
        }
        
        if threshold.metric_name in config_mapping:
            mapping = config_mapping[threshold.metric_name]
            
            # Mettre à jour les configurations
            for threshold_type, config_key in mapping.items():
                config = session.query(SystemConfig).filter_by(key_name=config_key).first()
                
                if config:
                    if threshold_type == 'warning':
                        config.value = str(int(threshold.warning_threshold))
                    else:  # critical
                        config.value = str(int(threshold.critical_threshold))
                    config.updated_at = datetime.utcnow()
                else:
                    # Créer la configuration si elle n'existe pas
                    value = threshold.warning_threshold if threshold_type == 'warning' else threshold.critical_threshold
                    new_config = SystemConfig(
                        key_name=config_key,
                        value=str(int(value)),
                        value_type='int',
                        description=f'Seuil {threshold_type} pour {threshold.metric_name} (synchronisé)',
                        category='alerts',
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(new_config)
        
    except Exception as e:
        current_app.logger.error(f"Erreur synchronisation SystemConfig: {e}")

@alerts_bp.route('/thresholds/batch', methods=['POST'])
@login_required
def upsert_alert_thresholds_batch():
    """Créer/mettre à jour des seuils en lot de manière atomique.
    Payload: { items: [ {id?, metric_name, server_type_id, warning_threshold, critical_threshold, unit, enabled, description?} ] }
    Règles: metric in (offset, latency, stratum); units ms/ms/level; warning < critical; enabled bool.
    Unicité logique: (metric_name, server_type_id).
    """
    try:
        data = request.get_json() or {}
        items = data.get('items', [])
        if not isinstance(items, list) or not items:
            return jsonify({'success': False, 'error': 'Aucun élément à traiter'}), 400

        valid_metrics = {'offset': 'ms', 'latency': 'ms', 'stratum': 'level', 'availability': '%'}

        from backend.models.alert_threshold import AlertThreshold
        from backend.models.server_type import ServerType
        with get_db_session_with_context() as session:
            # validation référentiels en amont
            st_ids = {int(it.get('server_type_id')) for it in items if str(it.get('server_type_id','')).isdigit()}
            if st_ids:
                existing = session.query(ServerType.id).filter(ServerType.id.in_(list(st_ids))).all()
                existing_ids = {row[0] for row in existing}
                missing = st_ids - existing_ids
                if missing:
                    return jsonify({'success': False, 'error': f'server_type_id inexistant: {sorted(list(missing))}'}), 400

            # upsert transactionnel
            upserts = []
            for it in items:
                metric = str(it.get('metric_name','')).strip().lower()
                st_id = it.get('server_type_id')
                try:
                    st_id = int(st_id)
                except Exception:
                    return jsonify({'success': False, 'error': f'server_type_id invalide pour {metric}'}), 400
                if metric not in valid_metrics:
                    return jsonify({'success': False, 'error': f'metric_name invalide: {metric}'}), 400
                # unité forcée selon métrique
                unit = valid_metrics[metric]
                try:
                    warn = float(it.get('warning_threshold'))
                    crit = float(it.get('critical_threshold'))
                except Exception:
                    return jsonify({'success': False, 'error': f'seuils invalides pour {metric}'}), 400

                # Règles d'inégalités par métrique
                if metric in ('offset', 'latency'):
                    if not (warn < crit):
                        return jsonify({'success': False, 'error': f'warning < critical requis pour {metric}'}), 400
                elif metric == 'availability':
                    # Disponibilité en %, bornage [0,100]
                    warn = max(0.0, min(100.0, warn))
                    crit = max(0.0, min(100.0, crit))
                    if abs(warn - crit) < 1e-9:
                        # Ajustement si égalité
                        crit = min(100.0, crit + 1.0)
                        warn = max(0.0, warn - 1.0)
                    if not (crit < warn):
                        return jsonify({'success': False, 'error': 'Pour availability: critical < warning requis'}), 400
                enabled = bool(it.get('enabled', True))
                desc = it.get('description')

                # chercher existant par (metric, server_type_id)
                existing = session.query(AlertThreshold).filter(
                    AlertThreshold.metric_name == metric,
                    AlertThreshold.server_type_id == st_id
                ).first()
                if existing:
                    existing.warning_threshold = warn
                    existing.critical_threshold = crit
                    existing.unit = unit
                    existing.enabled = enabled
                    if desc is not None:
                        existing.description = desc
                    existing.updated_at = datetime.utcnow()
                    upserts.append(existing.id)
                else:
                    new_th = AlertThreshold(
                        metric_name=metric,
                        server_type_id=st_id,
                        warning_threshold=warn,
                        critical_threshold=crit,
                        unit=unit,
                        enabled=enabled,
                        description=desc
                    )
                    session.add(new_th)
                    session.flush()
                    upserts.append(new_th.id)

            session.commit()
            return jsonify({'success': True, 'updated_ids': upserts, 'count': len(upserts)})
    except Exception as e:
        current_app.logger.error(f"Erreur batch thresholds: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
