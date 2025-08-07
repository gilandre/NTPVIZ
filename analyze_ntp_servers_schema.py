#!/usr/bin/env python3
"""
Script d'analyse holistique et détaillée de la table ntp_servers
Compare le modèle Python avec la structure MySQL réelle
"""
import sys
import logging
from pathlib import Path
from sqlalchemy import text, inspect, MetaData
from sqlalchemy.engine import reflection

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

def get_detailed_model_info(model_class):
    """Obtenir des informations détaillées sur le modèle SQLAlchemy"""
    logger.info(f"\n📋 ANALYSE DÉTAILLÉE DU MODÈLE {model_class.__name__}")
    logger.info("=" * 60)
    
    columns_info = {}
    for column in model_class.__table__.columns:
        column_info = {
            'name': column.name,
            'type': str(column.type),
            'nullable': column.nullable,
            'default': column.default,
            'primary_key': column.primary_key,
            'unique': column.unique,
            'index': column.index,
            'foreign_key': column.foreign_keys,
            'comment': getattr(column, 'comment', None)
        }
        columns_info[column.name] = column_info
        
        logger.info(f"  📝 {column.name}:")
        logger.info(f"    - Type: {column.type}")
        logger.info(f"    - Nullable: {column.nullable}")
        logger.info(f"    - Primary Key: {column.primary_key}")
        logger.info(f"    - Unique: {column.unique}")
        logger.info(f"    - Index: {column.index}")
        if column.default:
            logger.info(f"    - Default: {column.default}")
        if column.foreign_keys:
            logger.info(f"    - Foreign Keys: {column.foreign_keys}")
    
    return columns_info

def get_detailed_database_info(session, table_name):
    """Obtenir des informations détaillées sur la table MySQL"""
    logger.info(f"\n🗄️ ANALYSE DÉTAILLÉE DE LA TABLE {table_name}")
    logger.info("=" * 60)
    
    try:
        # Informations de base sur la table
        result = session.execute(text(f"SHOW TABLE STATUS LIKE '{table_name}'"))
        table_info = result.fetchone()
        if table_info:
            logger.info(f"  📊 Informations de la table:")
            logger.info(f"    - Nom: {table_info[0]}")
            logger.info(f"    - Engine: {table_info[1]}")
            logger.info(f"    - Version: {table_info[2]}")
            logger.info(f"    - Row Format: {table_info[3]}")
            logger.info(f"    - Rows: {table_info[4]}")
            logger.info(f"    - Avg Row Length: {table_info[5]}")
            logger.info(f"    - Data Length: {table_info[6]}")
            logger.info(f"    - Max Data Length: {table_info[7]}")
            logger.info(f"    - Index Length: {table_info[8]}")
            logger.info(f"    - Data Free: {table_info[9]}")
            logger.info(f"    - Auto Increment: {table_info[10]}")
            logger.info(f"    - Create Time: {table_info[11]}")
            logger.info(f"    - Update Time: {table_info[12]}")
            logger.info(f"    - Check Time: {table_info[13]}")
            logger.info(f"    - Collation: {table_info[14]}")
            logger.info(f"    - Checksum: {table_info[15]}")
            logger.info(f"    - Create Options: {table_info[16]}")
            logger.info(f"    - Comment: {table_info[17]}")
        
        # Structure détaillée des colonnes
        result = session.execute(text(f"DESCRIBE {table_name}"))
        columns_info = {}
        
        logger.info(f"\n  📝 Structure détaillée des colonnes:")
        for row in result.fetchall():
            column_name = row[0]
            column_type = row[1]
            is_null = row[2]
            key = row[3]
            default = row[4]
            extra = row[5]
            
            columns_info[column_name] = {
                'name': column_name,
                'type': column_type,
                'nullable': is_null == 'YES',
                'key': key,
                'default': default,
                'extra': extra
            }
            
            logger.info(f"    📝 {column_name}:")
            logger.info(f"      - Type: {column_type}")
            logger.info(f"      - Nullable: {is_null}")
            logger.info(f"      - Key: {key}")
            logger.info(f"      - Default: {default}")
            logger.info(f"      - Extra: {extra}")
        
        # Index de la table
        result = session.execute(text(f"SHOW INDEX FROM {table_name}"))
        indexes = {}
        logger.info(f"\n  🔍 Index de la table:")
        for row in result.fetchall():
            index_name = row[2]
            column_name = row[4]
            non_unique = row[1]
            seq_in_index = row[3]
            cardinality = row[6]
            sub_part = row[7]
            packed = row[8]
            null = row[9]
            index_type = row[10]
            comment = row[11]
            
            if index_name not in indexes:
                indexes[index_name] = []
            
            indexes[index_name].append({
                'column': column_name,
                'non_unique': non_unique,
                'seq_in_index': seq_in_index,
                'cardinality': cardinality,
                'sub_part': sub_part,
                'packed': packed,
                'null': null,
                'index_type': index_type,
                'comment': comment
            })
            
            logger.info(f"    🔍 {index_name} ({column_name}):")
            logger.info(f"      - Non Unique: {non_unique}")
            logger.info(f"      - Sequence: {seq_in_index}")
            logger.info(f"      - Cardinality: {cardinality}")
            logger.info(f"      - Index Type: {index_type}")
            if comment:
                logger.info(f"      - Comment: {comment}")
        
        return columns_info, indexes
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse de la table {table_name}: {e}")
        return {}, {}

