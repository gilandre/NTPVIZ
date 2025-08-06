"""
Décorateurs personnalisés pour NTP Monitor Enterprise
"""
from functools import wraps
from flask import jsonify, abort
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)

def admin_required(f):
    """
    Décorateur pour restreindre l'accès aux administrateurs uniquement
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vérifier si l'utilisateur est connecté
        if not current_user.is_authenticated:
            logger.warning("Tentative d'accès admin sans authentification")
            return jsonify({
                'status': 'error',
                'message': 'Authentification requise'
            }), 401
        
        # Vérifier si l'utilisateur a le rôle admin
        if not hasattr(current_user, 'role') or current_user.role != 'admin':
            logger.warning(f"Tentative d'accès admin par {current_user.username} (rôle: {getattr(current_user, 'role', 'inconnu')})")
            return jsonify({
                'status': 'error',
                'message': 'Privilèges administrateur requis'
            }), 403
        
        logger.info(f"Accès admin autorisé pour {current_user.username}")
        return f(*args, **kwargs)
    
    return decorated_function

def operator_or_admin_required(f):
    """
    Décorateur pour restreindre l'accès aux opérateurs et administrateurs
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vérifier si l'utilisateur est connecté
        if not current_user.is_authenticated:
            return jsonify({
                'status': 'error',
                'message': 'Authentification requise'
            }), 401
        
        # Vérifier si l'utilisateur a le rôle operator ou admin
        user_role = getattr(current_user, 'role', None)
        if user_role not in ['operator', 'admin']:
            logger.warning(f"Tentative d'accès opérateur par {current_user.username} (rôle: {user_role})")
            return jsonify({
                'status': 'error',
                'message': 'Privilèges opérateur ou administrateur requis'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def config_required(f):
    """
    Décorateur pour restreindre l'accès aux utilisateurs ayant les privilèges de configuration
    (admin et operator)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vérifier si l'utilisateur est connecté
        if not current_user.is_authenticated:
            logger.warning("Tentative d'accès configuration sans authentification")
            return jsonify({
                'status': 'error',
                'message': 'Authentification requise'
            }), 401
        
        # Vérifier si l'utilisateur a les privilèges de configuration
        user_role = getattr(current_user, 'role', None)
        if user_role not in ['admin', 'operator']:
            logger.warning(f"Tentative d'accès configuration par {current_user.username} (rôle: {user_role})")
            return jsonify({
                'status': 'error',
                'message': 'Privilèges de configuration requis (admin ou operator)'
            }), 403
        
        logger.info(f"Accès configuration autorisé pour {current_user.username} (rôle: {user_role})")
        return f(*args, **kwargs)
    
    return decorated_function

def api_key_required(f):
    """
    Décorateur pour l'authentification par clé API (pour usage futur)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Implémentation future pour API key
        return f(*args, **kwargs)
    
    return decorated_function 
