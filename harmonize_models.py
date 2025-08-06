#!/usr/bin/env python3
"""
Script d'harmonisation des modèles de base de données
Supprime les fichiers redondants et harmonise les définitions
"""
import os
import sys
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_redundant_files():
    """Supprimer les fichiers de modèles redondants"""
    redundant_files = [
        "backend/models/ntp_server_logical_delete.py",  # Redondant avec ntp_server.py
    ]
    
    for file_path in redundant_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"✅ Fichier supprimé: {file_path}")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de supprimer {file_path}: {e}")
        else:
            logger.info(f"ℹ️ Fichier déjà supprimé: {file_path}")

def update_ntp_server_model():
    """Mettre à jour le modèle NTPServer pour inclure toutes les colonnes nécessaires"""
    try:
        from backend.models.ntp_server import NTPServer
        
        # Vérifier que le modèle a toutes les colonnes nécessaires
        required_columns = [
            'id', 'name', 'address', 'port', 'server_type', 'is_active', 'priority',
            'timeout', 'max_offset', 'critical_offset', 'status', 'last_sync',
            'last_offset', 'last_latency', 'last_delay', 'last_stratum',
            'last_internet_status', 'last_error', 'error_count', 'consecutive_errors',
            'description', 'created_at', 'updated_at', 'created_by', 'deleted_at', 'deleted_by'
        ]
        
        # Vérifier les attributs du modèle
        model_attrs = [attr for attr in dir(NTPServer) if not attr.startswith('_')]
        logger.info(f"Attributs du modèle NTPServer: {model_attrs}")
        
        # Vérifier les colonnes de la table
        from backend.database_manager import get_db_session_with_context
        from sqlalchemy import text
        
        with get_db_session_with_context() as session:
            result = session.execute(text("DESCRIBE ntp_servers"))
            db_columns = [row[0] for row in result.fetchall()]
            logger.info(f"Colonnes de la base de données: {db_columns}")
            
            missing_columns = [col for col in required_columns if col not in db_columns]
            if missing_columns:
                logger.warning(f"⚠️ Colonnes manquantes dans la base de données: {missing_columns}")
            else:
                logger.info("✅ Toutes les colonnes requises sont présentes")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification du modèle: {e}")
        return False

def update_init_file():
    """Mettre à jour le fichier __init__.py pour supprimer les imports redondants"""
    init_content = '''"""
Modèles de base de données - NTP Monitor Enterprise
"""
from .user import User
from .ntp_server import NTPServer
from .ntp_log import NTPLog
from .alert import Alert
from .system_config import SystemConfig
from .alert_threshold import AlertThreshold
from .ntp_log_aggregated import (
    NTPLog15Min, NTPLog30Min, NTPLog1Hour, NTPLog6Hours, NTPLog24Hours, 
    AggregationStatus, BaseNTPLogAggregated
)

__all__ = [
    'User', 'NTPServer', 'NTPLog', 'Alert', 'SystemConfig', 'AlertThreshold',
    'NTPLog15Min', 'NTPLog30Min', 'NTPLog1Hour', 'NTPLog6Hours', 'NTPLog24Hours',
    'AggregationStatus', 'BaseNTPLogAggregated'
]
'''
    
    try:
        with open('backend/models/__init__.py', 'w') as f:
            f.write(init_content)
        logger.info("✅ Fichier __init__.py mis à jour")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de la mise à jour du fichier __init__.py: {e}")
        return False

def verify_model_consistency():
    """Vérifier la cohérence entre les modèles et la base de données"""
    try:
        from backend.database_manager import get_db_session_with_context
        from backend.models.ntp_server import NTPServer
        from backend.models.user import User
        from sqlalchemy import text
        
        with get_db_session_with_context() as session:
            # Tester les modèles
            logger.info("🧪 Test des modèles...")
            
            # Test User
            users = session.query(User).limit(1).all()
            logger.info(f"✅ Modèle User: {len(users)} utilisateur(s) trouvé(s)")
            
            # Test NTPServer
            servers = session.query(NTPServer).limit(1).all()
            logger.info(f"✅ Modèle NTPServer: {len(servers)} serveur(s) trouvé(s)")
            
            # Vérifier les colonnes critiques
            result = session.execute(text("DESCRIBE ntp_servers"))
            columns = [row[0] for row in result.fetchall()]
            
            critical_columns = ['server_type', 'max_offset', 'critical_offset', 'last_delay']
            missing_critical = [col for col in critical_columns if col not in columns]
            
            if missing_critical:
                logger.error(f"❌ Colonnes critiques manquantes: {missing_critical}")
                return False
            else:
                logger.info("✅ Toutes les colonnes critiques sont présentes")
                return True
                
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification de cohérence: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🔧 Début de l'harmonisation des modèles")
    
    # Nettoyer les fichiers redondants
    clean_redundant_files()
    
    # Mettre à jour le fichier __init__.py
    if update_init_file():
        logger.info("✅ Fichier __init__.py mis à jour avec succès")
    else:
        logger.error("❌ Échec de la mise à jour du fichier __init__.py")
        return False
    
    # Vérifier le modèle NTPServer
    if update_ntp_server_model():
        logger.info("✅ Modèle NTPServer vérifié avec succès")
    else:
        logger.error("❌ Échec de la vérification du modèle NTPServer")
        return False
    
    # Vérifier la cohérence globale
    if verify_model_consistency():
        logger.info("✅ Cohérence des modèles vérifiée")
        logger.info("🎉 Harmonisation terminée avec succès!")
        return True
    else:
        logger.error("❌ Problèmes de cohérence détectés")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 