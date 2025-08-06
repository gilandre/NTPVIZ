#!/usr/bin/env python3
"""
Script d'initialisation forcée du Database Manager
Corrige les problèmes d'initialisation asynchrone
"""
import sys
import os
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Initialiser le Database Manager"""
    logger.info("🔧 Initialisation forcée du Database Manager...")
    
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
            
            # Créer les seuils par défaut
            logger.info("🔧 Création des seuils d'alertes par défaut...")
            from backend.services.alert_service import alert_service
            
            with db_manager.get_session() as session:
                alert_service._create_default_thresholds(session)
                session.commit()
                logger.info("✅ Seuils par défaut créés")
            
            logger.info("🎉 Initialisation complète réussie!")
            return 0
            
        else:
            logger.error("❌ Échec de l'initialisation du Database Manager")
            return 1
            
    except Exception as e:
        logger.error(f"💥 Erreur lors de l'initialisation: {e}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 