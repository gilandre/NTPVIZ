# Gestion des serveurs NTP avec suppression logique
@admin_bp.route('/servers', methods=['GET'])
@login_required
def get_all_servers():
    """Récupérer tous les serveurs NTP (actifs, inactifs et supprimés)"""
    try:
        with get_db_session_with_context() as session:
            # Récupérer tous les serveurs, y compris supprimés
            servers = session.query(NTPServer).order_by(
                NTPServer.deleted_at.is_(None).desc(),  # Non supprimés en premier
                NTPServer.priority
            ).all()
            
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
                    'is_deleted': server.is_deleted,
                    'priority': server.priority,
                    'timeout': server.timeout,
                    'max_offset': server.max_offset,
                    'description': server.description,
                    'created_at': server.created_at.isoformat() if server.created_at else None,
                    'deleted_at': server.deleted_at.isoformat() if server.deleted_at else None,
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
    """Créer un nouveau serveur NTP avec vérification d'unicité"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'address', 'server_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Champ requis: {field}'}), 400
        
        with get_db_session_with_context() as session:
            # Vérifier l'unicité de l'adresse (serveurs actifs uniquement)
            existing = session.query(NTPServer).filter(
                NTPServer.address == data['address'],
                NTPServer.server_type == data['server_type'],
                NTPServer.deleted_at.is_(None)  # Non supprimé
            ).first()
            
            if existing:
                return jsonify({'error': 'Un serveur actif avec cette adresse existe déjà'}), 400
            
            # Priorité automatique
            max_priority = session.query(func.max(NTPServer.priority)).filter(
                NTPServer.deleted_at.is_(None)
            ).scalar() or 0
            
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

@admin_bp.route('/servers/<int:server_id>', methods=['DELETE'])
@config_required
def delete_server(server_id):
    """Suppression logique d'un serveur NTP"""
    try:
        with get_db_session_with_context() as session:
            server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
            if not server:
                return jsonify({'error': 'Serveur non trouvé'}), 404
            
            if server.is_deleted:
                return jsonify({'error': 'Serveur déjà supprimé'}), 400
                
            server_name = server.name
            
            # Suppression logique
            server.soft_delete(deleted_by_user_id=current_user.id)
            session.commit()
            
            logger.info(f"Serveur NTP supprimé logiquement: {server_name} par {current_user.username}")
            
            return jsonify({
                'success': True,
                'message': 'Serveur supprimé avec succès',
                'deleted_at': server.deleted_at.isoformat() if server.deleted_at else None
            })
        
    except Exception as e:
        logger.error(f"Erreur suppression logique serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/servers/<int:server_id>/restore', methods=['POST'])
@config_required
def restore_server(server_id):
    """Restaurer un serveur supprimé logiquement"""
    try:
        with get_db_session_with_context() as session:
            server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
            if not server:
                return jsonify({'error': 'Serveur non trouvé'}), 404
            
            if not server.is_deleted:
                return jsonify({'error': 'Serveur non supprimé'}), 400
            
            # Vérifier qu'aucun serveur actif n'utilise la même adresse
            existing = session.query(NTPServer).filter(
                NTPServer.address == server.address,
                NTPServer.server_type == server.server_type,
                NTPServer.deleted_at.is_(None),
                NTPServer.id != server_id
            ).first()
            
            if existing:
                return jsonify({'error': 'Un serveur actif utilise déjà cette adresse'}), 400
            
            server_name = server.name
            
            # Restauration
            server.restore()
            session.commit()
            
            logger.info(f"Serveur NTP restauré: {server_name} par {current_user.username}")
            
            return jsonify({
                'success': True,
                'message': 'Serveur restauré avec succès'
            })
        
    except Exception as e:
        logger.error(f"Erreur restauration serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/servers/deleted', methods=['GET'])
@login_required
def get_deleted_servers():
    """Récupérer les serveurs supprimés logiquement"""
    try:
        with get_db_session_with_context() as session:
            deleted_servers = session.query(NTPServer).filter(
                NTPServer.deleted_at.isnot(None)
            ).order_by(NTPServer.deleted_at.desc()).all()
            
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
            
            return jsonify(servers_data)
        
    except Exception as e:
        logger.error(f"Erreur récupération serveurs supprimés: {e}")
        return jsonify({'error': str(e)}), 500
