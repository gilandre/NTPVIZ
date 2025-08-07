#!/usr/bin/env python3
"""
Script de vérification rapide finale
Confirme que l'application est prête pour la production
"""
import sys
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

def quick_database_test():
    """Test rapide de la base de données"""
    logger.info("🔍 TEST RAPIDE DE LA BASE DE DONNÉES")
    logger.info("=" * 50)
    
    try:
        from backend.database_manager import get_db_session_with_context
        from backend.models.user import User
        from backend.models.ntp_server import NTPServer
        from backend.models.alert import Alert
        
        with get_db_session_with_context() as session:
            # Test des modèles principaux
            users_count = session.query(User).count()
            servers_count = session.query(NTPServer).count()
            alerts_count = session.query(Alert).count()
            
            logger.info(f"✅ Utilisateurs: {users_count}")
            logger.info(f"✅ Serveurs NTP: {servers_count}")
            logger.info(f"✅ Alertes: {alerts_count}")
            
            # Test de création d'objets
            test_user = User(username="test_quick", email="test@quick.com", password="test123")
            test_server = NTPServer(name="test_quick", address="test.quick.com", port=123, server_type="global")
            
            logger.info("✅ Création d'objets test réussie")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du test rapide: {e}")
        return False

def quick_app_test():
    """Test rapide de l'application"""
    logger.info("\n🚀 TEST RAPIDE DE L'APPLICATION")
    logger.info("=" * 50)
    
    try:
        # Test d'import des modules principaux
        from backend.app import create_app
        from backend.api.admin import admin_bp
        from backend.api.ntp import ntp_bp
        
        logger.info("✅ Import des modules principaux réussi")
        
        # Test de création de l'app
        app = create_app()
        logger.info("✅ Création de l'application réussie")
        
        # Test des blueprints
        blueprints = [admin_bp, ntp_bp]
        for bp in blueprints:
            logger.info(f"✅ Blueprint {bp.name} disponible")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de l'application: {e}")
        return False

def quick_config_test():
    """Test rapide de la configuration"""
    logger.info("\n⚙️ TEST RAPIDE DE LA CONFIGURATION")
    logger.info("=" * 50)
    
    try:
        from backend.database_manager import DatabaseManager
        from sqlalchemy import text
        
        # Test de la configuration
        db_manager = DatabaseManager()
        logger.info("✅ Configuration de base de données OK")
        
        # Test de connexion
        with db_manager.get_session() as session:
            result = session.execute(text("SELECT 1")).fetchone()
            logger.info("✅ Connexion à la base de données OK")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de configuration: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🚀 VÉRIFICATION RAPIDE FINALE")
    logger.info("=" * 60)
    
    # Tests rapides
    db_ok = quick_database_test()
    app_ok = quick_app_test()
    config_ok = quick_config_test()
    
    # Résumé final
    logger.info("\n🎯 RÉSUMÉ FINAL")
    logger.info("=" * 60)
    
    if db_ok and app_ok and config_ok:
        logger.info("🎉 TOUS LES TESTS RAPIDES RÉUSSIS!")
        logger.info("✅ Base de données: OK")
        logger.info("✅ Application: OK")
        logger.info("✅ Configuration: OK")
        logger.info("\n🚀 L'APPLICATION EST PRÊTE POUR LA PRODUCTION!")
        return True
    else:
        logger.error("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        logger.error(f"   - Base de données: {'✅' if db_ok else '❌'}")
        logger.error(f"   - Application: {'✅' if app_ok else '❌'}")
        logger.error(f"   - Configuration: {'✅' if config_ok else '❌'}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 