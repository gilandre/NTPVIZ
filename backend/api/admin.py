"""
API Admin - Administration et configuration
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.database import NTPServer
from backend.database import User
from backend.database import SystemConfig
from backend.database import Alert
# SUPPRIMÉ: Import Flask-SQLAlchemy circulaire
from backend.database_manager import get_db_session_with_context
from backend.services.ntp_service import ntp_service
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/status', methods=['GET'])
def get_admin_status():
    """Status administrateur de base (pas de login requis pour les tests)"""
    try:
        return jsonify({
            'success': True,
            'status': 'admin_api_available',
            'timestamp': datetime.utcnow().isoformat(),
            'features': ['servers', 'users', 'config', 'stats']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def admin_required(f):
    """Dcorateur pour les routes ncessitant des droits admin"""
    from functools import wraps
    
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'error': 'Droits administrateur requis'}), 403
        return f(*args, **kwargs)
    return decorated_function

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

# Gestion des serveurs NTP
@admin_bp.route('/servers', methods=['GET'])
@login_required
def get_all_servers():
    """Récupérer tous les serveurs NTP (actifs et inactifs)"""
    try:
        with get_db_session_with_context() as session:
            servers = session.query(NTPServer).order_by(NTPServer.priority).all()
            
            servers_data = []
            for server in servers:
                servers_data.append({
                    'id': server.id,
                    'name': server.name,
                    'address': server.address,
                    'port': server.port,
                    'server_type': server.server_type,
                    'status': server.status,
                    'is_active': server.is_active,
                    'priority': server.priority,
                    'timeout': server.timeout,
                    'max_offset': server.max_offset,
                    'description': server.description,
                    'created_at': server.created_at.isoformat() if server.created_at else None,
                    'last_sync': server.last_sync.isoformat() if server.last_sync else None,
                    'last_offset': server.last_offset,
                    'last_latency': server.last_latency,
                    'last_stratum': server.last_stratum
                })
            
            return jsonify(servers_data)
        
    except Exception as e:
        logger.error(f"Erreur récupération serveurs admin: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/servers', methods=['POST'])
@config_required
def create_server():
    """Créer un nouveau serveur NTP"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'address', 'server_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Champ requis: {field}'}), 400
        
        with get_db_session_with_context() as session:
            # Vérifier l'unicité de l'adresse
            existing = session.query(NTPServer).filter_by(address=data['address']).first()
            if existing:
                return jsonify({'error': 'Un serveur avec cette adresse existe déjà'}), 400
            
            # Priorité automatique
            max_priority = session.query(db.func.max(NTPServer.priority)).scalar() or 0
            
            # Créer le serveur
            server = NTPServer(
                name=data['name'],
                address=data['address'],
                server_type=data['server_type'],
                port=data.get('port', 123),
                timeout=data.get('timeout', 10),
                max_offset=data.get('max_offset', 1.0),
                critical_offset=data.get('critical_offset', 5.0),
                description=data.get('description'),
                priority=max_priority + 1,
                created_by=current_user.id
            )
            
            session.add(server)
            session.commit()
            
            logger.info(f"Serveur NTP créé: {server.name} par {current_user.username}")
            
            return jsonify({
                'success': True,
                'message': 'Serveur créé avec succès',
                'server': {
                    'id': server.id,
                    'name': server.name,
                    'address': server.address,
                    'server_type': server.server_type,
                    'port': server.port,
                    'priority': server.priority
                }
            }), 201
        
    except Exception as e:
        logger.error(f"Erreur création serveur: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/servers/<int:server_id>', methods=['PUT'])
@config_required
def update_server(server_id):
    """Mettre à jour un serveur NTP"""
    try:
        with get_db_session_with_context() as session:
            server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
            if not server:
                return jsonify({'error': 'Serveur non trouvé'}), 404
                
            data = request.get_json()
            
            # Champs modifiables
            updatable_fields = [
                'name', 'address', 'port', 'server_type', 'is_active',
                'timeout', 'max_offset', 'critical_offset', 'description', 'priority'
            ]
            
            for field in updatable_fields:
                if field in data:
                    if field == 'address' and data[field] != server.address:
                        # Vérifier l'unicité de la nouvelle adresse
                        existing = session.query(NTPServer).filter(
                            NTPServer.address == data[field],
                            NTPServer.id != server_id
                        ).first()
                        if existing:
                            return jsonify({'error': 'Un serveur avec cette adresse existe déjà'}), 400
                    
                    setattr(server, field, data[field])
            
            session.commit()
            
            logger.info(f"Serveur NTP modifié: {server.name} par {current_user.username}")
            
            return jsonify({
                'success': True,
                'message': 'Serveur mis à jour avec succès',
                'server': {
                    'id': server.id,
                    'name': server.name,
                    'address': server.address,
                    'is_active': server.is_active,
                    'priority': server.priority
                }
            })
        
    except Exception as e:
        logger.error(f"Erreur modification serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/servers/<int:server_id>', methods=['DELETE'])
@config_required
def delete_server(server_id):
    """Supprimer un serveur NTP"""
    try:
        with get_db_session_with_context() as session:
            server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
            if not server:
                return jsonify({'error': 'Serveur non trouvé'}), 404
                
            server_name = server.name
            
            # Supprimer (les logs et alertes seront supprimés en cascade)
            session.delete(server)
            session.commit()
            
            logger.info(f"Serveur NTP supprimé: {server_name} par {current_user.username}")
            
            return jsonify({
                'success': True,
                'message': 'Serveur supprimé avec succès'
            })
        
    except Exception as e:
        logger.error(f"Erreur suppression serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/servers/<int:server_id>/test', methods=['POST'])
@config_required
def test_server(server_id):
    """Tester un serveur NTP"""
    try:
        with get_db_session_with_context() as session:
            server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
            if not server:
                return jsonify({'error': 'Serveur non trouvé'}), 404
            
            # Test de connectivité
            connectivity = ntp_service.test_connectivity(server.address, server.port, server.timeout)
            
            # Test de requête NTP si accessible
            ntp_result = None
            if connectivity.get('reachable'):
                try:
                    ntp_result = ntp_service.query_server(server)
                except Exception as e:
                    logger.warning(f"Erreur test NTP serveur {server_id}: {e}")
            
            return jsonify({
                'server': {
                    'id': server.id,
                    'name': server.name,
                    'address': server.address,
                    'port': server.port,
                    'timeout': server.timeout,
                    'is_active': server.is_active
                },
                'connectivity': connectivity,
                'ntp_query': ntp_result,
                'timestamp': datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Erreur test serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

# Gestion des utilisateurs
@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Récupérer tous les utilisateurs"""
    try:
        with get_db_session_with_context() as session:
            users = session.query(User).order_by(User.username).all()
            
            users_data = []
            for user in users:
                users_data.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                })
            
            return jsonify(users_data)
        
    except Exception as e:
        logger.error(f"Erreur récupération utilisateurs: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    """Créer un nouvel utilisateur"""
    try:
        data = request.get_json()
        
        required_fields = ['username', 'email', 'password', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Champ requis: {field}'}), 400
        
        with get_db_session_with_context() as session:
            # Vérifier l'unicité
            if session.query(User).filter_by(username=data['username']).first():
                return jsonify({'error': 'Ce nom d\'utilisateur existe déjà'}), 400
            
            if session.query(User).filter_by(email=data['email']).first():
                return jsonify({'error': 'Cette adresse email existe déjà'}), 400
            
            # Valider le rôle
            if data['role'] not in ['admin', 'operator', 'viewer']:
                return jsonify({'error': 'Rôle invalide'}), 400
            
            # Créer l'utilisateur
            user = User(
                username=data['username'],
                email=data['email'],
                role=data['role']
            )
            
            # Définir le mot de passe
            user.set_password(data['password'])
            
            if data.get('first_name'):
                user.first_name = data['first_name']
            if data.get('last_name'):
                user.last_name = data['last_name']
            
            session.add(user)
            session.commit()
            
            logger.info(f"Utilisateur créé: {user.username} par {current_user.username}")
            
            return jsonify({
                'success': True,
                'message': 'Utilisateur créé avec succès',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'is_active': user.is_active
                }
            }), 201
        
    except Exception as e:
        logger.error(f"Erreur création utilisateur: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Mettre à jour un utilisateur"""
    try:
        with get_db_session_with_context() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'error': 'Utilisateur non trouvé'}), 404
                
            data = request.get_json()
            
            # Empêcher la modification de son propre compte
            if user.id == current_user.id:
                return jsonify({'error': 'Impossible de modifier son propre compte'}), 400
            
            # Champs modifiables
            updatable_fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
            
            for field in updatable_fields:
                if field in data:
                    if field == 'username' and data[field] != user.username:
                        if session.query(User).filter(User.username == data[field], User.id != user_id).first():
                            return jsonify({'error': 'Ce nom d\'utilisateur existe déjà'}), 400
                    
                    if field == 'email' and data[field] != user.email:
                        if session.query(User).filter(User.email == data[field], User.id != user_id).first():
                            return jsonify({'error': 'Cette adresse email existe déjà'}), 400
                    
                    setattr(user, field, data[field])
            
            # Changer le mot de passe si fourni
            if data.get('password'):
                user.set_password(data['password'])
            
            session.commit()
            
            logger.info(f"Utilisateur modifié: {user.username} par {current_user.username}")
            
            return jsonify({
                'success': True,
                'message': 'Utilisateur mis à jour avec succès',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'is_active': user.is_active
                }
            })
        
    except Exception as e:
        logger.error(f"Erreur modification utilisateur {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Supprimer un utilisateur"""
    try:
        with get_db_session_with_context() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
            # Empêcher la suppression de son propre compte
            if user.id == current_user.id:
                return jsonify({'error': 'Impossible de supprimer son propre compte'}), 400
            
            username = user.username
            session.delete(user)
            session.commit()
            
            logger.info(f"Utilisateur supprimé: {username} par {current_user.username}")
            
            return jsonify({
                'success': True,
                'message': 'Utilisateur supprimé avec succès'
            })
        
    except Exception as e:
        logger.error(f"Erreur suppression utilisateur {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

# Configuration système
@admin_bp.route('/config', methods=['GET'])
@config_required
def get_config():
    """Récupérer la configuration système"""
    try:
        category = request.args.get('category', 'all')
        
        with get_db_session_with_context() as session:
            if category == 'all':
                configs = session.query(SystemConfig).all()
            else:
                configs = session.query(SystemConfig).filter_by(category=category).all()
            
            # Grouper par catégorie
            result = {}
            for config in configs:
                if config.category not in result:
                    result[config.category] = []
                result[config.category].append({
                    'id': config.id,
                    'key': config.key_name,
                    'value': config.value,
                    'value_type': config.value_type,
                    'description': config.description,
                    'category': config.category,
                    'is_public': config.is_public,
                    'updated_at': config.updated_at.isoformat() if config.updated_at else None
                })
            
            return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erreur récupération configuration: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/config', methods=['POST'])
@admin_required
def update_config():
    """Mettre à jour la configuration système"""
    try:
        data = request.get_json()
        
        if not data or not data.get('configs'):
            return jsonify({'error': 'Données de configuration manquantes'}), 400
        
        updated_configs = []
        
        with get_db_session_with_context() as session:
            for config_data in data['configs']:
                key = config_data.get('key')
                value = config_data.get('value')
                
                if not key:
                    continue
                
                # Rechercher la configuration existante
                config = session.query(SystemConfig).filter_by(key_name=key).first()
                
                if config:
                    config.value = str(value)
                    config.updated_by = current_user.id
                    updated_configs.append(config.key_name)
                else:
                    # Créer une nouvelle configuration si elle n'existe pas
                    new_config = SystemConfig(
                        key=key,
                        value=str(value),
                        value_type=config_data.get('value_type', 'string'),
                        description=config_data.get('description', ''),
                        category=config_data.get('category', 'general'),
                        created_by=current_user.id,
                        updated_by=current_user.id
                    )
                    session.add(new_config)
                    updated_configs.append(key)
            
            session.commit()
            
            logger.info(f"Configuration mise à jour par {current_user.username}: {updated_configs}")
            
            return jsonify({
                'success': True,
                'message': f'{len(updated_configs)} configurations mises à jour',
                'updated_keys': updated_configs
            })
        
    except Exception as e:
        logger.error(f"Erreur mise à jour configuration: {e}")
        return jsonify({'error': str(e)}), 500

# Statistiques et monitoring
@admin_bp.route('/stats/overview')
@admin_required
def get_admin_overview():
    """Vue d'ensemble pour l'administration"""
    try:
        from backend.utils.init_data import get_database_info
        
        with get_db_session_with_context() as session:
            # Statistiques serveurs
            total_servers = session.query(NTPServer).count()
            active_servers = session.query(NTPServer).filter_by(is_active=True).count()
            global_servers = session.query(NTPServer).filter_by(server_type='global').count()
            local_servers = session.query(NTPServer).filter_by(server_type='local').count()
            
            # Statistiques utilisateurs
            total_users = session.query(User).count()
            active_users = session.query(User).filter_by(is_active=True).count()
            admin_users = session.query(User).filter_by(role='admin').count()
            operator_users = session.query(User).filter_by(role='operator').count()
            viewer_users = session.query(User).filter_by(role='viewer').count()
            
            # Statistiques alertes
            total_alerts = session.query(Alert).count()
            active_alerts = session.query(Alert).filter_by(status='active').count()
            unread_alerts = session.query(Alert).filter_by(status='unread').count()
            
            overview = {
                'database': get_database_info(),
                'servers': {
                    'total': total_servers,
                    'active': active_servers,
                    'global': global_servers,
                    'local': local_servers
                },
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'admins': admin_users,
                    'operators': operator_users,
                    'viewers': viewer_users
                },
                'alerts': {
                    'total': total_alerts,
                    'active': active_alerts,
                    'unread': unread_alerts
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        
        return jsonify(overview)
        
    except Exception as e:
        logger.error(f"Erreur vue d'ensemble admin: {e}")
        return jsonify({'error': str(e)}), 500

# ================== NOUVELLES FONCTIONNALITS ADMIN ==================

@admin_bp.route('/stats/detailed', methods=['GET'])
@admin_required
def get_detailed_stats():
    """Statistiques dtailles du systme"""
    try:
        # Priode d'analyse
        days = int(request.args.get('days', 7))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Logs NTP rcents
        from backend.database import NTPLog
        ntp_logs = NTPLog.query.filter(NTPLog.timestamp >= start_date).all()
        
        # Analyse des performances NTP
        ntp_stats = analyze_ntp_performance(ntp_logs)
        
        # Analyse des alertes
        alerts = Alert.query.filter(Alert.created_at >= start_date).all()
        alert_stats = analyze_alerts_trends(alerts)
        
        # Activit utilisateurs
        user_activity = analyze_user_activity(start_date)
        
        # Utilisation systme
        system_usage = get_system_usage_stats()
        
        return jsonify({
            'period_days': days,
            'start_date': start_date.isoformat(),
            'ntp_performance': ntp_stats,
            'alerts_analysis': alert_stats,
            'user_activity': user_activity,
            'system_usage': system_usage,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur statistiques dtailles: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/maintenance/cleanup', methods=['POST'])
@admin_required
def system_cleanup():
    """Nettoyage du systme et maintenance"""
    try:
        data = request.get_json()
        cleanup_options = data.get('options', {})
        
        results = {}
        
        # Nettoyage des logs anciens
        if cleanup_options.get('old_logs', False):
            retention_days = cleanup_options.get('log_retention_days', 30)
            results['logs_cleanup'] = cleanup_old_logs(retention_days)
        
        # Nettoyage des alertes rsolues
        if cleanup_options.get('resolved_alerts', False):
            results['alerts_cleanup'] = cleanup_resolved_alerts()
        
        # Optimisation de la base de donnes
        if cleanup_options.get('optimize_db', False):
            results['db_optimization'] = optimize_database()
        
        # Nettoyage des sessions expires
        if cleanup_options.get('expired_sessions', False):
            results['sessions_cleanup'] = cleanup_expired_sessions()
        
        logger.info(f"Maintenance systme excute par {current_user.username}: {list(cleanup_options.keys())}")
        
        return jsonify({
            'success': True,
            'message': 'Maintenance systme termine',
            'results': results,
            'executed_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur maintenance systme: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/backup/export', methods=['POST'])
@admin_required
def export_data():
    """Exporter les donnes de configuration"""
    try:
        data = request.get_json()
        export_options = data.get('options', {})
        
        export_data = {}
        
        # Exporter la configuration
        if export_options.get('config', True):
            configs = SystemConfig.query.all()
            export_data['configuration'] = [config.to_dict() for config in configs]
        
        # Exporter les serveurs
        if export_options.get('servers', True):
            servers = NTPServer.query.all()
            export_data['ntp_servers'] = [server.to_dict() for server in servers]
        
        # Exporter les utilisateurs (sans mots de passe)
        if export_options.get('users', True):
            users = User.query.all()
            export_data['users'] = [
                {
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
                for user in users
            ]
        
        # Mtadonnes de l'export
        export_data['metadata'] = {
            'version': '1.0.0',
            'exported_at': datetime.utcnow().isoformat(),
            'exported_by': current_user.username,
            'application': 'NTP Monitor Enterprise'
        }
        
        logger.info(f"Export de donnes par {current_user.username}: {list(export_options.keys())}")
        
        return jsonify({
            'success': True,
            'data': export_data,
            'message': 'Export gnr avec succs'
        })
        
    except Exception as e:
        logger.error(f"Erreur export donnes: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/backup/import', methods=['POST'])
@admin_required
def import_data():
    """Importer des donnes de configuration"""
    try:
        data = request.get_json()
        import_data = data.get('data', {})
        import_options = data.get('options', {})
        
        results = {}
        
        # Importer la configuration
        if import_options.get('config', False) and 'configuration' in import_data:
            results['config'] = import_configuration(import_data['configuration'])
        
        # Importer les serveurs
        if import_options.get('servers', False) and 'ntp_servers' in import_data:
            results['servers'] = import_ntp_servers(import_data['ntp_servers'])
        
        # Importer les utilisateurs
        if import_options.get('users', False) and 'users' in import_data:
            results['users'] = import_users(import_data['users'])
        
        logger.info(f"Import de donnes par {current_user.username}: {list(import_options.keys())}")
        
        return jsonify({
            'success': True,
            'message': 'Import termin avec succs',
            'results': results,
            'imported_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur import donnes: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/audit/logs', methods=['GET'])
@admin_required
def get_audit_logs():
    """Rcuprer les logs d'audit systme"""
    try:
        # Paramtres de pagination
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        
        # Filtres
        user_id = request.args.get('user_id')
        action_type = request.args.get('action_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Construction de la requte (simulation pour l'exemple)
        # En production, utiliser une table d'audit ddie
        audit_logs = generate_audit_logs_data(user_id, action_type, start_date, end_date)
        
        # Pagination
        total = len(audit_logs)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_logs = audit_logs[start_idx:end_idx]
        
        return jsonify({
            'logs': paginated_logs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            },
            'filters_applied': {
                'user_id': user_id,
                'action_type': action_type,
                'start_date': start_date,
                'end_date': end_date
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur rcupration logs audit: {e}")
        return jsonify({'error': str(e)}), 500

# ================== FONCTIONS UTILITAIRES ==================

def analyze_ntp_performance(logs):
    """Analyser les performances NTP"""
    if not logs:
        return {'message': 'Aucun log disponible'}
    
    offsets = [abs(log.offset) for log in logs if log.offset is not None]
    response_times = [log.response_time for log in logs if log.response_time is not None]
    
    return {
        'total_queries': len(logs),
        'successful_queries': len([log for log in logs if log.success]),
        'average_offset': sum(offsets) / len(offsets) if offsets else 0,
        'max_offset': max(offsets) if offsets else 0,
        'average_response_time': sum(response_times) / len(response_times) if response_times else 0,
        'success_rate': len([log for log in logs if log.success]) / len(logs) * 100 if logs else 0
    }

def analyze_alerts_trends(alerts):
    """Analyser les tendances des alertes"""
    if not alerts:
        return {'message': 'Aucune alerte disponible'}
    
    by_severity = {}
    by_status = {}
    
    for alert in alerts:
        # Par svrit
        severity = alert.severity
        if severity not in by_severity:
            by_severity[severity] = 0
        by_severity[severity] += 1
        
        # Par statut
        status = alert.status
        if status not in by_status:
            by_status[status] = 0
        by_status[status] += 1
    
    return {
        'total_alerts': len(alerts),
        'by_severity': by_severity,
        'by_status': by_status,
        'resolution_rate': by_status.get('resolved', 0) / len(alerts) * 100 if alerts else 0
    }

def analyze_user_activity(start_date):
    """Analyser l'activit des utilisateurs"""
    users = User.query.all()
    active_users = [user for user in users if user.last_login and user.last_login >= start_date]
    
    return {
        'total_users': len(users),
        'active_users': len(active_users),
        'activity_rate': len(active_users) / len(users) * 100 if users else 0,
        'most_active': [
            {
                'username': user.username,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'login_count': user.login_count
            }
            for user in sorted(active_users, key=lambda u: u.login_count or 0, reverse=True)[:5]
        ]
    }

def get_system_usage_stats():
    """Obtenir les statistiques d'utilisation systme"""
    try:
        import psutil
        import os
        
        # CPU et mmoire
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Informations base de donnes
        db_size = get_database_size()
        
        return {
            'cpu_usage': cpu_percent,
            'memory': {
                'total': memory.total,
                'used': memory.used,
                'percent': memory.percent
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'percent': (disk.used / disk.total) * 100
            },
            'database': db_size
        }
    except Exception as e:
        return {'error': f'Impossible de rcuprer les stats systme: {str(e)}'}

def cleanup_old_logs(retention_days):
    """Nettoyer les logs anciens"""
    try:
        from backend.database import NTPLog
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        old_logs = NTPLog.query.filter(NTPLog.timestamp < cutoff_date).all()
        count = len(old_logs)
        
        for log in old_logs:
            db.session.delete(log)
        
        db.session.commit()
        
        return {'deleted_logs': count, 'cutoff_date': cutoff_date.isoformat()}
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}

def cleanup_resolved_alerts():
    """Nettoyer les alertes rsolues anciennes"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        old_alerts = Alert.query.filter(
            Alert.status == 'resolved',
            Alert.updated_at < cutoff_date
        ).all()
        
        count = len(old_alerts)
        
        for alert in old_alerts:
            db.session.delete(alert)
        
        db.session.commit()
        
        return {'deleted_alerts': count}
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}

def optimize_database():
    """Optimiser la base de donnes"""
    try:
        # Simulation d'optimisation
        return {'status': 'completed', 'note': 'Optimisation simule'}
    except Exception as e:
        return {'error': str(e)}

def cleanup_expired_sessions():
    """Nettoyer les sessions expires"""
    try:
        # Simulation de nettoyage des sessions
        return {'deleted_sessions': 0, 'note': 'Nettoyage sessions simul'}
    except Exception as e:
        return {'error': str(e)}

def import_configuration(config_data):
    """Importer la configuration"""
    try:
        imported = 0
        for config_item in config_data:
            SystemConfig.set_config(
                key=config_item['key'],
                value=config_item['value'],
                value_type=config_item.get('value_type', 'string'),
                description=config_item.get('description'),
                category=config_item.get('category', 'general'),
                user_id=current_user.id
            )
            imported += 1
        
        return {'imported_configs': imported}
    except Exception as e:
        return {'error': str(e)}

def import_ntp_servers(servers_data):
    """Importer les serveurs NTP"""
    try:
        imported = 0
        for server_data in servers_data:
            if not NTPServer.query.filter_by(address=server_data['address']).first():
                server = NTPServer(
                    name=server_data['name'],
                    address=server_data['address'],
                    server_type=server_data.get('server_type', 'pool'),
                    port=server_data.get('port', 123),
                    is_active=server_data.get('is_active', True),
                    description=server_data.get('description'),
                    created_by=current_user.id
                )
                db.session.add(server)
                imported += 1
        
        db.session.commit()
        return {'imported_servers': imported}
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}

def import_users(users_data):
    """Importer les utilisateurs"""
    try:
        imported = 0
        for user_data in users_data:
            if not User.query.filter_by(username=user_data['username']).first():
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password='temp123',  # Mot de passe temporaire
                    role=user_data.get('role', 'viewer')
                )
                user.is_active = user_data.get('is_active', True)
                db.session.add(user)
                imported += 1
        
        db.session.commit()
        return {'imported_users': imported, 'note': 'Mots de passe temporaires assigns'}
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}

def generate_audit_logs_data(user_id, action_type, start_date, end_date):
    """Gnrer des donnes de logs d'audit (simulation)"""
    # En production, rcuprer depuis une table d'audit relle
    return [
        {
            'id': 1,
            'user_id': 1,
            'username': 'admin',
            'action': 'config_update',
            'resource': 'system_config',
            'details': 'Mise  jour ntp.query_interval',
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': '127.0.0.1'
        }
    ]

def get_database_size():
    """Obtenir la taille de la base de donnes"""
    try:
        import os
        db_path = 'instance/ntp_monitor_dev.db'  # Adapter selon l'environnement
        if os.path.exists(db_path):
            return {'size_bytes': os.path.getsize(db_path)}
        return {'size_bytes': 0}
    except Exception:
        return {'error': 'Impossible de dterminer la taille de la DB'} 
