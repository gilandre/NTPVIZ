"""
API Admin - Administration et configuration
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.database import NTPServer, ServerType
from backend.models.user import User
from backend.database import SystemConfig
from backend.database import Alert
# SUPPRIMÉ: Import Flask-SQLAlchemy circulaire
from backend.database_manager import get_db_session_with_context
from backend.services.ntp_service import ntp_service
from backend.services.audit_service import audit_service
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import joinedload
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
            # 🔧 CORRECTION : Filtrer les serveurs supprimés logiquement par défaut
            active_only = request.args.get('active_only', 'true').lower() == 'true'
            
            query = session.query(NTPServer)
            if active_only:
                query = query.filter(NTPServer.deleted_at.is_(None))
            
            servers = query.order_by(NTPServer.priority).all()
            
            servers_data = []
            for server in servers:
                # 🔧 CORRECTION : Normaliser les statuts serveurs
                normalized_status = server.status
                if normalized_status == 'ok':
                    normalized_status = 'online'
                elif normalized_status not in ['online', 'offline', 'unknown']:
                    normalized_status = 'unknown'
                
                st_label = None
                st_code = None
                st_id = None
                try:
                    # Tenter de récupérer via relation si chargée (selon modèle)
                    if hasattr(server, 'server_type_ref') and server.server_type_ref:
                        st_label = server.server_type_ref.label
                        st_code = server.server_type_ref.code
                        st_id = server.server_type_id
                    else:
                        # Fallback: résolution par code texte
                        normalized = (server.server_type or 'all').strip().lower()
                        mapping = {
                            'local': 'local', '1': 'local', 'internal': 'local',
                            'pool': 'pool', '2': 'pool', 'public': 'pool',
                            'global': 'internet', 'internet': 'internet',
                            'all': 'all', '0': 'all', '': 'all'
                        }
                        st_code = mapping.get(normalized, 'all')
                        st = session.query(ServerType).filter(ServerType.code == st_code).first()
                        if st:
                            st_label = st.label
                            st_id = st.id
                except Exception:
                    pass

                servers_data.append({
                    'id': server.id,
                    'name': server.name,
                    'address': server.address,
                    'port': server.port,
                    'server_type': server.server_type,
                    'server_type_id': st_id,
                    'server_type_code': st_code or server.server_type,
                    'server_type_label': st_label or server.server_type,
                    'status': normalized_status,
                    'is_active': server.is_active,
                    'is_deleted': server.is_deleted,
                    'priority': server.priority,
                    'timeout': server.timeout,
                    'max_offset': None,  # ❌ SUPPRIMÉ: Utiliser alert_thresholds
                    'description': server.description,
                    'created_at': server.created_at.isoformat() if server.created_at else None,
                    'last_sync': server.last_sync.isoformat() if server.last_sync else None,
                    'last_offset': server.last_offset,
                    'last_latency': server.last_latency,
                    'last_stratum': server.last_stratum,
                    'deleted_at': server.deleted_at.isoformat() if server.deleted_at else None,
                    'deleted_by': server.deleted_by
                })
            
            # Audit: consultation de la liste des serveurs
            try:
                audit_service.log_view('servers', details={'count': len(servers_data), 'active_only': active_only})
            except Exception:
                pass
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
        
        required_fields = ['name', 'address']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Champ requis: {field}'}), 400
        
        with get_db_session_with_context() as session:
            # Vérifier l'unicité de l'adresse (exclure les serveurs supprimés)
            existing = session.query(NTPServer).filter(
                NTPServer.address == data['address'],
                NTPServer.deleted_at == None
            ).first()
            if existing:
                return jsonify({'error': 'Un serveur actif avec cette adresse existe déjà'}), 400
            
            # Priorité automatique
            max_priority = session.query(func.max(NTPServer.priority)).scalar() or 0
            
            # Déterminer le type serveur (id/code) avec normalisation
            st_id = data.get('server_type_id')
            st_code_input = data.get('server_type')
            st_code = None
            if st_id:
                st = session.query(ServerType).filter(ServerType.id == int(st_id)).first()
                if not st:
                    return jsonify({'error': 'server_type_id invalide'}), 400
                st_code = st.code
            elif st_code_input:
                normalized = str(st_code_input).strip().lower()
                mapping = {
                    'local': 'local', '1': 'local', 'internal': 'local',
                    'pool': 'pool', '2': 'pool', 'public': 'pool',
                    'global': 'internet', 'internet': 'internet',
                    'all': 'all', '0': 'all', '': 'all'
                }
                st_code = mapping.get(normalized, 'all')
                st = session.query(ServerType).filter(ServerType.code == st_code).first()
                st_id = st.id if st else None
            else:
                # défaut: all
                st = session.query(ServerType).filter(ServerType.code == 'all').first()
                st_code = 'all'
                st_id = st.id if st else None

            # Créer le serveur
            server = NTPServer(
                name=data['name'],
                address=data['address'],
                server_type=st_code,
                port=data.get('port', 123),
                timeout=data.get('timeout', 10),
                max_offset=data.get('max_offset', 1.0),
                critical_offset=data.get('critical_offset', 5.0),
                description=data.get('description'),
                priority=max_priority + 1,
                created_by=current_user.id
            )
            # Définir aussi la FK si disponible
            try:
                server.server_type_id = int(st_id) if st_id else None
            except Exception:
                server.server_type_id = None
            
            session.add(server)
            session.commit()
            
            logger.info(f"Serveur NTP créé: {server.name} par {current_user.username}")
            try:
                audit_service.log_server_created({'id': server.id, 'name': server.name, 'address': server.address, 'server_type': server.server_type})
            except Exception:
                pass
            
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
                'name', 'address', 'port', 'server_type', 'server_type_id', 'is_active',
                'timeout', 'max_offset', 'critical_offset', 'description', 'priority'
            ]
            
            for field in updatable_fields:
                if field in data:
                    if field == 'address' and data[field] != server.address:
                        # Vérifier l'unicité de la nouvelle adresse (exclure les serveurs supprimés)
                        existing = session.query(NTPServer).filter(
                            NTPServer.address == data[field],
                            NTPServer.deleted_at == None,
                            NTPServer.id != server_id
                        ).first()
                        if existing:
                            return jsonify({'error': 'Un serveur actif avec cette adresse existe déjà'}), 400
                    
                    if field in ('server_type', 'server_type_id'):
                        # Normaliser/mise à jour du type
                        st_id = data.get('server_type_id')
                        st_code_input = data.get('server_type')
                        st = None
                        if st_id is not None:
                            st = session.query(ServerType).filter(ServerType.id == int(st_id)).first()
                        elif st_code_input is not None:
                            normalized = str(st_code_input).strip().lower()
                            mapping = {
                                'local': 'local', '1': 'local', 'internal': 'local',
                                'pool': 'pool', '2': 'pool', 'public': 'pool',
                                'global': 'internet', 'internet': 'internet',
                                'all': 'all', '0': 'all', '': 'all'
                            }
                            code = mapping.get(normalized, 'all')
                            st = session.query(ServerType).filter(ServerType.code == code).first()
                        if st:
                            server.server_type = st.code
                            server.server_type_id = st.id
                    else:
                        setattr(server, field, data[field])
            
            session.commit()
            
            logger.info(f"Serveur NTP modifié: {server.name} par {current_user.username}")
            try:
                audit_service.log_server_updated(server.id, {k: data.get(k) for k in data.keys()})
            except Exception:
                pass
            
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

@admin_bp.route('/servers/<int:server_id>', methods=['GET'])
@login_required
def get_server(server_id):
    """Récupérer un serveur NTP spécifique"""
    try:
        with get_db_session_with_context() as session:
            server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
            if not server:
                return jsonify({'error': 'Serveur non trouvé'}), 404
            
            # Résoudre type serveur
            st_label = None
            st_code = None
            st_id = None
            if hasattr(server, 'server_type_ref') and server.server_type_ref:
                st_label = server.server_type_ref.label
                st_code = server.server_type_ref.code
                st_id = server.server_type_id
            else:
                normalized = (server.server_type or 'all').strip().lower()
                mapping = {
                    'local': 'local', '1': 'local', 'internal': 'local',
                    'pool': 'pool', '2': 'pool', 'public': 'pool',
                    'global': 'internet', 'internet': 'internet',
                    'all': 'all', '0': 'all', '': 'all'
                }
                st_code = mapping.get(normalized, 'all')
                st = session.query(ServerType).filter(ServerType.code == st_code).first()
                if st:
                    st_label = st.label
                    st_id = st.id

            server_data = {
                'id': server.id,
                'name': server.name,
                'address': server.address,
                'port': server.port,
                'server_type': server.server_type,
                'server_type_id': st_id,
                'server_type_code': st_code or server.server_type,
                'server_type_label': st_label or server.server_type,
                'status': server.status,
                'is_active': server.is_active,
                'enabled': server.is_active,  # Alias pour compatibilité
                'priority': server.priority,
                'timeout': server.timeout,
                                    'max_offset': None,  # ❌ SUPPRIMÉ: Utiliser alert_thresholds
                'critical_offset': None,  # ❌ SUPPRIMÉ: Utiliser alert_thresholds
                'description': server.description,
                'created_at': server.created_at.isoformat() if server.created_at else None,
                'last_sync': server.last_sync.isoformat() if server.last_sync else None,
                'last_offset': server.last_offset,
                'last_latency': server.last_latency,
                'last_stratum': server.last_stratum,
                'created_by': server.created_by
            }
            
            try:
                audit_service.log_view('server', resource_id=server_id)
            except Exception:
                pass
            return jsonify(server_data)
        
    except Exception as e:
        logger.error(f"Erreur récupération serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/server-types', methods=['GET'])
@login_required
def list_server_types():
    """Référentiel des types de serveurs (code/label/id)."""
    try:
        with get_db_session_with_context() as session:
            rows = session.query(ServerType).filter(ServerType.is_active == True).all()
            data = [{'id': r.id, 'code': r.code, 'label': r.label} for r in rows]
            return jsonify({'success': True, 'items': data, 'total': len(data)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/servers/<int:server_id>', methods=['DELETE'])
@config_required
def delete_server(server_id):
    try:
        with get_db_session_with_context() as session:
            server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
            if not server:
                return jsonify({'error': 'Serveur non trouvé'}), 404
            if server.deleted_at is not None:
                return jsonify({'error': 'Serveur déjà supprimé'}), 400
            server.soft_delete(deleted_by_user_id=current_user.id)
            session.commit()
            try:
                audit_service.log_server_deleted({'id': server.id, 'name': server.name, 'address': server.address})
            except Exception:
                pass
            return jsonify({'success': True, 'message': 'Serveur supprimé avec succès', 'deleted_at': server.deleted_at.isoformat() if server.deleted_at else None})
    except Exception as e:
        logger.error(f"Erreur suppression logique serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

# AJOUTER la route de restauration :
@admin_bp.route('/servers/<int:server_id>/restore', methods=['POST'])
@config_required
def restore_server(server_id):
    try:
        with get_db_session_with_context() as session:
            server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
            if not server:
                return jsonify({'error': 'Serveur non trouvé'}), 404
            if server.deleted_at is None:
                return jsonify({'error': 'Serveur non supprimé'}), 400
            # Vérifier unicité
            existing = session.query(NTPServer).filter(
                NTPServer.address == server.address,
                NTPServer.server_type == server.server_type,
                NTPServer.deleted_at == None,
                NTPServer.id != server_id
            ).first()
            if existing:
                return jsonify({'error': 'Un serveur actif utilise déjà cette adresse'}), 400
            server.restore()
            session.commit()
            try:
                audit_service.log_admin_action('RESTORE', 'server', {'server_id': server_id})
            except Exception:
                pass
            return jsonify({'success': True, 'message': 'Serveur restauré avec succès'})
    except Exception as e:
        logger.error(f"Erreur restauration serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

# AJOUTER la route pour lister les supprimés :
@admin_bp.route('/servers/deleted', methods=['GET'])
@login_required
def get_deleted_servers():
    try:
        with get_db_session_with_context() as session:
            deleted_servers = session.query(NTPServer).filter(NTPServer.deleted_at != None).order_by(NTPServer.deleted_at.desc()).all()
            servers_data = []
            for server in deleted_servers:
                servers_data.append({
                    'id': server.id,
                    'name': server.name,
                    'address': server.address,
                    'server_type': server.server_type,
                    'deleted_at': server.deleted_at.isoformat() if server.deleted_at else None,
                    'deleted_by': server.deleted_by,
                    'created_at': server.created_at.isoformat() if server.created_at else None
                })
            try:
                audit_service.log_view('servers_deleted', details={'count': len(servers_data)})
            except Exception:
                pass
            return jsonify(servers_data)
    except Exception as e:
        logger.error(f"Erreur récupération serveurs supprimés: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/ntp/probe', methods=['POST'])
@admin_required
def ntp_probe():
    """Sonder un serveur NTP arbitraire (diagnostic) sans effet de bord DB."""
    try:
        data = request.get_json() or {}
        address = data.get('address')
        port = int(data.get('port', 123))
        timeout = float(data.get('timeout', 5))

        if not address:
            return jsonify({'error': 'Adresse requise'}), 400

        # Test de connectivité UDP simple
        connectivity = ntp_service.test_connectivity(address, port, timeout)
        # Sondage NTP ad-hoc (pas d'écriture DB)
        probe = None
        if connectivity.get('reachable'):
            try:
                probe = ntp_service.probe_ntp(address, port, timeout)
            except Exception as e:
                logger.warning(f"Erreur probe NTP {address}:{port}: {e}")

        # Audit de consultation (diagnostic)
        try:
            audit_service.log_view('ntp_probe', details={'address': address, 'port': port, 'reachable': connectivity.get('reachable')})
        except Exception:
            pass

        return jsonify({
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'address': address,
            'port': port,
            'connectivity': connectivity,
            'probe': probe
        })
    
    except Exception as e:
        logger.error(f"Erreur endpoint NTP probe: {e}")
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
            
            resp = {
                'server': {
                    'id': server.id,
                    'name': server.name,
                    'address': server.address,
                    'port': server.port,
                    'timeout': server.timeout,
                    'is_active': server.is_active
                },
                'connectivity': connectivity,
                'ntp_info': ntp_result,
                'timestamp': datetime.utcnow().isoformat()
            }
            try:
                audit_service.log_server_test(server.id, server.name, bool(connectivity.get('reachable')), {'connectivity': connectivity})
            except Exception:
                pass
            return jsonify(resp)
        
    except Exception as e:
        logger.error(f"Erreur test serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

# Gestion des utilisateurs
@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Récupérer tous les utilisateurs (excluant les supprimés logiquement)"""
    try:
        with get_db_session_with_context() as session:
            # Exclure seulement les utilisateurs supprimés logiquement
            users = session.query(User).filter(User.deleted_at.is_(None)).order_by(User.username).all()
            
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
            
            try:
                audit_service.log_view('users', details={'count': len(users_data)})
            except Exception:
                pass
            return jsonify(users_data)
        
    except Exception as e:
        logger.error(f"Erreur récupération utilisateurs: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    """Créer un nouvel utilisateur"""
    try:
        from backend.services.password_service import password_service
        
        data = request.get_json()
        
        # Champs requis (password maintenant optionnel)
        required_fields = ['email', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Champ requis: {field}'}), 400
        
        with get_db_session_with_context() as session:
            # Générer username automatiquement si non fourni
            username = data.get('username')
            if not username:
                if data.get('first_name') and data.get('last_name'):
                    existing_usernames = [u.username for u in session.query(User).all()]
                    username = password_service.generate_username(
                        data['first_name'], 
                        data['last_name'], 
                        existing_usernames
                    )
                else:
                    return jsonify({'error': 'Username requis ou prénom/nom pour génération automatique'}), 400
            
            # Vérifier l'unicité
            if session.query(User).filter_by(username=username).first():
                return jsonify({'error': 'Ce nom d\'utilisateur existe déjà'}), 400
            
            if session.query(User).filter_by(email=data['email']).first():
                return jsonify({'error': 'Cette adresse email existe déjà'}), 400
            
            # Valider le rôle
            if data['role'] not in ['admin', 'operator', 'viewer']:
                return jsonify({'error': 'Rôle invalide'}), 400
            
            # Générer mot de passe automatiquement si non fourni
            password = data.get('password')
            auto_generated_password = False
            password_validation = None
            
            if not password:
                password = password_service.generate_password(
                    length=12, 
                    readable=data.get('readable_password', False)
                )
                auto_generated_password = True
                password_validation = password_service.validate_password_strength(password)
            
            # Créer l'utilisateur
            user = User(
                username=username,
                email=data['email'],
                password=password,
                role=data['role']
            )
            
            # Définir les champs optionnels
            if data.get('first_name'):
                user.first_name = data['first_name']
            if data.get('last_name'):
                user.last_name = data['last_name']
            
            # Statut initial
            user.is_active = data.get('is_active', True)
            
            session.add(user)
            session.commit()
            
            # Stocker temporairement le mot de passe généré
            temp_token = None
            if auto_generated_password:
                temp_token = password_service.store_temporary_password(user.id, password)
            
            logger.info(f"Utilisateur créé: {user.username} par {current_user.username} (mot de passe {'auto-généré' if auto_generated_password else 'fourni'})")
            audit_service.log_user_created(user.to_dict(), auto_generated_password)
            
            response_data = {
                'success': True,
                'message': 'Utilisateur créé avec succès',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                },
                'auto_generated_username': not data.get('username'),
                'auto_generated_password': auto_generated_password
            }
            
            # Ajouter les infos de mot de passe généré (attention en production)
            if auto_generated_password:
                response_data.update({
                    'generated_password': password,  # À sécuriser en production
                    'password_validation': password_validation,
                    'temp_token': temp_token,
                    'password_expires_hours': 24
                })
            
            return jsonify(response_data), 201
        
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
            
            # Sauvegarder les données originales pour l'audit
            old_data = user.to_dict()
            
            # Champs modifiables (username non modifiable pour les utilisateurs existants)
            updatable_fields = ['email', 'first_name', 'last_name', 'role', 'is_active']
            
            for field in updatable_fields:
                if field in data:
                    if field == 'email' and data[field] != user.email:
                        if session.query(User).filter(User.email == data[field], User.id != user_id).first():
                            return jsonify({'error': 'Cette adresse email existe déjà'}), 400
                    
                    setattr(user, field, data[field])
            
            # Empêcher la modification du username pour les utilisateurs existants
            if 'username' in data and data['username'] != user.username:
                return jsonify({'error': 'Le nom d\'utilisateur ne peut pas être modifié pour un utilisateur existant'}), 400
            
            # Changer le mot de passe si fourni
            password_changed = False
            if data.get('password'):
                user.set_password(data['password'])
                password_changed = True
                audit_service.log_password_change(user.username, by_admin=True)
            
            session.commit()
            
            # Audit logging avec les changements
            new_data = user.to_dict()
            audit_service.log_user_updated(user.id, old_data, new_data)
            
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

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """Récupérer un utilisateur spécifique"""
    try:
        with get_db_session_with_context() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
            
            return jsonify(user_data)
        
    except Exception as e:
        logger.error(f"Erreur récupération utilisateur {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """Activer/Désactiver un utilisateur"""
    try:
        with get_db_session_with_context() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
            # Empêcher la modification de son propre statut
            if user.id == current_user.id:
                return jsonify({'error': 'Impossible de modifier le statut de son propre compte'}), 400
            
            # Basculer le statut
            old_status = user.is_active
            user.is_active = not user.is_active
            session.commit()
            
            action = "activé" if user.is_active else "désactivé"
            logger.info(f"Utilisateur {action}: {user.username} par {current_user.username}")
            audit_service.log_user_status_changed(user.id, user.username, old_status, user.is_active)
            
            return jsonify({
                'success': True,
                'message': f'Utilisateur {action} avec succès',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'is_active': user.is_active,
                    'status_changed': True,
                    'previous_status': old_status
                }
            })
        
    except Exception as e:
        logger.error(f"Erreur changement statut utilisateur {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/generate-password', methods=['POST'])
@admin_required
def generate_user_password(user_id):
    """Générer un nouveau mot de passe pour un utilisateur"""
    try:
        from backend.services.password_service import password_service
        
        data = request.get_json() or {}
        length = data.get('length', 12)
        readable = data.get('readable', False)
        
        with get_db_session_with_context() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
            # Générer le nouveau mot de passe
            new_password = password_service.generate_password(
                length=length, 
                readable=readable
            )
            
            # Valider la force du mot de passe
            validation = password_service.validate_password_strength(new_password)
            
            # Mettre à jour le mot de passe
            user.set_password(new_password)
            session.commit()
            
            # Stocker temporairement pour communication
            token = password_service.store_temporary_password(user.id, new_password)
            
            logger.info(f"Mot de passe généré pour utilisateur: {user.username} par {current_user.username}")
            audit_service.log_password_generated(user.id, user.username, validation.get('strength', 'Unknown'))
            
            return jsonify({
                'success': True,
                'message': 'Nouveau mot de passe généré avec succès',
                'password': new_password,  # À utiliser avec précaution en production
                'validation': validation,
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        
    except Exception as e:
        logger.error(f"Erreur génération mot de passe utilisateur {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Supprimer un utilisateur (suppression logique)"""
    try:
        with get_db_session_with_context() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
            # Empêcher la suppression de son propre compte
            # Récupérer l'utilisateur connecté dans cette session pour éviter les problèmes de contexte
            current_user_in_session = session.query(User).filter(User.id == current_user.id).first()
            if not current_user_in_session:
                return jsonify({'error': 'Utilisateur connecté non trouvé'}), 404
            
            if user.id == current_user_in_session.id:
                return jsonify({'error': 'Impossible de supprimer son propre compte'}), 400
            
            # Vérifier si l'utilisateur est déjà supprimé
            if user.is_deleted:
                return jsonify({'error': 'Cet utilisateur est déjà supprimé'}), 400
            
            # Sauvegarder les données avant suppression logique
            user_data = user.to_dict()
            
            # Suppression logique
            user.soft_delete(deleted_by_user_id=current_user.id)
            session.commit()
            
            logger.info(f"Utilisateur supprimé logiquement: {user.username} par {current_user.username}")
            audit_service.log_user_deleted(user_data)
            
            return jsonify({
                'success': True,
                'message': f'Utilisateur "{user.username}" supprimé avec succès',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'deleted_at': user.deleted_at.isoformat() if user.deleted_at else None
                }
            })
        
    except Exception as e:
        logger.error(f"Erreur suppression logique utilisateur {user_id}: {e}")
        return jsonify({'error': f'Erreur lors de la suppression: {str(e)}'}), 500

