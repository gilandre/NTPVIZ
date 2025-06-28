"""
Application Flask principale - NTP Monitor Enterprise
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_migrate import Migrate
from config.config import config

# Extensions
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
migrate = Migrate()

def create_app(config_name=None):
    """Factory pour créer l'application Flask"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__, 
                template_folder='../../frontend/templates',
                static_folder='../../frontend/static')
    
    # Configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialiser les extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configuration Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'
    
    # Configuration SocketIO
    socketio.init_app(app, 
                     cors_allowed_origins="*",
                     logger=app.config.get('SOCKETIO_LOGGER', False),
                     engineio_logger=app.config.get('SOCKETIO_ENGINEIO_LOGGER', False))
    
    # Enregistrer les blueprints
    from backend.api.main import main_bp
    from backend.api.auth import auth_bp
    from backend.api.ntp import ntp_bp
    from backend.api.admin import admin_bp
    from backend.api.config import config_bp
    from backend.api.websocket import websocket_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)  # Pas de préfixe pour que /api/user/profile soit accessible directement
    app.register_blueprint(ntp_bp, url_prefix='/api/ntp')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(config_bp, url_prefix='/api/config')
    app.register_blueprint(websocket_bp, url_prefix='/ws')
    
    # Configuration du logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/ntp_monitor.log',
                                         maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('NTP Monitor Enterprise startup')
    
    # Gestionnaire de chargement utilisateur pour Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from backend.models.user import User
        return User.query.get(int(user_id))
    
    # Variables globales pour les templates
    @app.context_processor
    def inject_global_vars():
        from datetime import datetime
        return {
            'app_name': 'NTP Monitor Enterprise',
            'app_version': '1.0.0',
            'current_datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    # Créer les tables et initialiser les données par défaut
    with app.app_context():
        # Importer tous les modèles pour assurer leur création
        from backend.models import User, NTPServer, NTPLog, Alert, SystemConfig
        
        # Créer les tables
        db.create_all()
        
        # Initialiser les données par défaut si nécessaire
        try:
            from backend.utils.init_data import init_default_data
            if User.query.count() == 0:  # Première installation
                init_default_data()
                app.logger.info('Données par défaut initialisées')
        except Exception as e:
            app.logger.error(f'Erreur initialisation données: {e}')
    
    return app 