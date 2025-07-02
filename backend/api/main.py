"""
API Main - Routes principales et dashboard
"""
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, redirect, url_for, current_app
from flask_login import login_required, current_user
from backend.database_manager import get_db_session_with_context
from backend.database import NTPServer
from backend.database import Alert
from backend.database import NTPLog
from backend.services.ntp_service import ntp_service
from backend.services.client_monitor_service import client_monitor_service
from datetime import datetime, timedelta
import logging
import time
import pytz
from datetime import timezone

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/login')
def login_redirect():
    """Redirection /login vers /auth/login pour compatibilité"""
    return redirect(url_for('auth.login'))

@main_bp.route('/')
@login_required
def dashboard():
    """Page d'accueil - Dashboard principal"""
    return render_template('dashboard.html')

@main_bp.route('/api/dashboard/summary')
@login_required
def dashboard_summary():
    """Résumé des données pour le dashboard"""
    try:
        with get_db_session_with_context() as session:
            # Statistiques des serveurs - TRIÉ PAR PRIORITÉ
            servers = session.query(NTPServer).filter_by(is_active=True).order_by(NTPServer.priority).all()
            synchronized_servers = [s for s in servers if s.status == 'ok']
            
            # Données détaillées des serveurs - TOUS LES CHAMPS NÉCESSAIRES
            servers_data = []
            for server in servers:
                servers_data.append({
                    'id': server.id,
                    'name': server.name,
                    'address': server.address,
                    'port': server.port,
                    'priority': server.priority,  # AJOUTÉ : priority manquant
                    'server_type': server.server_type,
                    'is_active': server.is_active,  # AJOUTÉ : is_active manquant
                    'status': server.status,
                    'last_sync': server.last_sync.isoformat() if server.last_sync else None,
                    'last_offset': server.last_offset if server.last_offset is not None else 0.0,
                    'last_delay': server.last_latency if server.last_latency is not None else 0.0,  # CORRIGÉ : last_delay au lieu de last_latency
                    'last_latency': server.last_latency if server.last_latency is not None else 0.0,  # GARDÉ : pour compatibilité
                    'last_stratum': server.last_stratum if server.last_stratum is not None else 0,  # AJOUTÉ : last_stratum manquant
                    'max_offset': server.max_offset
                })
            
            # Statistiques des alertes - FAIRE TOUTES LES REQUÊTES DANS LA SESSION
            total_active_alerts = session.query(Alert).filter_by(status='active').count()
            critical_alerts_count = session.query(Alert).filter_by(status='active', severity='critical').count()
            warning_alerts_count = session.query(Alert).filter_by(status='active', severity='warning').count()
            
            # Statistiques des clients (simulation)
            try:
                client_stats = client_monitor_service.get_connection_stats()
            except:
                client_stats = {'total_connections': 0, 'active_connections': 0}
            
            # Informations système
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
                    'data': servers_data  # Maintenant triés par priorité avec tous les champs
                },
                'alerts': {
                    'total': total_active_alerts,
                    'critical': critical_alerts_count,
                    'warning': warning_alerts_count
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
    """Données temps réel pour le dashboard"""
    try:
        # Interroger tous les serveurs
        results = ntp_service.query_all_servers()
        
        # Système local
        system_time = ntp_service.get_system_time()
        
        # Alertes récentes - CONVERTIR EN DICTIONNAIRE DANS LA SESSION
        with get_db_session_with_context() as session:
            recent_alerts = session.query(Alert).filter(
                Alert.created_at >= datetime.utcnow() - timedelta(minutes=5)
            ).order_by(Alert.created_at.desc()).limit(5).all()
            
            # Convertir en dictionnaire immédiatement dans la session
            alerts_data = []
            for alert in recent_alerts:
                alerts_data.append({
                    'id': alert.id,
                    'title': alert.title,
                    'message': alert.message,
                    'severity': alert.severity,
                    'status': alert.status,
                    'created_at': alert.created_at.isoformat() if alert.created_at else None,
                    'server_id': alert.server_id
                })
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'servers': results,
            'system': system_time,
            'recent_alerts': alerts_data
        })
        
    except Exception as e:
        logger.error(f"Erreur dashboard realtime: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/servers')
@login_required
def get_servers():
    """Liste des serveurs NTP configurés"""
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
                    'last_sync': server.last_sync.isoformat() if server.last_sync else None,
                    'last_offset': server.last_offset,
                    'last_latency': server.last_latency,
                    'last_stratum': server.last_stratum,
                    'timeout': server.timeout,
                    'max_offset': server.max_offset,
                    'description': server.description
                })
            
            return jsonify(servers_data)
        
    except Exception as e:
        logger.error(f"Erreur récupération serveurs: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/servers/<int:server_id>/stats')
@login_required
def get_server_stats(server_id):
    """Statistiques détaillées d'un serveur"""
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
    """Récuprer les alertes"""
    try:
        # Paramètres de pagination et de filtrage
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status', 'all')
        severity = request.args.get('severity', 'all')
        
        with get_db_session_with_context() as session:
            # Construire la requête
            query = session.query(Alert)
            
            # Filtrer par statut
            if status != 'all':
                if status == 'active':
                    query = query.filter(Alert.status.in_(['active', 'acknowledged']))
                else:
                    query = query.filter_by(status=status)
            
            # Filtrer par sévérité
            if severity != 'all':
                query = query.filter_by(severity=severity)
            
            # Ordonner par date de création (plus récent en premier)
            query = query.order_by(Alert.created_at.desc())
            
            # Récupérer les résultats avec pagination manuelle
            offset = (page - 1) * per_page
            alerts = query.offset(offset).limit(per_page).all()
            total = query.count()
            
            # Statistiques rapides
            total_alerts = session.query(Alert).count()
            active_alerts = session.query(Alert).filter_by(status='active').count()
            acknowledged_alerts = session.query(Alert).filter_by(status='acknowledged').count()
            resolved_alerts = session.query(Alert).filter_by(status='resolved').count()
            
            stats = {
                'total': total_alerts,
                'active': active_alerts,
                'acknowledged': acknowledged_alerts,
                'resolved': resolved_alerts
            }
            
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
                    'created_at': alert.created_at.isoformat() if alert.created_at else None,
                    'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
                }
                alerts_data.append(alert_dict)
        
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
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération alertes: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/alerts/recent')
@login_required
def get_recent_alerts():
    """Récuprer les alertes récentes pour le dashboard"""
    try:
        # Récuprer les alertes récentes (7 derniers jours)
        recent_date = datetime.utcnow() - timedelta(days=7)
        
        with get_db_session_with_context() as session:
            recent_alerts = session.query(Alert).filter(
                Alert.created_at >= recent_date
            ).order_by(Alert.created_at.desc()).limit(10).all()
            
            # Compter les alertes actives
            active_count = session.query(Alert).filter_by(status='active').count()
            unread_count = session.query(Alert).filter_by(is_read=False).count()
            
            # Statistiques par sévérité
            by_severity = {
                'critical': session.query(Alert).filter_by(severity='critical', status='active').count(),
                'warning': session.query(Alert).filter_by(severity='warning', status='active').count(),
                'info': session.query(Alert).filter_by(severity='info', status='active').count()
            }
            
            alerts_data = []
            for alert in recent_alerts:
                alerts_data.append({
                    'id': alert.id,
                    'title': alert.title,
                    'message': alert.message,
                    'severity': alert.severity,
                    'status': alert.status,
                    'server_id': alert.server_id,
                    'is_read': alert.is_read,
                    'created_at': alert.created_at.isoformat() if alert.created_at else None
                })
        
        return jsonify({
            'success': True,
            'alerts': alerts_data,
            'active_count': active_count,
            'unread_count': unread_count,
            'by_severity': by_severity,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération alertes récentes: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'alerts': [],
            'active_count': 0,
            'unread_count': 0,
            'by_severity': {'critical': 0, 'warning': 0, 'info': 0}
        }), 500

