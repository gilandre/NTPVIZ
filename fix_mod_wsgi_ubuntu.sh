#!/bin/bash
# Script de correction rapide mod_wsgi pour Ubuntu 24.04
# À utiliser si vous avez déjà le projet cloné

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
    exit 1
}

APP_DIR="/home/ntp-monitor/ntp-monitor-enterprise"

log "🔧 Correction mod_wsgi pour Ubuntu 24.04"

# Vérifier si on est root
if [[ $EUID -ne 0 ]]; then
    error "❌ Ce script doit être exécuté en tant que root (sudo)"
fi

# Installer mod_wsgi système
log "📦 Installation mod_wsgi système..."
apt update
apt install -y libapache2-mod-wsgi-py3 apache2-dev

# Créer requirements.txt corrigé
log "📝 Création requirements.txt corrigé..."
cat > "$APP_DIR/requirements_ubuntu.txt" << 'EOF'
# Requirements.txt corrigé pour Ubuntu 24.04
# mod_wsgi est installé via apt, pas pip

# Framework Flask
Flask==2.3.3
Werkzeug==2.3.7

# Base de données
SQLAlchemy==2.0.21
PyMySQL==1.1.0
Flask-Migrate==4.0.5

# Authentification et formulaires
Flask-Login==0.6.3
Flask-WTF==1.1.1
WTForms==3.0.1

# WebSocket et temps réel
Flask-SocketIO==5.3.6
python-socketio==5.8.0

# Cache et sessions Redis
redis==5.0.1

# Workers et tâches asynchrones
celery==5.3.4

# Monitoring NTP
ntplib==0.4.0
psutil==5.9.5

# Utilitaires
requests==2.31.0
python-dateutil==2.8.2
pytz==2023.3
python-dotenv==1.0.0

# Sécurité
cryptography==41.0.7
bcrypt==4.0.1

# CLI et outils
click==8.1.7
itsdangerous==2.1.2

# Développement
setuptools==68.2.2
wheel==0.41.2
EOF

# Réinstaller les dépendances
log "🔄 Réinstallation des dépendances..."
sudo -u ntp-monitor bash << 'EOF'
cd /home/ntp-monitor/ntp-monitor-enterprise
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements_ubuntu.txt
EOF

# Activer mod_wsgi
log "🌐 Activation mod_wsgi..."
a2enmod wsgi
systemctl restart apache2

# Vérifier installation
log "🧪 Vérification installation..."
if apache2ctl -M | grep -q wsgi; then
    log "✅ mod_wsgi système chargé avec succès"
else
    error "❌ mod_wsgi non chargé"
fi

log "🎉 Correction terminée ! Relancez le déploiement:"
echo "sudo systemctl restart ntp-monitor-enterprise"
echo "sudo systemctl restart apache2" 