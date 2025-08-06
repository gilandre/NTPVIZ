#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NTP Monitor Enterprise - Point d'entrée principal UNIFIÉ
Application de monitoring et synchronisation NTP
"""

import os
import sys
import logging
import time
from datetime import datetime
from pathlib import Path

# Configuration d'encodage UTF-8 pour Windows
if sys.platform.startswith('win'):
    import locale
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass
    
    try:
        locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'French_France.1252')
        except:
            pass

# Ajouter le répertoire racine au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Créer le répertoire logs s'il n'existe pas
os.makedirs('logs', exist_ok=True)

# Configuration du logging pour l'application principale
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def init_database():
    """Initialiser la base de données"""
    try:
        logger.info("🔧 Initialisation de la base de données...")
        
        # Importer les modules nécessaires
        from backend.database_manager import db_manager
        from backend.database import Base
        from backend.utils.init_data import init_default_data
        
        # Initialiser le gestionnaire de base de données
        db_manager.initialize()
        logger.info("✅ Gestionnaire de base de données initialisé")
        
        # Créer les tables
        Base.metadata.create_all(db_manager.engine)
        logger.info("✅ Tables créées")
        
        # Initialiser les données par défaut
        init_default_data()
        logger.info("✅ Données initiales créées")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation de la base de données: {e}")
        return False

# Import de l'application Flask APRÈS configuration logging
try:
    from backend.app import create_app, socketio
    logger.info("✅ Imports backend réussis")
except Exception as e:
    logger.error(f"❌ Erreur import backend: {e}")
    sys.exit(1)

# Créer l'application Flask
try:
    app = create_app()
    logger.info("✅ Application Flask créée")
except Exception as e:
    logger.error(f"❌ Erreur création app: {e}")
    sys.exit(1)

# Gestionnaires d'erreurs
@app.errorhandler(404)
def not_found_error(error):
    """Gestionnaire d'erreur 404"""
    from flask import request, jsonify, render_template
    logger.warning(f"Page non trouvée: {request.url}")
    
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Resource non trouvée',
            'message': 'L\'endpoint demandé n\'existe pas'
        }), 404
    
    try:
        return render_template('error.html', 
                             error_code=404, 
                             error_message="Page non trouvée"), 404
    except:
        return jsonify({
            'error': 'Page non trouvée',
            'code': 404
        }), 404

@app.errorhandler(500)  
def internal_error(error):
    """Gestionnaire d'erreur 500"""
    from flask import request, jsonify, render_template
    try:
        from backend.database_manager import db_manager
    except:
        pass
    
    logger.error(f"Erreur interne: {error}")
    
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Erreur interne',
            'message': 'Une erreur est survenue sur le serveur'
        }), 500
    
    try:
        return render_template('error.html', 
                             error_code=500, 
                             error_message="Erreur interne du serveur"), 500
    except:
        return jsonify({
            'error': 'Erreur interne du serveur',
            'code': 500
        }), 500

@app.errorhandler(403)
def forbidden_error(error):
    """Gestionnaire d'erreur 403"""
    from flask import request, jsonify, render_template
    logger.warning(f"Accès refusé: {request.url}")
    
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Accès refusé',
            'message': 'Vous n\'avez pas les permissions nécessaires'
        }), 403
    
    try:
        return render_template('errors/403.html'), 403
    except:
        return jsonify({
            'error': 'Accès refusé',
            'code': 403
        }), 403

# Routes de test déplacées dans backend/app.py

if __name__ == '__main__':
    try:
        logger.info("🎯 Démarrage de NTPVIZ - NTP Monitor Enterprise")
        
        # Vérifier que nous sommes dans le bon répertoire
        if not Path("app.py").exists():
            logger.error("❌ Fichier app.py non trouvé. Assurez-vous d'être dans le répertoire racine de NTPVIZ.")
            sys.exit(1)
        
        # Initialiser la base de données
        if not init_database():
            logger.error("❌ Impossible d'initialiser la base de données. Arrêt.")
            sys.exit(1)
        
        # Attendre un peu pour s'assurer que tout est prêt
        time.sleep(2)
        
        # Récupérer la configuration depuis les variables d'environnement
        port = int(os.environ.get('PORT', 5001))  # Port 5001 par défaut
        host = os.environ.get('HOST', '0.0.0.0')
        
        logger.info("🚀 Démarrage de NTP Monitor Enterprise...")
        logger.info("Configuration:")
        logger.info(f"  - Mode debug: {app.config.get('DEBUG', False)}")
        logger.info(f"  - Port: {port}")
        logger.info(f"  - Host: {host}")
        
        # Afficher les comptes utilisateur par défaut
        if app.config.get('DEBUG', False) or app.config.get('TESTING', False):
            logger.info("Comptes utilisateur par défaut (MODE DÉVELOPPEMENT):")
            logger.info("  - Administrateur: admin / admin123")
            logger.info("  - Opérateur: operator / operator123")
            logger.info("  - Visualiseur: viewer / viewer123")
        else:
            logger.info("Compte administrateur par défaut:")
            logger.info("  - Administrateur: admin / admin123")
            logger.info("  (Changez le mot de passe après la première connexion)")
        
        # Initialisation du monitoring autonome
        logger.info("Initialisation du monitoring autonome...")
        try:
            from backend.api.websocket import initialize_background_monitoring
            initialize_background_monitoring()
            logger.info("✅ Monitoring autonome initialisé")
        except Exception as e:
            logger.warning(f"⚠️ Erreur monitoring autonome: {e}")
        
        # Démarrer l'application avec SocketIO
        logger.info("✅ Démarrage du serveur Flask avec SocketIO...")
        # Configuration temporaire pour forcer le rechargement des templates
        app.config['DEBUG'] = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.jinja_env.auto_reload = True
        
        socketio.run(
            app,
            host=host,
            port=port,
            debug=True,  # Mode debug activé temporairement
            use_reloader=True,  # Reloader activé pour rechargement templates
            allow_unsafe_werkzeug=True,
            log_output=False  # Réduire les logs SocketIO
        )
        
    except KeyboardInterrupt:
        logger.info("Arrêt de l'application par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erreur lors du démarrage: {e}")
        sys.exit(1)
