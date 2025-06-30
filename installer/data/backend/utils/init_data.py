"""
Initialisation des donnes de base
"""
from backend.models.user import User
from backend.models.ntp_server import NTPServer
from backend.models.system_config import SystemConfig
from backend.app import db
from werkzeug.security import generate_password_hash
from config.config import Config
import logging

logger = logging.getLogger(__name__)

def init_default_data():
    """Initialiser les donnes par dfaut"""
    try:
        logger.info("Initialisation des donnes par dfaut...")
        
        # Crer l'utilisateur admin par dfaut
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@ntp-monitor.local',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                is_active=True
            )
            db.session.add(admin_user)
            logger.info("Utilisateur admin cr (admin/admin123)")
        
        # Crer les serveurs NTP par dfaut (4 pools + 1 local)
        for i, server_config in enumerate(Config.NTP_DEFAULT_SERVERS):
            existing_server = NTPServer.query.filter_by(address=server_config['address']).first()
            if not existing_server:
                ntp_server = NTPServer(
                    name=server_config['name'],
                    address=server_config['address'],
                    port=123,
                    server_type=server_config['type'],
                    description=server_config['description'],
                    is_active=True,
                    priority=i + 1,
                    timeout=10,
                    max_offset=1.0,
                    critical_offset=5.0
                )
                db.session.add(ntp_server)
                logger.info(f"Serveur NTP cr: {server_config['name']} ({server_config['address']})")
        
        # Configuration systme par dfaut
        system_configs = [
            {
                'key': 'monitoring_enabled',
                'value': 'true',
                'description': 'Activer le monitoring NTP'
            },
            {
                'key': 'alert_email_enabled',
                'value': 'false',
                'description': 'Activer les alertes par email'
            },
            {
                'key': 'query_interval',
                'value': '60',
                'description': 'Intervalle de requte NTP (secondes)'
            },
            {
                'key': 'max_offset_threshold',
                'value': '1.0',
                'description': 'Seuil d\'cart maximum (secondes)'
            },
            {
                'key': 'critical_offset_threshold',
                'value': '5.0',
                'description': 'Seuil d\'cart critique (secondes)'
            },
            {
                'key': 'client_monitoring_enabled',
                'value': 'true',
                'description': 'Activer le monitoring des clients'
            },
            {
                'key': 'dashboard_auto_refresh',
                'value': '30',
                'description': 'Intervalle de rafrachissement du dashboard (secondes)'
            },
            {
                'key': 'log_retention_days',
                'value': '30',
                'description': 'Dure de conservation des logs (jours)'
            }
        ]
        
        for config_data in system_configs:
            existing_config = SystemConfig.query.filter_by(key=config_data['key']).first()
            if not existing_config:
                config = SystemConfig(
                    key=config_data['key'],
                    value=config_data['value'],
                    description=config_data['description']
                )
                db.session.add(config)
                logger.info(f"Configuration systme cre: {config_data['key']}")
        
        # Sauvegarder les modifications
        db.session.commit()
        logger.info("Donnes par dfaut initialises avec succs")
        
        # Rsum des serveurs crs
        servers = NTPServer.query.filter_by(is_active=True).all()
        logger.info(f"Serveurs NTP configurs ({len(servers)}):")
        for server in servers:
            logger.info(f"  - {server.name}: {server.address} ({server.server_type})")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation des donnes: {e}")
        db.session.rollback()
        return False

def update_ntp_servers():
    """Mettre  jour les serveurs NTP avec la nouvelle configuration"""
    try:
        logger.info("Mise  jour des serveurs NTP...")
        
        # Dsactiver les anciens serveurs
        old_servers = NTPServer.query.filter(
            ~NTPServer.address.in_([s['address'] for s in Config.NTP_DEFAULT_SERVERS])
        ).all()
        
        for server in old_servers:
            server.is_active = False
            logger.info(f"Serveur dsactiv: {server.name} ({server.address})")
        
        # Crer ou mettre  jour les nouveaux serveurs
        for i, server_config in enumerate(Config.NTP_DEFAULT_SERVERS):
            existing_server = NTPServer.query.filter_by(address=server_config['address']).first()
            
            if existing_server:
                # Mettre  jour le serveur existant
                existing_server.name = server_config['name']
                existing_server.server_type = server_config['type']
                existing_server.description = server_config['description']
                existing_server.is_active = True
                existing_server.priority = i + 1
                logger.info(f"Serveur mis  jour: {server_config['name']} ({server_config['address']})")
            else:
                # Crer un nouveau serveur
                ntp_server = NTPServer(
                    name=server_config['name'],
                    address=server_config['address'],
                    port=123,
                    server_type=server_config['type'],
                    description=server_config['description'],
                    is_active=True,
                    priority=i + 1,
                    timeout=10,
                    max_offset=1.0,
                    critical_offset=5.0
                )
                db.session.add(ntp_server)
                logger.info(f"Nouveau serveur cr: {server_config['name']} ({server_config['address']})")
        
        db.session.commit()
        logger.info("Mise  jour des serveurs NTP termine")
        
        # Afficher la configuration actuelle
        active_servers = NTPServer.query.filter_by(is_active=True).order_by(NTPServer.priority).all()
        logger.info(f"Serveurs NTP actifs ({len(active_servers)}):")
        for server in active_servers:
            logger.info(f"  {server.priority}. {server.name}: {server.address} ({server.server_type})")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise  jour des serveurs NTP: {e}")
        db.session.rollback()
        return False

