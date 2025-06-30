#!/usr/bin/env python3
"""
NTP Monitor Enterprise - Point d'entre principal
Application de monitoring et synchronisation NTP
"""

import os
import sys
import logging
from datetime import datetime
from flask import jsonify, render_template, request

# Ajouter le rpertoire racine au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import de l'application Flask
from backend.app import create_app, socketio

# Configuration du logging pour l'application principale
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Crer l'application Flask
app = create_app()

# Gestionnaires d'erreurs globaux
@app.errorhandler(404)
def not_found_error(error):
    """Gestionnaire d'erreur 404"""
    logger.warning(f"Page non trouve: {request.url}")
    
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Endpoint non trouv',
            'message': f"L'endpoint {request.path} n'existe pas"
        }), 404
    
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Gestionnaire d'erreur 500"""
    logger.error(f"Erreur interne: {error}")
    
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur',
            'message': 'Une erreur est survenue lors du traitement de votre requte'
        }), 500
    
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    """Gestionnaire d'erreur 403"""
    logger.warning(f"Accs refus: {request.url}")
    
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Accs refus',
            'message': 'Vous n\'avez pas les permissions ncessaires'
        }), 403
    
    return render_template('errors/403.html'), 403

if __name__ == '__main__':
    try:
        logger.info("Dmarrage de NTP Monitor Enterprise...")
        logger.info("Configuration:")
        logger.info(f"  - Mode debug: {app.config.get('DEBUG', False)}")
        logger.info(f"  - Port: {os.environ.get('PORT', 5000)}")
        logger.info(f"  - Host: {os.environ.get('HOST', '127.0.0.1')}")
        
        # Afficher les comptes utilisateur par dfaut
        if app.config.get('DEBUG', False) or app.config.get('TESTING', False):
            logger.info("Comptes utilisateur par dfaut (MODE DVELOPPEMENT):")
            logger.info("  - Administrateur: admin / admin123")
            logger.info("  - Oprateur: operator / operator123")
            logger.info("  - Visualiseur: viewer / viewer123")
        else:
            logger.info("Compte administrateur par dfaut:")
            logger.info("  - Administrateur: admin / admin123")
            logger.info("  (Changez le mot de passe aprs la premire connexion)")
        
        # Dmarrer l'application avec SocketIO
        socketio.run(
            app,
            host=os.environ.get('HOST', '127.0.0.1'),
            port=int(os.environ.get('PORT', 5000)),
            debug=app.config.get('DEBUG', False),
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        logger.info("Arrt de l'application par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erreur lors du dmarrage: {e}")
        sys.exit(1) 
