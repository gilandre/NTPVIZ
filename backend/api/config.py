"""
API Configuration - Gestion avance des paramtres systme
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.database import SystemConfig
from backend.database import NTPServer
from backend.database import User
# SUPPRIMÉ: Import Flask-SQLAlchemy circulaire
from backend.database_manager import get_db_session_with_context
from datetime import datetime, timedelta
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
    """Dcorateur pour les routes ncessitant des droits de configuration"""
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
        
        return jsonify(categories_info)
        
    except Exception as e:
        logger.error(f"Erreur récupération catégories: {e}")
        return jsonify({'error': str(e)}), 500

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
            
            return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erreur récupération catégorie {category}: {e}")
        return jsonify({'error': str(e)}), 500

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

@config_bp.route('/ntp/settings', methods=['GET'])
@login_required
def get_ntp_settings():
    """Récupérer les paramètres NTP complets"""
    try:
        with get_db_session_with_context() as session:
            # Configuration NTP
            ntp_configs = session.query(SystemConfig).filter_by(category='ntp').all()
            
            # Serveurs NTP actifs
            servers = session.query(NTPServer).filter_by(is_active=True).order_by(NTPServer.priority).all()
            
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
        return jsonify({'error': str(e)}), 500

@config_bp.route('/ntp/settings', methods=['POST'])
@config_required
def update_ntp_settings():
    """Mettre  jour les paramtres NTP"""
    try:
        data = request.get_json()
        updated_configs = []
        
        # Paramtres NTP valids
        ntp_settings = {
            'ntp.query_interval': ('int', 10, 3600, 'Intervalle de requte'),
            'ntp.default_timeout': ('int', 1, 60, 'Timeout par dfaut'),
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
                            'error': f'{description}: valeur doit tre entre {min_val} et {max_val}'
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
        
        logger.info(f"Paramtres NTP mis  jour par {current_user.username}: {list(data.keys())}")
        
        return jsonify({
            'success': True,
            'message': 'Paramtres NTP mis  jour avec succs',
            'updated': updated_configs
        })
        
    except Exception as e:
        logger.error(f"Erreur mise à jour paramètres NTP: {e}")
        return jsonify({'error': str(e)}), 500

# ================== CONFIGURATION ALERTES ==================

@config_bp.route('/alerts/settings', methods=['GET'])
@login_required
def get_alerts_settings():
    """Récupérer les paramètres d'alertes"""
    try:
        with get_db_session_with_context() as session:
            # Configuration alertes
            alert_configs = session.query(SystemConfig).filter_by(category='alerts').all()
            
            # Statistiques d'alertes
            from backend.database import Alert
            recent_alerts = session.query(Alert).filter(
                Alert.created_at >= datetime.utcnow() - timedelta(days=7)
            ).all()
            
            alert_stats = {
                'total_alerts_7d': len(recent_alerts),
                'active_alerts': len([a for a in recent_alerts if a.status == 'active']),
                'critical_alerts': len([a for a in recent_alerts if a.severity == 'critical']),
                'warning_alerts': len([a for a in recent_alerts if a.severity == 'warning'])
            }
            
            # Conversion des données
            settings_data = {}
            for config in alert_configs:
                settings_data[config.key_name] = {
                    'id': config.id,
                    'key': config.key_name,
                    'value': config.value,
                    'value_type': config.value_type,
                    'description': config.description,
                    'category': config.category,
                    'is_public': config.is_public
                }
            
            return jsonify({
                'settings': settings_data,
                'statistics': alert_stats,
                'can_modify': current_user.can_configure
            })
        
    except Exception as e:
        logger.error(f"Erreur récupération paramètres alertes: {e}")
        return jsonify({'error': str(e)}), 500