@admin_bp.route('/users/<int:user_id>/restore', methods=['POST'])
@admin_required
def restore_user(user_id):
    """Restaurer un utilisateur supprimé logiquement"""
    try:
        with get_db_session_with_context() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
            # Vérifier si l'utilisateur est supprimé logiquement
            if not user.is_deleted:
                return jsonify({'error': 'Cet utilisateur n\'est pas supprimé'}), 400
            
            # Sauvegarder les données avant restauration
            user_data = user.to_dict()
            
            # Restaurer l'utilisateur
            user.restore()
            session.commit()
            
            logger.info(f"Utilisateur restauré: {user.username} par {current_user.username}")
            audit_service.log_user_updated(user.id, user_data, user.to_dict())
            
            return jsonify({
                'success': True,
                'message': f'Utilisateur "{user.username}" restauré avec succès',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active
                }
            })
        
    except Exception as e:
        logger.error(f"Erreur restauration utilisateur {user_id}: {e}")
        return jsonify({'error': f'Erreur lors de la restauration: {str(e)}'}), 500

@admin_bp.route('/users/deleted', methods=['GET'])
@admin_required
def get_deleted_users():
    """Récupérer la liste des utilisateurs supprimés logiquement"""
    try:
        with get_db_session_with_context() as session:
            # Récupérer uniquement les utilisateurs supprimés logiquement
            users = session.query(User).filter(User.deleted_at.isnot(None)).order_by(User.deleted_at.desc()).all()
            
            users_data = []
            for user in users:
                users_data.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'deleted_at': user.deleted_at.isoformat() if user.deleted_at else None,
                    'deleted_by': user.deleted_by
                })
            
            return jsonify(users_data)
        
    except Exception as e:
        logger.error(f"Erreur récupération utilisateurs supprimés: {e}")
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
@admin_bp.route('/stats')
@admin_required
def get_admin_stats():
    """Endpoint de compatibilité pour /stats - redirige vers /stats/overview"""
    return get_admin_overview()

