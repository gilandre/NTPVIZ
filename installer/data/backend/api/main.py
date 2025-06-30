"""
API Main - Routes principales et dashboard
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from backend.models.ntp_server import NTPServer
from backend.models.alert import Alert
from backend.models.ntp_log import NTPLog
from backend.services.ntp_service import ntp_service
from backend.services.client_monitor_service import client_monitor_service
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dashboard():
    """Page d'accueil - Dashboard principal"""
    return render_template('dashboard.html')

@main_bp.route('/api/dashboard/summary')
@login_required
def dashboard_summary():
    """Rsum des donnes pour le dashboard"""
    try:
        # Statistiques des serveurs
        servers = NTPServer.query.filter_by(is_active=True).all()
        synchronized_servers = [s for s in servers if s.status == 'ok']
        
        # Donnes dtailles des serveurs
        servers_data = []
        for server in servers:
            servers_data.append({
                'id': server.id,
                'name': server.name,
                'address': server.address,
                'port': server.port,
                'server_type': server.server_type,
                'status': server.status,
                'last_sync': server.last_sync.isoformat() if server.last_sync else None,
                'last_offset': server.last_offset if server.last_offset is not None else 0.0,
                'last_latency': server.last_latency if server.last_latency is not None else 0.0,
                'max_offset': server.max_offset
            })
        
        # Statistiques des alertes
        active_alerts = Alert.query.filter_by(status='active').all()
        
        # Statistiques des clients (simulation)
        try:
            client_stats = client_monitor_service.get_connection_stats()
        except:
            client_stats = {'total_connections': 0, 'active_connections': 0}
        
        # Informations systme
        system_info = {
            'local_time': datetime.now().isoformat(),
            'utc_time': datetime.utcnow().isoformat(),
            'timezone': 'Europe/Paris',
            'utc_offset_hours': 1,
            'is_dst': False
        }
        
        return jsonify({
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'servers': {
                'total': len(servers),
                'synchronized': len(synchronized_servers),
                'data': servers_data
            },
            'alerts': {
                'total': len(active_alerts),
                'critical': len([a for a in active_alerts if a.severity == 'critical']),
                'warning': len([a for a in active_alerts if a.severity == 'warning'])
            },
            'clients': client_stats,
            'system': system_info
        })
        
    except Exception as e:
        logger.error(f"Erreur dashboard summary: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/dashboard/realtime')
@login_required
def dashboard_realtime():
    """Donnes temps rel pour le dashboard"""
    try:
        # Interroger tous les serveurs
        results = ntp_service.query_all_servers()
        
        # Systme local
        system_time = ntp_service.get_system_time()
        
        # Alertes rcentes
        recent_alerts = Alert.query.filter(
            Alert.created_at >= datetime.utcnow() - timedelta(minutes=5)
        ).order_by(Alert.created_at.desc()).limit(5).all()
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'servers': results,
            'system': system_time,
            'recent_alerts': [alert.to_dict() for alert in recent_alerts]
        })
        
    except Exception as e:
        logger.error(f"Erreur dashboard realtime: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/servers')
@login_required
def get_servers():
    """Liste des serveurs NTP configurs"""
    try:
        servers = NTPServer.query.order_by(NTPServer.priority).all()
        return jsonify([server.to_dict() for server in servers])
        
    except Exception as e:
        logger.error(f"Erreur rcupration serveurs: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/servers/<int:server_id>/stats')
@login_required
def get_server_stats(server_id):
    """Statistiques dtailles d'un serveur"""
    try:
        hours = request.args.get('hours', 24, type=int)
        stats = ntp_service.get_server_statistics(server_id, hours)
        
        if not stats:
            return jsonify({'error': 'Serveur non trouv'}), 404
        
        # Ajouter l'historique des logs
        logs = NTPLog.get_recent_logs(server_id, hours)
        stats['logs'] = [log.to_dict() for log in logs[-50:]]  # Derniers 50 logs
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Erreur stats serveur {server_id}: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/alerts')
@login_required
def get_alerts():
    """Liste des alertes avec pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', 'all')
        severity = request.args.get('severity', 'all')
        
        query = Alert.query
        
        # Filtres
        if status != 'all':
            query = query.filter_by(status=status)
        if severity != 'all':
            query = query.filter_by(severity=severity)
        
        # Pagination
        alerts = query.order_by(Alert.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'alerts': [alert.to_dict() for alert in alerts.items],
            'pagination': {
                'page': alerts.page,
                'pages': alerts.pages,
                'per_page': alerts.per_page,
                'total': alerts.total,
                'has_next': alerts.has_next,
                'has_prev': alerts.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur rcupration alertes: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    """Acquitter une alerte"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        alert.acknowledge(current_user.id)
        
        return jsonify({
            'success': True,
            'message': 'Alerte acquitte',
            'alert': alert.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Erreur acquittement alerte {alert_id}: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    """Rsoudre une alerte"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        alert.resolve(current_user.id)
        
        return jsonify({
            'success': True,
            'message': 'Alerte rsolue',
            'alert': alert.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Erreur rsolution alerte {alert_id}: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/system/time')
@login_required
def get_system_time():
    """Informations systme dtailles sur l'heure - UTILISE LES VRAIES DONNES SYSTME"""
    try:
        #  Utiliser la fonction systme existante du service NTP
        from backend.services.ntp_service import ntp_service
        system_info = ntp_service.get_system_time()
        
        # Parser l'offset pour le frontend (format +HH:MM vers minutes)
        utc_offset_str = system_info.get('utc_offset', '+00:00')
        if ':' in utc_offset_str:
            sign = 1 if utc_offset_str[0] == '+' else -1
            hours, minutes = map(int, utc_offset_str[1:].split(':'))
            utc_offset_minutes = sign * (hours * 60 + minutes)
        else:
            utc_offset_minutes = 0
        
        # Format adapt pour le frontend
        return jsonify({
            'success': True,
            'local_time': system_info['local_time'],
            'utc_time': system_info['utc_time'],
            'timezone': system_info['timezone'],
            'utc_offset': system_info['utc_offset'],
            'utc_offset_minutes': utc_offset_minutes,  # Pour compatibilit frontend
            'is_dst': system_info['is_dst'],
            'timestamp': system_info['timestamp']
        })
        
    except Exception as e:
        logger.error(f"Erreur rcupration temps systme: {e}")
        
        # Fallback avec vraies donnes systme basiques
        try:
            now = datetime.now()
            utc_now = datetime.utcnow()
            return jsonify({
                'success': False,
                'local_time': now.isoformat(),
                'utc_time': utc_now.isoformat(),
                'timezone': 'System Error',
                'utc_offset': '+00:00',
                'utc_offset_minutes': 0,
                'is_dst': False,
                'timestamp': now.timestamp(),
                'error': str(e)
            })
        except:
            return jsonify({'error': 'Critical system time error'}), 500

@main_bp.route('/api/system/status')
@login_required
def get_system_status():
    """Status gnral du systme"""
    try:
        # Status des services
        ntp_status = client_monitor_service.get_service_status()
        ntp_stats = client_monitor_service.get_ntp_statistics()
        
        # Status des serveurs
        servers = NTPServer.query.filter_by(is_active=True).all()
        servers_status = {
            'total': len(servers),
            'online': len([s for s in servers if s.status != 'offline']),
            'offline': len([s for s in servers if s.status == 'offline']),
            'warning': len([s for s in servers if s.status == 'warning']),
            'critical': len([s for s in servers if s.status == 'critical'])
        }
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'ntp_service': ntp_status,
            'ntp_statistics': ntp_stats,
            'servers': servers_status,
            'alerts': {
                'active': len(Alert.get_active_alerts()),
                'unread': Alert.get_unread_count()
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur status systme: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/health')
def health_check():
    """Endpoint de vrification de sant (sans authentification)"""
    try:
        # Vrifications basiques
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'service': 'NTP Monitor Enterprise'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@main_bp.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    """Statistiques dtailles du dashboard"""
    try:
        # Paramtres
        hours = request.args.get('hours', 24, type=int)
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Nombre de requtes par serveur
        server_stats = []
        for server in NTPServer.query.filter_by(is_active=True).all():
            total_queries = NTPLog.query.filter(
                NTPLog.server_id == server.id,
                NTPLog.timestamp >= since
            ).count()
            
            successful_queries = NTPLog.query.filter(
                NTPLog.server_id == server.id,
                NTPLog.timestamp >= since,
                NTPLog.status == 'success'
            ).count()
            
            server_stats.append({
                'server_id': server.id,
                'server_name': server.name,
                'total_queries': total_queries,
                'successful_queries': successful_queries,
                'success_rate': (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                'current_status': server.status
            })
        
        # Alertes rcentes
        recent_alerts = Alert.query.filter(
            Alert.created_at >= since
        ).order_by(Alert.created_at.desc()).limit(10).all()
        
        return jsonify({
            'success': True,
            'period_hours': hours,
            'server_stats': server_stats,
            'recent_alerts': [alert.to_dict() for alert in recent_alerts],
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/dashboard/alerts')
@login_required
def dashboard_alerts():
    """Rcuprer les alertes pour le dashboard"""
    try:
        # Paramtres
        status = request.args.get('status', 'active')
        limit = request.args.get('limit', 10, type=int)
        
        query = Alert.query
        if status != 'all':
            query = query.filter_by(status=status)
        
        alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'alerts': [alert.to_dict() for alert in alerts],
            'total': len(alerts),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard alerts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/dashboard/health')
@login_required
def dashboard_health():
    """Vrification de sant des services"""
    try:
        health_status = {
            'database': 'ok',
            'ntp_service': 'ok',
            'client_monitor': 'ok',
            'overall': 'ok'
        }
        
        # Test de la base de donnes
        try:
            db.session.execute('SELECT 1')
        except Exception:
            health_status['database'] = 'error'
            health_status['overall'] = 'error'
        
        # Test du service NTP
        try:
            active_servers = NTPServer.query.filter_by(is_active=True).count()
            if active_servers == 0:
                health_status['ntp_service'] = 'warning'
        except Exception:
            health_status['ntp_service'] = 'error'
            health_status['overall'] = 'error'
        
        # Test du monitoring client
        try:
            client_stats = client_monitor_service.get_connection_stats()
            if not client_stats:
                health_status['client_monitor'] = 'warning'
        except Exception:
            health_status['client_monitor'] = 'error'
            health_status['overall'] = 'error'
        
        return jsonify({
            'success': True,
            'health': health_status,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error checking dashboard health: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/dashboard/export')
@login_required
def dashboard_export():
    """Export des donnes du dashboard"""
    try:
        # Vrifier les permissions
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'error': 'Permissions insuffisantes'}), 403
        
        # Paramtres
        hours = request.args.get('hours', 24, type=int)
        format_type = request.args.get('format', 'json')
        
        # Collecter les donnes
        export_data = {
            'export_info': {
                'timestamp': datetime.utcnow().isoformat(),
                'period_hours': hours,
                'exported_by': current_user.username
            },
            'servers': [],
            'logs': [],
            'alerts': []
        }
        
        # Donnes des serveurs
        for server in NTPServer.query.filter_by(is_active=True).all():
            export_data['servers'].append(server.to_dict())
        
        # Logs rcents
        since = datetime.utcnow() - timedelta(hours=hours)
        logs = NTPLog.query.filter(NTPLog.timestamp >= since).order_by(NTPLog.timestamp.desc()).limit(1000).all()
        for log in logs:
            export_data['logs'].append(log.to_dict())
        
        # Alertes rcentes
        alerts = Alert.query.filter(Alert.created_at >= since).order_by(Alert.created_at.desc()).all()
        for alert in alerts:
            export_data['alerts'].append(alert.to_dict())
        
        return jsonify({
            'success': True,
            'data': export_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error exporting dashboard data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 
