#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NTP Monitor Enterprise - Point d'entrée principal CORRIGÉ
Application de monitoring et synchronisation NTP
"""

import os
import sys
import logging
from datetime import datetime
# ✅ IMPORTS FLASK CORRIGÉS
from flask import Flask, jsonify, render_template, request

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

# ✅ GESTIONNAIRES D'ERREURS CORRIGÉS - Import request résolu
@app.errorhandler(404)
def not_found_error(error):
    """Gestionnaire d'erreur 404 - CORRIGÉ"""
    # request est maintenant importé en haut
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
        # Fallback si template non trouvé
        return jsonify({
            'error': 'Page non trouvée',
            'code': 404
        }), 404

@app.errorhandler(500)  
def internal_error(error):
    """Gestionnaire d'erreur 500 - CORRIGÉ"""
    # Gestion d'erreur sécurisée
    try:
        from backend.database_manager import db_manager
        # Pas de rollback automatique - géré par database_manager
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
        # Fallback si template non trouvé
        return jsonify({
            'error': 'Erreur interne du serveur',
            'code': 500
        }), 500

@app.errorhandler(403)
def forbidden_error(error):
    """Gestionnaire d'erreur 403 - CORRIGÉ"""
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

if __name__ == '__main__':
    try:
        logger.info("🚀 Démarrage de NTP Monitor Enterprise...")
        logger.info("Configuration:")
        logger.info(f"  - Mode debug: {app.config.get('DEBUG', False)}")
        logger.info(f"  - Port: {os.environ.get('PORT', 5000)}")
        logger.info(f"  - Host: {os.environ.get('HOST', '127.0.0.1')}")
        
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
        logger.info("✅ Démarrage du serveur...")
        socketio.run(
            app,
            host=os.environ.get('HOST', '127.0.0.1'),
            port=int(os.environ.get('PORT', 5000)),
            debug=app.config.get('DEBUG', False),
            allow_unsafe_werkzeug=True,
            log_output=False  # Réduire les logs SocketIO
        )
        
    except KeyboardInterrupt:
        logger.info("Arrêt de l'application par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erreur lors du démarrage: {e}")
        sys.exit(1)
