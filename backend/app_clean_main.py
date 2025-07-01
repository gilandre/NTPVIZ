#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NTP Monitor Enterprise - Application principale PROPRE
Version sans Flask-Migrate pour éviter les imports circulaires
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from backend.database_manager import DatabaseManager
import logging

def create_app():
    """Créer l'application Flask sans Flask-Migrate"""
    print("🚀 NTP Monitor Enterprise - VERSION PROPRE")
    print("=" * 60)
    print("📊 Configuration MySQL:")
    print("   - Host: localhost:3306")
    print("   - Database: ntp_monitor")
    print("   - User: root")
    
    # Créer l'application Flask
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'ntp-monitor-enterprise-2025'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ntp_monitor'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_timeout': 20,
        'pool_recycle': -1,
        'pool_pre_ping': True
    }
    
    # Initialiser le gestionnaire de base de données
    db_manager = DatabaseManager()
    if not db_manager.initialize():
        print("❌ Erreur initialisation base de données")
        sys.exit(1)
    
    # Configuration des logs
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )
    
    # Enregistrer les blueprints
    try:
        from backend.api.main import main_bp
        from backend.api.auth import auth_bp
        from backend.api.ntp import ntp_bp
        from backend.api.config import config_bp
        from backend.api.admin import admin_bp
        from backend.api.alerts import alerts_bp
        
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(ntp_bp, url_prefix='/api/ntp')
        app.register_blueprint(config_bp, url_prefix='/api/config')
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
        
        print("✅ Blueprints enregistrés avec succès")
        
    except Exception as e:
        print(f"❌ Erreur enregistrement blueprints: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Gestionnaire d'erreurs global
    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Erreur interne du serveur", "details": str(error)}, 500
    
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Ressource non trouvée"}, 404
    
    print("✅ Application Flask créée avec succès")
    return app

if __name__ == '__main__':
    # Créer l'application
    app = create_app()
    
    # Lancer le serveur
    print("🌐 Démarrage serveur sur http://127.0.0.1:5000")
    print("🔄 Service NTP et dashboard temps réel")
    print("📊 Graphiques mis à jour automatiquement")
    
    try:
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur demandé")
    except Exception as e:
        print(f"❌ Erreur serveur: {e}")
        sys.exit(1)
