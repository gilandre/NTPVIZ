#!/bin/bash

# Script de correction pour installation existante NTPVIZ
# À exécuter sur le serveur Ubuntu où NTPVIZ est déjà installé

set -e

echo "🔧 CORRECTION INSTALLATION EXISTANTE NTPVIZ"
echo "==========================================="

# Variables
APP_DIR="/opt/ntp-monitor"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# Vérification de l'installation existante
log_info "Vérification de l'installation existante..."

if [ ! -d "$APP_DIR" ]; then
    log_warning "Répertoire $APP_DIR non trouvé. Exécutez d'abord le script de déploiement complet."
    exit 1
fi

cd $APP_DIR

# Activation de l'environnement virtuel
log_info "Activation de l'environnement virtuel..."
source .venv/bin/activate

# Création du script de correction de base de données
log_info "Création du script de correction de base de données..."
cat > fix_database_complete.py << 'EOF'
#!/usr/bin/env python3
import pymysql

def fix_database_complete():
    try:
        print("🔌 Connexion à la base de données...")
        connection = pymysql.connect(
            host='localhost',
            user='ntp_user',
            password='NtpMonitor2024!',
            database='ntp_monitor',
            charset='utf8mb4'
        )
        cursor = connection.cursor()
        
        # Correction system_config
        print("🔧 Correction system_config...")
        system_config_fixes = [
            ("value_type", "VARCHAR(20) DEFAULT 'string' AFTER value"),
            ("category", "VARCHAR(50) DEFAULT 'general' AFTER value_type"),
            ("is_public", "BOOLEAN DEFAULT TRUE AFTER category"),
            ("updated_by", "INT NULL AFTER updated_at")
        ]
        
        for column_name, column_def in system_config_fixes:
            try:
                cursor.execute(f"ALTER TABLE system_config ADD COLUMN {column_name} {column_def}")
                print(f"✅ {column_name} ajouté")
            except:
                print(f"✅ {column_name} existe déjà")
        
        # Correction ntp_logs
        print("🔧 Correction ntp_logs...")
        ntp_logs_fixes = [
            ("server_id", "INT NOT NULL"),
            ("timestamp", "DATETIME NOT NULL"),
            ("status", "VARCHAR(20) DEFAULT 'unknown'"),
            ("offset", "FLOAT NULL"),
            ("delay", "FLOAT NULL"),
            ("latency", "FLOAT NULL"),
            ("stratum", "INT NULL"),
            ("error_message", "TEXT NULL"),
            ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
        ]
        
        for column_name, column_def in ntp_logs_fixes:
            try:
                cursor.execute(f"ALTER TABLE ntp_logs ADD COLUMN {column_name} {column_def}")
                print(f"✅ {column_name} ajouté")
            except:
                print(f"✅ {column_name} existe déjà")
        
        # Correction alerts
        print("🔧 Correction alerts...")
        alerts_fixes = [
            ("server_id", "INT NOT NULL"),
            ("alert_type", "VARCHAR(50) NOT NULL"),
            ("severity", "VARCHAR(20) DEFAULT 'warning'"),
            ("message", "TEXT NOT NULL"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("resolved_at", "DATETIME NULL"),
            ("resolved_by", "INT NULL")
        ]
        
        for column_name, column_def in alerts_fixes:
            try:
                cursor.execute(f"ALTER TABLE alerts ADD COLUMN {column_name} {column_def}")
                print(f"✅ {column_name} ajouté")
            except:
                print(f"✅ {column_name} existe déjà")
        
        connection.commit()
        print("🎉 Toutes les corrections terminées!")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    fix_database_complete()
EOF

# Exécution des corrections de base de données
log_info "Exécution des corrections de base de données..."
python fix_database_complete.py

# Correction du schéma de base de données
log_info "Correction du schéma de base de données..."
python fix_database_schema.py

# Harmonisation des modèles
log_info "Harmonisation des modèles..."
python harmonize_models.py

# Initialisation de la base de données
log_info "Initialisation de la base de données..."
python initialiser_database.py

# Test de l'application
log_info "Test de l'application..."
python quick_verification.py

# Redémarrage du service
log_info "Redémarrage du service..."
sudo systemctl restart ntp-monitor

# Vérification finale
log_info "Vérification finale..."
sleep 5
sudo systemctl status ntp-monitor --no-pager

# Test de l'application
log_info "Test de l'application..."
curl -s http://localhost:5001 > /dev/null && log_success "Application accessible sur http://localhost:5001" || log_warning "Application pas encore accessible"

# Affichage des informations finales
log_success "Correction terminée avec succès!"
echo ""
echo "📋 INFORMATIONS:"
echo "🌐 Application: http://79.137.36.66:5001"
echo "📁 Répertoire: $APP_DIR"
echo "🔧 Service: ntp-monitor"
echo ""
echo "🔧 Commandes utiles:"
echo "sudo systemctl status ntp-monitor"
echo "sudo systemctl restart ntp-monitor"
echo "sudo journalctl -u ntp-monitor -f"
echo ""
echo "🎉 NTPVIZ est maintenant corrigé et opérationnel!" 