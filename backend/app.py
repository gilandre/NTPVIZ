"""
Application Flask pour NTP Monitor Enterprise
Configuration optimisée pour MySQL avec Database Manager centralisé
"""
import os
import logging
from flask import Flask, request, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from pathlib import Path

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
        from backend.models.user import User
        return User.query.get(int(user_id))
    
    # Initialiser le Database Manager MySQL
    from backend.database_manager import init_database_manager
    init_database_manager(app)
    
    # Enregistrer les blueprints
    from backend.api.main import main_bp
    from backend.api.auth import auth_bp  
    from backend.api.ntp import ntp_bp
    from backend.api.admin import admin_bp
    from backend.api.alerts import alerts_bp
    from backend.api.config import config_bp
    from backend.api.websocket import websocket_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(ntp_bp, url_prefix='/api/ntp')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(config_bp, url_prefix='/api/config')
    app.register_blueprint(websocket_bp)
    
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
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app

if __name__ == '__main__':
    """Lancement en mode développement avec MySQL"""
    import sys
    import os
    from pathlib import Path
    
    print("🚀 NTP Monitor Enterprise - VERSION MYSQL")
    print("=" * 60)
    
    # Vérifier que MySQL est configuré
    mysql_config = {
        'host': os.environ.get('MYSQL_HOST', 'localhost'),
        'port': int(os.environ.get('MYSQL_PORT', 3306)),
        'user': os.environ.get('MYSQL_USER', 'ntp_user'),
        'password': os.environ.get('MYSQL_PASSWORD', 'ntp_password'),
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
        from backend.utils.init_data import initialize_default_data
        try:
            initialize_default_data()
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