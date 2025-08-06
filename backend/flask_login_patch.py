"""
Patch pour Flask-Login 0.6.3
Résout le problème de test_client manquant
"""
import sys
from unittest.mock import MagicMock

# Créer un mock pour test_client
class MockFlaskLoginClient:
    def __init__(self, *args, **kwargs):
        pass

# Injecter le mock dans flask_login
def patch_flask_login():
    """Patcher flask_login pour éviter l'erreur test_client"""
    try:
        import flask_login
        if not hasattr(flask_login, 'test_client'):
            flask_login.test_client = MockFlaskLoginClient
        if not hasattr(flask_login, 'FlaskLoginClient'):
            flask_login.FlaskLoginClient = MockFlaskLoginClient
    except ImportError:
        pass

# Appliquer le patch automatiquement
patch_flask_login() 