@config_bp.route('/alerts/test', methods=['POST'])
@config_required
def test_alert_config():
    """Tester la configuration des alertes"""
    try:
        data = request.get_json()
        test_type = data.get('type', 'email')
        
        if test_type == 'email':
            # Test notification email
            result = test_email_notification(data)
        elif test_type == 'webhook':
            # Test webhook
            result = test_webhook_notification(data)
        else:
            return jsonify({'error': 'Type de test non support'}), 400
        
        return jsonify({
            'success': result.get('success', False),
            'message': result.get('message', ''),
            'details': result.get('details', {}),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur test alerte: {e}")
        return jsonify({'error': str(e)}), 500

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
        'system': 'Configuration systme de base et informations gnrales',
        'ntp': 'Paramtres de synchronisation NTP et serveurs de temps',
        'alerts': 'Configuration des alertes, notifications et seuils',
        'network': 'Paramtres rseau, connectivit et timeouts',
        'monitoring': 'Configuration du monitoring, logs et mtriques',
        'security': 'Paramtres de scurit, audit et authentification',
        'general': 'Paramtres gnraux de l\'application'
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
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Rcuprer la configuration email
        smtp_host = SystemConfig.get_config('alerts.email.smtp_host')
        smtp_port = int(SystemConfig.get_config('alerts.email.smtp_port', 587))
        smtp_user = SystemConfig.get_config('alerts.email.smtp_user')
        smtp_password = SystemConfig.get_config('alerts.email.smtp_password')
        use_tls = SystemConfig.get_config('alerts.email.use_tls', True, 'bool')
        
        if not all([smtp_host, smtp_user, smtp_password]):
            return {
                'success': False,
                'message': 'Configuration email incomplte (SMTP host, user, password requis)',
                'details': {
                    'smtp_host': bool(smtp_host),
                    'smtp_user': bool(smtp_user),
                    'smtp_password': bool(smtp_password)
                }
            }
        
        # Crer le message de test
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = config.get('test_recipient', smtp_user)
        msg['Subject'] = 'Test NTP Monitor - Configuration Email'
        
        body = f"""
Ceci est un message de test pour vrifier la configuration email de NTP Monitor.

Si vous recevez ce message, la configuration est correcte.

Configuration teste:
- Serveur SMTP: {smtp_host}:{smtp_port}
- Utilisateur: {smtp_user}
- TLS: {'Activ' if use_tls else 'Dsactiv'}

Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Connexion et envoi
        server = smtplib.SMTP(smtp_host, smtp_port)
        if use_tls:
            server.starttls()
        server.login(smtp_user, smtp_password)
        
        text = msg.as_string()
        server.sendmail(smtp_user, [config.get('test_recipient', smtp_user)], text)
        server.quit()
        
        return {
            'success': True,
            'message': f'Test email envoy avec succs  {config.get("test_recipient", smtp_user)}',
            'details': {
                'smtp_host': smtp_host,
                'smtp_port': smtp_port,
                'recipient': config.get('test_recipient', smtp_user)
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
        import requests
        
        # Rcuprer la configuration webhook
        webhook_url = SystemConfig.get_config('alerts.webhook.url')
        webhook_secret = SystemConfig.get_config('alerts.webhook.secret')
        timeout = int(SystemConfig.get_config('alerts.webhook.timeout', 10))
        
        if not webhook_url:
            return {
                'success': False,
                'message': 'URL webhook non configure',
                'details': {'webhook_url': False}
            }
        
        # Payload de test
        test_payload = {
            'type': 'test',
            'title': 'Test NTP Monitor Webhook',
            'message': 'Ceci est un test de la configuration webhook',
            'timestamp': datetime.utcnow().isoformat(),
            'severity': 'info',
            'source': 'ntp_monitor_config_test'
        }
        
        # Headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'NTP-Monitor/1.0'
        }
        
        if webhook_secret:
            import hmac
            import hashlib
            payload_str = json.dumps(test_payload)
            signature = hmac.new(
                webhook_secret.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
            headers['X-NTP-Signature'] = f'sha256={signature}'
        
        # Envoi de la requte
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers=headers,
            timeout=timeout,
            verify=True
        )
        
        if response.status_code in [200, 201, 202]:
            return {
                'success': True,
                'message': f'Test webhook russi (HTTP {response.status_code})',
                'details': {
                    'url': webhook_url,
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'has_secret': bool(webhook_secret)
                }
            }
        else:
            return {
                'success': False,
                'message': f'Test webhook chou (HTTP {response.status_code})',
                'details': {
                    'url': webhook_url,
                    'status_code': response.status_code,
                    'response_text': response.text[:200]
                }
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'message': 'Timeout lors du test webhook',
            'details': {'error_type': 'timeout', 'timeout': timeout}
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'message': 'Erreur de connexion au webhook',
            'details': {'error_type': 'connection_error', 'url': webhook_url}
        }
    except Exception as e:
        logger.error(f"Erreur test webhook: {e}")
        return {
            'success': False,
            'message': f'Erreur test webhook: {str(e)}',
            'details': {'error_type': type(e).__name__}
        } 
