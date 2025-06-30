"""
API WebSocket - Mises  jour temps rel
"""
import os
import time
import threading
import logging
from datetime import datetime, timedelta
from flask import request
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from backend.app import socketio
from backend.services.ntp_service import ntp_service
from backend.services.client_monitor_service import client_monitor_service
from backend.models.alert import Alert

logger = logging.getLogger(__name__)

# Variables globales pour le monitoring
active_connections = {}
background_tasks = {}

@socketio.on('connect')
def handle_connect():
    """Gestionnaire de connexion WebSocket"""
    try:
        logger.info(f"Nouvelle tentative de connexion WebSocket - SID: {request.sid}")
        
        # TEMPORAIRE: Debug auth
        if not current_user.is_authenticated:
            logger.warning("Connexion WebSocket refusée : utilisateur non authentifié")
            emit('auth_error', {'message': 'Non authentifié'})
            return False
        
        active_connections[request.sid] = {
            'user_id': current_user.id,
            'username': current_user.username,
            'connected_at': datetime.utcnow(),
            'role': current_user.role
        }
        
        join_room('authenticated')
        logger.info(f"Connexion WebSocket réussie: {current_user.username}")
        
        emit('connection_established', {
            'user': current_user.username,
            'role': current_user.role,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur connexion WebSocket: {e}")
        emit('connection_error', {'message': str(e)})
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """Gestionnaire de dconnexion WebSocket"""
    if request.sid in active_connections:
        user_info = active_connections[request.sid]
        del active_connections[request.sid]
        logger.info(f"Dconnexion WebSocket: {user_info['username']}")
    
    leave_room('authenticated')

@socketio.on('subscribe_realtime')
def handle_subscribe_realtime(data):
    """S'abonner aux mises  jour temps rel"""
    if not current_user.is_authenticated:
        return
    
    subscription_type = data.get('type', 'all')
    
    if subscription_type in ['dashboard', 'all']:
        join_room('dashboard_updates')
    
    if subscription_type in ['alerts', 'all']:
        join_room('alert_updates')
    
    if subscription_type in ['ntp', 'all']:
        join_room('ntp_updates')
    
    emit('subscription_confirmed', {
        'type': subscription_type,
        'timestamp': datetime.utcnow().isoformat()
    })

@socketio.on('unsubscribe_realtime')
def handle_unsubscribe_realtime(data):
    """Se dsabonner des mises  jour temps rel"""
    if not current_user.is_authenticated:
        return
    
    subscription_type = data.get('type', 'all')
    
    if subscription_type in ['dashboard', 'all']:
        leave_room('dashboard_updates')
    
    if subscription_type in ['alerts', 'all']:
        leave_room('alert_updates')
    
    if subscription_type in ['ntp', 'all']:
        leave_room('ntp_updates')

@socketio.on('request_ntp_query')
def handle_ntp_query_request(data):
    """Demande manuelle de requte NTP"""
    if not current_user.is_authenticated:
        return
    
    try:
        server_id = data.get('server_id')
        if server_id:
            from backend.models.ntp_server import NTPServer
            server = NTPServer.query.get(server_id)
            if server:
                result = ntp_service.query_server(server)
                emit('ntp_query_result', result)
        else:
            results = ntp_service.query_all_servers()
            emit('ntp_query_results', results)
    
    except Exception as e:
        logger.error(f"Erreur requte NTP: {e}")
        emit('error', {'message': str(e)})

def start_dashboard_updates(interval=30):
    """Dmarrer les mises  jour du dashboard"""
    if 'dashboard' in background_tasks:
        return
    
    def dashboard_worker():
        logger.info("Dmarrage du worker dashboard")
        
        while 'dashboard' in background_tasks:
            try:
                from app import app
                with app.app_context():
                    results = ntp_service.query_all_servers()
                    
                    dashboard_data = {
                        'ntp_queries': results,
                        'server_count': len(results),
                        'online_servers': len([r for r in results if r.get('status') == 'ok']),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    if active_connections:
                        socketio.emit('dashboard_update', dashboard_data, room='authenticated')
                        logger.debug(f"[DASHBOARD] Mise  jour envoye  {len(active_connections)} utilisateur(s)")
                    else:
                        logger.debug("[DASHBOARD] Collecte en arrire-plan")
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"[DASHBOARD] Erreur: {e}")
                time.sleep(30)
    
    background_tasks['dashboard'] = True
    thread = threading.Thread(target=dashboard_worker, daemon=True)
    thread.start()

def start_ntp_monitoring(interval=60):
    """Dmarrer le monitoring NTP automatique"""
    if 'ntp_monitoring' in background_tasks:
        return
    
    def ntp_monitoring_worker():
        logger.info("Dmarrage du monitoring NTP automatique")
        
        while 'ntp_monitoring' in background_tasks:
            try:
                from app import app
                with app.app_context():
                    results = ntp_service.query_all_servers()
                    system_stats = client_monitor_service.get_ntp_statistics()
                    
                    if active_connections:
                        socketio.emit('ntp_monitoring_update', {
                            'ntp_queries': results,
                            'system_stats': system_stats,
                            'timestamp': datetime.utcnow().isoformat()
                        }, room='authenticated')
                        logger.debug(f"[NTP_MONITORING] Mise  jour envoye")
                    else:
                        logger.debug("[NTP_MONITORING] Monitoring en arrire-plan")
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"[NTP_MONITORING] Erreur: {e}")
                time.sleep(30)
    
    background_tasks['ntp_monitoring'] = True
    thread = threading.Thread(target=ntp_monitoring_worker, daemon=True)
    thread.start()

def start_client_monitoring(interval=30):
    """Dmarrer le monitoring des clients"""
    if 'client_monitoring' in background_tasks:
        return
    
    def client_monitoring_worker():
        logger.info("Dmarrage du monitoring clients NTP")
        
        while 'client_monitoring' in background_tasks:
            try:
                from app import app
                with app.app_context():
                    connections = client_monitor_service.get_active_connections()
                    client_stats = client_monitor_service.get_client_statistics(1)
                    service_status = client_monitor_service.get_service_status()
                    
                    if active_connections:
                        socketio.emit('client_monitoring_update', {
                            'active_connections': connections,
                            'client_stats': client_stats,
                            'service_status': service_status,
                            'timestamp': datetime.utcnow().isoformat()
                        }, room='authenticated')
                        logger.debug(f"[CLIENT_MONITORING] Mise  jour envoye")
                    else:
                        logger.debug("[CLIENT_MONITORING] Monitoring en arrire-plan")
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"[CLIENT_MONITORING] Erreur: {e}")
                time.sleep(30)
    
    background_tasks['client_monitoring'] = True
    thread = threading.Thread(target=client_monitoring_worker, daemon=True)
    thread.start()