def compare_detailed_schemas(model_columns, db_columns, table_name):
    """Comparaison détaillée des schémas"""
    logger.info(f"\n🔍 COMPARAISON DÉTAILLÉE DES SCHÉMAS")
    logger.info("=" * 60)
    
    # Colonnes dans le modèle mais pas en DB
    missing_in_db = set(model_columns.keys()) - set(db_columns.keys())
    if missing_in_db:
        logger.error(f"❌ Colonnes manquantes en DB:")
        for col in missing_in_db:
            model_info = model_columns[col]
            logger.error(f"    - {col}: {model_info['type']} (nullable={model_info['nullable']})")
    else:
        logger.info("✅ Toutes les colonnes du modèle sont présentes en DB")
    
    # Colonnes en DB mais pas dans le modèle
    extra_in_db = set(db_columns.keys()) - set(model_columns.keys())
    if extra_in_db:
        logger.warning(f"⚠️ Colonnes supplémentaires en DB:")
        for col in extra_in_db:
            db_info = db_columns[col]
            logger.warning(f"    - {col}: {db_info['type']} (nullable={db_info['nullable']})")
    else:
        logger.info("✅ Pas de colonnes supplémentaires en DB")
    
    # Comparaison détaillée des types
    common_columns = set(model_columns.keys()) & set(db_columns.keys())
    type_analysis = []
    
    logger.info(f"\n📊 Analyse détaillée des types pour {len(common_columns)} colonnes communes:")
    for col in common_columns:
        model_info = model_columns[col]
        db_info = db_columns[col]
        
        model_type = str(model_info['type']).lower()
        db_type = db_info['type'].lower()
        
        # Analyse détaillée des types
        type_compatibility = "✅ Compatible"
        if 'varchar' in model_type and 'varchar' not in db_type:
            type_compatibility = "⚠️ Différence VARCHAR"
        elif 'int' in model_type and 'int' not in db_type:
            type_compatibility = "⚠️ Différence INT"
        elif 'float' in model_type and 'float' not in db_type:
            type_compatibility = "⚠️ Différence FLOAT"
        elif 'datetime' in model_type and 'datetime' not in db_type:
            type_compatibility = "⚠️ Différence DATETIME"
        
        type_analysis.append({
            'column': col,
            'model_type': model_type,
            'db_type': db_type,
            'compatibility': type_compatibility,
            'model_nullable': model_info['nullable'],
            'db_nullable': db_info['nullable']
        })
        
        logger.info(f"    📝 {col}:")
        logger.info(f"      - Modèle: {model_type} (nullable={model_info['nullable']})")
        logger.info(f"      - DB: {db_type} (nullable={db_info['nullable']})")
        logger.info(f"      - Compatibilité: {type_compatibility}")
    
    return type_analysis

def test_ntp_servers_operations(session):
    """Tester les opérations spécifiques à ntp_servers"""
    logger.info(f"\n🧪 TESTS DES OPÉRATIONS NTP_SERVERS")
    logger.info("=" * 60)
    
    try:
        # Test de lecture
        servers = session.execute(text("SELECT COUNT(*) FROM ntp_servers")).fetchone()[0]
        logger.info(f"✅ Nombre total de serveurs: {servers}")
        
        # Test de lecture avec filtres
        active_servers = session.execute(text("SELECT COUNT(*) FROM ntp_servers WHERE is_active = 1")).fetchone()[0]
        logger.info(f"✅ Serveurs actifs: {active_servers}")
        
        # Test de lecture avec jointures (si applicable)
        try:
            result = session.execute(text("""
                SELECT s.name, s.address, COUNT(a.id) as alert_count 
                FROM ntp_servers s 
                LEFT JOIN alerts a ON s.id = a.server_id 
                GROUP BY s.id 
                LIMIT 5
            """))
            logger.info("✅ Test de jointure avec alerts réussi")
        except Exception as e:
            logger.warning(f"⚠️ Test de jointure échoué: {e}")
        
        # Test de création d'un objet (sans sauvegarder)
        from backend.models.ntp_server import NTPServer
        test_server = NTPServer(
            name="test_server",
            address="test.example.com",
            port=123,
            server_type="global",
            is_active=True
        )
        logger.info("✅ Test de création d'objet NTPServer réussi")
        
        # Test des propriétés du modèle
        logger.info(f"✅ Propriétés du modèle testées:")
        logger.info(f"    - name: {test_server.name}")
        logger.info(f"    - address: {test_server.address}")
        logger.info(f"    - port: {test_server.port}")
        logger.info(f"    - server_type: {test_server.server_type}")
        logger.info(f"    - is_active: {test_server.is_active}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors des tests: {e}")
        return False

