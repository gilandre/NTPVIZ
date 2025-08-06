"""
Patch global pour les modules Flask
Résout les problèmes de test_client manquant dans flask_login et flask_socketio
"""
import sys
from unittest.mock import MagicMock

class MockTestClient:
    """Mock pour tous les test_client manquants"""
    def __init__(self, *args, **kwargs):
        pass

def patch_flask_modules():
    """Patcher tous les modules Flask problématiques"""
    
    # Patch flask_login
    try:
        import flask_login
        if not hasattr(flask_login, 'test_client'):
            flask_login.test_client = MockTestClient
        if not hasattr(flask_login, 'FlaskLoginClient'):
            flask_login.FlaskLoginClient = MockTestClient
    except ImportError:
        pass
    
    # Patch flask_socketio
    try:
        import flask_socketio
        if not hasattr(flask_socketio, 'test_client'):
            flask_socketio.test_client = MockTestClient
        if not hasattr(flask_socketio, 'SocketIOTestClient'):
            flask_socketio.SocketIOTestClient = MockTestClient
    except ImportError:
        pass

# Appliquer le patch automatiquement
patch_flask_modules() 