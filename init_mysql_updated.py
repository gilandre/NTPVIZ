#!/usr/bin/env python3
"""
Script d'initialisation de la base de données MySQL pour NTP Monitor
MISE À JOUR - Utilisation de l'utilisateur ntpmonitor
"""
import os
import sys
import pymysql
from datetime import datetime
from werkzeug.security import generate_password_hash

def create_mysql_connection():
    """Créer une connexion MySQL avec utilisateur ntpmonitor"""
    try:
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='ntpmonitor',
            password='ntp2025secure',
            database='ntp_monitor',
            autocommit=True,
            charset='utf8mb4'
        )
        print("✅ Connexion MySQL établie avec utilisateur ntpmonitor")
        return connection
    except Exception as e:
        print(f"❌ Erreur connexion MySQL: {e}")
        return None

def create_tables(connection):
    """Créer les tables nécessaires"""
    cursor = connection.cursor()
    
    # Table des utilisateurs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            role VARCHAR(20) DEFAULT 'viewer',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_username (username),
            INDEX idx_email (email),
            INDEX idx_role (role)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Table des serveurs NTP
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ntp_servers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            address VARCHAR(255) NOT NULL,
            port INT DEFAULT 123,
            is_active BOOLEAN DEFAULT TRUE,
            priority INT DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_address (address),
            INDEX idx_active (is_active)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Table des logs NTP
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ntp_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            server_id INT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            offset_ms FLOAT,
            delay_ms FLOAT,
            jitter_ms FLOAT,
            stratum INT,
            status VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (server_id) REFERENCES ntp_servers(id) ON DELETE CASCADE,
            INDEX idx_server_timestamp (server_id, timestamp),
            INDEX idx_timestamp (timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Table des alertes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            alert_type VARCHAR(50) DEFAULT 'info',
            severity VARCHAR(20) DEFAULT 'medium',
            status VARCHAR(20) DEFAULT 'active',
            server_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP NULL,
            FOREIGN KEY (server_id) REFERENCES ntp_servers(id) ON DELETE SET NULL,
            INDEX idx_status (status),
            INDEX idx_type (alert_type),
            INDEX idx_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Table de configuration système
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            id INT AUTO_INCREMENT PRIMARY KEY,
            key_name VARCHAR(100) UNIQUE NOT NULL,
            value TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_key (key_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    print("✅ Tables MySQL créées/vérifiées")

def create_default_users(connection):
    """Créer les utilisateurs par défaut"""
    cursor = connection.cursor()
    
    users = [
        {
            'username': 'admin',
            'email': 'admin@ntp-monitor.local',
            'password': 'admin123',
            'first_name': 'Administrator',
            'last_name': 'System',
            'role': 'admin'
        },
        {
            'username': 'operator',
            'email': 'operator@ntp-monitor.local', 
            'password': 'operator123',
            'first_name': 'Operator',
            'last_name': 'NTP',
            'role': 'operator'
        },
        {
            'username': 'viewer',
            'email': 'viewer@ntp-monitor.local',
            'password': 'viewer123',
            'first_name': 'Viewer',
            'last_name': 'ReadOnly',
            'role': 'viewer'
        }
    ]
    
    for user in users:
        # Vérifier si l'utilisateur existe déjà
        cursor.execute("SELECT id FROM users WHERE username = %s", (user['username'],))
        if cursor.fetchone():
            print(f"⚠️  Utilisateur {user['username']} existe déjà")
            continue
            
        # Créer l'utilisateur
        password_hash = generate_password_hash(user['password'])
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user['username'],
            user['email'], 
            password_hash,
            user['first_name'],
            user['last_name'],
            user['role'],
            True
        ))
        print(f"✅ Utilisateur {user['username']} créé")

def create_default_servers(connection):
    """Créer les serveurs NTP par défaut"""
    cursor = connection.cursor()
    
    servers = [
        ('Pool NTP 0', '0.pool.ntp.org', 123, True, 1, 'Serveur NTP Pool principal'),
        ('Pool NTP 1', '1.pool.ntp.org', 123, True, 2, 'Serveur NTP Pool secondaire'),
        ('Pool NTP 2', '2.pool.ntp.org', 123, True, 3, 'Serveur NTP Pool tertiaire'),
        ('Pool NTP 3', '3.pool.ntp.org', 123, True, 4, 'Serveur NTP Pool quaternaire'),
        ('Pool NTP Generic', 'pool.ntp.org', 123, True, 5, 'Serveur NTP Pool générique')
    ]
    
    for name, address, port, active, priority, description in servers:
        # Vérifier si le serveur existe déjà
        cursor.execute("SELECT id FROM ntp_servers WHERE address = %s", (address,))
        if cursor.fetchone():
            print(f"⚠️  Serveur {address} existe déjà")
            continue
            
        # Créer le serveur
        cursor.execute("""
            INSERT INTO ntp_servers (name, address, port, is_active, priority, description)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, address, port, active, priority, description))
        print(f"✅ Serveur NTP {address} créé")

def create_system_config(connection):
    """Créer la configuration système par défaut"""
    cursor = connection.cursor()
    
    configs = [
        ('app_name', 'EmaraudeNTP VIZ V1.0.0', 'Nom de l\'application'),
        ('app_version', '1.0.0', 'Version de l\'application'),
        ('app_editor', '© Quantinnum EA', 'Éditeur de l\'application'),
        ('monitoring_interval', '60', 'Intervalle de monitoring en secondes'),
        ('alert_threshold_offset', '100', 'Seuil d\'alerte pour l\'offset en ms'),
        ('alert_threshold_delay', '500', 'Seuil d\'alerte pour le délai en ms'),
        ('retention_days', '30', 'Durée de rétention des logs en jours')
    ]
    
    for key, value, description in configs:
        # Vérifier si la config existe déjà
        cursor.execute("SELECT id FROM system_config WHERE key_name = %s", (key,))
        if cursor.fetchone():
            print(f"⚠️  Configuration {key} existe déjà")
            continue
            
        # Créer la configuration
        cursor.execute("""
            INSERT INTO system_config (key_name, value, description)
            VALUES (%s, %s, %s)
        """, (key, value, description))
        print(f"✅ Configuration {key} créée")

def main():
    """Fonction principale"""
    print("🚀 Initialisation de la base de données MySQL NTP Monitor")
    print("👤 Utilisation de l'utilisateur MySQL: ntpmonitor")
    
    # Connexion à MySQL
    connection = create_mysql_connection()
    if not connection:
        sys.exit(1)
    
    try:
        # Créer les tables
        create_tables(connection)
        
        # Créer les utilisateurs par défaut
        create_default_users(connection)
        
        # Créer les serveurs NTP par défaut
        create_default_servers(connection)
        
        # Créer la configuration système
        create_system_config(connection)
        
        print("\n✅ Initialisation MySQL terminée avec succès!")
        print("\n🔐 Comptes de connexion créés:")
        print("   Admin: admin/admin123")
        print("   Operator: operator/operator123")
        print("   Viewer: viewer/viewer123")
        print("\n🌐 Application accessible sur: http://79.137.36.66/")
        print("🗄️  Base de données: MySQL (ntp_monitor)")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        connection.close()

if __name__ == "__main__":
    main() 