@main_bp.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    """Acquitter une alerte"""
    try:
        with get_db_session_with_context() as session:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return jsonify({'error': 'Alerte non trouvée'}), 404
            
            # Marquer comme acquittée
            alert.status = 'acknowledged'
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = current_user.id
            session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Alerte acquittée',
                'alert': {
                    'id': alert.id,
                    'title': alert.title,
                    'status': alert.status,
                    'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
                }
            })
        
    except Exception as e:
        logger.error(f"Erreur acquittement alerte {alert_id}: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    """Résoudre une alerte"""
    try:
        with get_db_session_with_context() as session:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return jsonify({'error': 'Alerte non trouvée'}), 404
            
            # Marquer comme résolue
            alert.status = 'resolved'
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = current_user.id
            session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Alerte résolue',
                'alert': {
                    'id': alert.id,
                    'title': alert.title,
                    'status': alert.status,
                    'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
                }
            })
        
    except Exception as e:
        logger.error(f"Erreur résolution alerte {alert_id}: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/system/time')
@login_required
def get_system_time():
    """Informations système sur l'heure - VERSION SIMPLIFIÉE ET ROBUSTE"""
    try:
        # Obtenir l'heure actuelle locale et UTC de manière fiable
        now_local = datetime.now()
        now_utc = datetime.utcnow()
        
        # Calculer le décalage UTC en secondes puis en minutes
        local_offset_seconds = time.timezone if not time.daylight else time.altzone
        utc_offset_minutes = -local_offset_seconds // 60
        
        # Format du décalage pour affichage (+/-HH:MM)
        hours = abs(utc_offset_minutes) // 60
        minutes = abs(utc_offset_minutes) % 60
        sign = '+' if utc_offset_minutes >= 0 else '-'
        utc_offset_str = f"{sign}{hours:02d}:{minutes:02d}"
        
        # Détection heure d'été
        is_dst = time.daylight and time.localtime().tm_isdst
        
        # Nom de la timezone (essayer d'obtenir le nom système)
        try:
            import locale
            timezone_name = time.tzname[1] if is_dst else time.tzname[0]
            if not timezone_name or timezone_name in ('', 'GMT'):
                timezone_name = f"UTC{utc_offset_str}"
        except:
            timezone_name = f"UTC{utc_offset_str}"
        
        return jsonify({
            'success': True,
            'local_time': now_local.strftime('%H:%M:%S'),
            'utc_time': now_utc.strftime('%H:%M:%S'),
            'local_time_full': now_local.isoformat(),
            'utc_time_full': now_utc.isoformat(),
            'timezone': timezone_name,
            'utc_offset': utc_offset_str,
            'utc_offset_minutes': utc_offset_minutes,
            'is_dst': bool(is_dst),
            'timestamp': now_local.timestamp(),
            'date_locale': now_local.strftime('%d/%m/%Y'),
            'day_name': now_local.strftime('%A'),
            'server_uptime': time.time() - getattr(get_system_time, '_start_time', time.time())
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération temps système: {e}")
        
        # Fallback ultra-simple
        try:
            now = datetime.now()
            utc_now = datetime.utcnow()
            return jsonify({
                'success': False,
                'local_time': now.strftime('%H:%M:%S'),
                'utc_time': utc_now.strftime('%H:%M:%S'),
                'local_time_full': now.isoformat(),
                'utc_time_full': utc_now.isoformat(),
                'timezone': 'Système',
                'utc_offset': '+00:00',
                'utc_offset_minutes': 0,
                'is_dst': False,
                'timestamp': now.timestamp(),
                'error': str(e)
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'error': f'Erreur critique temps système: {fallback_error}'
            }), 500

# Initialiser le temps de démarrage pour l'uptime
if not hasattr(get_system_time, '_start_time'):
    get_system_time._start_time = time.time()

@main_bp.route('/api/system/status')
@login_required
def get_system_status():
    """Status général du système"""
    try:
        # Status des services
        ntp_status = client_monitor_service.get_service_status()
        ntp_stats = client_monitor_service.get_ntp_statistics()
        
        # Status des serveurs avec Database Manager
        with get_db_session_with_context() as session:
            servers = session.query(NTPServer).filter_by(is_active=True).all()
            servers_status = {
                'total': len(servers),
                'online': len([s for s in servers if s.status != 'offline']),
                'offline': len([s for s in servers if s.status == 'offline']),
                'warning': len([s for s in servers if s.status == 'warning']),
                'critical': len([s for s in servers if s.status == 'critical'])
            }
            
            # Alertes actives avec Database Manager
            active_alerts = session.query(Alert).filter_by(status='active').all()
            unread_alerts = session.query(Alert).filter_by(is_read=False).all()
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'ntp_service': ntp_status,
            'ntp_statistics': ntp_stats,
            'servers': servers_status,
            'alerts': {
                'active': len(active_alerts),
                'unread': len(unread_alerts)
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
        with get_db_session_with_context() as session:
            servers = session.query(NTPServer).filter_by(is_active=True).all()
            
            for server in servers:
                total_queries = session.query(NTPLog).filter(
                    NTPLog.server_id == server.id,
                    NTPLog.timestamp >= since
                ).count()
                
                successful_queries = session.query(NTPLog).filter(
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
            recent_alerts = session.query(Alert).filter(
                Alert.created_at >= since
            ).order_by(Alert.created_at.desc()).limit(10).all()
            
            recent_alerts_data = []
            for alert in recent_alerts:
                recent_alerts_data.append({
                    'id': alert.id,
                    'title': alert.title,
                    'message': alert.message,
                    'status': alert.status,
                    'severity': alert.severity,
                    'created_at': alert.created_at.isoformat() if alert.created_at else None,
                    'server_id': alert.server_id
                })
        
        return jsonify({
            'success': True,
            'period_hours': hours,
            'server_stats': server_stats,
            'recent_alerts': recent_alerts_data,
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
        
        with get_db_session_with_context() as session:
            query = session.query(Alert)
            if status != 'all':
                query = query.filter_by(status=status)
            
            alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
            
            alerts_data = []
            for alert in alerts:
                alerts_data.append({
                    'id': alert.id,
                    'title': alert.title,
                    'message': alert.message,
                    'status': alert.status,
                    'severity': alert.severity,
                    'created_at': alert.created_at.isoformat() if alert.created_at else None,
                    'server_id': alert.server_id
                })
        
        return jsonify({
            'success': True,
            'alerts': alerts_data,
            'total': len(alerts_data),
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
        
        # Test de la base de donnes avec syntaxe SQLAlchemy 2.x
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
        except Exception:
            health_status['database'] = 'error'
            health_status['overall'] = 'error'
        
        # Test du service NTP
        try:
            with get_db_session_with_context() as session:
                active_servers = session.query(NTPServer).filter_by(is_active=True).count()
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
        
        with get_db_session_with_context() as session:
            # Donnes des serveurs
            servers = session.query(NTPServer).filter_by(is_active=True).all()
            for server in servers:
                export_data['servers'].append({
                    'id': server.id,
                    'name': server.name,
                    'address': server.address,
                    'port': server.port,
                    'status': server.status,
                    'last_sync': server.last_sync.isoformat() if server.last_sync else None
                })
            
            # Logs rcents
            since = datetime.utcnow() - timedelta(hours=hours)
            logs = session.query(NTPLog).filter(NTPLog.timestamp >= since).order_by(NTPLog.timestamp.desc()).limit(1000).all()
            for log in logs:
                export_data['logs'].append({
                    'id': log.id,
                    'server_id': log.server_id,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'status': log.status,
                    'offset': log.offset,
                    'delay': log.delay
                })
            
            # Alertes rcentes
            alerts = session.query(Alert).filter(Alert.created_at >= since).order_by(Alert.created_at.desc()).all()
            for alert in alerts:
                export_data['alerts'].append({
                    'id': alert.id,
                    'title': alert.title,
                    'message': alert.message,
                    'status': alert.status,
                    'severity': alert.severity,
                    'created_at': alert.created_at.isoformat() if alert.created_at else None,
                    'server_id': alert.server_id
                })
        
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

@main_bp.route('/api/test/auth')
@login_required
def test_auth():
    """Route de test pour vrifier l'authentification API"""
    try:
        from flask_login import current_user
        return jsonify({
            'success': True,
            'authenticated': True,
            'user': current_user.username,
            'user_id': current_user.id,
            'roles': current_user.roles,
            'message': 'Authentification russie',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'authenticated': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500 
