#!/usr/bin/env python3
"""
Script de correction finale des problèmes NTP Monitor
- Correction du PATH pour systemctl
- Ajout des colonnes manquantes dans la base de données
"""
import os
import sys
import pymysql
import subprocess

def run_command(command, description, capture_output=True):
    """Exécuter une commande avec gestion d'erreur"""
    try:
        print(f"🔧 {description}...")
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {description} réussi")
                if result.stdout.strip():
                    print(f"   Output: {result.stdout.strip()}")
            else:
                print(f"❌ {description} échoué")
                print(f"   Error: {result.stderr.strip()}")
            return result.returncode == 0
        else:
            result = subprocess.run(command, shell=True)
            return result.returncode == 0
    except Exception as e:
        print(f"❌ Erreur lors de {description}: {e}")
        return False

def fix_systemctl_path():
    """Corriger le problème systemctl PATH"""
    print("🔧 Correction du problème systemctl...")
    
    # Vérifier où est systemctl
    systemctl_paths = ["/bin/systemctl", "/usr/bin/systemctl", "/sbin/systemctl", "/usr/sbin/systemctl"]
    systemctl_path = None
    
    for path in systemctl_paths:
        if os.path.exists(path):
            systemctl_path = path
            print(f"✅ systemctl trouvé: {path}")
            break
    
    if not systemctl_path:
        print("❌ systemctl non trouvé")
        return False
    
    # Créer un script wrapper pour corriger le PATH
    wrapper_script = f'''#!/bin/bash
# Script wrapper pour corriger le PATH pour NTP Monitor
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin"

# Vérifier que systemctl existe
if [ ! -f "{systemctl_path}" ]; then
    echo "Erreur: systemctl non trouvé à {systemctl_path}"
    exit 1
fi

# Exécuter systemctl avec le PATH corrigé
exec "{systemctl_path}" "$@"
'''
    
    try:
        with open('/usr/local/bin/systemctl-fixed', 'w') as f:
            f.write(wrapper_script)
        os.chmod('/usr/local/bin/systemctl-fixed', 0o755)
        print("✅ Script wrapper systemctl créé")
        
        # Créer un lien symbolique
        if os.path.exists('/usr/local/bin/systemctl'):
            os.remove('/usr/local/bin/systemctl')
        os.symlink('/usr/local/bin/systemctl-fixed', '/usr/local/bin/systemctl')
        print("✅ Lien symbolique systemctl créé")
        
        return True
    except Exception as e:
        print(f"❌ Erreur création wrapper systemctl: {e}")
        return False

def update_database_schema():
    """Mettre à jour le schéma de base de données avec les nouvelles colonnes"""
    print("🗄️ Mise à jour du schéma de base de données...")
    
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
        print("✅ Connexion MySQL établie")
        cursor = connection.cursor()
        
        # Ajouter les colonnes manquantes à ntp_servers
        columns_to_add = [
            "ADD COLUMN IF NOT EXISTS timeout INT DEFAULT 10",
            "ADD COLUMN IF NOT EXISTS max_offset FLOAT DEFAULT 1.0",
            "ADD COLUMN IF NOT EXISTS critical_offset FLOAT DEFAULT 5.0",
            "ADD COLUMN IF NOT EXISTS server_type VARCHAR(20) DEFAULT 'global'",
            "ADD COLUMN IF NOT EXISTS last_offset FLOAT",
            "ADD COLUMN IF NOT EXISTS last_delay FLOAT", 
            "ADD COLUMN IF NOT EXISTS last_jitter FLOAT",
            "ADD COLUMN IF NOT EXISTS last_check TIMESTAMP NULL",
            "ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'unknown'",
            "ADD COLUMN IF NOT EXISTS polling_interval INT DEFAULT 60",
            "ADD COLUMN IF NOT EXISTS retry_count INT DEFAULT 3",
            "ADD COLUMN IF NOT EXISTS max_retries INT DEFAULT 5"
        ]
        
        for column_sql in columns_to_add:
            try:
                sql = f"ALTER TABLE ntp_servers {column_sql}"
                cursor.execute(sql)
                print(f"✅ Colonne ajoutée: {column_sql}")
            except pymysql.err.OperationalError as e:
                if "Duplicate column" in str(e):
                    print(f"⚠️ Colonne déjà existante: {column_sql}")
                else:
                    print(f"❌ Erreur ajout colonne: {e}")
        
        # Mettre à jour les serveurs existants avec des valeurs par défaut
        cursor.execute("""
            UPDATE ntp_servers 
            SET 
                timeout = COALESCE(timeout, 10),
                max_offset = COALESCE(max_offset, 1.0),
                critical_offset = COALESCE(critical_offset, 5.0),
                server_type = COALESCE(server_type, 'global'),
                status = COALESCE(status, 'unknown'),
                polling_interval = COALESCE(polling_interval, 60),
                retry_count = COALESCE(retry_count, 3),
                max_retries = COALESCE(max_retries, 5)
            WHERE id IS NOT NULL
        """)
        print("✅ Serveurs existants mis à jour")
        
        connection.close()
        print("✅ Schéma de base de données mis à jour")
        return True
        
    except Exception as e:
        print(f"❌ Erreur mise à jour base de données: {e}")
        return False

def main():
    print("🚀 Correction finale des problèmes NTP Monitor")
    
    # 1. Corriger systemctl
    fix_systemctl_path()
    
    # 2. Mettre à jour le schéma de base de données
    update_database_schema()
    
    # 3. Tester systemctl
    print("\n🧪 Test systemctl corrigé...")
    run_command("systemctl --version", "Test systemctl version")
    
    print("\n✅ Corrections finales terminées!")
    print("\n📋 Résumé:")
    print("   - PATH systemctl corrigé")
    print("   - Schéma MySQL mis à jour")
    print("   - Colonnes NTPServer ajoutées")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("❌ Ce script doit être exécuté en tant que root (sudo)")
        sys.exit(1)
    main() 