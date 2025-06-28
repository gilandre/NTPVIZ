"""
Initialisation des données de base
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
    """Initialiser les données par défaut"""
    try:
        logger.info("Initialisation des données par défaut...")
        
        # Créer l'utilisateur admin par défaut
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
            logger.info("Utilisateur admin créé (admin/admin123)")
        
        # Créer les serveurs NTP par défaut (4 pools + 1 local)
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
                logger.info(f"Serveur NTP créé: {server_config['name']} ({server_config['address']})")
        
        # Configuration système par défaut
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
                'description': 'Intervalle de requête NTP (secondes)'
            },
            {
                'key': 'max_offset_threshold',
                'value': '1.0',
                'description': 'Seuil d\'écart maximum (secondes)'
            },
            {
                'key': 'critical_offset_threshold',
                'value': '5.0',
                'description': 'Seuil d\'écart critique (secondes)'
            },
            {
                'key': 'client_monitoring_enabled',
                'value': 'true',
                'description': 'Activer le monitoring des clients'
            },
            {
                'key': 'dashboard_auto_refresh',
                'value': '30',
                'description': 'Intervalle de rafraîchissement du dashboard (secondes)'
            },
            {
                'key': 'log_retention_days',
                'value': '30',
                'description': 'Durée de conservation des logs (jours)'
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
                logger.info(f"Configuration système créée: {config_data['key']}")
        
        # Sauvegarder les modifications
        db.session.commit()
        logger.info("Données par défaut initialisées avec succès")
        
        # Résumé des serveurs créés
        servers = NTPServer.query.filter_by(is_active=True).all()
        logger.info(f"Serveurs NTP configurés ({len(servers)}):")
        for server in servers:
            logger.info(f"  - {server.name}: {server.address} ({server.server_type})")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation des données: {e}")
        db.session.rollback()
        return False

def update_ntp_servers():
    """Mettre à jour les serveurs NTP avec la nouvelle configuration"""
    try:
        logger.info("Mise à jour des serveurs NTP...")
        
        # Désactiver les anciens serveurs
        old_servers = NTPServer.query.filter(
            ~NTPServer.address.in_([s['address'] for s in Config.NTP_DEFAULT_SERVERS])
        ).all()
        
        for server in old_servers:
            server.is_active = False
            logger.info(f"Serveur désactivé: {server.name} ({server.address})")
        
        # Créer ou mettre à jour les nouveaux serveurs
        for i, server_config in enumerate(Config.NTP_DEFAULT_SERVERS):
            existing_server = NTPServer.query.filter_by(address=server_config['address']).first()
            
            if existing_server:
                # Mettre à jour le serveur existant
                existing_server.name = server_config['name']
                existing_server.server_type = server_config['type']
                existing_server.description = server_config['description']
                existing_server.is_active = True
                existing_server.priority = i + 1
                logger.info(f"Serveur mis à jour: {server_config['name']} ({server_config['address']})")
            else:
                # Créer un nouveau serveur
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
                logger.info(f"Nouveau serveur créé: {server_config['name']} ({server_config['address']})")
        
        db.session.commit()
        logger.info("Mise à jour des serveurs NTP terminée")
        
        # Afficher la configuration actuelle
        active_servers = NTPServer.query.filter_by(is_active=True).order_by(NTPServer.priority).all()
        logger.info(f"Serveurs NTP actifs ({len(active_servers)}):")
        for server in active_servers:
            logger.info(f"  {server.priority}. {server.name}: {server.address} ({server.server_type})")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des serveurs NTP: {e}")
        db.session.rollback()
        return False

def clean_old_data():
    """Nettoyer les anciennes données"""
    try:
        logger.info("Nettoyage des anciennes données...")
        
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
        
        # Supprimer les alertes résolues anciennes (plus de 7 jours)
        from backend.models.alert import Alert
        
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        old_alerts = Alert.query.filter(
            Alert.status == 'resolved',
            Alert.created_at < cutoff_date
        ).all()
        
        for alert in old_alerts:
            db.session.delete(alert)
        
        if old_alerts:
            logger.info(f"Suppression de {len(old_alerts)} alertes résolues anciennes")
        
        db.session.commit()
        logger.info("Nettoyage terminé")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage: {e}")
        db.session.rollback()
        return False

def reset_database():
    """Réinitialiser complètement la base de données (ATTENTION!)"""
    try:
        logger.warning("ATTENTION: Réinitialisation complète de la base de données")
        
        # Supprimer toutes les tables
        db.drop_all()
        
        # Recréer les tables
        db.create_all()
        
        # Réinitialiser les données par défaut
        init_default_data()
        
        logger.info("Base de données réinitialisée avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation: {e}")
        raise

def create_test_data():
    """Créer des données de test pour le développement UNIQUEMENT"""
    try:
        from flask import current_app
        
        # Ne créer des données de test qu'en mode développement
        if current_app.config.get('ENV', 'production') == 'production':
            logger.info("Mode production détecté - Aucune donnée de test créée")
            return False
        
        if not current_app.debug and not current_app.config.get('TESTING', False):
            logger.info("Mode production ou non-debug détecté - Aucune donnée de test créée")
            return False
        
        logger.info("Mode développement détecté - Création des données de test...")
        
        # Créer des utilisateurs de test UNIQUEMENT en développement
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
        
        # Créer des serveurs NTP de test supplémentaires UNIQUEMENT en développement
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
                    description=f"Serveur de test {server_data['type']} - DÉVELOPPEMENT UNIQUEMENT",
                    is_active=False  # Désactivé par défaut
                )
                db.session.add(server)
        
        db.session.commit()
        logger.info("Données de test créées (MODE DÉVELOPPEMENT)")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la création des données de test: {e}")
        return False

def get_database_info():
    """Récupérer les informations sur la base de données"""
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
        logger.error(f"Erreur lors de la récupération des infos DB: {e}")
        return {'error': str(e)} 