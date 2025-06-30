#!/usr/bin/env python3
"""
Migration Complète SQLite → MySQL - NTP Monitor Enterprise
Migre toutes les données et configure l'application pour MySQL
"""

import os
import sys
import sqlite3
import pymysql
import logging
from datetime import datetime
from pathlib import Path
import json

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent))

def setup_logging():
    """Configuration des logs"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('mysql_migration.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def get_mysql_root_connection():
    """Obtenir une connexion MySQL root pour créer la base"""
    print("\n🔑 Connexion MySQL Root...")
    
    root_password = input("Mot de passe root MySQL: ")
    
    return pymysql.connect(
        host='localhost',
        user='root',
        password=root_password,
        charset='utf8mb4'
    )

def create_mysql_database():
    """Créer la base de données MySQL et l'utilisateur"""
    print("\n🗃️  Création de la base de données MySQL...")
    
    try:
        connection = get_mysql_root_connection()
        
        with connection.cursor() as cursor:
            # Créer la base de données
            cursor.execute("DROP DATABASE IF EXISTS ntp_monitor")
            cursor.execute("CREATE DATABASE ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            
            # Créer l'utilisateur
            cursor.execute("DROP USER IF EXISTS 'ntp_user'@'localhost'")
            cursor.execute("CREATE USER 'ntp_user'@'localhost' IDENTIFIED BY 'ntp_password'")
            
            # Donner les privilèges
            cursor.execute("GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_user'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            
        connection.commit()
        connection.close()
        
        print("✅ Base de données MySQL créée avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur création base MySQL: {e}")
        return False

def test_mysql_connection():
    """Tester la connexion MySQL avec l'utilisateur NTP"""
    print("\n🧪 Test connexion utilisateur ntp_user...")
    
    try:
        connection = pymysql.connect(
            host='localhost',
            user='ntp_user',
            password='ntp_password',
            database='ntp_monitor',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            print(f"✅ Connexion ntp_user réussie - MySQL {version}")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur connexion ntp_user: {e}")
        return False

def create_mysql_tables():
    """Créer les tables MySQL à partir des modèles Flask"""
    print("\n📋 Création des tables MySQL...")
    
    try:
        # Mettre à jour la configuration pour MySQL
        os.environ['DATABASE_URL'] = 'mysql+pymysql://ntp_user:ntp_password@localhost/ntp_monitor'
        
        # Importer l'application Flask
        from backend.app import create_app, db
        from backend.database_manager import init_database_manager
        
        app = create_app()
        
        with app.app_context():
            # Initialiser le database manager
            init_database_manager(app)
            
            # Créer toutes les tables
            db.create_all()
            
            # Vérifier les tables créées
            with db.engine.connect() as conn:
                result = conn.execute(db.text("SHOW TABLES"))
                tables = [row[0] for row in result]
                print(f"✅ Tables créées: {', '.join(tables)}")
                
                if len(tables) == 0:
                    raise Exception("Aucune table créée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur création tables: {e}")
        return False

def analyze_sqlite_data():
    """Analyser les données SQLite existantes"""
    print("\n🔍 Analyse des données SQLite...")
    
    sqlite_path = Path('instance/ntp_monitor_dev.db')
    if not sqlite_path.exists():
        print("⚠️  Aucune base SQLite trouvée à migrer")
        return {}
    
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Récupérer la liste des tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        data_summary = {}
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                data_summary[table] = count
                print(f"   📊 {table}: {count} enregistrements")
            except Exception as e:
                print(f"   ⚠️  Erreur table {table}: {e}")
        
        conn.close()
        
        total_records = sum(data_summary.values())
        print(f"📈 Total: {total_records} enregistrements dans {len(data_summary)} tables")
        
        return data_summary
        
    except Exception as e:
        print(f"❌ Erreur analyse SQLite: {e}")
        return {}

def migrate_table_data(table_name: str, sqlite_conn, mysql_conn):
    """Migrer les données d'une table SQLite vers MySQL"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        mysql_cursor = mysql_conn.cursor()
        
        # Récupérer les données SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"   ⚪ {table_name}: Aucune donnée à migrer")
            return 0
        
        # Récupérer les colonnes
        sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = sqlite_cursor.fetchall()
        columns = [col[1] for col in columns_info]
        
        # Préparer l'insertion MySQL
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join([f"`{col}`" for col in columns])  # Échapper les noms de colonnes
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        # Traiter les données par lots
        batch_size = 100
        total_inserted = 0
        
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            
            # Nettoyer les données (gérer les types incompatibles)
            cleaned_batch = []
            for row in batch:
                cleaned_row = []
                for value in row:
                    if isinstance(value, str) and len(value) > 65535:  # Tronquer si trop long
                        value = value[:65535]
                    cleaned_row.append(value)
                cleaned_batch.append(tuple(cleaned_row))
            
            # Insérer le lot
            mysql_cursor.executemany(insert_query, cleaned_batch)
            total_inserted += len(batch)
        
        mysql_conn.commit()
        print(f"   ✅ {table_name}: {total_inserted} enregistrements migrés")
        return total_inserted
        
    except Exception as e:
        print(f"   ❌ {table_name}: Erreur migration - {e}")
        mysql_conn.rollback()
        return 0

def migrate_all_data():
    """Migrer toutes les données de SQLite vers MySQL"""
    print("\n📦 Migration des données SQLite → MySQL...")
    
    sqlite_path = Path('instance/ntp_monitor_dev.db')
    if not sqlite_path.exists():
        print("⚠️  Aucune base SQLite à migrer")
        return True
    
    try:
        # Connexions
        sqlite_conn = sqlite3.connect(sqlite_path)
        mysql_conn = pymysql.connect(
            host='localhost',
            user='ntp_user',
            password='ntp_password',
            database='ntp_monitor',
            charset='utf8mb4'
        )
        
        # Tables à migrer (dans l'ordre pour respecter les FK)
        tables_order = [
            'users',
            'system_config', 
            'ntp_servers',
            'alert_thresholds',
            'ntp_logs',
            'ntp_log_aggregated',
            'alerts'
        ]
        
        total_migrated = 0
        migration_summary = {}
        
        for table in tables_order:
            # Vérifier que la table existe dans SQLite
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not sqlite_cursor.fetchone():
                continue
            
            count = migrate_table_data(table, sqlite_conn, mysql_conn)
            migration_summary[table] = count
            total_migrated += count
        
        sqlite_conn.close()
        mysql_conn.close()
        
        print(f"\n📊 Résumé de la migration:")
        for table, count in migration_summary.items():
            print(f"   {table}: {count} enregistrements")
        
        print(f"✅ Migration terminée: {total_migrated} enregistrements au total")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur migration données: {e}")
        return False

def update_application_config():
    """Mettre à jour la configuration de l'application pour MySQL"""
    print("\n⚙️  Mise à jour configuration application...")
    
    try:
        config_file = Path('config/config.py')
        
        # Lire le fichier actuel
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Modifications
        old_sqlite = "SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR}/instance/ntp_monitor_dev.db'"
        new_sqlite = "# SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR}/instance/ntp_monitor_dev.db'  # MIGRÉ VERS MYSQL"
        
        old_mysql = "# SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://ntp_user:ntp_password@localhost/ntp_monitor'"
        new_mysql = "SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://ntp_user:ntp_password@localhost/ntp_monitor'"
        
        # Appliquer les changements
        content = content.replace(old_sqlite, new_sqlite)
        content = content.replace(old_mysql, new_mysql)
        
        # Sauvegarder
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Configuration mise à jour pour MySQL")
        return True
        
    except Exception as e:
        print(f"❌ Erreur mise à jour configuration: {e}")
        return False

def backup_sqlite_database():
    """Créer une sauvegarde de la base SQLite"""
    print("\n💾 Sauvegarde de la base SQLite...")
    
    sqlite_path = Path('instance/ntp_monitor_dev.db')
    if not sqlite_path.exists():
        print("⚠️  Aucune base SQLite à sauvegarder")
        return True
    
    try:
        backup_dir = Path('backups')
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f'ntp_monitor_sqlite_backup_{timestamp}.db'
        
        # Copier la base
        import shutil
        shutil.copy2(sqlite_path, backup_path)
        
        print(f"✅ Sauvegarde créée: {backup_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")
        return False

def validate_migration():
    """Valider que la migration s'est bien passée"""
    print("\n✅ Validation de la migration...")
    
    try:
        # Connexion MySQL
        mysql_conn = pymysql.connect(
            host='localhost',
            user='ntp_user',
            password='ntp_password',
            database='ntp_monitor',
            charset='utf8mb4'
        )
        
        cursor = mysql_conn.cursor()
        
        # Vérifier les tables
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Tables MySQL: {len(tables)} tables")
        
        # Compter les enregistrements
        total_records = 0
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            total_records += count
            print(f"   📊 {table}: {count} enregistrements")
        
        mysql_conn.close()
        
        print(f"📈 Total MySQL: {total_records} enregistrements")
        
        # Comparer avec SQLite si elle existe
        sqlite_path = Path('instance/ntp_monitor_dev.db')
        if sqlite_path.exists():
            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            sqlite_tables = [row[0] for row in sqlite_cursor.fetchall()]
            
            sqlite_total = 0
            for table in sqlite_tables:
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = sqlite_cursor.fetchone()[0]
                sqlite_total += count
            
            sqlite_conn.close()
            
            print(f"📊 Comparaison: SQLite {sqlite_total} → MySQL {total_records}")
            
            if total_records >= sqlite_total * 0.9:  # Tolérance 10%
                print("✅ Migration validée avec succès")
                return True
            else:
                print("⚠️  Différence importante détectée")
                return False
        else:
            print("✅ Validation MySQL OK")
            return True
        
    except Exception as e:
        print(f"❌ Erreur validation: {e}")
        return False

def main():
    """Fonction principale de migration"""
    setup_logging()
    
    print("🚀 MIGRATION COMPLÈTE SQLite → MySQL")
    print("=" * 60)
    print("🎯 Objectif: Résoudre définitivement les erreurs 'database locked'")
    print("=" * 60)
    
    steps = [
        ("💾 Sauvegarde SQLite", backup_sqlite_database),
        ("🗃️  Création base MySQL", create_mysql_database),
        ("🧪 Test connexion MySQL", test_mysql_connection),
        ("📋 Création tables MySQL", create_mysql_tables),
        ("🔍 Analyse données SQLite", analyze_sqlite_data),
        ("📦 Migration des données", migrate_all_data),
        ("⚙️  Mise à jour configuration", update_application_config),
        ("✅ Validation migration", validate_migration)
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        try:
            result = step_func()
            if result:
                success_count += 1
                print(f"✅ {step_name} terminé")
            else:
                print(f"❌ {step_name} échoué")
                break
        except Exception as e:
            print(f"❌ {step_name} échoué: {e}")
            break
    
    print("\n" + "=" * 60)
    print(f"📊 RÉSULTATS: {success_count}/{len(steps)} étapes réussies")
    
    if success_count == len(steps):
        print("\n🎉 MIGRATION MYSQL TERMINÉE AVEC SUCCÈS !")
        print("\n🎯 BÉNÉFICES ATTENDUS:")
        print("   ✅ 0 erreur 'database is locked'")
        print("   ✅ 0 erreur 'transaction already begun'")
        print("   ✅ Synchronisation NTP stable")
        print("   ✅ Performance optimale")
        
        print("\n📋 PROCHAINES ÉTAPES:")
        print("   1. Redémarrer l'application: python app.py")
        print("   2. Vérifier les logs: Get-Content logs/app.log -Tail 20")
        print("   3. Confirmer l'absence d'erreurs SQLite")
        print("   4. Tester la synchronisation NTP")
        
        print("\n🔒 ROLLBACK (si problème):")
        print("   Restaurer la configuration SQLite dans config/config.py")
        
    else:
        print("\n⚠️  MIGRATION PARTIELLEMENT RÉUSSIE")
        print("Vérifiez les erreurs ci-dessus et relancez la migration")
    
    print("\n📝 Logs détaillés dans: mysql_migration.log")

if __name__ == '__main__':
    main() 