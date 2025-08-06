"""
Application Flask pour NTP Monitor Enterprise
Configuration optimisée pour MySQL avec Database Manager centralisé
"""
import os
import sys
import logging

# Patch global Flask avant tout import
try:
    from .flask_patch import patch_flask_modules
    patch_flask_modules()
except ImportError:
    pass

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
                     engineio_logger=False,
                     ping_timeout=60,
                     ping_interval=25,
                     allow_upgrades=True,
                     transports=['polling', 'websocket'])
    
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
    from backend.api.thresholds import thresholds_bp
    from backend.api.aggregation import aggregation_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(ntp_bp, url_prefix='/api/ntp')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(config_bp, url_prefix='/api/config')
    app.register_blueprint(thresholds_bp, url_prefix='/api/thresholds')
    app.register_blueprint(aggregation_bp, url_prefix='/api/aggregation')
    
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
    
    # Routes de test pour le développement
    if app.config.get('DEBUG', False) or app.config.get('TESTING', False):
        @app.route('/test-admin-modal')
        def test_admin_modal():
            """Page de test pour le modal d'administration"""
            try:
                with open('test_admin_modal.html', 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                return "Fichier de test non trouvé", 404

        @app.route('/test-admin-realtime')
        def test_admin_realtime():
            """Route de test en temps réel pour le modal d'administration"""
            try:
                with open('test_admin_modal_realtime.html', 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                return "Fichier de test en temps réel non trouvé", 404

        @app.route('/test-admin-diagnostic')
        def test_admin_diagnostic():
            """Route de diagnostic pour le modal d'administration"""
            try:
                with open('test_admin_diagnostic.html', 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                return "Fichier de diagnostic non trouvé", 404

        @app.route('/test-admin-coherence')
        def test_admin_coherence():
            """Route de test de cohérence pour le modal d'administration"""
            try:
                with open('test_admin_coherence.html', 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                return "Fichier de test de cohérence non trouvé", 404

        @app.route('/test-admin-improvements')
        def test_admin_improvements():
            """Route de test des améliorations du modal d'administration"""
            try:
                with open('test_admin_modal_improvements.html', 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                return "Fichier de test des améliorations non trouvé", 404

        @app.route('/test-canvas-elements')
        def test_canvas_elements():
            """Route de test des éléments canvas pour les graphiques"""
            try:
                with open('test_canvas_elements.html', 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                return "Fichier de test des éléments canvas non trouvé", 404

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

# Suppression du bloc if __name__ == '__main__' pour éviter les redémarrages en boucle
# L'application doit être démarrée uniquement depuis app.py principal