def clean_old_data():
    """Nettoyer les anciennes donnes"""
    try:
        logger.info("Nettoyage des anciennes donnes...")
        
        # Supprimer les logs anciens (plus de 30 jours)
        from datetime import datetime, timedelta
        from backend.models.ntp_log import NTPLog
        
        retention_days = int(SystemConfig.get_value('log_retention_days', '30'))
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        old_logs = NTPLog.query.filter(NTPLog.timestamp < cutoff_date).all()
        for log in old_logs:
            db.session.delete(log)
        
        if old_logs:
            logger.info(f"Suppression de {len(old_logs)} logs anciens")
        
        # Supprimer les alertes rsolues anciennes (plus de 7 jours)
        from backend.models.alert import Alert
        
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        old_alerts = Alert.query.filter(
            Alert.status == 'resolved',
            Alert.created_at < cutoff_date
        ).all()
        
        for alert in old_alerts:
            db.session.delete(alert)
        
        if old_alerts:
            logger.info(f"Suppression de {len(old_alerts)} alertes rsolues anciennes")
        
        db.session.commit()
        logger.info("Nettoyage termin")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage: {e}")
        db.session.rollback()
        return False

def reset_database():
    """Rinitialiser compltement la base de donnes (ATTENTION!)"""
    try:
        logger.warning("ATTENTION: Rinitialisation complte de la base de donnes")
        
        # Supprimer toutes les tables
        db.drop_all()
        
        # Recrer les tables
        db.create_all()
        
        # Rinitialiser les donnes par dfaut
        init_default_data()
        
        logger.info("Base de donnes rinitialise avec succs")
        
    except Exception as e:
        logger.error(f"Erreur lors de la rinitialisation: {e}")
        raise

def create_test_data():
    """Crer des donnes de test pour le dveloppement UNIQUEMENT"""
    try:
        from flask import current_app
        
        # Ne crer des donnes de test qu'en mode dveloppement
        if current_app.config.get('ENV', 'production') == 'production':
            logger.info("Mode production dtect - Aucune donne de test cre")
            return False
        
        if not current_app.debug and not current_app.config.get('TESTING', False):
            logger.info("Mode production ou non-debug dtect - Aucune donne de test cre")
            return False
        
        logger.info("Mode dveloppement dtect - Cration des donnes de test...")
        
        # Crer des utilisateurs de test UNIQUEMENT en dveloppement
        test_users = [
            {'username': 'operator', 'email': 'operator@test.com', 'role': 'operator', 'password': 'operator123'},
            {'username': 'viewer', 'email': 'viewer@test.com', 'role': 'viewer', 'password': 'viewer123'}
        ]
        
        for user_data in test_users:
            if not User.query.filter_by(username=user_data['username']).first():
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    role=user_data['role']
                )
                user.first_name = user_data['role'].capitalize()
                user.last_name = 'Test'
                db.session.add(user)
        
        # Crer des serveurs NTP de test supplmentaires UNIQUEMENT en dveloppement
        test_servers = [
            {'name': 'Test Local 1', 'address': '192.168.1.100', 'type': 'local'},
            {'name': 'Test Local 2', 'address': '10.0.0.100', 'type': 'local'},
        ]
        
        for server_data in test_servers:
            if not NTPServer.query.filter_by(address=server_data['address']).first():
                server = NTPServer(
                    name=server_data['name'],
                    address=server_data['address'],
                    server_type=server_data['type'],
                    priority=99,
                    description=f"Serveur de test {server_data['type']} - DVELOPPEMENT UNIQUEMENT",
                    is_active=False  # Dsactiv par dfaut
                )
                db.session.add(server)
        
        db.session.commit()
        logger.info("Donnes de test cres (MODE DVELOPPEMENT)")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la cration des donnes de test: {e}")
        return False

def get_database_info():
    """Rcuprer les informations sur la base de donnes"""
    try:
        info = {
            'users_count': User.query.count(),
            'ntp_servers_count': NTPServer.query.count(),
            'active_servers_count': NTPServer.query.filter_by(is_active=True).count(),
            'system_configs_count': SystemConfig.query.count(),
            'database_url': current_app.config.get('SQLALCHEMY_DATABASE_URI', 'Unknown')
        }
        
        # Masquer les mots de passe dans l'URL
        if 'password' in info['database_url']:
            parts = info['database_url'].split('@')
            if len(parts) > 1:
                user_part = parts[0].split('://')[1]
                if ':' in user_part:
                    user, _ = user_part.split(':', 1)
                    info['database_url'] = info['database_url'].replace(user_part, f"{user}:***")
        
        return info
        
    except Exception as e:
        logger.error(f"Erreur lors de la rcupration des infos DB: {e}")
        return {'error': str(e)} 
