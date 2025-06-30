"""
API WebSocket - Mises  jour temps rel
"""
from flask import Blueprint
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from backend.app import socketio
from backend.services.ntp_service import ntp_service
from backend.services.client_monitor_service import client_monitor_service
from backend.models.alert import Alert
from datetime import datetime, timedelta
import logging
import threading
import time

logger = logging.getLogger(__name__)

websocket_bp = Blueprint('websocket', __name__)

# Variables globales pour les tches en arrire-plan
background_tasks = {}
active_connections = set()

@socketio.on('connect')
def handle_connect():
    """Gestion de la connexion WebSocket"""
    if not current_user.is_authenticated:
        logger.warning("Tentative de connexion WebSocket non authentifie")
        disconnect()
        return False
    
    active_connections.add(current_user.id)
    
    # Rejoindre les rooms selon les permissions
    join_room('authenticated')
    
    if current_user.can_configure:
        join_room('operators')
    
    if current_user.is_admin:
        join_room('admins')
    
    logger.info(f"WebSocket connect: {current_user.username}")
    
    # Envoyer les donnes initiales
    emit('connection_established', {
        'message': 'Connexion WebSocket tablie',
        'user': current_user.username,
        'timestamp': datetime.utcnow().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Gestion de la dconnexion WebSocket"""
    if current_user.is_authenticated:
        active_connections.discard(current_user.id)
        
        # Quitter les rooms
        leave_room('authenticated')
        if current_user.can_configure:
            leave_room('operators')
        if current_user.is_admin:
            leave_room('admins')
        
        logger.info(f"WebSocket dconnect: {current_user.username}")

@socketio.on('subscribe_realtime')
def handle_subscribe_realtime(data):
    """S'abonner aux mises  jour temps rel"""
    if not current_user.is_authenticated:
        disconnect()
        return
    
    subscription_type = data.get('type', 'dashboard')
    interval = data.get('interval', 30)
    
    logger.info(f"Abonnement temps rel: {current_user.username} -> {subscription_type}")
    
    # Dmarrer la tche en arrire-plan si ncessaire
    if subscription_type == 'dashboard' and subscription_type not in background_tasks:
        start_dashboard_updates(interval)
    elif subscription_type == 'ntp_monitoring':
        start_ntp_monitoring(interval)
    elif subscription_type == 'client_monitoring':
        start_client_monitoring(interval)
    
    emit('subscription_confirmed', {
        'type': subscription_type,
        'interval': interval,
        'timestamp': datetime.utcnow().isoformat()
    })

@socketio.on('unsubscribe_realtime')
def handle_unsubscribe_realtime(data):
    """Se dsabonner des mises  jour temps rel"""
    if not current_user.is_authenticated:
        return
    
    subscription_type = data.get('type', 'dashboard')
    
    logger.info(f"Dsabonnement temps rel: {current_user.username} <- {subscription_type}")
    
    emit('unsubscription_confirmed', {
        'type': subscription_type,
        'timestamp': datetime.utcnow().isoformat()
    })

@socketio.on('request_ntp_query')
def handle_ntp_query_request(data):
    """Requte NTP manuelle"""
    if not current_user.is_authenticated:
        disconnect()
        return
    
    try:
        results = ntp_service.query_all_servers()
        emit('ntp_query_results', {
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur requte NTP WebSocket: {e}")
        emit('error', {'message': str(e)})

def start_dashboard_updates(interval=30):
    """Dmarrer les mises  jour du dashboard"""
    if 'dashboard' in background_tasks:
        return
    
    def dashboard_worker():
        logger.info("Dmarrage des mises  jour dashboard temps rel")
        
        while 'dashboard' in background_tasks:
            try:
                if active_connections:
                    results = ntp_service.query_all_servers()
                    system_time = ntp_service.get_system_time()
                    
                    recent_alerts = Alert.query.filter(
                        Alert.created_at >= datetime.utcnow() - timedelta(minutes=5)
                    ).order_by(Alert.created_at.desc()).limit(5).all()
                    
                    socketio.emit('dashboard_update', {
                        'servers': results,
                        'system_time': system_time,
                        'recent_alerts': [alert.to_dict() for alert in recent_alerts],
                        'timestamp': datetime.utcnow().isoformat()
                    }, room='authenticated')
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Erreur mise  jour dashboard: {e}")
                time.sleep(10)
    
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
                if active_connections:
                    # Monitoring complet
                    results = ntp_service.query_all_servers()
                    
                    # Statistiques systme
                    system_stats = client_monitor_service.get_ntp_statistics()
                    
                    # Envoyer les mises  jour
                    socketio.emit('ntp_monitoring_update', {
                        'ntp_queries': results,
                        'system_stats': system_stats,
                        'timestamp': datetime.utcnow().isoformat()
                    }, room='authenticated')
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Erreur monitoring NTP: {e}")
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
                if active_connections:
                    # Connexions actives
                    connections = client_monitor_service.get_active_connections()
                    
                    # Statistiques clients
                    client_stats = client_monitor_service.get_client_statistics(1)  # Dernire heure
                    
                    # Status du service
                    service_status = client_monitor_service.get_service_status()
                    
                    # Envoyer les mises  jour
                    socketio.emit('client_monitoring_update', {
                        'active_connections': connections,
                        'client_stats': client_stats,
                        'service_status': service_status,
                        'timestamp': datetime.utcnow().isoformat()
                    }, room='authenticated')
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Erreur monitoring clients: {e}")
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
    logger.info("Toutes les tches en arrire-plan arrtes")

# Gestionnaire d'vnements personnaliss
@socketio.on('ping')
def handle_ping():
    """Rpondre au ping pour vrifier la connexion"""
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
        
        # Statistiques rcentes
        stats = ntp_service.get_server_statistics(server_id, 24)
        
        emit('server_details', {
            'server': server.to_dict(),
            'statistics': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur rcupration dtails serveur: {e}")
        emit('error', {'message': str(e)}) 
