#!/usr/bin/env python3
"""
Script de configuration MySQL pour NTP Monitor Enterprise
Migre les données de SQLite vers MySQL et teste la performance
"""

import os
import sys
import sqlite3
import pymysql
import logging
from datetime import datetime
from pathlib import Path

# Configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'ntp_user',
    'password': 'ntp_password',
    'database': 'ntp_monitor',
    'charset': 'utf8mb4'
}

SQLITE_DB = Path('instance/ntp_monitor_dev.db')

def setup_logging():
    """Configuration des logs"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('mysql_migration.log'),
            logging.StreamHandler()
        ]
    )

def create_mysql_database():
    """Créer la base de données MySQL et l'utilisateur"""
    print("\n🔧 Création de la base de données MySQL...")
    
    try:
        # Connexion en tant que root pour créer la BD
        root_password = input("Mot de passe root MySQL: ")
        
        connection = pymysql.connect(
            host=MYSQL_CONFIG['host'],
            user='root',
            password=root_password,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Créer la base de données
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            
            # Créer l'utilisateur
            cursor.execute(f"CREATE USER IF NOT EXISTS '{MYSQL_CONFIG['user']}'@'localhost' IDENTIFIED BY '{MYSQL_CONFIG['password']}'")
            
            # Donner les privilèges
            cursor.execute(f"GRANT ALL PRIVILEGES ON {MYSQL_CONFIG['database']}.* TO '{MYSQL_CONFIG['user']}'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            
        connection.commit()
        connection.close()
        
        print("✅ Base de données MySQL créée avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de la BD: {e}")
        return False

def test_mysql_connection():
    """Tester la connexion MySQL"""
    print("\n🧪 Test de la connexion MySQL...")
    
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ Connexion MySQL réussie - Version: {version[0]}")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion MySQL: {e}")
        return False

def create_mysql_tables():
    """Créer les tables MySQL à partir du modèle Flask"""
    print("\n📋 Création des tables MySQL...")
    
    # Importer l'application Flask pour créer les tables
    sys.path.append(str(Path.cwd()))
    
    try:
        from backend.app import create_app, db
        
        # Créer l'application avec configuration MySQL
        os.environ['DATABASE_URL'] = f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}"
        
        app = create_app()
        
        with app.app_context():
            # Créer toutes les tables
            db.create_all()
            print("✅ Tables MySQL créées avec succès")
            
            # Afficher les tables créées
            with db.engine.connect() as conn:
                result = conn.execute(db.text("SHOW TABLES"))
                tables = [row[0] for row in result]
                print(f"📊 Tables créées: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables: {e}")
        return False

def migrate_data():
    """Migrer les données de SQLite vers MySQL"""
    print("\n📦 Migration des données SQLite → MySQL...")
    
    if not SQLITE_DB.exists():
        print("⚠️  Pas de base SQLite à migrer")
        return True
    
    try:
        # Connexion SQLite
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Connexion MySQL
        mysql_conn = pymysql.connect(**MYSQL_CONFIG)
        mysql_cursor = mysql_conn.cursor()
        
        # Tables à migrer
        tables_to_migrate = [
            'users', 'ntp_servers', 'ntp_logs', 'alerts', 
            'alert_thresholds', 'system_config', 'ntp_log_aggregated'
        ]
        
        total_records = 0
        
        for table in tables_to_migrate:
            try:
                # Vérifier si la table existe dans SQLite
                sqlite_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not sqlite_cursor.fetchone():
                    continue
                
                # Récupérer les données SQLite
                sqlite_cursor.execute(f"SELECT * FROM {table}")
                rows = sqlite_cursor.fetchall()
                
                if not rows:
                    continue
                
                # Récupérer les colonnes
                sqlite_cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in sqlite_cursor.fetchall()]
                
                # Préparer l'insertion MySQL
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join(columns)
                insert_query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
                
                # Insérer les données
                mysql_cursor.executemany(insert_query, rows)
                mysql_conn.commit()
                
                print(f"✅ {table}: {len(rows)} enregistrements migrés")
                total_records += len(rows)
                
            except Exception as e:
                print(f"⚠️  Erreur migration {table}: {e}")
        
        sqlite_conn.close()
        mysql_conn.close()
        
        print(f"✅ Migration terminée: {total_records} enregistrements au total")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        return False