@admin_bp.route('/stats/overview')
@admin_required
def get_admin_overview():
    """Vue d'ensemble pour l'administration"""
    try:
        from backend.utils.init_data import get_database_info
        
        with get_db_session_with_context() as session:
            # Statistiques serveurs (uniquement lignes valides: non supprimées + actives pour les KPI par type)
            servers_q = session.query(NTPServer).filter(NTPServer.deleted_at.is_(None))
            total_servers = servers_q.count()
            active_servers = servers_q.filter(NTPServer.is_active == True).count()
            global_servers = servers_q.filter(NTPServer.is_active == True, NTPServer.server_type == 'global').count()
            local_servers = servers_q.filter(NTPServer.is_active == True, NTPServer.server_type == 'local').count()

            # Statistiques utilisateurs (uniquement lignes valides: non supprimées)
            users_q = session.query(User).filter(User.deleted_at.is_(None))
            total_users = users_q.count()
            active_users = users_q.filter(User.is_active == True).count()
            admin_users = users_q.filter(User.is_active == True, User.role == 'admin').count()
            operator_users = users_q.filter(User.is_active == True, User.role == 'operator').count()
            viewer_users = users_q.filter(User.is_active == True, User.role == 'viewer').count()

            # Statistiques alertes (considérer valides = actives)
            alerts_q = session.query(Alert)
            total_alerts = alerts_q.filter(Alert.status == 'active').count()
            active_alerts = total_alerts
            unread_alerts = alerts_q.filter(Alert.is_read == False, Alert.status == 'active').count()

            # Détails pour "Répartition des Alertes" et "Alertes par Serveur"
            from collections import defaultdict
            from sqlalchemy.orm import joinedload
            severity_counts = {'info': 0, 'warning': 0, 'critical': 0}
            server_counts = defaultdict(int)
            active_list = session.query(Alert).options(joinedload(Alert.server)).filter(Alert.status == 'active').all()
            for alert in active_list:
                # Répartition par sévérité
                sev = (alert.severity or '').lower()
                if sev in severity_counts:
                    severity_counts[sev] += 1
                else:
                    severity_counts[sev] = severity_counts.get(sev, 0) + 1

                # Répartition par serveur: ne compter que serveurs valides (actifs + non supprimés)
                if alert.server is not None and (alert.server.deleted_at is None) and bool(alert.server.is_active):
                    name = alert.server.name or f"Server {alert.server_id}"
                    server_counts[name] += 1
                else:
                    server_counts['Système'] += 1
            
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
                    'unread': unread_alerts,
                    'by_severity': severity_counts,
                    'by_server': dict(sorted(server_counts.items(), key=lambda kv: kv[1], reverse=True)[:10])
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
    """Statistiques détaillées du système"""
    try:
        # Période d'analyse
        days = int(request.args.get('days', 7))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        with get_db_session_with_context() as session:
            # Logs NTP récents
            from backend.database import NTPLog
            ntp_logs = session.query(NTPLog).filter(NTPLog.timestamp >= start_date).all()
            
            # Analyse des performances NTP
            ntp_stats = analyze_ntp_performance(ntp_logs)
            
            # Analyse des alertes
            alerts = session.query(Alert).filter(Alert.created_at >= start_date).all()
            alert_stats = analyze_alerts_trends(alerts)
            
            # Activité utilisateurs
            user_activity = analyze_user_activity(start_date)
            
            # Utilisation système
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
        logger.error(f"Erreur statistiques détaillées: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/maintenance/cleanup', methods=['POST'])
@admin_required
def system_cleanup():
    """Nettoyage du système et maintenance"""
    try:
        data = request.get_json()
        cleanup_options = data.get('options', {})
        
        results = {}
        
        # Nettoyage des logs anciens (avec archivage dans table d'archives)
        if cleanup_options.get('old_logs', False):
            retention_days = cleanup_options.get('log_retention_days', 30)
            results['logs_cleanup'] = cleanup_old_logs_with_archive(retention_days)
        
        # Nettoyage des alertes (archivage + purge)
        if cleanup_options.get('resolved_alerts', False):
            resolved_retention = cleanup_options.get('resolved_retention_days', 0)
            ack_retention = cleanup_options.get('ack_retention_days', 30)
            results['alerts_cleanup'] = cleanup_resolved_alerts_with_archive(resolved_retention, ack_retention)
        
        # Optimisation de la base de données (OPTIMIZE/ANALYZE)
        if cleanup_options.get('optimize_db', False):
            results['db_optimization'] = optimize_database()
        
        # Nettoyage des sessions expirées
        if cleanup_options.get('expired_sessions', False):
            results['sessions_cleanup'] = cleanup_expired_sessions()

        # Purge/archivage des fichiers de logs applicatifs (optionnel)
        if cleanup_options.get('file_logs', False):
            file_retention = cleanup_options.get('file_log_retention_days', 30)
            results['file_logs'] = cleanup_file_logs_with_archive(file_retention)
        
        logger.info(f"Maintenance système exécutée par {current_user.username}: {list(cleanup_options.keys())}")
        try:
            audit_service.log_admin_action('MAINTENANCE', 'system', {
                'options': cleanup_options,
                'results': results
            })
        except Exception:
            pass
        
        return jsonify({
            'success': True,
            'message': 'Maintenance système terminée',
            'results': results,
            'executed_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur maintenance système: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/backup/export', methods=['POST'])
@admin_required
def export_data():
    """Exporter les données de configuration"""
    try:
        data = request.get_json()
        export_options = data.get('options', {})
        
        export_data = {}
        
        with get_db_session_with_context() as session:
            # Exporter la configuration
            if export_options.get('config', True):
                configs = session.query(SystemConfig).all()
                export_data['configuration'] = [config.to_dict() for config in configs]
            
            # Exporter les serveurs
            if export_options.get('servers', True):
                servers = session.query(NTPServer).all()
                export_data['ntp_servers'] = [server.to_dict() for server in servers]
            
            # Exporter les utilisateurs (sans mots de passe)
            if export_options.get('users', True):
                users = session.query(User).all()
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
        
        # Métadonnées de l'export
        export_data['metadata'] = {
            'version': '1.0.0',
            'exported_at': datetime.utcnow().isoformat(),
            'exported_by': current_user.username,
            'application': 'NTP Monitor Enterprise'
        }
        
        logger.info(f"Export de données par {current_user.username}: {list(export_options.keys())}")
        
        return jsonify({
            'success': True,
            'data': export_data,
            'message': 'Export généré avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur export données: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/backup/export.csv', methods=['POST'])
@admin_required
def export_data_csv():
    """Exporter les données sélectionnées en CSV consolidé (section-first)."""
    try:
        from io import StringIO
        import csv
        data = request.get_json() or {}
        options = data.get('options', {})

        output = StringIO()
        writer = csv.writer(output)
        # En-tête superset pour toutes les sections
        header = [
            'section', 'id', 'key', 'value', 'value_type', 'category', 'is_public',
            'username', 'email', 'role', 'user_is_active', 'user_created_at',
            'server_name', 'server_address', 'server_type', 'server_is_active', 'server_priority', 'server_timeout', 'server_created_at'
        ]
        writer.writerow(header)

        with get_db_session_with_context() as session:
            # Config
            if options.get('config', True):
                configs = session.query(SystemConfig).all()
                for c in configs:
                    writer.writerow([
                        'config', c.id, c.key_name, c.value, c.value_type, c.category, c.is_public,
                        '', '', '', '', '',
                        '', '', '', '', '', '', ''
                    ])
            # Users (sans mot de passe)
            if options.get('users', True):
                users = session.query(User).filter(User.deleted_at.is_(None)).all()
                for u in users:
                    writer.writerow([
                        'user', u.id, '', '', '', '', '',
                        u.username, u.email, u.role, bool(u.is_active),
                        u.created_at.isoformat() if u.created_at else '',
                        '', '', '', '', '', '', ''
                    ])
            # Servers
            if options.get('servers', True):
                servers = session.query(NTPServer).filter(NTPServer.deleted_at.is_(None)).all()
                for s in servers:
                    writer.writerow([
                        'server', s.id, '', '', '', '', '',
                        '', '', '', '', '',
                        s.name, s.address, s.server_type, bool(s.is_active), s.priority, s.timeout,
                        s.created_at.isoformat() if s.created_at else ''
                    ])

        csv_content = output.getvalue()
        from flask import make_response
        resp = make_response(csv_content)
        resp.headers['Content-Type'] = 'text/csv; charset=utf-8'
        ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        resp.headers['Content-Disposition'] = f'attachment; filename=backup_export_{ts}.csv'
        return resp
    except Exception as e:
        logger.error(f"Erreur export CSV: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/backup/import', methods=['POST'])
@admin_required
def import_data():
    """Importer des données de configuration"""
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
        
        logger.info(f"Import de données par {current_user.username}: {list(import_options.keys())}")
        
        return jsonify({
            'success': True,
            'message': 'Import terminéé avec succès',
            'results': results,
            'imported_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur import données: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/audit/logs', methods=['GET'])
@admin_required
def get_audit_logs():
    """Récupérer les logs d'audit système (table audit_logs)"""
    try:
        from backend.models import AuditLog
        from sqlalchemy import and_
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        user_id = request.args.get('user_id')
        action_type = request.args.get('action_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        with get_db_session_with_context() as session:
            q = session.query(AuditLog)
            if user_id:
                q = q.filter(AuditLog.user_id == int(user_id))
            if action_type:
                q = q.filter(AuditLog.action == action_type)
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    q = q.filter(AuditLog.timestamp >= start_dt)
                except ValueError:
                    pass
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    q = q.filter(AuditLog.timestamp <= end_dt)
                except ValueError:
                    pass

            total = q.count()
            logs = q.order_by(AuditLog.timestamp.desc()).offset((page-1)*per_page).limit(per_page).all()
            data = [log.to_dict() for log in logs]

        return jsonify({
            'logs': data,
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
        logger.error(f"Erreur récupération logs audit: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/audit/logs/export', methods=['GET'])
@admin_required
def export_audit_logs():
    """Exporter les logs d'audit en CSV (filtres + pagination serveur-side)"""
    try:
        from backend.models import AuditLog
        from io import StringIO
        import csv
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 1000)), 5000)
        user_id = request.args.get('user_id')
        action_type = request.args.get('action_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        with get_db_session_with_context() as session:
            q = session.query(AuditLog)
            if user_id:
                q = q.filter(AuditLog.user_id == int(user_id))
            if action_type:
                q = q.filter(AuditLog.action == action_type)
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    q = q.filter(AuditLog.timestamp >= start_dt)
                except ValueError:
                    pass
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    q = q.filter(AuditLog.timestamp <= end_dt)
                except ValueError:
                    pass

            total = q.count()
            logs = q.order_by(AuditLog.timestamp.desc()).offset((page-1)*per_page).limit(per_page).all()
            # IMPORTANT: matérialiser les données avant la fermeture de session pour éviter DetachedInstanceError
            rows = [log.to_dict() for log in logs]

        # Générer CSV
        import csv
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['timestamp', 'user', 'action', 'resource', 'details', 'ip', 'user_agent'])
        for d in rows:
            writer.writerow([
                d.get('timestamp'),
                d.get('username'),
                d.get('action'),
                d.get('resource') or d.get('endpoint'),
                d.get('details') or '',
                d.get('ip_address'),
                d.get('user_agent')
            ])

        output = si.getvalue()
        from flask import make_response
        resp = make_response(output)
        resp.headers['Content-Type'] = 'text/csv; charset=utf-8'
        resp.headers['Content-Disposition'] = 'attachment; filename=audit_logs.csv'

        try:
            audit_service.log_view('audit_export', details={'count': len(logs), 'page': page, 'per_page': per_page})
        except Exception:
            pass
        return resp
    except Exception as e:
        logger.error(f"Erreur export logs d'audit: {e}")
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
        'successful_queries': len([log for log in logs if log.status == 'success']),
        'average_offset': sum(offsets) / len(offsets) if offsets else 0,
        'max_offset': max(offsets) if offsets else 0,
        'average_response_time': sum(response_times) / len(response_times) if response_times else 0,
        'success_rate': len([log for log in logs if log.status == 'success']) / len(logs) * 100 if logs else 0
    }

def analyze_alerts_trends(alerts):
    """Analyser les tendances des alertes"""
    if not alerts:
        return {'message': 'Aucune alerte disponible'}
    
    by_severity = {}
    by_status = {}
    
    for alert in alerts:
        # Par sévérité
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
    """Analyser l'activité des utilisateurs"""
    try:
        with get_db_session_with_context() as session:
            users = session.query(User).all()
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
    except Exception as e:
        return {'error': str(e)}

def get_system_usage_stats():
    """Obtenir les statistiques d'utilisation système"""
    try:
        import psutil
        import os
        
        # CPU et mémoire
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Informations base de données
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
        return {'error': f'Impossible de récupérer les stats système: {str(e)}'}

def cleanup_old_logs(retention_days):
    """Nettoyer les logs anciens"""
    try:
        from backend.database import NTPLog
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        with get_db_session_with_context() as session:
            old_logs = session.query(NTPLog).filter(NTPLog.timestamp < cutoff_date).all()
            count = len(old_logs)
            
            for log in old_logs:
                session.delete(log)
            
            # La session sera automatiquement committée par le context manager
        
        return {'deleted_logs': count, 'cutoff_date': cutoff_date.isoformat()}
    except Exception as e:
        return {'error': str(e)}

def cleanup_old_logs_with_archive(retention_days):
    """Purger les ntp_logs anciens en les archivant d'abord, en s'adaptant dynamiquement au schéma réel."""
    try:
        from sqlalchemy import text
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        batch_tag = datetime.utcnow().strftime('ARCH_%Y%m%d_%H%M%S')

        with get_db_session_with_context() as session:
            # S'assurer du schéma correct de ntp_logs_archive
            schema_actions = ensure_ntp_logs_archive_schema(session)

            # Récupérer dynamiquement la liste de colonnes de ntp_logs
            cols_rows = session.execute(text("SHOW COLUMNS FROM ntp_logs")).fetchall()
            def get_field(r):
                try:
                    return r['Field']
                except Exception:
                    return r[0]
            columns = [get_field(r) for r in cols_rows]
            # Récupérer dynamiquement la liste de colonnes de ntp_logs_archive (cas où la table archive existait déjà avec un schéma différent)
            arch_rows = session.execute(text("SHOW COLUMNS FROM ntp_logs_archive")).fetchall()
            archive_columns = { get_field(r) for r in arch_rows }
            # Whitelist de colonnes sûres (compat multi-schémas)
            allowed = {
                'id', 'server_id', 'timestamp', 'offset', 'delay', 'stratum',
                'error_message', 'client_ip', 'user_agent', 'created_at',
                # colonnes optionnelles si présentes
                'latency', 'success', 'response_time', 'jitter', 'status'
            }
            # Intersecter avec les colonnes réellement présentes dans la table d'archive
            selected_cols = [c for c in columns if c in allowed and c in archive_columns]
            col_list = ", ".join(f"`{c}`" for c in selected_cols)

            insert_sql = text(f"""
                INSERT INTO ntp_logs_archive ({col_list}, batch_tag)
                SELECT {col_list}, :batch
                FROM ntp_logs
                WHERE timestamp < :cutoff
            """)
            session.execute(insert_sql, { 'batch': batch_tag, 'cutoff': cutoff_date })

            # Supprimer les anciens logs de la table principale
            delete_sql = text("DELETE FROM ntp_logs WHERE timestamp < :cutoff")
            result = session.execute(delete_sql, { 'cutoff': cutoff_date })
            deleted_count = result.rowcount if hasattr(result, 'rowcount') else None

        return {'archived_batch': batch_tag, 'cutoff_date': cutoff_date.isoformat(), 'deleted_count': deleted_count, 'archive_schema': schema_actions}
    except Exception as e:
        return {'error': str(e)}

def ensure_ntp_logs_archive_schema(session):
    """Recréer la table ntp_logs_archive à l'identique de ntp_logs (+ batch_tag)."""
    from sqlalchemy import text
    actions = []
    # Sauvegarder l'existante si présente, puis recréer proprement
    exists = session.execute(text("SHOW TABLES LIKE 'ntp_logs_archive'"))
    if exists.fetchone():
        ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        session.execute(text(f"RENAME TABLE ntp_logs_archive TO ntp_logs_archive_old_{ts}"))
        actions.append('renamed_old')
    session.execute(text("CREATE TABLE ntp_logs_archive LIKE ntp_logs"))
    actions.append('created_from_like')
    # Ajouter batch_tag
    try:
        session.execute(text("ALTER TABLE ntp_logs_archive ADD COLUMN batch_tag VARCHAR(32) NOT NULL"))
    except Exception:
        pass
    return actions

def cleanup_file_logs_with_archive(retention_days):
    """Archiver les fichiers du répertoire logs/ plus anciens que N jours vers logs/archive/ avec un préfixe daté."""
    try:
        import os
        import shutil
        base_dir = os.path.abspath(os.path.join(os.getcwd(), 'logs'))
        archive_dir = os.path.join(base_dir, 'archive')
        os.makedirs(archive_dir, exist_ok=True)
        cutoff_ts = (datetime.utcnow() - timedelta(days=retention_days)).timestamp()
        moved = []
        if os.path.isdir(base_dir):
            for name in os.listdir(base_dir):
                if name == 'archive':
                    continue
                fpath = os.path.join(base_dir, name)
                try:
                    if os.path.isfile(fpath):
                        st = os.stat(fpath)
                        if st.st_mtime < cutoff_ts:
                            dest = os.path.join(archive_dir, f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{name}")
                            shutil.move(fpath, dest)
                            moved.append(name)
                except Exception:
                    continue
        return { 'archived_files': moved, 'archive_dir': archive_dir }
    except Exception as e:
        return { 'error': str(e) }

def cleanup_resolved_alerts():
    """Nettoyer les alertes résolues anciennes"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        with get_db_session_with_context() as session:
            old_alerts = session.query(Alert).filter(
                Alert.status == 'resolved',
                Alert.updated_at < cutoff_date
            ).all()
            
            count = len(old_alerts)
            
            for alert in old_alerts:
                session.delete(alert)
            
            # La session sera automatiquement committée par le context manager
        
        return {'deleted_alerts': count}
    except Exception as e:
        return {'error': str(e)}

def cleanup_resolved_alerts_with_archive(resolved_retention_days=0, acknowledged_retention_days=30):
    """Archiver puis purger les alertes résolues/acknowledged au-delà des rétentions, dans alerts_archive."""
    try:
        from sqlalchemy import text
        now = datetime.utcnow()
        resolved_cutoff = now - timedelta(days=resolved_retention_days)
        ack_cutoff = now - timedelta(days=acknowledged_retention_days)
        batch_tag = now.strftime('ALRCH_%Y%m%d_%H%M%S')

        with get_db_session_with_context() as session:
            # Créer table d'archive si absente
            session.execute(text(
                """
                CREATE TABLE IF NOT EXISTS alerts_archive (
                  id INT PRIMARY KEY,
                  server_id INT,
                  alert_type VARCHAR(50),
                  severity VARCHAR(20),
                  title VARCHAR(200),
                  message TEXT,
                  details JSON,
                  status VARCHAR(20),
                  is_read TINYINT(1),
                  acknowledged_at DATETIME NULL,
                  acknowledged_by INT NULL,
                  resolved_at DATETIME NULL,
                  resolved_by INT NULL,
                  created_at DATETIME,
                  updated_at DATETIME,
                  occurrence_count INT,
                  first_occurrence DATETIME,
                  last_occurrence DATETIME,
                  auto_resolved TINYINT(1),
                  batch_tag VARCHAR(32) NOT NULL
                ) ENGINE=InnoDB
                """
            ))

            # Archiver les résolues selon rétention
            session.execute(text(
                """
                INSERT INTO alerts_archive
                (id, server_id, alert_type, severity, title, message, details, status, is_read,
                 acknowledged_at, acknowledged_by, resolved_at, resolved_by, created_at, updated_at,
                 occurrence_count, first_occurrence, last_occurrence, auto_resolved, batch_tag)
                SELECT id, server_id, alert_type, severity, title, message, details, status, is_read,
                       acknowledged_at, acknowledged_by, resolved_at, resolved_by, created_at, updated_at,
                       occurrence_count, first_occurrence, last_occurrence, auto_resolved, :batch
                FROM alerts
                WHERE (status = 'resolved' AND updated_at < :resolved_cutoff)
                   OR (status = 'acknowledged' AND updated_at < :ack_cutoff)
                """
            ), { 'batch': batch_tag, 'resolved_cutoff': resolved_cutoff, 'ack_cutoff': ack_cutoff })

            # Supprimer les mêmes lignes de la table principale
            del_result = session.execute(text(
                """
                DELETE FROM alerts
                WHERE (status = 'resolved' AND updated_at < :resolved_cutoff)
                   OR (status = 'acknowledged' AND updated_at < :ack_cutoff)
                """
            ), { 'resolved_cutoff': resolved_cutoff, 'ack_cutoff': ack_cutoff })
            deleted_count = del_result.rowcount if hasattr(del_result, 'rowcount') else None

        return {
            'archived_batch': batch_tag,
            'resolved_cutoff': resolved_cutoff.isoformat(),
            'ack_cutoff': ack_cutoff.isoformat(),
            'deleted_count': deleted_count
        }
    except Exception as e:
        return {'error': str(e)}

def optimize_database():
    """Optimiser la base de données MySQL: OPTIMIZE TABLE + ANALYZE TABLE sur tables principales."""
    try:
        from sqlalchemy import text
        tables = ['ntp_logs', 'ntp_servers', 'alerts', 'users', 'system_config']
        optimize_results = {}
        with get_db_session_with_context() as session:
            for t in tables:
                try:
                    session.execute(text(f"OPTIMIZE TABLE {t}"))
                    session.execute(text(f"ANALYZE TABLE {t}"))
                    optimize_results[t] = 'optimized'
                except Exception as te:
                    optimize_results[t] = f'error: {te}'
        return { 'status': 'completed', 'tables': optimize_results }
    except Exception as e:
        return {'error': str(e)}

def cleanup_expired_sessions():
    """Nettoyer les sessions expirées"""
    try:
        # Simulation de nettoyage des sessions
        return {'deleted_sessions': 0, 'note': 'Nettoyage sessions simulé'}
    except Exception as e:
        return {'error': str(e)}

def import_configuration(config_data):
    """Importer la configuration"""
    try:
        imported = 0
        with get_db_session_with_context() as session:
            for config_item in config_data:
                SystemConfig.set_config(
                    session=session,
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
        with get_db_session_with_context() as session:
            for server_data in servers_data:
                if not session.query(NTPServer).filter_by(address=server_data['address']).first():
                    server = NTPServer(
                        name=server_data['name'],
                        address=server_data['address'],
                        server_type=server_data.get('server_type', 'pool'),
                        port=server_data.get('port', 123),
                        is_active=server_data.get('is_active', True),
                        description=server_data.get('description'),
                        created_by=current_user.id
                    )
                    session.add(server)
                    imported += 1
            
            # La session sera automatiquement committée par le context manager
        
        return {'imported_servers': imported}
    except Exception as e:
        return {'error': str(e)}

def import_users(users_data):
    """Importer les utilisateurs"""
    try:
        imported = 0
        with get_db_session_with_context() as session:
            for user_data in users_data:
                if not session.query(User).filter_by(username=user_data['username']).first():
                    user = User(
                        username=user_data['username'],
                        email=user_data['email'],
                        password='temp123',  # Mot de passe temporaire
                        role=user_data.get('role', 'viewer')
                    )
                    user.is_active = user_data.get('is_active', True)
                    session.add(user)
                    imported += 1
            
            # La session sera automatiquement committée par le context manager
        
        return {'imported_users': imported, 'note': 'Mots de passe temporaires assignés'}
    except Exception as e:
        return {'error': str(e)}

def generate_audit_logs_data(user_id, action_type, start_date, end_date):
    """Générer des données de logs d'audit (simulation)"""
    # En production, récupérerer depuis une table d'audit réelle
    
    # 🔧 CORRECTION : Standardiser les actions d'audit
    standard_actions = {
        'config_update': 'update',
        'config_create': 'create',
        'config_delete': 'delete',
        'user_login': 'login',
        'user_logout': 'logout'
    }
    
    base_action = 'config_update'
    if action_type and action_type in standard_actions:
        base_action = action_type
    
    standardized_action = standard_actions.get(base_action, 'update')
    
    return [
        {
            'id': 1,
            'user_id': 1,
            'username': 'admin',
            'action': standardized_action,
            'resource': 'system_config',
            'details': 'Mise à jour ntp.query_interval',
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': '127.0.0.1'
        }
    ]

def get_database_size():
    """Obtenir la taille de la base de données"""
    try:
        import os
        db_path = 'instance/ntp_monitor_dev.db'  # Adapter selon l'environnement
        if os.path.exists(db_path):
            return {'size_bytes': os.path.getsize(db_path)}
        return {'size_bytes': 0}
    except Exception:
        return {'error': 'Impossible de dterminéer la taille de la DB'} 

# Endpoints pour l'historique des alertes
@admin_bp.route('/alerts/history', methods=['GET'])
@admin_required
def get_historical_alerts():
    """Récupérer l'historique des alertes (non actives) avec filtres et pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        severity = request.args.get('severity')
        server_id = request.args.get('server_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search')
        
        with get_db_session_with_context() as session:
            # Base query - exclure les alertes actives avec chargement de la relation serveur
            query = session.query(Alert).options(joinedload(Alert.server)).filter(Alert.status != 'active')
            
            # Filtres
            if status:
                query = query.filter(Alert.status == status)
            if severity:
                query = query.filter(Alert.severity == severity)
            if server_id:
                query = query.filter(Alert.server_id == server_id)
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    query = query.filter(Alert.created_at >= start_dt)
                except ValueError:
                    pass
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    query = query.filter(Alert.created_at <= end_dt)
                except ValueError:
                    pass
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (Alert.message.like(search_term)) |
                    (Alert.server.has(NTPServer.name.like(search_term)))
                )
            
            # Tri par date de création décroissante
            query = query.order_by(Alert.created_at.desc())
            
            # Pagination
            total = query.count()
            alerts = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Formatage des données
            alerts_data = []
            for alert in alerts:
                # 🔧 CORRECTION : Standardiser la structure des alertes
                alerts_data.append({
                    'id': alert.id,
                    'server_id': alert.server_id,
                    'server_name': alert.server.name if alert.server else f"Server {alert.server_id}",
                    'title': alert.message,  # Utiliser message comme title
                    'message': alert.message,
                    'severity': alert.severity,
                    'status': alert.status,
                    'created_at': alert.created_at.isoformat() if alert.created_at else None,
                    'updated_at': alert.updated_at.isoformat() if alert.updated_at else None,
                    'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                    'resolved_by': alert.resolved_by,
                    'notes': alert.details
                })
            
            try:
                audit_service.log_view('alerts_history', details={'count': len(alerts_data), 'page': page, 'per_page': per_page})
            except Exception:
                pass
            return jsonify({
                'alerts': alerts_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            })
            
    except Exception as e:
        logger.error(f"Erreur récupération historique alertes: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/alerts/history/export', methods=['GET'])
@admin_required
def export_historical_alerts():
    """Exporter l'historique des alertes en CSV"""
    try:
        from flask import Response
        import csv
        import io
        
        status = request.args.get('status')
        severity = request.args.get('severity')
        server_id = request.args.get('server_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search')
        
        with get_db_session_with_context() as session:
            # Base query - exclure les alertes actives avec chargement de la relation serveur
            query = session.query(Alert).options(joinedload(Alert.server)).filter(Alert.status != 'active')
            
            # Filtres
            if status:
                query = query.filter(Alert.status == status)
            if severity:
                query = query.filter(Alert.severity == severity)
            if server_id:
                query = query.filter(Alert.server_id == server_id)
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    query = query.filter(Alert.created_at >= start_dt)
                except ValueError:
                    pass
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    query = query.filter(Alert.created_at <= end_dt)
                except ValueError:
                    pass
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (Alert.message.like(search_term)) |
                    (Alert.server.has(NTPServer.name.like(search_term)))
                )
            
            # Tri par date de création décroissante
            query = query.order_by(Alert.created_at.desc())
            
            # Récupérer toutes les alertes (sans pagination pour l'export)
            alerts = query.all()
            
            # Créer le CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # En-têtes
            headers = [
                'ID', 'Serveur', 'Message', 'Sévérité', 'Statut', 
                'Créé le', 'Mis à jour le', 'Résolu le', 'Résolu par', 'Notes'
            ]
            writer.writerow(headers)
            
            # Données
            for alert in alerts:
                writer.writerow([
                    alert.id,
                    alert.server.name if alert.server else f"Server {alert.server_id}",
                    alert.message,
                    alert.severity,
                    alert.status,
                    alert.created_at.isoformat() if alert.created_at else '',
                    alert.updated_at.isoformat() if alert.updated_at else '',
                    alert.resolved_at.isoformat() if alert.resolved_at else '',
                    alert.resolved_by or '',
                    alert.details or ''
                ])
            
            # Préparer la réponse
            output.seek(0)
            csv_content = output.getvalue()
            
            # Générer le nom de fichier
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"alertes_historiques_{timestamp}.csv"
            
            return Response(
                csv_content,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename={filename}'}
            )
            
    except Exception as e:
        logger.error(f"Erreur export historique alertes: {e}")
        return jsonify({'error': str(e)}), 500 

@admin_bp.route('/users/check-unique', methods=['GET'])
@admin_required
def check_user_unique():
    """Vérifier l'unicité du username et/ou de l'email.
    Paramètres: username, email, exclude_id (ignorer un utilisateur existant lors de l'édition).
    Retour: { username: { unique: bool, message: str }, email: { unique: bool, message: str } }
    """
    try:
        username = request.args.get('username', type=str)
        email = request.args.get('email', type=str)
        exclude_id = request.args.get('exclude_id', type=int)

        result = {
            'username': { 'unique': True, 'message': '' },
            'email': { 'unique': True, 'message': '' }
        }

        with get_db_session_with_context() as session:
            if username:
                q = session.query(User).filter(User.username == username)
                if exclude_id:
                    q = q.filter(User.id != exclude_id)
                exists = session.query(q.exists()).scalar()
                if exists:
                    result['username'] = { 'unique': False, 'message': "Nom d'utilisateur déjà utilisé" }
            if email:
                q = session.query(User).filter(User.email == email)
                if exclude_id:
                    q = q.filter(User.id != exclude_id)
                exists = session.query(q.exists()).scalar()
                if exists:
                    result['email'] = { 'unique': False, 'message': 'Adresse email déjà utilisée' }

        return jsonify(result)
    except Exception as e:
        logger.error(f"Erreur check-unique utilisateurs: {e}")
        return jsonify({'error': str(e)}), 500 
