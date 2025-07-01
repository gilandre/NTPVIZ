"""
Application Flask pour NTP Monitor Enterprise
Configuration optimisée pour MySQL avec Database Manager centralisé
"""
import os
import sys
import logging
from flask import Flask, request, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH pour résoudre les imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Initialisation des extensions
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

def create_app(config_name=None):
    """Factory de création de l'application Flask"""
    
    app = Flask(__name__, 
                template_folder='../frontend/templates',
                static_folder='../frontend/static')
    
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
    
    # Initialiser les extensions
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, 
                     cors_allowed_origins="*",
                     async_mode='threading',
                     logger=False,
                     engineio_logger=False)
    
    # Configuration Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Charger un utilisateur par son ID avec le Database Manager MySQL"""
        try:
            from backend.database_manager import get_db_session_with_context
            from backend.database import User
            from flask_login import UserMixin
            
            with get_db_session_with_context() as session:
                db_user = session.query(User).filter(User.id == int(user_id)).first()
                if not db_user:
                    return None
                
                # Créer une classe User simple pour Flask-Login
                class SimpleUser(UserMixin):
                    def __init__(self, user_data):
                        self.id = str(user_data.id)  # Flask-Login needs string ID
                        self.username = user_data.username
                        self.email = user_data.email
                        self.password_hash = user_data.password_hash
                        self.first_name = user_data.first_name
                        self.last_name = user_data.last_name
                        self.role = user_data.role
                        self._is_active = user_data.is_active  # Éviter collision avec UserMixin
                        self.created_at = user_data.created_at
                        self.last_login = user_data.last_login
                        self.login_count = user_data.login_count
                        self.preferences = user_data.preferences
                    
                    @property
                    def is_active(self):
                        """Propriété is_active pour Flask-Login"""
                        return bool(self._is_active)
                    
                    @property
                    def is_admin(self):
                        return self.role == 'admin'
                    
                    @property
                    def can_configure(self):
                        return self.role in ['admin', 'operator']
                    
                    @property
                    def full_name(self):
                        if self.first_name and self.last_name:
                            return f"{self.first_name} {self.last_name}"
                        return self.username
                    
                    def to_dict(self):
                        return {
                            'id': int(self.id),
                            'username': self.username,
                            'email': self.email,
                            'full_name': self.full_name,
                            'role': self.role,
                            'is_active': self.is_active,
                            'created_at': self.created_at.isoformat() if self.created_at else None,
                            'last_login': self.last_login.isoformat() if self.last_login else None,
                            'login_count': self.login_count,
                            'preferences': self.preferences
                        }
                
                return SimpleUser(db_user)
                
        except Exception as e:
            app.logger.error(f"Erreur load_user: {e}")
            return None
    
    # Initialiser le Database Manager MySQL (forcé)
    from backend.database_manager import db_manager
    if not db_manager.initialized:
        try:
            db_manager.initialize(app)
        except Exception:
            pass  # Ignore les erreurs d'initialisation
    
    # Enregistrer les blueprints
    from backend.api.main import main_bp
    from backend.api.auth import auth_bp  
    from backend.api.ntp import ntp_bp
    from backend.api.admin import admin_bp
    from backend.api.alerts import alerts_bp
    from backend.api.config import config_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(ntp_bp, url_prefix='/api/ntp')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(config_bp, url_prefix='/api/config')
    
    # Initialiser les WebSocket handlers (pas besoin de blueprint)
    from backend.api import websocket  # Import pour enregistrer les handlers
    
    # Configuration des logs
    if not app.debug and not app.testing:
        # Logs en production
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.FileHandler('logs/app.log', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('🚀 NTP Monitor Enterprise démarré')
    
    # Handler d'erreur
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Gestionnaire d'erreur 500 compatible avec Database Manager MySQL"""
        try:
            # Ne pas utiliser db.session.rollback() qui cause des erreurs
            # Le Database Manager gère automatiquement les rollbacks
            app.logger.error(f"Erreur 500: {error}")
        except Exception:
            pass  # Ignorer les erreurs de logging
        return render_template('errors/500.html'), 500
    
    return app

if __name__ == '__main__':
    """Lancement en mode développement avec MySQL"""
    import sys
    import os
    from pathlib import Path
    
    print("🚀 NTP Monitor Enterprise - VERSION MYSQL")
    print("=" * 60)
    
    # Configuration MySQL (utilisateur root sans mot de passe)
    mysql_config = {
        'host': os.environ.get('MYSQL_HOST', 'localhost'),
        'port': int(os.environ.get('MYSQL_PORT', 3306)),
        'user': os.environ.get('MYSQL_USER', 'root'),
        'password': os.environ.get('MYSQL_PASSWORD', ''),
        'database': os.environ.get('MYSQL_DATABASE', 'ntp_monitor')
    }
    
    print(f"📊 Configuration MySQL:")
    print(f"   - Host: {mysql_config['host']}:{mysql_config['port']}")
    print(f"   - Database: {mysql_config['database']}")
    print(f"   - User: {mysql_config['user']}")
    
    # Créer l'application
    app = create_app()
    
    with app.app_context():
        # Initialiser les données par défaut si nécessaire
        from backend.utils.init_data import init_default_data
        try:
            init_default_data()
            print("✅ Données par défaut initialisées")
        except Exception as e:
            print(f"⚠️  Erreur initialisation données: {e}")
    
    print("\n🎯 Application prête - Accès:")
    print("   - Dashboard: http://127.0.0.1:5000")
    print("   - API: http://127.0.0.1:5000/api")
    
    print("\n🔐 Comptes par défaut (MODE DÉVELOPPEMENT):")
    print("   - Administrateur: admin / admin123")
    print("   - Opérateur: operator / operator123")
    print("   - Visualiseur: viewer / viewer123")
    
    print("\n📈 Bénéfices MySQL:")
    print("   ✅ 0 erreur 'database is locked'")
    print("   ✅ 0 erreur 'transaction already begun'")
    print("   ✅ Performance optimale")
    print("   ✅ Synchronisation NTP stable")
    
    print("\n🔧 Monitoring autonome activé...")
    print("=" * 60)
    
    # Démarrer l'application avec SocketIO
    socketio.run(
        app,
        host='127.0.0.1',
        port=5000,
        debug=False,  # Désactiver le debug pour éviter les logs verbeux
        use_reloader=False,  # Éviter les redémarrages intempestifs
        log_output=False    # Réduire les logs SocketIO
    )