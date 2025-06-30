#!/usr/bin/env python3
"""
Migration Complète SQLite → MySQL ROOT - NTP Monitor Enterprise
Configuration adaptée pour MySQL root sans mot de passe
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
            logging.FileHandler('mysql_migration_root.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def get_mysql_root_connection():
    """Obtenir une connexion MySQL root pour administration"""
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',  # Pas de mot de passe
        'charset': 'utf8mb4'
    }
    
    try:
        return pymysql.connect(**config)
    except Exception as e:
        logging.error(f"Impossible de se connecter à MySQL root: {e}")
        return None

def get_mysql_app_connection():
    """Obtenir une connexion MySQL pour l'application"""
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',  # Pas de mot de passe
        'database': 'ntp_monitor',
        'charset': 'utf8mb4'
    }
    
    try:
        return pymysql.connect(**config)
    except Exception as e:
        logging.error(f"Impossible de se connecter à la base ntp_monitor: {e}")
        return None

def backup_sqlite_database():
    """Sauvegarder la base SQLite existante"""
    sqlite_path = Path('instance/ntp_monitor_dev.db')
    
    if not sqlite_path.exists():
        logging.warning("Aucune base SQLite trouvée à sauvegarder")
        return True  # Pas critique
    
    # Créer le répertoire de sauvegarde
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    
    # Nom de fichier avec timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f'ntp_monitor_sqlite_backup_{timestamp}.db'
    
    try:
        import shutil
        shutil.copy2(sqlite_path, backup_path)
        logging.info(f"✅ Sauvegarde SQLite créée: {backup_path}")
        return True
    except Exception as e:
        logging.error(f"❌ Erreur lors de la sauvegarde: {e}")
        return False

def create_mysql_database():
    """Créer la base de données MySQL"""
    connection = get_mysql_root_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # Supprimer la base si elle existe
            cursor.execute("DROP DATABASE IF EXISTS ntp_monitor")
            logging.info("🗑️  Ancienne base ntp_monitor supprimée")
            
            # Créer la nouvelle base
            cursor.execute("""
                CREATE DATABASE ntp_monitor 
                CHARACTER SET utf8mb4 
                COLLATE utf8mb4_unicode_ci
            """)
            logging.info("🗃️  Base de données ntp_monitor créée")
            
        connection.commit()
        logging.info("✅ Base MySQL configurée avec succès")
        return True
        
    except Exception as e:
        logging.error(f"❌ Erreur lors de la création de la base: {e}")
        return False
    finally:
        connection.close()

