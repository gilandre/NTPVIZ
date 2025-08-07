#!/usr/bin/env python3
"""
Script de vérification approfondie du schéma de base de données
Compare les modèles Python avec la structure MySQL réelle
"""
import sys
import logging
from pathlib import Path
from sqlalchemy import text, inspect

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

def get_model_columns(model_class):
    """Extraire les colonnes d'un modèle SQLAlchemy"""
    columns = {}
    for column in model_class.__table__.columns:
        columns[column.name] = {
            'type': str(column.type),
            'nullable': column.nullable,
            'default': column.default,
            'primary_key': column.primary_key,
            'unique': column.unique,
            'index': column.index
        }
    return columns

def get_database_columns(session, table_name):
    """Extraire les colonnes d'une table MySQL"""
    try:
        result = session.execute(text(f"DESCRIBE {table_name}"))
        columns = {}
        for row in result.fetchall():
            column_name = row[0]
            column_type = row[1]
            is_null = row[2]
            key = row[3]
            default = row[4]
            extra = row[5]
            
            columns[column_name] = {
                'type': column_type,
                'nullable': is_null == 'YES',
                'key': key,
                'default': default,
                'extra': extra
            }
        return columns
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des colonnes de {table_name}: {e}")
        return {}

def compare_columns(model_columns, db_columns, table_name):
    """Comparer les colonnes du modèle avec celles de la base de données"""
    logger.info(f"\n🔍 Comparaison pour la table {table_name}:")
    
    # Colonnes dans le modèle mais pas en DB
    missing_in_db = set(model_columns.keys()) - set(db_columns.keys())
    if missing_in_db:
        logger.error(f"❌ Colonnes manquantes en DB: {list(missing_in_db)}")
    else:
        logger.info("✅ Toutes les colonnes du modèle sont présentes en DB")
    
    # Colonnes en DB mais pas dans le modèle
    extra_in_db = set(db_columns.keys()) - set(model_columns.keys())
    if extra_in_db:
        logger.warning(f"⚠️ Colonnes supplémentaires en DB: {list(extra_in_db)}")
    else:
        logger.info("✅ Pas de colonnes supplémentaires en DB")
    
    # Comparaison des types
    common_columns = set(model_columns.keys()) & set(db_columns.keys())
    type_mismatches = []
    
    for col in common_columns:
        model_type = str(model_columns[col]['type']).lower()
        db_type = db_columns[col]['type'].lower()
        
        # Simplifier la comparaison des types
        if 'varchar' in model_type and 'varchar' not in db_type:
            type_mismatches.append(f"{col}: modèle={model_type}, DB={db_type}")
        elif 'int' in model_type and 'int' not in db_type:
            type_mismatches.append(f"{col}: modèle={model_type}, DB={db_type}")
        elif 'float' in model_type and 'float' not in db_type:
            type_mismatches.append(f"{col}: modèle={model_type}, DB={db_type}")
        elif 'datetime' in model_type and 'datetime' not in db_type:
            type_mismatches.append(f"{col}: modèle={model_type}, DB={db_type}")
    
    if type_mismatches:
        logger.warning(f"⚠️ Différences de types: {type_mismatches}")
    else:
        logger.info("✅ Types de colonnes cohérents")
    
    return len(missing_in_db) == 0 and len(type_mismatches) == 0

def verify_all_models():
    """Vérifier tous les modèles avec la base de données"""
    try:
        from backend.database_manager import get_db_session_with_context
        from backend.models.user import User
        from backend.models.ntp_server import NTPServer
        from backend.models.alert import Alert
        from backend.models.system_config import SystemConfig
        from backend.models.alert_threshold import AlertThreshold
        
        logger.info("🔍 VÉRIFICATION APPROFONDIE DU SCHÉMA DE BASE DE DONNÉES")
        logger.info("=" * 60)
        
        models_to_check = [
            (User, 'users'),
            (NTPServer, 'ntp_servers'),
            (Alert, 'alerts'),
            (SystemConfig, 'system_config'),
            (AlertThreshold, 'alert_thresholds')
        ]
        
        all_consistent = True
        
        with get_db_session_with_context() as session:
            for model_class, table_name in models_to_check:
                logger.info(f"\n📋 Vérification du modèle {model_class.__name__} -> table {table_name}")
                
                # Extraire les colonnes du modèle
                model_columns = get_model_columns(model_class)
                logger.info(f"Colonnes du modèle: {list(model_columns.keys())}")
                
                # Extraire les colonnes de la base de données
                db_columns = get_database_columns(session, table_name)
                logger.info(f"Colonnes en DB: {list(db_columns.keys())}")
                
                # Comparer
                is_consistent = compare_columns(model_columns, db_columns, table_name)
                if not is_consistent:
                    all_consistent = False
                
                # Test de requête simple
                try:
                    count = session.query(model_class).count()
                    logger.info(f"✅ Test de requête réussi: {count} enregistrements trouvés")
                except Exception as e:
                    logger.error(f"❌ Erreur lors du test de requête: {e}")
                    all_consistent = False
        
        logger.info("\n" + "=" * 60)
        if all_consistent:
            logger.info("🎉 TOUS LES MODÈLES SONT COHÉRENTS AVEC LA BASE DE DONNÉES!")
            logger.info("✅ Aucun écart détecté entre les modèles et MySQL")
        else:
            logger.error("⚠️ DES ÉCARTS ONT ÉTÉ DÉTECTÉS ENTRE LES MODÈLES ET LA BASE DE DONNÉES")
            logger.info("🔧 Exécutez 'python fix_database_schema.py' pour corriger")
        
        return all_consistent
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification: {e}")
        return False

def test_database_operations():
    """Tester les opérations de base de données"""
    logger.info("\n🧪 TEST DES OPÉRATIONS DE BASE DE DONNÉES")
    
    try:
        from backend.database_manager import get_db_session_with_context
        from backend.models.user import User
        from backend.models.ntp_server import NTPServer
        from backend.models.alert import Alert
        
        with get_db_session_with_context() as session:
            # Test User
            users = session.query(User).limit(5).all()
            logger.info(f"✅ Test User: {len(users)} utilisateurs récupérés")
            
            # Test NTPServer
            servers = session.query(NTPServer).limit(5).all()
            logger.info(f"✅ Test NTPServer: {len(servers)} serveurs récupérés")
            
            # Test Alert
            alerts = session.query(Alert).limit(5).all()
            logger.info(f"✅ Test Alert: {len(alerts)} alertes récupérées")
            
            # Test de création d'un objet (sans sauvegarder)
            test_user = User(username="test_verify", email="test@verify.com", password="test123")
            logger.info("✅ Test de création d'objet réussi")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur lors des tests de base de données: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🚀 VÉRIFICATION APPROFONDIE DU SCHÉMA DE BASE DE DONNÉES")
    logger.info("=" * 60)
    
    # Vérifier la cohérence des modèles
    models_consistent = verify_all_models()
    
    # Tester les opérations de base de données
    operations_ok = test_database_operations()
    
    logger.info("\n" + "=" * 60)
    if models_consistent and operations_ok:
        logger.info("🎉 VÉRIFICATION APPROFONDIE RÉUSSIE!")
        logger.info("✅ Aucun écart entre les modèles et la base de données")
        logger.info("✅ Toutes les opérations de base de données fonctionnent")
        return True
    else:
        logger.error("⚠️ DES PROBLÈMES ONT ÉTÉ DÉTECTÉS")
        if not models_consistent:
            logger.info("🔧 Exécutez: python fix_database_schema.py")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 