def test_concurrency():
    """Tester la performance de concurrence MySQL vs SQLite"""
    print("\n⚡ Test de performance et concurrence...")
    
    import threading
    import time
    
    def mysql_test():
        """Test MySQL"""
        try:
            connection = pymysql.connect(**MYSQL_CONFIG)
            start_time = time.time()
            
            with connection.cursor() as cursor:
                for i in range(100):
                    cursor.execute("INSERT INTO ntp_logs (server_id, timestamp, success) VALUES (%s, %s, %s)", 
                                 (1, datetime.now(), True))
                connection.commit()
            
            connection.close()
            return time.time() - start_time
            
        except Exception as e:
            print(f"Erreur test MySQL: {e}")
            return float('inf')
    
    def sqlite_test():
        """Test SQLite"""
        try:
            connection = sqlite3.connect(SQLITE_DB)
            start_time = time.time()
            
            cursor = connection.cursor()
            for i in range(100):
                cursor.execute("INSERT INTO ntp_logs (server_id, timestamp, success) VALUES (?, ?, ?)", 
                             (1, datetime.now(), True))
            connection.commit()
            connection.close()
            
            return time.time() - start_time
            
        except Exception as e:
            print(f"Erreur test SQLite: {e}")
            return float('inf')
    
    # Test séquentiel
    print("📊 Test séquentiel (1 thread)...")
    mysql_time = mysql_test()
    sqlite_time = sqlite_test()
    
    print(f"   MySQL: {mysql_time:.3f}s")
    print(f"   SQLite: {sqlite_time:.3f}s")
    
    # Test concurrent
    print("📊 Test concurrent (5 threads)...")
    
    # MySQL concurrent
    threads = []
    mysql_times = []
    
    def mysql_thread():
        mysql_times.append(mysql_test())
    
    start = time.time()
    for _ in range(5):
        t = threading.Thread(target=mysql_thread)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    mysql_concurrent = time.time() - start
    
    print(f"   MySQL concurrent: {mysql_concurrent:.3f}s (max thread: {max(mysql_times):.3f}s)")
    
    # SQLite concurrent (sera probablement bloqué)
    try:
        sqlite_times = []
        threads = []
        
        def sqlite_thread():
            sqlite_times.append(sqlite_test())
        
        start = time.time()
        for _ in range(5):
            t = threading.Thread(target=sqlite_thread)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        sqlite_concurrent = time.time() - start
        print(f"   SQLite concurrent: {sqlite_concurrent:.3f}s (max thread: {max(sqlite_times):.3f}s)")
        
    except Exception as e:
        print(f"   SQLite concurrent: ÉCHEC - {e}")

def update_config():
    """Mettre à jour la configuration pour utiliser MySQL"""
    print("\n⚙️  Mise à jour de la configuration...")
    
    config_file = Path('config/config.py')
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Commenter SQLite et décommenter MySQL
        content = content.replace(
            "SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR}/instance/ntp_monitor_dev.db'",
            "# SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR}/instance/ntp_monitor_dev.db'"
        )
        
        content = content.replace(
            "# SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://ntp_user:ntp_password@localhost/ntp_monitor'",
            "SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://ntp_user:ntp_password@localhost/ntp_monitor'"
        )
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Configuration mise à jour pour MySQL")
        return True
        
    except Exception as e:
        print(f"❌ Erreur mise à jour config: {e}")
        return False

def main():
    """Fonction principale"""
    setup_logging()
    
    print("🚀 Configuration MySQL pour NTP Monitor Enterprise")
    print("=" * 60)
    
    steps = [
        ("Création base de données MySQL", create_mysql_database),
        ("Test connexion MySQL", test_mysql_connection),
        ("Création des tables", create_mysql_tables),
        ("Migration des données", migrate_data),
        ("Test de performance", test_concurrency),
        ("Mise à jour configuration", update_config)
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        try:
            if step_func():
                success_count += 1
                print(f"✅ {step_name} terminé")
            else:
                print(f"❌ {step_name} échoué")
        except Exception as e:
            print(f"❌ {step_name} échoué: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Résultats: {success_count}/{len(steps)} étapes réussies")
    
    if success_count == len(steps):
        print("🎉 Migration MySQL terminée avec succès !")
        print("\n📋 Prochaines étapes:")
        print("   1. Installer PyMySQL: pip install PyMySQL==1.1.0")
        print("   2. Redémarrer l'application: python app.py")
        print("   3. Vérifier les logs pour confirmer l'absence d'erreurs 'database locked'")
    else:
        print("⚠️  Migration partiellement réussie - Vérifiez les erreurs ci-dessus")

if __name__ == '__main__':
    main() 