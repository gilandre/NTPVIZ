"""
API Configuration - Gestion avancée des paramètres système
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.database import SystemConfig
from backend.database import NTPServer
from backend.database import User
# SUPPRIMÉ: Import Flask-SQLAlchemy circulaire
from backend.database_manager import get_db_session_with_context
from datetime import datetime, timedelta
from sqlalchemy import func
import logging
import json

logger = logging.getLogger(__name__)

config_bp = Blueprint('config', __name__)

@config_bp.route('/system', methods=['GET'])
def get_system_config():
    """Récupérer la configuration système de base (pas de login requis pour les tests)"""
    try:
        with get_db_session_with_context() as session:
            configs = session.query(SystemConfig).filter_by(is_public=True).all()
            return jsonify({
                'success': True,
                'configs': {config.key_name: config.value for config in configs},
                'count': len(configs)
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def config_required(f):
    """Dcorateur pour les routes nécessitant des droits de configuration"""
    from functools import wraps
    
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.can_configure:
            return jsonify({'error': 'Droits de configuration requis'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ================== CONFIGURATION GNRALE ==================

@config_bp.route('/categories', methods=['GET'])
@login_required
def get_config_categories():
    """Récupérer toutes les catégories de configuration disponibles"""
    try:
        with get_db_session_with_context() as session:
            categories = session.query(SystemConfig.category).distinct().all()
            categories_info = {}
            
            # Ajouter les catégories existantes
            for (category,) in categories:
                configs = session.query(SystemConfig).filter_by(category=category).all()
                categories_info[category] = {
                    'name': category,
                    'display_name': get_category_display_name(category),
                    'description': get_category_description(category),
                    'icon': get_category_icon(category),
                    'count': len(configs),
                    'public_count': len([c for c in configs if c.is_public or current_user.is_admin])
                }
            
            # S'assurer que la catégorie 'alerts' existe toujours
            if 'alerts' not in categories_info:
                categories_info['alerts'] = {
                    'name': 'alerts',
                    'display_name': get_category_display_name('alerts'),
                    'description': get_category_description('alerts'),
                    'icon': get_category_icon('alerts'),
                    'count': 0,
                    'public_count': 0
                }
        
        return jsonify({
            'success': True,
            'data': categories_info
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération catégories: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@config_bp.route('/category/<category>', methods=['GET'])
@login_required
def get_category_config(category):
    """Récupérer la configuration d'une catégorie spécifique"""
    try:
        with get_db_session_with_context() as session:
            # Construire la requête avec filtrage des permissions
            if current_user.is_admin:
                configs = session.query(SystemConfig).filter_by(category=category).all()
            else:
                configs = session.query(SystemConfig).filter_by(category=category, is_public=True).all()
            
            configs_data = []
            for config in configs:
                configs_data.append({
                    'id': config.id,
                    'key': config.key_name,
                    'value': config.value,
                    'value_type': config.value_type,
                    'description': config.description,
                    'category': config.category,
                    'is_public': config.is_public,
                    'created_at': config.created_at.isoformat() if config.created_at else None,
                    'updated_at': config.updated_at.isoformat() if config.updated_at else None
                })
            
            result = {
                'category': category,
                'display_name': get_category_display_name(category),
                'description': get_category_description(category),
                'configs': configs_data,
                'last_updated': max([c.updated_at for c in configs]).isoformat() if configs else None,
                'can_modify': current_user.can_configure
            }
            
            return jsonify({
                'success': True,
                'data': result
            })
        
    except Exception as e:
        logger.error(f"Erreur récupération catégorie {category}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@config_bp.route('/bulk-update', methods=['POST'])
@config_required
def bulk_update_config():
    """Mise à jour en masse de la configuration"""
    try:
        data = request.get_json()
        updated_configs = []
        errors = []
        
        with get_db_session_with_context() as session:
            for config_update in data.get('configs', []):
                try:
                    key = config_update.get('key')
                    value = config_update.get('value')
                    value_type = config_update.get('value_type', 'string')
                    
                    if not key:
                        errors.append({'key': 'unknown', 'error': 'Clé manquante'})
                        continue
                    
                    # Validation
                    validation_error = validate_config_value(key, value, value_type)
                    if validation_error:
                        errors.append({'key': key, 'error': validation_error})
                        continue
                    
                    # Rechercher ou créer la configuration
                    config = session.query(SystemConfig).filter_by(key_name=key).first()
                    
                    if config:
                        # Mettre à jour la configuration existante
                        config.value = str(value)
                        config.value_type = value_type
                        config.updated_by = current_user.id
                        config.updated_at = datetime.utcnow()
                    else:
                        # Créer une nouvelle configuration
                        config = SystemConfig(
                            key=key,
                            value=str(value),
                            value_type=value_type,
                            description=config_update.get('description', ''),
                            category=config_update.get('category', 'general'),
                            created_by=current_user.id,
                            updated_by=current_user.id
                        )
                        session.add(config)
                    
                    updated_configs.append({
                        'id': config.id,
                        'key': config.key_name,
                        'value': config.value,
                        'value_type': config.value_type,
                        'description': config.description,
                        'category': config.category
                    })
                    
                except Exception as e:
                    errors.append({'key': config_update.get('key', 'unknown'), 'error': str(e)})
            
            if not errors:
                session.commit()
            
            # Log des modifications
            if updated_configs:
                logger.info(f"Configuration bulk update par {current_user.username}: "
                           f"{len(updated_configs)} configs modifiées")
            
            return jsonify({
                'success': len(errors) == 0,
                'message': f'{len(updated_configs)} configurations mises à jour',
                'updated': updated_configs,
                'errors': errors,
                'timestamp': datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Erreur bulk update configuration: {e}")
        return jsonify({'error': str(e)}), 500

# ================== CONFIGURATION NTP ==================

@config_bp.route('/ntp', methods=['GET'])
@login_required
def get_ntp_config():
    """Récupérer la configuration NTP de base"""
    try:
        with get_db_session_with_context() as session:
            # Configuration NTP de base
            ntp_configs = session.query(SystemConfig).filter_by(category='ntp').all()
            
            # Serveurs NTP actifs (non supprimés)
            servers = session.query(NTPServer).filter(
                NTPServer.is_active == True,
                NTPServer.deleted_at.is_(None)
            ).order_by(NTPServer.priority).all()
            
            # Statistiques de base
            from backend.database import NTPLog
            recent_logs = session.query(NTPLog).filter(
                NTPLog.timestamp >= datetime.utcnow() - timedelta(hours=1)
            ).limit(50).all()
            
            # Calculs de performance
            avg_offset = 0
            max_offset = 0
            if recent_logs:
                offsets = [abs(log.offset) for log in recent_logs if log.offset is not None]
                if offsets:
                    avg_offset = sum(offsets) / len(offsets)
                    max_offset = max(offsets)
            
            # Configuration de base
            config_data = {}
            for config in ntp_configs:
                config_data[config.key_name] = config.value
            
            servers_data = []
            for server in servers:
                servers_data.append({
                    'id': server.id,
                    'name': server.name,
                    'address': server.address,
                    'port': server.port,
                    'priority': server.priority,
                    'status': server.status,
                    'is_active': server.is_active,
                    'last_sync': server.last_sync.isoformat() if server.last_sync else None,
                    'last_offset': server.last_offset,
                    'last_latency': server.last_latency
                })
            
            return jsonify({
                'success': True,
                'config': config_data,
                'servers': servers_data,
                'statistics': {
                    'total_servers': len(servers),
                    'online_servers': len([s for s in servers if s.status != 'offline']),
                    'avg_offset_1h': round(avg_offset, 4),
                    'max_offset_1h': round(max_offset, 4),
                    'total_queries_1h': len(recent_logs)
                }
            })
        
    except Exception as e:
        logger.error(f"Erreur récupération configuration NTP: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@config_bp.route('/ntp/settings', methods=['GET', 'POST'])
@login_required
def ntp_settings():
    """Gestion complète des paramètres NTP (GET et POST)"""
    if request.method == 'GET':
        return get_ntp_settings()
    else:
        return update_ntp_settings()

def get_ntp_settings():
    """Récupérer les paramètres NTP complets"""
    try:
        with get_db_session_with_context() as session:
            # Configuration NTP
            ntp_configs = session.query(SystemConfig).filter_by(category='ntp').all()
            
            # Serveurs NTP actifs (non supprimés)
            servers = session.query(NTPServer).filter(
                NTPServer.is_active == True,
                NTPServer.deleted_at.is_(None)
            ).order_by(NTPServer.priority).all()
            
            # Statistiques récentes
            from backend.database import NTPLog
            recent_logs = session.query(NTPLog).filter(
                NTPLog.timestamp >= datetime.utcnow() - timedelta(hours=24)
            ).limit(100).all()
            
            # Calculs de performance
            avg_offset = 0
            max_offset = 0
            if recent_logs:
                offsets = [abs(log.offset) for log in recent_logs if log.offset is not None]
                if offsets:
                    avg_offset = sum(offsets) / len(offsets)
                    max_offset = max(offsets)
            
            # Conversion des données
            settings_data = {}
            for config in ntp_configs:
                settings_data[config.key_name] = {
                    'id': config.id,
                    'key': config.key_name,
                    'value': config.value,
                    'value_type': config.value_type,
                    'description': config.description,
                    'category': config.category
                }
            
            servers_data = []
            for server in servers:
                servers_data.append({
                    'id': server.id,
                    'name': server.name,
                    'address': server.address,
                    'port': server.port,
                    'priority': server.priority,
                    'status': server.status,
                    'is_active': server.is_active,
                    'last_sync': server.last_sync.isoformat() if server.last_sync else None,
                    'last_offset': server.last_offset,
                    'last_latency': server.last_latency
                })
            
            return jsonify({
                'success': True,
                'settings': settings_data,
                'servers': servers_data,
                'statistics': {
                    'total_servers': len(servers),
                    'online_servers': len([s for s in servers if s.status != 'offline']),
                    'avg_offset_24h': round(avg_offset, 4),
                    'max_offset_24h': round(max_offset, 4),
                    'total_queries_24h': len(recent_logs)
                },
                'can_modify': current_user.can_configure
            })
        
    except Exception as e:
        logger.error(f"Erreur récupération paramètres NTP: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def update_ntp_settings():
    """Mettre à jour les paramètres NTP"""
    try:
        data = request.get_json()
        updated_configs = []
        
        # Paramètres NTP valides
        ntp_settings = {
            'ntp.query_interval': ('int', 10, 3600, 'Intervalle de requête'),
            'ntp.default_timeout': ('int', 1, 60, 'Timeout par défaut'),
            'ntp.max_offset_warning': ('float', 0.1, 60.0, 'Seuil d\'alerte'),
            'ntp.max_offset_critical': ('float', 0.5, 300.0, 'Seuil critique'),
            'ntp.retry_attempts': ('int', 1, 10, 'Tentatives de reconnexion'),
            'ntp.enable_monitoring': ('bool', None, None, 'Activer le monitoring')
        }
        
        for key, value in data.items():
            if key in ntp_settings:
                value_type, min_val, max_val, description = ntp_settings[key]
                
                # Validation
                if value_type in ['int', 'float'] and min_val is not None:
                    if not (min_val <= float(value) <= max_val):
                        return jsonify({
                            'error': f'{description}: valeur doit être entre {min_val} et {max_val}'
                        }), 400
                
                # Utiliser le Database Manager pour créer/mettre à jour la configuration
                with get_db_session_with_context() as session:
                    config = session.query(SystemConfig).filter_by(key_name=key).first()
                    
                    if config:
                        # Mettre à jour la configuration existante
                        config.value = str(value)
                        config.value_type = value_type
                        config.updated_by = current_user.id
                        config.updated_at = datetime.utcnow()
                    else:
                        # Créer une nouvelle configuration
                        config = SystemConfig(
                            key=key,
                            value=str(value),
                            value_type=value_type,
                            description=description,
                            category='ntp',
                            created_by=current_user.id,
                            updated_by=current_user.id
                        )
                        session.add(config)
                    
                    session.commit()
                    
                    updated_configs.append({
                        'id': config.id,
                        'key': config.key_name,
                        'value': config.value,
                        'value_type': config.value_type,
                        'description': config.description,
                        'category': config.category
                    })
        
        logger.info(f"Paramètres NTP mis à jour par {current_user.username}: {list(data.keys())}")
        
        return jsonify({
            'success': True,
            'message': 'Paramètres NTP mis à jour avec succès',
            'updated': updated_configs
        })
        
    except Exception as e:
        logger.error(f"Erreur mise à jour paramètres NTP: {e}")
        return jsonify({'error': str(e)}), 500

# ================== CONFIGURATION ALERTES ==================

@config_bp.route('/alerts', methods=['GET', 'POST'])
@login_required
def alerts_config():
    """Gestion complète des alertes (GET et POST)"""
    if request.method == 'GET':
        return get_alerts_config()
    else:
        return save_alerts_config()

def get_alerts_config():
    """Récupérer la configuration complète des alertes"""
    try:
        with get_db_session_with_context() as session:
            # Récupérer toutes les configurations d'alertes
            alert_configs = session.query(SystemConfig).filter_by(category='alerts').all()
            
            # Organiser par sous-catégories
            config = {
                # Seuils d'alerte
                'offset_warning_threshold': 100,
                'offset_critical_threshold': 1000,
                'latency_warning_threshold': 500,
                'latency_critical_threshold': 2000,
                'stratum_max_threshold': 3,
                'connection_timeout': 30,
                'max_consecutive_failures': 3,
                
                # Notifications
                'email_notifications': True,
                'email_addresses': '',
                'webhook_notifications': False,
                'webhook_url': '',
                'min_alert_interval': 15,
                'escalation_enabled': False,
                'escalation_delay': 2,
                
                # Rétention
                'resolved_alerts_retention': 30,
                'acknowledged_alerts_retention': 7,
                'detailed_logs_retention': 7,
                'aggregated_logs_retention': 90,
                
                # Avancé
                'check_interval': 60,
                'ntp_timeout': 10,
                'debug_mode': False,
                'require_auth_alerts': True,
                'audit_log': True,
                'log_level': 'INFO'
            }
            
            # Mettre à jour avec les valeurs de la base de données
            for alert_config in alert_configs:
                key = alert_config.key_name.replace('alerts.', '')
                if key in config:
                    config[key] = alert_config.get_typed_value()
            
            return jsonify({
                'success': True,
                'config': config,
                'can_modify': current_user.can_configure
            })
        
    except Exception as e:
        logger.error(f"Erreur récupération configuration alertes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def save_alerts_config():
    """Sauvegarder la configuration des alertes"""
    try:
        data = request.get_json()
        updated_configs = []
        
        with get_db_session_with_context() as session:
            for key, value in data.items():
                # Préfixer avec 'alerts.' pour la catégorie
                full_key = f'alerts.{key}'
                
                # Déterminer le type de valeur
                if isinstance(value, bool):
                    value_type = 'bool'
                elif isinstance(value, int):
                    value_type = 'int'
                elif isinstance(value, float):
                    value_type = 'float'
                else:
                    value_type = 'string'
                
                # Rechercher ou créer la configuration
                config = session.query(SystemConfig).filter_by(key_name=full_key).first()
                
                if config:
                    # Mettre à jour la configuration existante
                    config.value = str(value)
                    config.value_type = value_type
                    config.updated_by = current_user.id
                    config.updated_at = datetime.utcnow()
                else:
                    # Créer une nouvelle configuration
                    config = SystemConfig(
                        key=full_key,
                        value=str(value),
                        value_type=value_type,
                        description=f'Configuration alerte: {key}',
                        category='alerts',
                        created_by=current_user.id,
                        updated_by=current_user.id
                    )
                    session.add(config)
                
                updated_configs.append({
                    'id': config.id,
                    'key': config.key_name,
                    'value': config.value,
                    'value_type': config.value_type,
                    'description': config.description,
                    'category': config.category
                })
            
            session.commit()
        
        logger.info(f"Configuration des alertes mise à jour par {current_user.username}: {updated_configs}")
        
        return jsonify({
            'success': True,
            'message': 'Configuration des alertes mise à jour avec succès',
            'updated': updated_configs
        })
        
    except Exception as e:
        logger.error(f"Erreur sauvegarde configuration alertes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@config_bp.route('/alerts/test', methods=['POST'])
@config_required
def test_alerts_config():
    """Tester la configuration des alertes"""
    try:
        data = request.get_json() or {}
        test_type = data.get('test_type', 'all')
        
        results = {}
        
        if test_type in ['all', 'email']:
            results['email'] = test_email_notification(data)
        
        if test_type in ['all', 'webhook']:
            results['webhook'] = test_webhook_notification(data)
        
        if test_type in ['all', 'thresholds']:
            results['thresholds'] = test_alert_thresholds(data)
        
        overall_success = all(result.get('success', False) for result in results.values())
        
        return jsonify({
            'success': overall_success,
            'results': results,
            'message': 'Tests terminés' if overall_success else 'Certains tests ont échoué'
        })
        
    except Exception as e:
        logger.error(f"Erreur test configuration alertes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def test_alert_thresholds(config):
    """Tester la cohérence des seuils d'alerte"""
    try:
        # Récupérer les seuils
        offset_warning = config.get('offset_warning_threshold', 100)
        offset_critical = config.get('offset_critical_threshold', 1000)
        latency_warning = config.get('latency_warning_threshold', 500)
        latency_critical = config.get('latency_critical_threshold', 2000)
        
        issues = []
        
        # Validation des seuils avec configuration centralisée
        from backend.config.alert_metrics import ALERT_METRICS
        
        # Récupérer les seuils depuis la configuration centralisée
        offset_config = ALERT_METRICS.get('offset', {})
        latency_config = ALERT_METRICS.get('latency', {})
        
        # Seuils minimums depuis la configuration
        min_offset_warning = get_min_threshold("offset")
        min_latency_warning = get_min_threshold("latency")
        
        if offset_critical <= offset_warning:
            issues.append('Le seuil critique d\'offset doit être supérieur au seuil d\'avertissement')
        
        if latency_critical <= latency_warning:
            issues.append('Le seuil critique de latence doit être supérieur au seuil d\'avertissement')
        
        if offset_warning < min_offset_warning:
            issues.append(f'Le seuil d\'avertissement d\'offset est très bas (< {min_offset_warning}ms)')
        
        if latency_warning < min_latency_warning:
            issues.append(f'Le seuil d\'avertissement de latence est très bas (< {min_latency_warning}ms)')
        
        if issues:
            return {
                'success': False,
                'message': 'Problèmes détectés dans la configuration des seuils',
                'details': {'issues': issues}
            }
        else:
            return {
                'success': True,
                'message': 'Configuration des seuils cohérente',
                'details': {
                    'offset_warning': offset_warning,
                    'offset_critical': offset_critical,
                    'latency_warning': latency_warning,
                    'latency_critical': latency_critical
                }
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Erreur test seuils: {str(e)}',
            'details': {'error_type': type(e).__name__}
        }

# ================== UTILITAIRES ==================

def get_category_display_name(category):
    """Nom d'affichage pour une catgorie"""
    names = {
        'system': 'Systme',
        'ntp': 'NTP & Synchronisation',
        'alerts': 'Alertes & Notifications',
        'network': 'Rseau & Connectivit',
        'monitoring': 'Surveillance & Logs',
        'security': 'Scurit & Audit',
        'general': 'Gnral'
    }
    return names.get(category, category.title())

def get_category_description(category):
    """Description pour une catgorie"""
    descriptions = {
        'system': 'Configuration système de base et informations générales',
        'ntp': 'Paramètres de synchronisation NTP et serveurs de temps',
        'alerts': 'Configuration des alertes, notifications et seuils',
        'network': 'Paramètres réseau, connectivité et timeouts',
        'monitoring': 'Configuration du monitoring, logs et mtriques',
        'security': 'Paramètres de sécurité, audit et authentification',
        'general': 'Paramètres généraux de l\'application'
    }
    return descriptions.get(category, f'Configuration {category}')

def get_category_icon(category):
    """Icne Font Awesome pour une catgorie"""
    icons = {
        'system': 'fas fa-server',
        'ntp': 'fas fa-clock',
        'alerts': 'fas fa-bell',
        'network': 'fas fa-network-wired',
        'monitoring': 'fas fa-chart-line',
        'security': 'fas fa-shield-alt',
        'general': 'fas fa-cog'
    }
    return icons.get(category, 'fas fa-cog')

def validate_config_value(key, value, value_type):
    """Valider une valeur de configuration"""
    try:
        if value_type == 'int':
            int(value)
        elif value_type == 'float':
            float(value)
        elif value_type == 'bool':
            if str(value).lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
                return "Valeur boolenne invalide"
        elif value_type == 'json':
            json.loads(value if isinstance(value, str) else json.dumps(value))
        
        # Validations spcifiques par cl
        key_validations = {
            'ntp.query_interval': lambda v: 10 <= int(v) <= 3600,
            'ntp.default_timeout': lambda v: 1 <= int(v) <= 60,
            'ntp.max_offset_warning': lambda v: 0.1 <= float(v) <= 60.0,
            'ntp.max_offset_critical': lambda v: 0.5 <= float(v) <= 300.0
        }
        
        if key in key_validations:
            if not key_validations[key](value):
                return f"Valeur hors limites pour {key}"
        
        return None
        
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        return f"Valeur invalide: {str(e)}"

def test_email_notification(config):
    """Tester la notification email"""
    try:
        # Pour l'instant, retourner un test simulé
        email_addresses = config.get('email_addresses', '')
        if not email_addresses:
            return {
                'success': False,
                'message': 'Aucune adresse email configurée',
                'details': {'email_addresses': False}
            }
        
        # Simulation du test email
        return {
            'success': True,
            'message': f'Test email simulé pour {email_addresses}',
            'details': {
                'recipients': email_addresses.split(','),
                'test_mode': True
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur test email: {e}")
        return {
            'success': False,
            'message': f'Erreur test email: {str(e)}',
            'details': {'error_type': type(e).__name__}
        }

def test_webhook_notification(config):
    """Tester la notification webhook"""
    try:
        webhook_url = config.get('webhook_url', '')
        if not webhook_url:
            return {
                'success': False,
                'message': 'URL webhook non configurée',
                'details': {'webhook_url': False}
            }
        
        # Validation de l'URL
        if not webhook_url.startswith(('http://', 'https://')):
            return {
                'success': False,
                'message': 'URL webhook invalide (doit commencer par http:// ou https://)',
                'details': {'webhook_url': webhook_url}
            }
        
        # Simulation du test webhook
        return {
            'success': True,
            'message': f'Test webhook simulé pour {webhook_url}',
            'details': {
                'url': webhook_url,
                'test_mode': True
            }
        }
            
    except Exception as e:
        logger.error(f"Erreur test webhook: {e}")
        return {
            'success': False,
            'message': f'Erreur test webhook: {str(e)}',
            'details': {'error_type': type(e).__name__}
        } 

@config_bp.route('/alerts/conditions', methods=['POST'])
@login_required
@config_required
def save_alert_conditions():
    """Sauvegarder les conditions d'alerte"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données manquantes'
            }), 400
        
        # Validation des données
        required_fields = [
            'use_threshold_conditions', 'use_latency_conditions',
            'use_availability_conditions', 'use_stratum_conditions'
        ]
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Champ requis manquant: {field}'
                }), 400
        
        # Sauvegarder dans la base de données
        with get_db_session_with_context() as session:
            # Créer ou mettre à jour les configurations
            configs_to_save = [
                ('alerts.use_threshold_conditions', data['use_threshold_conditions'], 'bool'),
                ('alerts.use_latency_conditions', data['use_latency_conditions'], 'bool'),
                ('alerts.use_availability_conditions', data['use_availability_conditions'], 'bool'),
                ('alerts.use_stratum_conditions', data['use_stratum_conditions'], 'bool'),
                ('alerts.threshold_warning', data.get('threshold_warning', 0), 'float'),
                ('alerts.threshold_critical', data.get('threshold_critical', 0), 'float'),
                ('alerts.latency_warning', data.get('latency_warning', 0), 'float'),
                ('alerts.latency_critical', data.get('latency_critical', 0), 'float'),
                ('alerts.availability_warning', data.get('availability_warning', 0), 'float'),
                ('alerts.availability_critical', data.get('availability_critical', 0), 'float'),
                ('alerts.stratum_max', data.get('stratum_max', 0), 'int')
            ]
            
            for key, value, value_type in configs_to_save:
                config = session.query(SystemConfig).filter_by(key_name=key).first()
                
                if config:
                    # Mettre à jour la configuration existante
                    config.value = str(value)
                    config.value_type = value_type
                    config.updated_at = datetime.utcnow()
                else:
                    # Créer une nouvelle configuration
                    config = SystemConfig(
                        key_name=key,
                        value=str(value),
                        value_type=value_type,
                        description=f'Configuration alerte: {key}',
                        category='alerts'
                    )
                    session.add(config)
            
            session.commit()
            
            logger.info(f"Conditions d'alerte sauvegardées par {current_user.username}")
            
            return jsonify({
                'success': True,
                'message': 'Conditions d\'alerte sauvegardées avec succès'
            }), 201
            
    except Exception as e:
        logger.error(f"Erreur sauvegarde conditions alerte: {e}")
        return jsonify({
            'success': False,
            'error': f'Erreur sauvegarde: {str(e)}'
        }), 500

@config_bp.route('/alerts/conditions', methods=['GET'])
@login_required
def get_alert_conditions():
    """Récupérer les conditions d'alerte"""
    try:
        with get_db_session_with_context() as session:
            # Récupérer toutes les configurations d'alerte
            configs = session.query(SystemConfig).filter(
                SystemConfig.key_name.like('alerts.%')
            ).all()
            
            conditions = {}
            for config in configs:
                key = config.key_name.replace('alerts.', '')
                
                # Convertir la valeur selon le type avec gestion d'erreur
                try:
                    if config.value_type == 'bool':
                        conditions[key] = config.value.lower() == 'true'
                    elif config.value_type == 'int':
                        # Gérer les valeurs float stockées comme string
                        float_val = float(config.value) if config.value else 0.0
                        conditions[key] = int(float_val)
                    elif config.value_type == 'float':
                        conditions[key] = float(config.value) if config.value else 0.0
                    else:
                        conditions[key] = config.value
                except (ValueError, TypeError) as e:
                    logger.warning(f"Erreur conversion valeur {key}: {config.value} (type: {config.value_type}) - {e}")
                    # Valeur par défaut selon le type
                    if config.value_type == 'bool':
                        conditions[key] = False
                    elif config.value_type == 'int':
                        conditions[key] = 0
                    elif config.value_type == 'float':
                        conditions[key] = 0.0
                    else:
                        conditions[key] = config.value or ''
            
            return jsonify({
                'success': True,
                'conditions': conditions
            })
            
    except Exception as e:
        logger.error(f"Erreur récupération conditions alerte: {e}")
        return jsonify({
            'success': False,
            'error': f'Erreur récupération: {str(e)}'
        }), 500 
