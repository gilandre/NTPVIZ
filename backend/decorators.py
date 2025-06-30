"""
Dcorateurs personnaliss pour NTP Monitor Enterprise
"""
from functools import wraps
from flask import jsonify, abort
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)

def admin_required(f):
    """
    Dcorateur pour restreindre l'accs aux administrateurs uniquement
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vrifier si l'utilisateur est connect
        if not current_user.is_authenticated:
            logger.warning("Tentative d'accs admin sans authentification")
            return jsonify({
                'status': 'error',
                'message': 'Authentification requise'
            }), 401
        
        # Vrifier si l'utilisateur a le rle admin
        if not hasattr(current_user, 'role') or current_user.role != 'admin':
            logger.warning(f"Tentative d'accs admin par {current_user.username} (rle: {getattr(current_user, 'role', 'inconnu')})")
            return jsonify({
                'status': 'error',
                'message': 'Privilges administrateur requis'
            }), 403
        
        logger.info(f"Accs admin autoris pour {current_user.username}")
        return f(*args, **kwargs)
    
    return decorated_function

def operator_or_admin_required(f):
    """
    Dcorateur pour restreindre l'accs aux oprateurs et administrateurs
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vrifier si l'utilisateur est connect
        if not current_user.is_authenticated:
            return jsonify({
                'status': 'error',
                'message': 'Authentification requise'
            }), 401
        
        # Vrifier si l'utilisateur a le rle operator ou admin
        user_role = getattr(current_user, 'role', None)
        if user_role not in ['operator', 'admin']:
            logger.warning(f"Tentative d'accs oprateur par {current_user.username} (rle: {user_role})")
            return jsonify({
                'status': 'error',
                'message': 'Privilges oprateur ou administrateur requis'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def api_key_required(f):
    """
    Dcorateur pour l'authentification par cl API (pour usage futur)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Implmentation future pour API key
        return f(*args, **kwargs)
    
    return decorated_function 
