#!/usr/bin/env python3
"""
Script de correction du schéma de base de données
Ajoute les colonnes manquantes aux tables users et ntp_servers
"""
import sys
import logging
from pathlib import Path
from sqlalchemy import text

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

def fix_users_table():
    """Corriger la table users en ajoutant les colonnes manquantes"""
    try:
        from backend.database_manager import get_db_session_with_context
        
        with get_db_session_with_context() as session:
            # Vérifier les colonnes existantes
            result = session.execute(text("DESCRIBE users"))
            existing_columns = [row[0] for row in result.fetchall()]
            logger.info(f"Colonnes existantes dans users: {existing_columns}")
            
            # Colonnes à ajouter
            columns_to_add = [
                ("last_login", "DATETIME NULL"),
                ("login_count", "INT DEFAULT 0"),
                ("preferences", "TEXT NULL"),
                ("deleted_at", "DATETIME NULL"),
                ("deleted_by", "INT NULL")
            ]
            
            for column_name, column_def in columns_to_add:
                if column_name not in existing_columns:
                    try:
                        session.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}"))
                        logger.info(f"✅ Colonne {column_name} ajoutée à la table users")
                    except Exception as e:
                        logger.warning(f"⚠️ Impossible d'ajouter {column_name}: {e}")
                else:
                    logger.info(f"✅ Colonne {column_name} existe déjà")
            
            session.commit()
            logger.info("✅ Table users corrigée")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la correction de la table users: {e}")
        return False

def fix_ntp_servers_table():
    """Corriger la table ntp_servers en ajoutant les colonnes manquantes"""
    try:
        from backend.database_manager import get_db_session_with_context
        
        with get_db_session_with_context() as session:
            # Vérifier les colonnes existantes
            result = session.execute(text("DESCRIBE ntp_servers"))
            existing_columns = [row[0] for row in result.fetchall()]
            logger.info(f"Colonnes existantes dans ntp_servers: {existing_columns}")
            
            # Colonnes à ajouter
            columns_to_add = [
                ("server_type", "VARCHAR(20) NOT NULL DEFAULT 'global'"),
                ("last_delay", "FLOAT NULL"),
                ("deleted_at", "DATETIME NULL"),
                ("deleted_by", "INT NULL"),
                ("max_offset", "FLOAT DEFAULT 1.0"),
                ("critical_offset", "FLOAT DEFAULT 5.0")
            ]
            
            for column_name, column_def in columns_to_add:
                if column_name not in existing_columns:
                    try:
                        session.execute(text(f"ALTER TABLE ntp_servers ADD COLUMN {column_name} {column_def}"))
                        logger.info(f"✅ Colonne {column_name} ajoutée à la table ntp_servers")
                    except Exception as e:
                        logger.warning(f"⚠️ Impossible d'ajouter {column_name}: {e}")
                else:
                    logger.info(f"✅ Colonne {column_name} existe déjà")
            
            session.commit()
            logger.info("✅ Table ntp_servers corrigée")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la correction de la table ntp_servers: {e}")
        return False

def verify_schema():
    """Vérifier que le schéma est correct"""
    try:
        from backend.database_manager import get_db_session_with_context
        
        with get_db_session_with_context() as session:
            # Vérifier la table users
            result = session.execute(text("DESCRIBE users"))
            users_columns = [row[0] for row in result.fetchall()]
            logger.info(f"Colonnes users: {users_columns}")
            
            # Vérifier la table ntp_servers
            result = session.execute(text("DESCRIBE ntp_servers"))
            ntp_columns = [row[0] for row in result.fetchall()]
            logger.info(f"Colonnes ntp_servers: {ntp_columns}")
            
            # Vérifier les colonnes requises
            required_users_columns = ['last_login', 'login_count', 'preferences', 'deleted_at', 'deleted_by']
            required_ntp_columns = ['server_type', 'last_delay', 'deleted_at', 'deleted_by', 'max_offset', 'critical_offset']
            
            missing_users = [col for col in required_users_columns if col not in users_columns]
            missing_ntp = [col for col in required_ntp_columns if col not in ntp_columns]
            
            if missing_users:
                logger.error(f"❌ Colonnes manquantes dans users: {missing_users}")
            else:
                logger.info("✅ Toutes les colonnes requises sont présentes dans users")
                
            if missing_ntp:
                logger.error(f"❌ Colonnes manquantes dans ntp_servers: {missing_ntp}")
            else:
                logger.info("✅ Toutes les colonnes requises sont présentes dans ntp_servers")
            
            return len(missing_users) == 0 and len(missing_ntp) == 0
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🔧 Début de la correction du schéma de base de données")
    
    # Corriger la table users
    if fix_users_table():
        logger.info("✅ Table users corrigée avec succès")
    else:
        logger.error("❌ Échec de la correction de la table users")
        return False
    
    # Corriger la table ntp_servers
    if fix_ntp_servers_table():
        logger.info("✅ Table ntp_servers corrigée avec succès")
    else:
        logger.error("❌ Échec de la correction de la table ntp_servers")
        return False
    
    # Vérifier le schéma
    if verify_schema():
        logger.info("✅ Schéma de base de données vérifié et corrigé")
        logger.info("🎉 Base de données prête pour l'application!")
        return True
    else:
        logger.error("❌ Problèmes détectés dans le schéma")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 