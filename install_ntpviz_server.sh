#!/bin/bash

# Script d'installation complet NTPVIZ sur serveur Ubuntu
# À exécuter directement sur le serveur Ubuntu

set -e

echo "🚀 INSTALLATION NTPVIZ SUR SERVEUR UBUNTU"
echo "=========================================="

# Variables
APP_DIR="/opt/ntp-monitor"
GITHUB_REPO="https://github.com/gilandre/NTPVIZ.git"
GITHUB_BRANCH="MacDev"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérification des prérequis
log_info "Vérification des prérequis..."

# Vérifier si on est root
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
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    mysql-server \
    mysql-client \
    git \
    curl \
    wget \
    ufw \
    nginx \
    supervisor

# Configuration de MySQL
log_info "Configuration de MySQL..."
sudo systemctl start mysql
sudo systemctl enable mysql

# Sécurisation de MySQL (sans mot de passe root)
log_info "Sécurisation de MySQL..."
sudo mysql_secure_installation <<EOF

y
0

y
y
y
y
EOF

# Création de la base de données et de l'utilisateur
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

# Vérification de l'environnement virtuel
log_info "Vérification de l'environnement virtuel..."
which python
python --version

# Mise à jour de pip
log_info "Mise à jour de pip..."
pip install --upgrade pip

# Installation des dépendances de base
log_info "Installation des dépendances de base..."
pip install flask flask-login flask-socketio sqlalchemy pymysql

# Installation complète depuis requirements.txt
log_info "Installation complète depuis requirements.txt..."
pip install -r requirements.txt

# Vérification des modules installés
log_info "Vérification des modules installés..."
python -c "import flask; print('✅ Flask installé')"
python -c "import flask_login; print('✅ Flask-Login installé')"
python -c "import flask_socketio; print('✅ Flask-SocketIO installé')"
python -c "import sqlalchemy; print('✅ SQLAlchemy installé')"
python -c "import pymysql; print('✅ PyMySQL installé')"

# Configuration de l'environnement
log_info "Configuration de l'environnement..."
cp env.example .env

# Configuration du fichier .env
log_info "Configuration du fichier .env..."
cat > .env <<EOF
FLASK_APP=app.py
FLASK_ENV=production
DATABASE_URL=mysql+pymysql://ntp_user:NtpMonitor2024!@localhost/ntp_monitor
SECRET_KEY=your-secret-key-change-this-in-production
DEBUG=False
HOST=0.0.0.0
PORT=5001
EOF

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

# Rechargement de systemd et démarrage du service
log_info "Démarrage du service..."
sudo systemctl daemon-reload
sudo systemctl enable ntp-monitor
sudo systemctl start ntp-monitor

# Vérification du statut du service
log_info "Vérification du statut du service..."
sudo systemctl status ntp-monitor --no-pager

# Test de l'application
log_info "Test de l'application..."
sleep 5
curl -s http://localhost:5001 > /dev/null && log_success "Application accessible sur http://localhost:5001" || log_warning "Application pas encore accessible"

# Affichage des informations finales
log_success "Installation terminée avec succès!"
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