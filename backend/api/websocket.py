"""
API WebSocket - Mises à jour temps réel
VERSION CORRIGÉE - Évite les redémarrages en boucle
"""
import os
import time
import threading
import logging
import json
from datetime import datetime, timedelta
from flask import request, current_app
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from backend.app import socketio
from backend.services.ntp_service import ntp_service
from backend.services.client_monitor_service import client_monitor_service
from backend.database import Alert

logger = logging.getLogger(__name__)

# Variables globales pour le monitoring
active_connections = {}
background_tasks = {}

def serialize_datetime(obj):
    """Sérialiser les objets datetime pour JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    else:
        return obj

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
    """Gestionnaire de déconnexion WebSocket"""
    try:
        if request.sid in active_connections:
            user_info = active_connections[request.sid]
            logger.info(f"Déconnexion WebSocket: {user_info['username']}")
            del active_connections[request.sid]
        
        leave_room('authenticated')
        
    except Exception as e:
        logger.error(f"Erreur déconnexion WebSocket: {e}")

@socketio.on('subscribe_realtime')
def handle_subscribe_realtime(data):
    """S'abonner aux mises à jour temps réel"""
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
    """Se désabonner des mises à jour temps réel"""
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
            from backend.database import NTPServer
            from backend.database_manager import get_db_session_with_context
            
            with get_db_session_with_context() as session:
                server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
                if server:
                    result = ntp_service.query_server(server)
                    emit('ntp_query_result', result)
        else:
            results = ntp_service.query_all_servers()
            emit('ntp_query_results', results)
    
    except Exception as e:
        logger.error(f"Erreur requte NTP: {e}")
        emit('error', {'message': str(e)})

@socketio.on('ping')
def handle_ping():
    """Gestionnaire de ping pour maintenir la connexion"""
    emit('pong', {'timestamp': datetime.utcnow().isoformat()})

