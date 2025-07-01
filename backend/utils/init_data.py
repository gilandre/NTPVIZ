"""
Initialisation des données par défaut - VERSION CORRIGÉE
"""
import logging
from datetime import datetime
from backend.database_manager import get_db_session_with_context, db_manager
from backend.models.user import User
from backend.models.ntp_server import NTPServer
from backend.models.system_config import SystemConfig

logger = logging.getLogger(__name__)

def init_default_data():
    """Initialise les données par défaut"""
    try:
        logger.info("🚀 Initialisation des données par défaut...")
        
        # Vérifier que le Database Manager est initialisé
        if not db_manager.initialized:
            logger.info("Initialisation du Database Manager...")
            if not db_manager.initialize():
                logger.error("Échec initialisation Database Manager")
                return False
        
        with get_db_session_with_context() as session:
            # Vérifier si l'utilisateur admin existe déjà
            admin_user = session.query(User).filter_by(username='admin').first()
            
            if not admin_user:
                logger.info("Création de l'utilisateur administrateur par défaut...")
                admin_user = User(
                    username='admin',
                    email='admin@ntp-monitor.local',
                    first_name='Administrateur',
                    last_name='Système',
                    role='admin',
                    is_active=True
                )
                admin_user.set_password('admin123')
                session.add(admin_user)
                logger.info("✅ Utilisateur admin créé")
            else:
                logger.info("✅ Utilisateur admin existe déjà")
            
            # Vérifier si l'utilisateur opérateur existe
            operator_user = session.query(User).filter_by(username='operator').first()
            
            if not operator_user:
                logger.info("Création de l'utilisateur opérateur par défaut...")
                operator_user = User(
                    username='operator',
                    email='operator@ntp-monitor.local',
                    first_name='Opérateur',
                    last_name='Système',
                    role='operator',
                    is_active=True
                )
                operator_user.set_password('operator123')
                session.add(operator_user)
                logger.info("✅ Utilisateur operator créé")
            else:
                logger.info("✅ Utilisateur operator existe déjà")
            
            # Vérifier si l'utilisateur visualiseur existe
            viewer_user = session.query(User).filter_by(username='viewer').first()
            
            if not viewer_user:
                logger.info("Création de l'utilisateur visualiseur par défaut...")
                viewer_user = User(
                    username='viewer',
                    email='viewer@ntp-monitor.local',
                    first_name='Visualiseur',
                    last_name='Système',
                    role='viewer',
                    is_active=True
                )
                viewer_user.set_password('viewer123')
                session.add(viewer_user)
                logger.info("✅ Utilisateur viewer créé")
            else:
                logger.info("✅ Utilisateur viewer existe déjà")
            
            # Ajouter les serveurs NTP par défaut
            default_servers = [
                {'name': 'Pool NTP 0', 'address': '0.pool.ntp.org', 'port': 123, 'priority': 1},
                {'name': 'Pool NTP 1', 'address': '1.pool.ntp.org', 'port': 123, 'priority': 2},
                {'name': 'Pool NTP 2', 'address': '2.pool.ntp.org', 'port': 123, 'priority': 3},
                {'name': 'Pool NTP 3', 'address': '3.pool.ntp.org', 'port': 123, 'priority': 4},
                {'name': 'Serveur Temps France', 'address': 'ntp.pool.ntp.org', 'port': 123, 'priority': 5},
                {'name': 'Serveur de secours', 'address': 'time.cloudflare.com', 'port': 123, 'priority': 6}
            ]
            
            for server_data in default_servers:
                existing_server = session.query(NTPServer).filter_by(address=server_data['address']).first()
                
                if not existing_server:
                    server = NTPServer(
                        name=server_data['name'],
                        address=server_data['address'],
                        server_type='global',
                        port=server_data['port'],
                        priority=server_data['priority'],
                        is_active=True
                    )
                    session.add(server)
                    logger.info(f"✅ Serveur NTP {server_data['name']} ajouté")
                else:
                    logger.info(f"✅ Serveur NTP {server_data['name']} existe déjà")
            
            # Configuration système par défaut
            config_entries = [
                {'key': 'ntp_sync_interval', 'value': '300', 'description': 'Intervalle de synchronisation NTP (secondes)'},
                {'key': 'alert_threshold_offset', 'value': '5000', 'description': 'Seuil d\'alerte pour le décalage temporel (ms)'},
                {'key': 'dashboard_refresh_rate', 'value': '30', 'description': 'Taux de rafraichissement du dashboard (secondes)'},
                {'key': 'log_retention_days', 'value': '30', 'description': 'Durée de rétention des logs (jours)'},
                {'key': 'email_notifications', 'value': 'false', 'description': 'Notifications par email activées'},
                {'key': 'monitoring_enabled', 'value': 'true', 'description': 'Monitoring automatique activé'}
            ]
            
            for config_data in config_entries:
                existing_config = session.query(SystemConfig).filter_by(key=config_data['key']).first()
                
                if not existing_config:
                    config = SystemConfig(
                        key=config_data['key'],
                        value=config_data['value'],
                        description=config_data['description']
                    )
                    session.add(config)
                    logger.info(f"✅ Configuration {config_data['key']} ajoutée")
                else:
                    logger.info(f"✅ Configuration {config_data['key']} existe déjà")
            
            # Valider les changements
            session.commit()
            logger.info("✅ Données par défaut initialisées avec succès")
            return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation des données: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_database_info():
    """Récupérer les informations sur la base de données"""
    try:
        with get_db_session_with_context() as session:
            info = {
                'users_count': session.query(User).count(),
                'ntp_servers_count': session.query(NTPServer).count(),
                'active_servers_count': session.query(NTPServer).filter_by(is_active=True).count(),
                'system_configs_count': session.query(SystemConfig).count(),
                'database_type': 'MySQL',
                'database_name': 'ntp_monitor'
            }
            
            return info
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des infos DB: {e}")
        return {
            'users_count': 0,
            'ntp_servers_count': 0, 
            'active_servers_count': 0,
            'system_configs_count': 0,
            'database_type': 'Unknown',
            'database_name': 'Unknown',
            'error': str(e)
        } 