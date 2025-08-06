#!/usr/bin/env python3
"""
Script de correction du schéma de base de données
Ajoute les colonnes manquantes à la table users
"""
import sys
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

def fix_users_table():
    """Corriger la table users en ajoutant les colonnes manquantes"""
    logger.info("🔧 Correction du schéma de la table users...")
    
    try:
        from backend.database_manager import get_db_session_with_context
        from sqlalchemy import text
        
        with get_db_session_with_context() as session:
            # Vérifier si les colonnes existent
            result = session.execute(text("SHOW COLUMNS FROM users LIKE 'last_login'"))
            has_last_login = result.fetchone() is not None
            
            result = session.execute(text("SHOW COLUMNS FROM users LIKE 'login_count'"))
            has_login_count = result.fetchone() is not None
            
            # Ajouter les colonnes manquantes
            if not has_last_login:
                logger.info("Ajout de la colonne last_login...")
                session.execute(text("ALTER TABLE users ADD COLUMN last_login DATETIME NULL"))
                logger.info("✅ Colonne last_login ajoutée")
            
            if not has_login_count:
                logger.info("Ajout de la colonne login_count...")
                session.execute(text("ALTER TABLE users ADD COLUMN login_count INT DEFAULT 0"))
                logger.info("✅ Colonne login_count ajoutée")
            
            # Vérifier si la colonne preferences existe
            result = session.execute(text("SHOW COLUMNS FROM users LIKE 'preferences'"))
            has_preferences = result.fetchone() is not None
            
            if not has_preferences:
                logger.info("Ajout de la colonne preferences...")
                session.execute(text("ALTER TABLE users ADD COLUMN preferences JSON NULL"))
                logger.info("✅ Colonne preferences ajoutée")
            
            # Vérifier si les colonnes de suppression logique existent
            result = session.execute(text("SHOW COLUMNS FROM users LIKE 'deleted_at'"))
            has_deleted_at = result.fetchone() is not None
            
            result = session.execute(text("SHOW COLUMNS FROM users LIKE 'deleted_by'"))
            has_deleted_by = result.fetchone() is not None
            
            if not has_deleted_at:
                logger.info("Ajout de la colonne deleted_at...")
                session.execute(text("ALTER TABLE users ADD COLUMN deleted_at DATETIME NULL, ADD INDEX idx_deleted_at (deleted_at)"))
                logger.info("✅ Colonne deleted_at ajoutée")
            
            if not has_deleted_by:
                logger.info("Ajout de la colonne deleted_by...")
                session.execute(text("ALTER TABLE users ADD COLUMN deleted_by INT NULL, ADD FOREIGN KEY (deleted_by) REFERENCES users(id)"))
                logger.info("✅ Colonne deleted_by ajoutée")
            
            # Commit des changements
            session.commit()
            logger.info("✅ Schéma de la table users corrigé")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la correction: {e}")
        return False

def verify_schema():
    """Vérifier que le schéma est correct"""
    logger.info("🔍 Vérification du schéma...")
    
    try:
        from backend.database_manager import get_db_session_with_context
        from backend.models.user import User
        from sqlalchemy import text
        
        with get_db_session_with_context() as session:
            # Tester une requête simple
            users = session.query(User).limit(1).all()
            logger.info(f"✅ Requête test réussie - {len(users)} utilisateur(s) trouvé(s)")
            
            # Vérifier la structure de la table
            result = session.execute(text("DESCRIBE users"))
            columns = [row[0] for row in result.fetchall()]
            
            required_columns = [
                'id', 'username', 'email', 'password_hash', 
                'first_name', 'last_name', 'role', 'is_active', 
                'created_at', 'last_login', 'login_count', 'preferences'
            ]
            
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                logger.error(f"❌ Colonnes manquantes: {missing_columns}")
                return False
            else:
                logger.info("✅ Toutes les colonnes requises sont présentes")
                return True
                
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🚀 CORRECTION DU SCHÉMA DE BASE DE DONNÉES")
    logger.info("=" * 50)
    
    # Corriger le schéma
    if fix_users_table():
        logger.info("✅ Correction du schéma terminée")
        
        # Vérifier le schéma
        if verify_schema():
            logger.info("✅ Vérification du schéma réussie")
            logger.info("🎉 Base de données prête pour l'application!")
            return 0
        else:
            logger.error("❌ Échec de la vérification du schéma")
            return 1
    else:
        logger.error("❌ Échec de la correction du schéma")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 