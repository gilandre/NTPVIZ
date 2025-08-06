#!/usr/bin/env python3
"""
Script d'initialisation de la base de données - NTP Monitor Enterprise
Version production compatible Ubuntu 24.04
"""
import sys
import os
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

def check_environment():
    """Vérifier l'environnement"""
    logger.info("🔍 Vérification de l'environnement...")
    
    # Vérifier les fichiers essentiels
    required_files = [
        'backend/database_manager.py',
        'backend/utils/init_data.py',
        'env.example'
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            logger.error(f"❌ Fichier manquant: {file_path}")
            return False
    
    logger.info("✅ Environnement vérifié")
    return True

def setup_database():
    """Configurer la base de données"""
    logger.info("🗄️ Configuration de la base de données...")
    
    try:
        # Importer et initialiser le Database Manager
        from backend.database_manager import DatabaseManager
        
        # Créer l'instance
        db_manager = DatabaseManager()
        
        # Forcer l'initialisation
        success = db_manager.initialize()
        
        if success:
            logger.info("✅ Database Manager initialisé avec succès")
            
            # Tester une session
            with db_manager.get_session() as session:
                from backend.database import User
                users = session.query(User).all()
                logger.info(f"✅ Test de session réussi - {len(users)} utilisateurs trouvés")
            
            return True
        else:
            logger.error("❌ Échec de l'initialisation du Database Manager")
            return False
            
    except Exception as e:
        logger.error(f"💥 Erreur lors de l'initialisation: {e}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False

def create_default_data():
    """Créer les données par défaut"""
    logger.info("📊 Création des données par défaut...")
    
    try:
        from backend.utils.init_data import init_default_data
        
        if init_default_data():
            logger.info("✅ Données par défaut créées avec succès")
            return True
        else:
            logger.error("❌ Échec création données par défaut")
            return False
            
    except Exception as e:
        logger.error(f"💥 Erreur création données: {e}")
        return False

def create_alert_thresholds():
    """Créer les seuils d'alertes par défaut"""
    logger.info("🔔 Création des seuils d'alertes...")
    
    try:
        from backend.services.alert_service import alert_service
        from backend.database_manager import get_db_session_with_context
        
        with get_db_session_with_context() as session:
            alert_service._create_default_thresholds(session)
            session.commit()
            logger.info("✅ Seuils d'alertes créés")
            return True
            
    except Exception as e:
        logger.error(f"💥 Erreur création seuils: {e}")
        return False

def test_database():
    """Tester la base de données"""
    logger.info("🧪 Test de la base de données...")
    
    try:
        from backend.database_manager import get_db_session_with_context
        from backend.database import User, NTPServer, SystemConfig
        
        with get_db_session_with_context() as session:
            # Compter les entités
            users_count = session.query(User).count()
            servers_count = session.query(NTPServer).count()
            config_count = session.query(SystemConfig).count()
            
            logger.info(f"✅ Base de données testée:")
            logger.info(f"   - Utilisateurs: {users_count}")
            logger.info(f"   - Serveurs NTP: {servers_count}")
            logger.info(f"   - Configurations: {config_count}")
            
            return True
            
    except Exception as e:
        logger.error(f"💥 Erreur test DB: {e}")
        return False

def main():
    """Fonction principale d'initialisation"""
    logger.info("🚀 INITIALISATION BASE DE DONNÉES - NTP Monitor Enterprise")
    logger.info("=" * 60)
    
    steps = [
        ("Vérification environnement", check_environment),
        ("Configuration base de données", setup_database),
        ("Création données par défaut", create_default_data),
        ("Création seuils d'alertes", create_alert_thresholds),
        ("Test base de données", test_database)
    ]
    
    for step_name, step_func in steps:
        logger.info(f"\n📋 {step_name}...")
        if not step_func():
            logger.error(f"❌ Échec: {step_name}")
            return 1
        logger.info(f"✅ {step_name} terminé")
    
    logger.info("\n🎉 INITIALISATION TERMINÉE AVEC SUCCÈS!")
    logger.info("=" * 60)
    logger.info("📋 Prochaines étapes:")
    logger.info("   1. Démarrer l'application: python app.py")
    logger.info("   2. Accéder à l'interface: http://localhost:5001")
    logger.info("   3. Se connecter avec: admin/admin123")
    logger.info("   4. Changer les mots de passe par défaut")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 