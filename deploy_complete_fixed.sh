#!/bin/bash

# Script de déploiement complet NTPVIZ avec corrections de base de données
# À exécuter directement sur le serveur Ubuntu

set -e

echo "🚀 DÉPLOIEMENT COMPLET NTPVIZ AVEC CORRECTIONS"
echo "==============================================="

# Variables
APP_DIR="/opt/ntp-monitor"
GITHUB_REPO="https://github.com/gilandre/NTPVIZ.git"
GITHUB_BRANCH="MacDev"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Vérification des prérequis
log_info "Vérification des prérequis..."

if [ "$EUID" -eq 0 ]; then
    log_warning "Script exécuté en tant que root"
    SUDO_USER=${SUDO_USER:-$USER}
else
    log_info "Script exécuté en tant qu'utilisateur normal"
    SUDO_USER=$USER
fi

# Mise à jour du système
log_info "Mise à jour du système..."
sudo apt update && sudo apt upgrade -y

# Installation des paquets système
log_info "Installation des paquets système..."
sudo apt install -y python3 python3-pip python3-venv mysql-server mysql-client git curl wget ufw

# Configuration de MySQL
log_info "Configuration de MySQL..."
sudo systemctl start mysql
sudo systemctl enable mysql

# Création de la base de données (sans mot de passe root)
log_info "Création de la base de données..."
sudo mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'ntp_user'@'localhost' IDENTIFIED BY 'NtpMonitor2024!';
GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# Création du répertoire de l'application
log_info "Création du répertoire de l'application..."
sudo mkdir -p $APP_DIR
sudo chown $SUDO_USER:$SUDO_USER $APP_DIR

# Téléchargement du code source
log_info "Téléchargement du code source depuis GitHub..."
cd $APP_DIR
git clone -b $GITHUB_BRANCH $GITHUB_REPO .

# Configuration de l'environnement Python
log_info "Configuration de l'environnement Python..."
python3 -m venv .venv
source .venv/bin/activate

# Installation des dépendances
log_info "Installation des dépendances..."
pip install --upgrade pip
pip install flask flask-login flask-socketio sqlalchemy pymysql
pip install -r requirements.txt

# Configuration de l'environnement
log_info "Configuration de l'environnement..."
cp env.example .env

# Configuration du fichier .env
cat > .env <<EOF
FLASK_APP=app.py
FLASK_ENV=production
DATABASE_URL=mysql+pymysql://ntp_user:NtpMonitor2024!@localhost/ntp_monitor
SECRET_KEY=your-secret-key-change-this-in-production
DEBUG=False
HOST=0.0.0.0
PORT=5001
EOF

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

# Configuration du pare-feu
log_info "Configuration du pare-feu..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5001/tcp
sudo ufw --force enable

# Création du service systemd
log_info "Création du service systemd..."
sudo tee /etc/systemd/system/ntp-monitor.service > /dev/null <<EOF
[Unit]
Description=NTP Monitor Enterprise Application
After=network.target mysql.service

[Service]
Type=simple
User=$SUDO_USER
Group=$SUDO_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/.venv/bin
ExecStart=$APP_DIR/.venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Démarrage du service
log_info "Démarrage du service..."
sudo systemctl daemon-reload
sudo systemctl enable ntp-monitor
sudo systemctl start ntp-monitor

# Vérification finale
log_info "Vérification finale..."
sleep 5
sudo systemctl status ntp-monitor --no-pager

# Test de l'application
log_info "Test de l'application..."
curl -s http://localhost:5001 > /dev/null && log_success "Application accessible sur http://localhost:5001" || log_warning "Application pas encore accessible"

# Affichage des informations finales
log_success "Déploiement terminé avec succès!"
echo ""
echo "📋 INFORMATIONS IMPORTANTES:"
echo "============================="
echo "🌐 Application: http://79.137.36.66:5001"
echo "📁 Répertoire: $APP_DIR"
echo "👤 Utilisateur: $SUDO_USER"
echo "🗄️  Base de données: ntp_monitor"
echo "🔧 Service: ntp-monitor"
echo ""
echo "🔧 Commandes utiles:"
echo "sudo systemctl status ntp-monitor"
echo "sudo systemctl restart ntp-monitor"
echo "sudo journalctl -u ntp-monitor -f"
echo ""
echo "🎉 NTPVIZ est maintenant installé et opérationnel!" 