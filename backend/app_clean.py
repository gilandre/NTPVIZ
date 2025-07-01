"""
Application Flask principale - NTP Monitor Enterprise
Version nettoyée sans Flask-SQLAlchemy et sans imports circulaires
"""
import os
import sys
import logging
from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Importer la base de données centralisée (sans imports circulaires)
from backend.database import Base, User
from backend.database_manager import DatabaseManager

# Extensions globales
login_manager = LoginManager()
socketio = SocketIO()

def create_app(config_name=None):
    """Factory de création de l'application Flask propre"""
    
    app = Flask(__name__, 
                template_folder='../frontend/templates',
                static_folder='../frontend/static')
    
    print("🚀 NTP Monitor Enterprise - VERSION MYSQL PROPRE")
    print("=" * 60)
    print("📊 Configuration MySQL:")
    print("   - Host: localhost:3306")
    print("   - Database: ntp_monitor")
    print("   - User: root")
    
    # Configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    
    if config_name == 'production':
        from config.config import ProductionConfig
        app.config.from_object(ProductionConfig)
    elif config_name == 'testing':
        from config.config import TestingConfig  
        app.config.from_object(TestingConfig)
    else:
        from config.config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    
    # Initialiser le Database Manager MySQL (sans Flask-SQLAlchemy)
    try:
        print("[INFO] 🔧 Début initialisation Database Manager MySQL propre...")
        
        db_manager = DatabaseManager()
        success = db_manager.initialize(app)
        
        if not success:
            raise Exception("Échec initialisation Database Manager")
        
        # Créer les tables automatiquement
        with db_manager.get_session() as session:
            Base.metadata.create_all(bind=session.bind)
        
        app.db_manager = db_manager
        print("[INFO] ✅ Database Manager MySQL propre initialisé avec succès")
        print("[INFO] 📊 Tables créées automatiquement")
        
    except Exception as e:
        print(f"❌ Erreur initialisation Database Manager: {e}")
        print("💡 Vérifiez que MySQL Server est démarré et accessible")
        print("📋 Configuration attendue:")
        print("   - Host: localhost:3306")
        print("   - Database: ntp_monitor")  
        print("   - User: root (sans mot de passe)")
        sys.exit(1)
    
    # Configuration Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Charger un utilisateur depuis la base de données"""
        try:
            with app.db_manager.get_session_with_app_context(app) as session:
                return session.query(User).filter(User.id == int(user_id)).first()
        except Exception:
            return None
    
    # Configuration SocketIO
    socketio.init_app(app, 
                     cors_allowed_origins="*",
                     async_mode='threading',
                     logger=False,
                     engineio_logger=False)
    
    # Enregistrer les blueprints
    from backend.api.main import main_bp
    from backend.api.ntp import ntp_bp
    from backend.api.auth import auth_bp
    from backend.api.admin import admin_bp
    from backend.api.config import config_bp
    from backend.api.alerts import alerts_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(ntp_bp, url_prefix='/api/ntp')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(config_bp, url_prefix='/api/config')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    
    # Configuration des logs
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/app.log', maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('NTP Monitor Enterprise startup')
    
    # Initialiser les données par défaut
    try:
        with app.app_context():
            init_default_data(app.db_manager)
        print("✅ Données par défaut initialisées")
    except Exception as e:
        print(f"⚠️  Erreur lors de l'initialisation des données: {e}")
    
    return app

def init_default_data(db_manager):
    """Initialiser les données par défaut"""
    from backend.database import User, NTPServer, SystemConfig
    
    with db_manager.get_session() as session:
        # Vérifier si des données existent déjà
        if session.query(User).count() > 0:
            return
        
        # Créer les utilisateurs par défaut
        admin_user = User('admin', 'admin@ntp-monitor.local', 'admin123', 'admin')
        operator_user = User('operator', 'operator@ntp-monitor.local', 'operator123', 'operator')
        viewer_user = User('viewer', 'viewer@ntp-monitor.local', 'viewer123', 'viewer')
        
        session.add_all([admin_user, operator_user, viewer_user])
        
        # Créer les serveurs NTP par défaut
        servers = [
            NTPServer(name='Pool FR 0', address='0.fr.pool.ntp.org', priority=1),
            NTPServer(name='Pool FR 1', address='1.fr.pool.ntp.org', priority=2),
            NTPServer(name='Pool Europe', address='europe.pool.ntp.org', priority=3),
            NTPServer(name='Cloudflare Time', address='time.cloudflare.com', priority=4)
        ]
        
        for server in servers:
            server.is_active = True
            session.add(server)
        
        # Configuration système par défaut
        configs = [
            SystemConfig(key_name='app_name', value='NTP Monitor Enterprise', category='general'),
            SystemConfig(key_name='max_logs_days', value='30', category='maintenance'),
            SystemConfig(key_name='alert_email_enabled', value='false', category='alerts'),
            SystemConfig(key_name='monitoring_interval', value='60', category='monitoring')
        ]
        
        for config in configs:
            session.add(config)
        
        session.commit()

if __name__ == '__main__':
    app = create_app()
    
    print("\n🎯 Application prête - Accès:")
    print("   - Dashboard: http://127.0.0.1:5000")
    print("   - API: http://127.0.0.1:5000/api")
    print("\n🔐 Comptes par défaut (MODE DÉVELOPPEMENT):")
    print("   - Administrateur: admin / admin123")
    print("   - Opérateur: operator / operator123")
    print("   - Visualiseur: viewer / viewer123")
    print("\n📈 Avantages version propre:")
    print("   ✅ 0 import circulaire")
    print("   ✅ 0 erreur Flask-SQLAlchemy")
    print("   ✅ Architecture cohérente")
    print("   ✅ Database Manager pur")
    print("   ✅ Performances optimisées")
    
    try:
        socketio.run(app, host='127.0.0.1', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de l'application")
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        sys.exit(1) 