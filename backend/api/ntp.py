"""
API NTP - Requtes et monitoring des serveurs NTP
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.database import NTPServer
from backend.database import NTPLog
from backend.database import Alert
from backend.services.ntp_service import ntp_service
from backend.services.client_monitor_service import client_monitor_service
# SUPPRIMÉ: Import Flask-SQLAlchemy circulaire
from backend.database_manager import get_db_session_with_context
from datetime import datetime, timedelta
import logging
from sqlalchemy import and_

logger = logging.getLogger(__name__)

ntp_bp = Blueprint('ntp', __name__)

@ntp_bp.route('/servers', methods=['GET'])
@login_required
def get_all_servers():
    """Récupérer tous les serveurs NTP"""
    try:
        with get_db_session_with_context() as session:
            servers = session.query(NTPServer).filter(
                NTPServer.is_active == True,
                NTPServer.deleted_at.is_(None)
            ).order_by(NTPServer.priority).all()
            
            servers_data = []
            for server in servers:
                server_data = {
                    'id': server.id,
                    'name': server.name,
                    'address': server.address,
                    'port': server.port,
                    'server_type': server.server_type,
                    'status': server.status,
                    'last_sync': server.last_sync.isoformat() if server.last_sync else None,
                    'last_offset': server.last_offset,
                    'last_delay': server.last_latency,
                    'last_stratum': server.last_stratum,
                    'is_active': server.is_active,
                    'priority': server.priority,
                    'max_offset': None,  # ❌ SUPPRIMÉ: Utiliser alert_thresholds
                    'timeout': server.timeout,
                    'description': server.description
                }
                servers_data.append(server_data)
        
        return jsonify({
            'success': True,
            'servers': servers_data,
            'total': len(servers_data),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération serveurs: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/servers', methods=['POST'])
@login_required
def create_server():
    """Créer un nouveau serveur NTP"""
    try:
        data = request.get_json()
        
        # Validation des données
        required_fields = ['name', 'address']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Champ requis: {field}'}), 400
        
        with get_db_session_with_context() as session:
            # Vérifier si l'adresse existe déjà
            existing = session.query(NTPServer).filter_by(address=data['address']).first()
            if existing:
                return jsonify({'error': 'Un serveur avec cette adresse existe déjà'}), 400
            
            server = NTPServer(
                name=data['name'],
                address=data['address'],
                port=data.get('port', 123),
                server_type=data.get('server_type', 'pool'),
                description=data.get('description', ''),
                is_active=data.get('is_active', True),
                priority=data.get('priority', 1),
                max_offset=data.get('max_offset', 1.0),
                timeout=data.get('timeout', 10)
            )
            
            session.add(server)
            session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Serveur créé avec succès',
                'server_id': server.id
            }), 201
        
    except Exception as e:
        logger.error(f"Erreur création serveur: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/servers/<int:server_id>', methods=['PUT'])
@login_required
def update_server(server_id):
    """Mettre à jour un serveur NTP"""
    try:
        with get_db_session_with_context() as session:
            server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
            if not server:
                return jsonify({'error': 'Serveur non trouvé'}), 404
                
            data = request.get_json()
            
            # Mettre à jour les champs modifiables
            updatable_fields = ['name', 'address', 'port', 'server_type', 'description', 
                               'is_active', 'priority', 'max_offset', 'timeout']
            
            for field in updatable_fields:
                if field in data:
                    setattr(server, field, data[field])
            
            session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Serveur mis à jour avec succès'
            })
        
    except Exception as e:
        logger.error(f"Erreur mise à jour serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/servers/<int:server_id>', methods=['DELETE'])
@login_required
def delete_server(server_id):
    """Supprimer un serveur NTP"""
    try:
        with get_db_session_with_context() as session:
            server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
            if not server:
                return jsonify({'error': 'Serveur non trouvé'}), 404
            
            # Supprimer les logs associés
            session.query(NTPLog).filter_by(server_id=server_id).delete()
            
            session.delete(server)
            session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Serveur supprimé avec succès'
            })
        
    except Exception as e:
        logger.error(f"Erreur suppression serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/query/all', methods=['POST'])
@login_required
def query_all_servers():
    """Interroger tous les serveurs NTP actifs"""
    try:
        results = ntp_service.query_all_servers()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'results': results,
            'total_servers': len(results),
            'successful_queries': len([r for r in results if r.get('success', False)])
        })
        
    except Exception as e:
        logger.error(f"Erreur requte tous serveurs: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/query/<int:server_id>', methods=['POST'])
@login_required
def query_server(server_id):
    """Interroger un serveur NTP spécifique"""
    try:
        with get_db_session_with_context() as session:
            server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
            if not server:
                return jsonify({'error': 'Serveur non trouvé'}), 404
            
            if not server.is_active:
                return jsonify({'error': 'Serveur désactivé'}), 400
            
            result = ntp_service.query_server(server)
            
            return jsonify({
                'success': True,
                'timestamp': datetime.utcnow().isoformat(),
                'result': result
            })
        
    except Exception as e:
        logger.error(f"Erreur requête serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/test-connectivity', methods=['POST'])
@login_required
def test_connectivity():
    """Tester la connectivit vers un serveur NTP"""
    try:
        data = request.get_json()
        address = data.get('address')
        port = data.get('port', 123)
        timeout = data.get('timeout', 5)
        
        if not address:
            return jsonify({'error': 'Adresse requise'}), 400
        
        result = ntp_service.test_connectivity(address, port, timeout)
        
        return jsonify({
            'success': True,
            'address': address,
            'port': port,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur test connectivit: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/servers/<int:server_id>/logs')
@login_required
def get_server_logs(server_id):
    """Récupérer les logs d'un serveur"""
    try:
        with get_db_session_with_context() as session:
            server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
            if not server:
                return jsonify({'error': 'Serveur non trouvé'}), 404
                
            hours = request.args.get('hours', 24, type=int)
            limit = request.args.get('limit', 100, type=int)
            
            # Récupérer les logs récents
            since = datetime.utcnow() - timedelta(hours=hours)
            logs = session.query(NTPLog).filter(
                NTPLog.server_id == server_id,
                NTPLog.timestamp >= since
            ).order_by(NTPLog.timestamp.desc()).limit(limit).all()
            
            logs_data = []
            for log in logs:
                logs_data.append({
                    'id': log.id,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'status': log.status,
                    'offset': log.offset,
                    'delay': getattr(log, 'delay', None),
                    'latency': getattr(log, 'latency', None),
                    'stratum': getattr(log, 'stratum', None),
                    'response_time': getattr(log, 'response_time', None),
                    'error_message': log.error_message
                })
            
            return jsonify({
                'server_id': server_id,
                'server_name': server.name,
                'period_hours': hours,
                'total_logs': len(logs_data),
                'logs': logs_data
            })
        
    except Exception as e:
        logger.error(f"Erreur récupération logs serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/servers/<int:server_id>/statistics')
@login_required
def get_server_statistics(server_id):
    """Rcuprer les statistiques dtailles d'un serveur"""
    try:
        hours = request.args.get('hours', 24, type=int)
        stats = ntp_service.get_server_statistics(server_id, hours)
        
        if not stats:
            return jsonify({'error': 'Serveur non trouv ou aucune donne'}), 404
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Erreur statistiques serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/clients/connections')
@login_required
def get_client_connections():
    """Rcuprer les connexions clients NTP actives"""
    try:
        connections = client_monitor_service.get_active_connections()
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'active_connections': len(connections),
            'connections': connections
        })
        
    except Exception as e:
        logger.error(f"Erreur rcupration connexions clients: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/clients/statistics')
@login_required
def get_client_statistics():
    """Rcuprer les statistiques des clients NTP"""
    try:
        hours = request.args.get('hours', 24, type=int)
        stats = client_monitor_service.get_client_statistics(hours)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Erreur statistiques clients: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/service/status')
@login_required
def get_ntp_service_status():
    """Status du service NTP local"""
    try:
        status = client_monitor_service.get_service_status()
        stats = client_monitor_service.get_ntp_statistics()
        
        # Retourner une structure combine et aplatie pour le frontend
        return jsonify({
            'service_status': status.get('service_status', 'unknown'),
            'port': status.get('port', 123),
            'port_listening': status.get('port_listening', False),
            'active_connections': stats.get('active_connections', 0),
            'unique_clients': stats.get('unique_clients', 0),
            'stratum': stats.get('stratum', 0),
            'precision': stats.get('precision', 0),
            'rootdelay': stats.get('rootdelay', 0),
            'rootdispersion': stats.get('rootdispersion', 0),
            'peer': stats.get('peer', ''),
            'refid': stats.get('refid', ''),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur status service NTP: {e}")
        return jsonify({
            'service_status': 'error',
            'port': 123,
            'port_listening': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@ntp_bp.route('/service/peers')
@login_required
def get_ntp_peers():
    """Rcuprer les pairs NTP via ntpq"""
    try:
        peers = client_monitor_service.get_ntpq_peers()
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'peers_count': len(peers),
            'peers': peers
        })
        
    except Exception as e:
        logger.error(f"Erreur rcupration pairs NTP: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/alerts/server/<int:server_id>')
@login_required
def get_server_alerts(server_id):
    """Récupérer les alertes d'un serveur spécifique"""
    try:
        with get_db_session_with_context() as session:
            server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
            if not server:
                return jsonify({'error': 'Serveur non trouvé'}), 404
            
            # Filtres
            status = request.args.get('status', 'all')
            hours = request.args.get('hours', 24, type=int)
            
            query = session.query(Alert).filter_by(server_id=server_id)
            
            if status != 'all':
                query = query.filter_by(status=status)
            
            if hours > 0:
                since = datetime.utcnow() - timedelta(hours=hours)
                query = query.filter(Alert.created_at >= since)
            
            alerts = query.order_by(Alert.created_at.desc()).all()
            
            alerts_data = []
            for alert in alerts:
                alerts_data.append({
                    'id': alert.id,
                    'title': alert.title,
                    'alert_type': alert.alert_type,
                    'message': alert.message,
                    'status': alert.status,
                    'created_at': alert.created_at.isoformat() if alert.created_at else None,
                    'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                    'server_id': alert.server_id,
                    'threshold_id': alert.threshold_id,
                    'severity': alert.severity
                })
            
            return jsonify({
                'server_id': server_id,
                'server_name': server.name,
                'alerts_count': len(alerts_data),
                'alerts': alerts_data
            })
        
    except Exception as e:
        logger.error(f"Erreur récupération alertes serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/analytics/offset-trends')
def get_offset_trends():
    """Récupérer les tendances d'écart pour tous les serveurs - FENÊTRE GLISSANTE 24H"""
    try:
        hours = request.args.get('hours', 24, type=int)
        interval_minutes = request.args.get('interval_minutes', 30, type=int)  # minutes pour plus de granularité
        
        with get_db_session_with_context() as session:
            servers = session.query(NTPServer).filter_by(is_active=True).all()
            trends = {}
            since = datetime.utcnow() - timedelta(hours=hours)
            
            for server in servers:
                # Récupérer les logs avec intervalle
                logs = session.query(NTPLog).filter(
                    NTPLog.server_id == server.id,
                    NTPLog.timestamp >= since,
                    NTPLog.status == 'success',
                    NTPLog.offset != None
                ).order_by(NTPLog.timestamp).all()
                
                # Grouper par intervalle de minutes pour plus de granularité
                grouped_data = []
                current_time = since
                
                while current_time < datetime.utcnow():
                    interval_end = current_time + timedelta(minutes=interval_minutes)
                    
                    interval_logs = [
                        log for log in logs 
                        if current_time <= log.timestamp < interval_end
                    ]
                    
                    if interval_logs:
                        # Calculs statistiques détaillés
                        offsets = [log.offset for log in interval_logs]
                        avg_offset = sum(abs(offset) for offset in offsets) / len(offsets)
                        max_offset = max(abs(offset) for offset in offsets)
                        min_offset = min(abs(offset) for offset in offsets)
                        
                        grouped_data.append({
                            'timestamp': current_time.isoformat(),
                            'avg_offset': avg_offset,
                            'max_offset': max_offset,
                            'min_offset': min_offset,
                            'samples': len(interval_logs),
                            'raw_avg': sum(offsets) / len(offsets)  # Moyenne avec signe
                        })
                    else:
                        # Point de données manquant - interpolation ou valeur nulle
                        grouped_data.append({
                            'timestamp': current_time.isoformat(),
                            'avg_offset': None,
                            'max_offset': None,
                            'min_offset': None,
                            'samples': 0,
                            'raw_avg': None
                        })
                    
                    current_time = interval_end
                
                trends[server.id] = {
                    'server_name': server.name,
                    'server_address': server.address,
                    'data': grouped_data
                }
        
        return jsonify({
            'success': True,
            'period_hours': hours,
            'interval_minutes': interval_minutes,
            'servers_count': len(trends),
            'trends': trends,
            'timestamp': datetime.utcnow().isoformat(),
            'window_start': since.isoformat(),
            'window_end': datetime.utcnow().isoformat(),
            'data_points_per_server': len(grouped_data) if grouped_data else 0
        })
        
    except Exception as e:
        logger.error(f"Erreur tendances offset: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/system/time-comparison')
@login_required
def get_time_comparison():
    """Comparaison de l'heure système avec les serveurs NTP"""
    try:
        system_time = ntp_service.get_system_time()
        
        with get_db_session_with_context() as session:
            servers = session.query(NTPServer).filter_by(is_active=True).all()
            
            comparisons = []
            
            for server in servers:
                if server.last_sync and server.last_offset is not None:
                    comparisons.append({
                        'server_id': server.id,
                        'server_name': server.name,
                        'server_address': server.address,
                        'last_sync': server.last_sync.isoformat(),
                        'offset': server.last_offset,
                        'offset_ms': server.last_offset * 1000,
                        'status': server.status,
                        'within_threshold': True  # ❌ SUPPRIMÉ: server.max_offset - Utiliser alert_thresholds
                    })
        
        return jsonify({
            'system_time': system_time,
            'servers': comparisons,
            'timestamp': datetime.utcnow().isoformat(),
            'synchronized_servers': len([c for c in comparisons if c['within_threshold']])
        })
        
    except Exception as e:
        logger.error(f"Erreur comparaison temps: {e}")
        return jsonify({'error': str(e)}), 500 

@ntp_bp.route('/status', methods=['GET'])
@login_required
def get_ntp_status():
    """Récupérer le status global du service NTP"""
    try:
        with get_db_session_with_context() as session:
            # Serveurs NTP
            servers = session.query(NTPServer).filter_by(is_active=True).all()
            
            # Statistiques récentes
            from backend.database import NTPLog
            recent_logs = session.query(NTPLog).filter(
                NTPLog.timestamp >= datetime.utcnow() - timedelta(hours=1)
            ).all()
            
            # Calculs
            online_servers = len([s for s in servers if s.status != 'offline'])
            total_queries = len(recent_logs)
            
            # Performance moyenne
            avg_offset = 0
            if recent_logs:
                offsets = [abs(log.offset) for log in recent_logs if log.offset is not None]
                if offsets:
                    avg_offset = sum(offsets) / len(offsets)
            
            return jsonify({
                'success': True,
                'status': 'operational' if online_servers > 0 else 'degraded',
                'servers': {
                    'total': len(servers),
                    'online': online_servers,
                    'offline': len(servers) - online_servers
                },
                'performance': {
                    'avg_offset_1h': round(avg_offset, 4),
                    'total_queries_1h': total_queries
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Erreur récupération status NTP: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ntp_bp.route('/stats', methods=['GET'])
@login_required
def get_ntp_stats():
    """Récupérer les statistiques détaillées NTP"""
    try:
        with get_db_session_with_context() as session:
            # Statistiques sur 24h
            from backend.database import NTPLog
            logs_24h = session.query(NTPLog).filter(
                NTPLog.timestamp >= datetime.utcnow() - timedelta(hours=24)
            ).all()
            
            # Statistiques sur 1h
            logs_1h = session.query(NTPLog).filter(
                NTPLog.timestamp >= datetime.utcnow() - timedelta(hours=1)
            ).all()
            
            # Calculs de performance
            def calculate_stats(logs):
                if not logs:
                    return {'avg_offset': 0, 'max_offset': 0, 'min_offset': 0, 'total': 0}
                
                offsets = [log.offset for log in logs if log.offset is not None]
                if not offsets:
                    return {'avg_offset': 0, 'max_offset': 0, 'min_offset': 0, 'total': len(logs)}
                
                return {
                    'avg_offset': round(sum(offsets) / len(offsets), 4),
                    'max_offset': round(max(offsets), 4),
                    'min_offset': round(min(offsets), 4),
                    'total': len(logs)
                }
            
            stats_24h = calculate_stats(logs_24h)
            stats_1h = calculate_stats(logs_1h)
            
            # Serveurs
            servers = session.query(NTPServer).filter_by(is_active=True).all()
            server_stats = {}
            for server in servers:
                server_logs = session.query(NTPLog).filter(
                    and_(NTPLog.server_id == server.id, 
                         NTPLog.timestamp >= datetime.utcnow() - timedelta(hours=1))
                ).all()
                
                server_stats[server.name] = {
                    'status': server.status,
                    'last_sync': server.last_sync.isoformat() if server.last_sync else None,
                    'last_offset': server.last_offset,
                    'queries_1h': len(server_logs)
                }
            
            return jsonify({
                'success': True,
                'periods': {
                    '1h': stats_1h,
                    '24h': stats_24h
                },
                'servers': server_stats,
                'total_servers': len(servers),
                'timestamp': datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Erreur récupération statistiques NTP: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500 
