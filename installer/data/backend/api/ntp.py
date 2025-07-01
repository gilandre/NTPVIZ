"""
API NTP - Requtes et monitoring des serveurs NTP
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.models.ntp_server import NTPServer
from backend.models.ntp_log import NTPLog
from backend.models.alert import Alert
from backend.services.ntp_service import ntp_service
from backend.services.client_monitor_service import client_monitor_service
from backend.database_manager import db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

ntp_bp = Blueprint('ntp', __name__)

@ntp_bp.route('/servers', methods=['GET'])
@login_required
def get_all_servers():
    """Rcuprer tous les serveurs NTP"""
    try:
        servers = NTPServer.query.filter_by(is_active=True).order_by(NTPServer.priority).all()
        
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
                'last_stratum': None,
                'is_active': server.is_active,
                'priority': server.priority,
                'max_offset': server.max_offset,
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
        logger.error(f"Erreur rcupration serveurs: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/servers', methods=['POST'])
@login_required
def create_server():
    """Crer un nouveau serveur NTP"""
    try:
        data = request.get_json()
        
        # Validation des donnes
        required_fields = ['name', 'address']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Champ requis: {field}'}), 400
        
        # Vrifier si l'adresse existe dj
        existing = NTPServer.query.filter_by(address=data['address']).first()
        if existing:
            return jsonify({'error': 'Un serveur avec cette adresse existe dj'}), 400
        
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
        
        db.session.add(server)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Serveur cr avec succs',
            'server_id': server.id
        }), 201
        
    except Exception as e:
        logger.error(f"Erreur cration serveur: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/servers/<int:server_id>', methods=['PUT'])
@login_required
def update_server(server_id):
    """Mettre  jour un serveur NTP"""
    try:
        server = NTPServer.query.get_or_404(server_id)
        data = request.get_json()
        
        # Mettre  jour les champs modifiables
        updatable_fields = ['name', 'address', 'port', 'server_type', 'description', 
                           'is_active', 'priority', 'max_offset', 'timeout']
        
        for field in updatable_fields:
            if field in data:
                setattr(server, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Serveur mis  jour avec succs'
        })
        
    except Exception as e:
        logger.error(f"Erreur mise  jour serveur {server_id}: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/servers/<int:server_id>', methods=['DELETE'])
@login_required
def delete_server(server_id):
    """Supprimer un serveur NTP"""
    try:
        server = NTPServer.query.get_or_404(server_id)
        
        # Supprimer les logs associs
        NTPLog.query.filter_by(server_id=server_id).delete()
        
        db.session.delete(server)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Serveur supprim avec succs'
        })
        
    except Exception as e:
        logger.error(f"Erreur suppression serveur {server_id}: {e}")
        db.session.rollback()
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
    """Interroger un serveur NTP spcifique"""
    try:
        server = NTPServer.query.get_or_404(server_id)
        
        if not server.is_active:
            return jsonify({'error': 'Serveur dsactiv'}), 400
        
        result = ntp_service.query_server(server)
        
        return jsonify({
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Erreur requte serveur {server_id}: {e}")
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
    """Rcuprer les logs d'un serveur"""
    try:
        server = NTPServer.query.get_or_404(server_id)
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        logs = NTPLog.get_recent_logs(server_id, hours)
        logs = logs[:limit]  # Limiter le nombre de rsultats
        
        return jsonify({
            'server_id': server_id,
            'server_name': server.name,
            'period_hours': hours,
            'total_logs': len(logs),
            'logs': [log.to_dict() for log in logs]
        })
        
    except Exception as e:
        logger.error(f"Erreur rcupration logs serveur {server_id}: {e}")
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
        
        return jsonify({
            'service': status,
            'statistics': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur status service NTP: {e}")
        return jsonify({'error': str(e)}), 500

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
    """Rcuprer les alertes d'un serveur spcifique"""
    try:
        server = NTPServer.query.get_or_404(server_id)
        
        # Filtres
        status = request.args.get('status', 'all')
        hours = request.args.get('hours', 24, type=int)
        
        query = Alert.query.filter_by(server_id=server_id)
        
        if status != 'all':
            query = query.filter_by(status=status)
        
        if hours > 0:
            since = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(Alert.created_at >= since)
        
        alerts = query.order_by(Alert.created_at.desc()).all()
        
        return jsonify({
            'server_id': server_id,
            'server_name': server.name,
            'alerts_count': len(alerts),
            'alerts': [alert.to_dict() for alert in alerts]
        })
        
    except Exception as e:
        logger.error(f"Erreur rcupration alertes serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/analytics/offset-trends')
@login_required
def get_offset_trends():
    """Rcuprer les tendances d'cart pour tous les serveurs"""
    try:
        hours = request.args.get('hours', 24, type=int)
        interval = request.args.get('interval', 1, type=int)  # heures
        
        servers = NTPServer.query.filter_by(is_active=True).all()
        trends = {}
        
        for server in servers:
            # Rcuprer les logs avec intervalle
            since = datetime.utcnow() - timedelta(hours=hours)
            logs = NTPLog.query.filter(
                NTPLog.server_id == server.id,
                NTPLog.timestamp >= since,
                NTPLog.status == 'success',
                NTPLog.offset.isnot(None)
            ).order_by(NTPLog.timestamp).all()
            
            # Grouper par intervalle
            grouped_data = []
            current_time = since
            
            while current_time < datetime.utcnow():
                interval_end = current_time + timedelta(hours=interval)
                
                interval_logs = [
                    log for log in logs 
                    if current_time <= log.timestamp < interval_end
                ]
                
                if interval_logs:
                    avg_offset = sum(abs(log.offset) for log in interval_logs) / len(interval_logs)
                    max_offset = max(abs(log.offset) for log in interval_logs)
                    
                    grouped_data.append({
                        'timestamp': current_time.isoformat(),
                        'avg_offset': avg_offset,
                        'max_offset': max_offset,
                        'samples': len(interval_logs)
                    })
                
                current_time = interval_end
            
            trends[server.id] = {
                'server_name': server.name,
                'server_address': server.address,
                'data': grouped_data
            }
        
        return jsonify({
            'period_hours': hours,
            'interval_hours': interval,
            'servers_count': len(trends),
            'trends': trends,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur tendances offset: {e}")
        return jsonify({'error': str(e)}), 500

@ntp_bp.route('/system/time-comparison')
@login_required
def get_time_comparison():
    """Comparaison de l'heure systme avec les serveurs NTP"""
    try:
        system_time = ntp_service.get_system_time()
        servers = NTPServer.query.filter_by(is_active=True).all()
        
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
                    'within_threshold': abs(server.last_offset) <= server.max_offset
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