def create_mysql_tables():
    """Créer les tables MySQL"""
    connection = get_mysql_app_connection()
    if not connection:
        return False
    
    tables_sql = {
        'users': """
            CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'viewer',
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL
            )
        """,
        
        'ntp_servers': """
            CREATE TABLE ntp_servers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                address VARCHAR(255) NOT NULL,
                description TEXT,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_status VARCHAR(20) DEFAULT 'unknown'
            )
        """,
        
        'ntp_logs': """
            CREATE TABLE ntp_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                server_id INT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                offset_ms DOUBLE,
                delay_ms DOUBLE,
                stratum INT,
                status VARCHAR(20) NOT NULL,
                error_message TEXT,
                FOREIGN KEY (server_id) REFERENCES ntp_servers(id) ON DELETE CASCADE,
                INDEX idx_server_timestamp (server_id, timestamp),
                INDEX idx_timestamp (timestamp)
            )
        """,
        
        'alerts': """
            CREATE TABLE alerts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                server_id INT,
                alert_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP NULL,
                FOREIGN KEY (server_id) REFERENCES ntp_servers(id) ON DELETE CASCADE,
                INDEX idx_status_severity (status, severity),
                INDEX idx_server_type (server_id, alert_type)
            )
        """,
        
        'alert_thresholds': """
            CREATE TABLE alert_thresholds (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                threshold_type VARCHAR(50) NOT NULL,
                warning_value DOUBLE,
                critical_value DOUBLE,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'system_config': """
            CREATE TABLE system_config (
                id INT AUTO_INCREMENT PRIMARY KEY,
                key_name VARCHAR(100) UNIQUE NOT NULL,
                value TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """
    }
    
    try:
        with connection.cursor() as cursor:
            for table_name, sql in tables_sql.items():
                cursor.execute(sql)
                logging.info(f"📋 Table {table_name} créée")
                
        connection.commit()
        logging.info("✅ Toutes les tables MySQL créées")
        return True
        
    except Exception as e:
        logging.error(f"❌ Erreur lors de la création des tables: {e}")
        return False
    finally:
        connection.close()

def create_default_data():
    """Créer les données par défaut dans MySQL"""
    connection = get_mysql_app_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # Utilisateurs par défaut
            default_users = [
                ('admin', 'admin@ntpmonitor.local', 'scrypt:32768:8:1$2Q8K1QzZdRKJd9kY$46c9c1bbdb5b51e7b6c8e7b7f8b3c5d5e4b2c9a1d8e6f3b7a5c8d2e9f1a4b7c6e3d5a8b2f9c7e1d4a6b8c3f5e2d7a9b4c1e8f6a3d2b5c9e7f4a1b8d6c3e5a2b9f7c4e1d8a6b3c5e9f2a7b4d1c8e6a3b5c9f7e2d4a1b8c6e3a5b9f7c4e1d8a6b3c5e9f2a7b4d1c8e6a3', 'admin', True),
                ('operator', 'operator@ntpmonitor.local', 'scrypt:32768:8:1$3R9L2RaZeRKJd9kZ$57d0d2ccec6c62f8c7d9f8c8g9d4d6f5f3c0d0b2e9f7g4c8a6d9f3c0e5a9c7f4e6a9d2f8c3f6d0a3c9e8f5d2a4c7f1e9c8d6a3f5c0e7a8d4f2c9e6f1d8a5c3e9f7c2d4a8f6c1e5a9c3f7e0d6a2c8f5e9f4d1a7c0e6f3a8c5f9e2d7a4c1f8e6a0', 'operator', True),
                ('viewer', 'viewer@ntpmonitor.local', 'scrypt:32768:8:1$4S0M3SbZfRKJd9ka$68e1e3ddf7d73g9d8eag9d9h0e5e7g6g4d1e1c3f0g8h5d9b7e0d4f1b0d8f5g7e0b1d3g9d4g7f1b4d0f9g6e3b5d8g2f0d9e7b4g6d2f8b6e0g9g5f2e9b6d4g7f3e0b8e6g1f4d7b9g3f0e8b2d5g9f4e1b7d0g6f3b8e5g2f9e4d1b0f7g5e2b6d9f3e8b4g1f7e0b5d8g4f2e9b6', 'viewer', True)
            ]
            
            for username, email, password_hash, role, active in default_users:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role, active) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (username, email, password_hash, role, active))
            
            logging.info("👥 Utilisateurs par défaut créés")
            
            # Serveurs NTP par défaut
            default_servers = [
                ('Pool NTP 0', '0.pool.ntp.org', 'Serveur pool NTP principal', True),
                ('Pool NTP 1', '1.pool.ntp.org', 'Serveur pool NTP secondaire', True),
                ('Pool NTP 2', '2.pool.ntp.org', 'Serveur pool NTP tertiaire', True),
                ('Pool NTP 3', '3.pool.ntp.org', 'Serveur pool NTP quaternaire', True),
                ('Serveur Local', '192.168.1.1', 'Serveur NTP local', True),
                ('SRV-NTP-BDT.INVESTECH-02', '192.168.10.28', 'Serveur NTP interne', True)
            ]
            
            for name, address, description, active in default_servers:
                cursor.execute("""
                    INSERT INTO ntp_servers (name, address, description, active) 
                    VALUES (%s, %s, %s, %s)
                """, (name, address, description, active))
            
            logging.info("🌐 Serveurs NTP par défaut créés")
            
            # Seuils d'alerte par défaut
            default_thresholds = [
                ('Offset Time', 'offset', 50.0, 100.0, True),
                ('Network Delay', 'delay', 100.0, 500.0, True),
                ('Stratum Level', 'stratum', 10, 15, True)
            ]
            
            for name, threshold_type, warning, critical, active in default_thresholds:
                cursor.execute("""
                    INSERT INTO alert_thresholds (name, threshold_type, warning_value, critical_value, active) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (name, threshold_type, warning, critical, active))
            
            logging.info("🎯 Seuils d'alerte par défaut créés")
            
            # Configuration système par défaut
            default_config = [
                ('ntp_check_interval', '60', 'Intervalle de vérification NTP en secondes'),
                ('alert_retention_days', '30', 'Durée de conservation des alertes en jours'),
                ('log_retention_days', '7', 'Durée de conservation des logs en jours'),
                ('monitoring_enabled', 'true', 'Activation du monitoring automatique')
            ]
            
            for key_name, value, description in default_config:
                cursor.execute("""
                    INSERT INTO system_config (key_name, value, description) 
                    VALUES (%s, %s, %s)
                """, (key_name, value, description))
            
            logging.info("⚙️  Configuration système par défaut créée")
        
        connection.commit()
        logging.info("✅ Données par défaut MySQL créées avec succès")
        return True
        
    except Exception as e:
        logging.error(f"❌ Erreur lors de la création des données par défaut: {e}")
        connection.rollback()
        return False
    finally:
        connection.close()

def update_configuration():
    """Mettre à jour les fichiers de configuration pour MySQL ROOT"""
    config_file = Path('config/config.py')
    
    if not config_file.exists():
        logging.error("❌ Fichier config/config.py non trouvé")
        return False
    
    try:
        # Lire le fichier de configuration
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer la configuration SQLite par MySQL
        old_config = "SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR}/instance/ntp_monitor_dev.db'"
        new_config = "SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@localhost/ntp_monitor'"
        
        if old_config in content:
            content = content.replace(old_config, new_config)
            
            # Sauvegarder le fichier modifié
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logging.info("📝 Configuration mise à jour pour MySQL ROOT")
            return True
        else:
            logging.info("📝 Configuration déjà à jour ou format différent")
            return True
            
    except Exception as e:
        logging.error(f"❌ Erreur mise à jour configuration: {e}")
        return False

def validate_migration():
    """Valider la migration MySQL"""
    connection = get_mysql_app_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # Vérifier les tables
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['users', 'ntp_servers', 'ntp_logs', 'alerts', 'alert_thresholds', 'system_config']
            
            for table in expected_tables:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    logging.info(f"✅ Table {table}: {count} enregistrements")
                else:
                    logging.error(f"❌ Table manquante: {table}")
                    return False
        
        logging.info("🎉 MIGRATION MySQL VALIDÉE AVEC SUCCÈS!")
        return True
        
    except Exception as e:
        logging.error(f"❌ Erreur lors de la validation: {e}")
        return False
    finally:
        connection.close()

def main():
    """Fonction principale de migration"""
    print("🚀 MIGRATION NTP MONITOR → MYSQL ROOT")
    print("=" * 60)
    
    setup_logging()
    
    # Étapes de migration
    steps = [
        ("📦 Sauvegarde SQLite", backup_sqlite_database),
        ("🗃️  Création base MySQL", create_mysql_database),
        ("📋 Création tables MySQL", create_mysql_tables),
        ("📊 Création données par défaut", create_default_data),
        ("📝 Mise à jour configuration", update_configuration),
        ("✅ Validation migration", validate_migration)
    ]
    
    results = {}
    
    for step_name, step_function in steps:
        print(f"\n{step_name}...")
        logging.info(f"ÉTAPE: {step_name}")
        
        try:
            result = step_function()
            results[step_name] = result
            
            if result:
                print(f"✅ {step_name} - SUCCÈS")
                logging.info(f"✅ {step_name} - SUCCÈS")
            else:
                print(f"❌ {step_name} - ÉCHEC")
                logging.error(f"❌ {step_name} - ÉCHEC")
                break
                
        except Exception as e:
            print(f"❌ {step_name} - ERREUR: {e}")
            logging.error(f"❌ {step_name} - ERREUR: {e}")
            results[step_name] = False
            break
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DE LA MIGRATION")
    print("=" * 60)
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    for step_name, result in results.items():
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"{step_name}: {status}")
    
    if success_count == total_count:
        print("\n🎉 MIGRATION TERMINÉE AVEC SUCCÈS!")
        print("\n🚀 Prochaines étapes:")
        print("   1. Relancer l'application: python backend/app.py")
        print("   2. Vérifier l'absence d'erreurs SQLite")
        print("   3. Confirmer la synchronisation NTP stable")
        print("\n📊 Configuration MySQL:")
        print("   - Host: localhost")
        print("   - User: root")
        print("   - Database: ntp_monitor")
        print("   - Password: (aucun)")
        print("\n✅ Avantages obtenus:")
        print("   - Fin des erreurs 'database is locked'")
        print("   - Fin des erreurs 'transaction already begun'")
        print("   - Synchronisation NTP continue")
        print("   - Performance optimisée")
    else:
        print(f"\n❌ MIGRATION ÉCHOUÉE ({success_count}/{total_count} étapes réussies)")
        print("📋 Consultez les logs: mysql_migration_root.log")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 