def analyze_data_quality(session):
    """Analyser la qualité des données"""
    logger.info(f"\n📊 ANALYSE DE LA QUALITÉ DES DONNÉES")
    logger.info("=" * 60)
    
    try:
        # Statistiques générales
        total_servers = session.execute(text("SELECT COUNT(*) FROM ntp_servers")).fetchone()[0]
        active_servers = session.execute(text("SELECT COUNT(*) FROM ntp_servers WHERE is_active = 1")).fetchone()[0]
        inactive_servers = session.execute(text("SELECT COUNT(*) FROM ntp_servers WHERE is_active = 0")).fetchone()[0]
        
        logger.info(f"📈 Statistiques générales:")
        logger.info(f"    - Total serveurs: {total_servers}")
        logger.info(f"    - Serveurs actifs: {active_servers}")
        logger.info(f"    - Serveurs inactifs: {inactive_servers}")
        logger.info(f"    - Taux d'activation: {active_servers/total_servers*100:.1f}%")
        
        # Analyse des types de serveurs
        server_types = session.execute(text("""
            SELECT server_type, COUNT(*) as count 
            FROM ntp_servers 
            GROUP BY server_type
        """)).fetchall()
        
        logger.info(f"\n🏷️ Types de serveurs:")
        for server_type, count in server_types:
            logger.info(f"    - {server_type}: {count}")
        
        # Analyse des ports
        ports = session.execute(text("""
            SELECT port, COUNT(*) as count 
            FROM ntp_servers 
            GROUP BY port 
            ORDER BY count DESC 
            LIMIT 5
        """)).fetchall()
        
        logger.info(f"\n🔌 Ports les plus utilisés:")
        for port, count in ports:
            logger.info(f"    - Port {port}: {count} serveurs")
        
        # Analyse des statuts
        statuses = session.execute(text("""
            SELECT status, COUNT(*) as count 
            FROM ntp_servers 
            GROUP BY status
        """)).fetchall()
        
        logger.info(f"\n📊 Statuts des serveurs:")
        for status, count in statuses:
            logger.info(f"    - {status}: {count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse des données: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🚀 ANALYSE HOLISTIQUE ET DÉTAILLÉE DE LA TABLE NTP_SERVERS")
    logger.info("=" * 80)
    
    try:
        from backend.database_manager import get_db_session_with_context
        from backend.models.ntp_server import NTPServer
        
        with get_db_session_with_context() as session:
            # 1. Analyse détaillée du modèle
            model_columns = get_detailed_model_info(NTPServer)
            
            # 2. Analyse détaillée de la base de données
            db_columns, indexes = get_detailed_database_info(session, 'ntp_servers')
            
            # 3. Comparaison détaillée
            type_analysis = compare_detailed_schemas(model_columns, db_columns, 'ntp_servers')
            
            # 4. Tests des opérations
            operations_ok = test_ntp_servers_operations(session)
            
            # 5. Analyse de la qualité des données
            data_quality_ok = analyze_data_quality(session)
            
            # 6. Résumé final
            logger.info(f"\n🎯 RÉSUMÉ FINAL DE L'ANALYSE")
            logger.info("=" * 80)
            
            missing_count = len(set(model_columns.keys()) - set(db_columns.keys()))
            extra_count = len(set(db_columns.keys()) - set(model_columns.keys()))
            type_issues = len([a for a in type_analysis if '⚠️' in a['compatibility']])
            
            logger.info(f"📊 Métriques de cohérence:")
            logger.info(f"    - Colonnes manquantes en DB: {missing_count}")
            logger.info(f"    - Colonnes supplémentaires en DB: {extra_count}")
            logger.info(f"    - Problèmes de types: {type_issues}")
            logger.info(f"    - Tests d'opérations: {'✅ Réussi' if operations_ok else '❌ Échec'}")
            logger.info(f"    - Qualité des données: {'✅ OK' if data_quality_ok else '❌ Problème'}")
            
            if missing_count == 0 and type_issues == 0 and operations_ok:
                logger.info("🎉 ANALYSE HOLISTIQUE RÉUSSIE - Aucun problème critique détecté!")
                return True
            else:
                logger.warning("⚠️ DES PROBLÈMES ONT ÉTÉ DÉTECTÉS - Vérification recommandée")
                return False
                
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 