@socketio.on('get_dashboard_data')
def handle_get_dashboard_data():
    """Envoyer les données du dashboard à la demande"""
    try:
        if not current_user.is_authenticated:
            emit('auth_error', {'message': 'Non authentifié'})
            return
        
        # Récupérer les données sans créer une nouvelle app
        results = ntp_service.query_all_servers()
        
        # Sérialiser les objets datetime
        serialized_results = serialize_datetime(results)
        
        dashboard_data = {
            'ntp_queries': serialized_results,
            'server_count': len(results),
            'online_servers': len([r for r in results if r.get('status') == 'ok']),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        emit('dashboard_update', dashboard_data)
        
    except Exception as e:
        logger.error(f"Erreur récupération données dashboard: {e}")
        emit('dashboard_error', {'message': str(e)})

@socketio.on('get_ntp_data')
def handle_get_ntp_data():
    """Envoyer les données NTP à la demande"""
    try:
        if not current_user.is_authenticated:
            emit('auth_error', {'message': 'Non authentifié'})
            return
        
        # Récupérer les données sans créer une nouvelle app
        results = ntp_service.query_all_servers()
        system_stats = client_monitor_service.get_ntp_statistics()
        
        # Sérialiser les objets datetime
        serialized_results = serialize_datetime(results)
        serialized_stats = serialize_datetime(system_stats)
        
        emit('ntp_monitoring_update', {
            'ntp_queries': serialized_results,
            'system_stats': serialized_stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération données NTP: {e}")
        emit('ntp_error', {'message': str(e)})

@socketio.on('get_client_data')
def handle_get_client_data():
    """Envoyer les données clients à la demande"""
    try:
        if not current_user.is_authenticated:
            emit('auth_error', {'message': 'Non authentifié'})
            return
        
        # Récupérer les données sans créer une nouvelle app
        connections = client_monitor_service.get_active_connections()
        client_stats = client_monitor_service.get_client_statistics(1)
        service_status = client_monitor_service.get_service_status()
        
        # Sérialiser les objets datetime
        serialized_connections = serialize_datetime(connections)
        serialized_client_stats = serialize_datetime(client_stats)
        serialized_service_status = serialize_datetime(service_status)
        
        emit('client_monitoring_update', {
            'active_connections': serialized_connections,
            'client_stats': serialized_client_stats,
            'service_status': serialized_service_status,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération données clients: {e}")
        emit('client_error', {'message': str(e)})

# VERSION CORRIGÉE - Workers simplifiés sans création d'app

def start_dashboard_updates(interval=30):
    """Démarrer les mises à jour du dashboard - VERSION CORRIGÉE"""
    if 'dashboard' in background_tasks:
        return
    
    def dashboard_worker():
        logger.info("Démarrage du worker dashboard")
        logger.info("🔄 Worker dashboard démarré - boucle de monitoring active")
        
        while 'dashboard' in background_tasks:
            try:
                # Ne pas créer d'app, utiliser les services directement
                results = ntp_service.query_all_servers()
                
                # Sérialiser les objets datetime
                serialized_results = serialize_datetime(results)
                
                dashboard_data = {
                    'ntp_queries': serialized_results,
                    'server_count': len(results),
                    'online_servers': len([r for r in results if r.get('status') == 'ok']),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                if active_connections:
                    socketio.emit('dashboard_update', dashboard_data, room='authenticated')
                    logger.debug(f"[DASHBOARD] Mise à jour envoyée à {len(active_connections)} utilisateur(s)")
                else:
                    logger.debug("[DASHBOARD] Collecte en arrière-plan")
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"[DASHBOARD] Erreur: {e}")
                time.sleep(30)
    
    background_tasks['dashboard'] = True
    thread = threading.Thread(target=dashboard_worker, daemon=True)
    thread.start()

def start_ntp_monitoring(interval=60):
    """Démarrer le monitoring NTP automatique - VERSION CORRIGÉE"""
    if 'ntp_monitoring' in background_tasks:
        return
    
    def ntp_monitoring_worker():
        logger.info("Démarrage du monitoring NTP automatique")
        logger.info("🔄 Worker NTP monitoring démarré - boucle de monitoring active")
        
        while 'ntp_monitoring' in background_tasks:
            try:
                # Ne pas créer d'app, utiliser les services directement
                results = ntp_service.query_all_servers()
                system_stats = client_monitor_service.get_ntp_statistics()
                
                # Sérialiser les objets datetime
                serialized_results = serialize_datetime(results)
                serialized_stats = serialize_datetime(system_stats)
                
                ntp_data = {
                    'ntp_queries': serialized_results,
                    'system_stats': serialized_stats,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                if active_connections:
                    socketio.emit('ntp_monitoring_update', ntp_data, room='authenticated')
                    logger.debug(f"[NTP_MONITORING] Mise à jour envoyée")
                else:
                    logger.debug("[NTP_MONITORING] Monitoring en arrière-plan")
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"[NTP_MONITORING] Erreur: {e}")
                time.sleep(30)
    
    background_tasks['ntp_monitoring'] = True
    thread = threading.Thread(target=ntp_monitoring_worker, daemon=True)
    thread.start()

def start_client_monitoring(interval=30):
    """Démarrer le monitoring des clients - VERSION CORRIGÉE"""
    if 'client_monitoring' in background_tasks:
        return
    
    def client_monitoring_worker():
        logger.info("Démarrage du monitoring clients NTP")
        logger.info("🔄 Worker client monitoring démarré - boucle de monitoring active")
        
        while 'client_monitoring' in background_tasks:
            try:
                # Ne pas créer d'app, utiliser les services directement
                connections = client_monitor_service.get_active_connections()
                client_stats = client_monitor_service.get_client_statistics(1)
                service_status = client_monitor_service.get_service_status()
                
                # Sérialiser les objets datetime
                serialized_connections = serialize_datetime(connections)
                serialized_client_stats = serialize_datetime(client_stats)
                serialized_service_status = serialize_datetime(service_status)
                
                client_data = {
                    'active_connections': serialized_connections,
                    'client_stats': serialized_client_stats,
                    'service_status': serialized_service_status,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                if active_connections:
                    socketio.emit('client_monitoring_update', client_data, room='authenticated')
                    logger.debug(f"[CLIENT_MONITORING] Mise à jour envoyée")
                else:
                    logger.debug("[CLIENT_MONITORING] Monitoring en arrière-plan")
                
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
        
        logger.info(f"Notification d'alerte envoyée: {alert.title}")
        
    except Exception as e:
        logger.error(f"Erreur envoi notification alerte: {e}")

def send_server_status_update(server):
    """Envoyer une mise à jour de status de serveur"""
    try:
        socketio.emit('server_status_update', {
            'server': server.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        }, room='authenticated')
        
    except Exception as e:
        logger.error(f"Erreur envoi mise à jour serveur: {e}")

def stop_background_task(task_name):
    """Arrêter une tâche en arrière-plan"""
    if task_name in background_tasks:
        del background_tasks[task_name]
        logger.info(f"Tâche arrêtée: {task_name}")

def stop_all_background_tasks():
    """Arrêter toutes les tâches en arrière-plan"""
    for task_name in list(background_tasks.keys()):
        stop_background_task(task_name)
    logger.info("Toutes les tâches arrêtées")

@socketio.on('get_server_details')
def handle_get_server_details(data):
    """Récuprer les détails d'un serveur"""
    if not current_user.is_authenticated:
        return
    
    server_id = data.get('server_id')
    
    try:
        from backend.database import NTPServer
        from backend.database_manager import get_db_session_with_context
        
        with get_db_session_with_context() as session:
            server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
            
            if not server:
                emit('error', {'message': 'Serveur non trouvé'})
                return
            
            stats = ntp_service.get_server_statistics(server_id, 24)
            
            emit('server_details', {
                'server': {
                    'id': server.id,
                    'name': server.name,
                    'address': server.address,
                    'status': server.status,
                    'is_active': server.is_active,
                    'last_sync': server.last_sync.isoformat() if server.last_sync else None,
                    'last_offset': server.last_offset,
                    'last_latency': server.last_latency,
                    'last_stratum': server.last_stratum
                },
                'statistics': stats,
                'timestamp': datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Erreur récupération détails serveur: {e}")
        emit('error', {'message': str(e)})

def get_active_connections_count():
    """Obtenir le nombre de connexions actives"""
    return len(active_connections)

def get_background_tasks_status():
    """Obtenir le statut des tâches en arrière-plan"""
    return {
        'active_tasks': list(background_tasks.keys()),
        'task_count': len(background_tasks),
        'active_connections': len(active_connections)
    }

@socketio.on('get_system_status')
def handle_get_system_status():
    """Obtenir le statut du système"""
    try:
        if not current_user.is_authenticated:
            emit('auth_error', {'message': 'Non authentifié'})
            return
        
        status = get_background_tasks_status()
        emit('system_status', status)
        
    except Exception as e:
        logger.error(f"Erreur récupération statut système: {e}")
        emit('system_error', {'message': str(e)})

def start_all_background_workers():
    """Démarrer tous les workers de monitoring - VERSION CORRIGÉE"""
    logger.info("DÉMARRAGE AUTOMATIQUE DES WORKERS DE MONITORING")
    
    try:
        start_dashboard_updates(30)
        logger.info("Worker dashboard démarré (30s)")
        
        start_ntp_monitoring(60)
        logger.info("Worker NTP monitoring démarré (60s)")
        
        start_client_monitoring(30)
        logger.info("Worker client monitoring démarré (30s)")
        
        logger.info("TOUS LES WORKERS DÉMARRÉS - MONITORING AUTONOME ACTIF")
        
    except Exception as e:
        logger.error(f"Erreur démarrage workers: {e}")

def initialize_background_monitoring():
    """Fonction d'initialisation pour app.py - VERSION CORRIGÉE"""
    import threading
    import time
    
    def delayed_start():
        logger.info("⏰ Démarrage différé des workers (5 secondes)...")
        time.sleep(5)
        logger.info("🚀 Lancement des workers de monitoring...")
        start_all_background_workers()
    
    init_thread = threading.Thread(target=delayed_start, daemon=True)
    init_thread.start()
    logger.info("Initialisation des workers programmée")
