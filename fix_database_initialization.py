#!/usr/bin/env python3
"""
Script d'initialisation de la base de données SQLite pour NTP Monitor
Correction des problèmes de connexion
"""
import os
import sys
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

def create_database_schema(db_path):
    """Créer le schéma de la base de données SQLite"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Table des utilisateurs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            role VARCHAR(20) NOT NULL DEFAULT 'viewer',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            login_count INTEGER DEFAULT 0,
            preferences TEXT DEFAULT '{
                "theme": "light",
                "language": "fr",
                "notifications": true,
                "auto_refresh": true,
                "refresh_interval": 30
            }'
        )
    """)
    
    # Table des serveurs NTP
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ntp_servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            address VARCHAR(255) NOT NULL,
            port INTEGER DEFAULT 123,
            server_type VARCHAR(20) DEFAULT 'pool',
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            priority INTEGER DEFAULT 1,
            timeout INTEGER DEFAULT 10,
            max_offset REAL DEFAULT 1.0,
            critical_offset REAL DEFAULT 5.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table des logs NTP
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ntp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            delay REAL,
            offset REAL,
            jitter REAL,
            stratum INTEGER,
            precision INTEGER,
            status VARCHAR(20) DEFAULT 'unknown',
            error_message TEXT,
            FOREIGN KEY (server_id) REFERENCES ntp_servers (id)
        )
    """)
    
    # Table de configuration système
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name VARCHAR(100) UNIQUE NOT NULL,
            value TEXT,
            category VARCHAR(50) DEFAULT 'general',
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table des alertes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER,
            alert_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) DEFAULT 'info',
            title VARCHAR(200) NOT NULL,
            message TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_acknowledged BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (server_id) REFERENCES ntp_servers (id)
        )
    """)
    
    conn.commit()
    return conn

def insert_default_users(conn):
    """Insérer les utilisateurs par défaut"""
    cursor = conn.cursor()
    
    # Vérifier si des utilisateurs existent déjà
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("Création des utilisateurs par défaut...")
        
        users = [
            ('admin', 'admin@ntp-monitor.local', 'admin123', 'admin', 'Administrateur', 'Système'),
            ('operator', 'operator@ntp-monitor.local', 'operator123', 'operator', 'Opérateur', 'Système'),
            ('viewer', 'viewer@ntp-monitor.local', 'viewer123', 'viewer', 'Visualiseur', 'Système')
        ]
        
        for username, email, password, role, first_name, last_name in users:
            password_hash = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, first_name, last_name, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (username, email, password_hash, role, first_name, last_name))
            print(f"✅ Utilisateur créé: {username}/{password}")
        
        conn.commit()
        print("✅ Utilisateurs par défaut créés")
    else:
        print("✅ Utilisateurs existants trouvés")

def insert_default_servers(conn):
    """Insérer les serveurs NTP par défaut"""
    cursor = conn.cursor()
    
    # Vérifier si des serveurs existent déjà
    cursor.execute("SELECT COUNT(*) FROM ntp_servers")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("Création des serveurs NTP par défaut...")
        
        servers = [
            ('Pool FR 0', '0.fr.pool.ntp.org', 'pool', 'Serveur NTP Pool France 0', 1),
            ('Pool FR 1', '1.fr.pool.ntp.org', 'pool', 'Serveur NTP Pool France 1', 2),
            ('Pool Europe', 'europe.pool.ntp.org', 'pool', 'Serveur NTP Pool Europe', 3),
            ('Cloudflare Time', 'time.cloudflare.com', 'public', 'Service de temps Cloudflare', 4),
            ('Google Time', 'time.google.com', 'public', 'Service de temps Google', 5)
        ]
        
        for name, address, server_type, description, priority in servers:
            cursor.execute("""
                INSERT INTO ntp_servers (name, address, server_type, description, priority, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (name, address, server_type, description, priority))
            print(f"✅ Serveur NTP créé: {name} ({address})")
        
        conn.commit()
        print("✅ Serveurs NTP par défaut créés")
    else:
        print("✅ Serveurs NTP existants trouvés")

def insert_default_config(conn):
    """Insérer la configuration système par défaut"""
    cursor = conn.cursor()
    
    # Vérifier si la configuration existe déjà
    cursor.execute("SELECT COUNT(*) FROM system_config")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("Création de la configuration système par défaut...")
        
        configs = [
            ('app_name', 'EmaraudeNTP VIZ V1.0.0', 'general', 'Nom de l\'application'),
            ('app_version', '1.0.0', 'general', 'Version de l\'application'),
            ('editor', '© Quantinnum EA', 'general', 'Éditeur de l\'application'),
            ('max_logs_days', '30', 'maintenance', 'Nombre de jours de conservation des logs'),
            ('alert_email_enabled', 'false', 'alerts', 'Activation des alertes par email'),
            ('monitoring_interval', '60', 'monitoring', 'Intervalle de monitoring en secondes'),
            ('database_type', 'sqlite', 'database', 'Type de base de données utilisée'),
            ('theme', 'light', 'interface', 'Thème par défaut de l\'interface'),
            ('language', 'fr', 'interface', 'Langue par défaut')
        ]
        
        for key_name, value, category, description in configs:
            cursor.execute("""
                INSERT INTO system_config (key_name, value, category, description)
                VALUES (?, ?, ?, ?)
            """, (key_name, value, category, description))
        
        conn.commit()
        print("✅ Configuration système créée")
    else:
        print("✅ Configuration système existante trouvée")

def main():
    """Fonction principale"""
    print("🚀 Initialisation de la base de données NTP Monitor")
    print("=" * 50)
    
    # Chemin de la base de données
    db_path = "/opt/NTPVIZ/instance/ntp_monitor.db"
    instance_dir = os.path.dirname(db_path)
    
    # Créer le répertoire instance s'il n'existe pas
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        print(f"✅ Répertoire créé: {instance_dir}")
    
    try:
        # Créer et initialiser la base de données
        print(f"📊 Création de la base de données: {db_path}")
        conn = create_database_schema(db_path)
        
        # Insérer les données par défaut
        insert_default_users(conn)
        insert_default_servers(conn)
        insert_default_config(conn)
        
        # Fermer la connexion
        conn.close()
        
        # Changer les permissions
        os.chmod(db_path, 0o664)
        print(f"✅ Permissions définies pour: {db_path}")
        
        print("=" * 50)
        print("🎉 Initialisation terminée avec succès!")
        print("\n📋 Identifiants de connexion:")
        print("   • admin/admin123 (Administrateur)")
        print("   • operator/operator123 (Opérateur)")
        print("   • viewer/viewer123 (Visualiseur)")
        print("\n🌐 URL d'accès: http://79.137.36.66/")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 