def send_alert_notification(alert):
    """Envoyer une notification d'alerte via WebSocket"""
    try:
        socketio.emit('new_alert', {
            'alert': alert.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        }, room='authenticated')
        
        logger.info(f"Notification d'alerte envoye: {alert.title}")
        
    except Exception as e:
        logger.error(f"Erreur envoi notification alerte: {e}")

def send_server_status_update(server):
    """Envoyer une mise  jour de status de serveur"""
    try:
        socketio.emit('server_status_update', {
            'server': server.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        }, room='authenticated')
        
    except Exception as e:
        logger.error(f"Erreur envoi mise  jour serveur: {e}")

def stop_background_task(task_name):
    """Arrter une tche en arrire-plan"""
    if task_name in background_tasks:
        del background_tasks[task_name]
        logger.info(f"Tche arrte: {task_name}")

def stop_all_background_tasks():
    """Arrter toutes les tches en arrire-plan"""
    for task_name in list(background_tasks.keys()):
        stop_background_task(task_name)
    logger.info("Toutes les tches arrtes")

@socketio.on('ping')
def handle_ping():
    """Rpondre au ping"""
    emit('pong', {'timestamp': datetime.utcnow().isoformat()})

@socketio.on('get_server_details')
def handle_get_server_details(data):
    """Rcuprer les dtails d'un serveur"""
    if not current_user.is_authenticated:
        return
    
    server_id = data.get('server_id')
    
    try:
        from backend.models.ntp_server import NTPServer
        server = NTPServer.query.get(server_id)
        
        if not server:
            emit('error', {'message': 'Serveur non trouv'})
            return
        
        stats = ntp_service.get_server_statistics(server_id, 24)
        
        emit('server_details', {
            'server': server.to_dict(),
            'statistics': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur rcupration dtails serveur: {e}")
        emit('error', {'message': str(e)})

def start_all_background_workers():
    """Dmarrer tous les workers de monitoring"""
    logger.info("DMARRAGE AUTOMATIQUE DES WORKERS DE MONITORING")
    
    try:
        start_dashboard_updates(30)
        logger.info("Worker dashboard dmarr (30s)")
        
        start_ntp_monitoring(60)
        logger.info("Worker NTP monitoring dmarr (60s)")
        
        start_client_monitoring(30)
        logger.info("Worker client monitoring dmarr (30s)")
        
        logger.info("TOUS LES WORKERS DMARRS - MONITORING AUTONOME ACTIF")
        
    except Exception as e:
        logger.error(f"Erreur dmarrage workers: {e}")

def initialize_background_monitoring():
    """Fonction d'initialisation pour app.py"""
    import threading
    import time
    
    def delayed_start():
        time.sleep(5)
        start_all_background_workers()
    
    init_thread = threading.Thread(target=delayed_start, daemon=True)
    init_thread.start()
    logger.info("Initialisation des workers programme")
