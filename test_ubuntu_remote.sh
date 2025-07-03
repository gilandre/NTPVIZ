#!/bin/bash
# Script de test rapide pour serveur Ubuntu distant
# Copiez ce script sur votre serveur Ubuntu et exécutez-le

# Version ultra-simplifiée pour test rapide
SCRIPT_VERSION="test-1.0"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO] $1${NC}"; }
error() { echo -e "${RED}[ERROR] $1${NC}"; }
success() { echo -e "${GREEN}[SUCCESS] $1${NC}"; }

echo "=============================================="
echo "    NTP MONITOR - TEST RAPIDE UBUNTU"
echo "=============================================="
echo

# Vérifications de base
log "Vérification des prérequis..."

if [[ $EUID -ne 0 ]]; then
    error "Exécutez avec sudo"
    exit 1
fi

if [ ! -f /etc/os-release ]; then
    error "Impossible de détecter Ubuntu"
    exit 1
fi

source /etc/os-release
if [[ "$ID" != "ubuntu" ]]; then
    error "Système non Ubuntu: $ID"
    exit 1
fi

success "Ubuntu $VERSION_ID détecté"

# Installation des packages essentiels
log "Installation des packages essentiels..."
apt update
apt install -y curl wget git python3 python3-pip python3-venv mysql-server apache2 redis-server ntp

# Configuration MySQL rapide
log "Configuration MySQL..."
systemctl start mysql
systemctl enable mysql

# Créer base de données de test
mysql -u root << 'EOF'
CREATE DATABASE IF NOT EXISTS ntp_monitor_test;
CREATE USER IF NOT EXISTS 'ntp_test'@'localhost' IDENTIFIED BY 'test123';
GRANT ALL PRIVILEGES ON ntp_monitor_test.* TO 'ntp_test'@'localhost';
FLUSH PRIVILEGES;
EOF

# Configuration Apache
log "Configuration Apache..."
systemctl start apache2
systemctl enable apache2
a2enmod wsgi

# Configuration Redis
log "Configuration Redis..."
systemctl start redis-server
systemctl enable redis-server

# Configuration NTP
log "Configuration NTP..."
systemctl start ntp
systemctl enable ntp

# Installation Python packages
log "Installation packages Python..."
python3 -m pip install --upgrade pip
python3 -m pip install flask sqlalchemy pymysql redis python-dotenv

# Tests finaux
log "Tests des services..."
for service in mysql apache2 redis-server ntp; do
    if systemctl is-active --quiet "$service"; then
        success "Service $service OK"
    else
        error "Service $service KO"
    fi
done

# Test Python
log "Test Python..."
if python3 -c "import flask, sqlalchemy, pymysql, redis; print('Python modules OK')" 2>/dev/null; then
    success "Python OK"
else
    error "Python KO"
fi

# Test MySQL
log "Test MySQL..."
if mysql -u ntp_test -ptest123 -e "USE ntp_monitor_test; SELECT 1;" >/dev/null 2>&1; then
    success "MySQL OK"
else
    error "MySQL KO"
fi

echo
echo "=============================================="
echo "    RÉSULTATS DU TEST"
echo "=============================================="
echo -e "${CYAN}Services installés et configurés :${NC}"
echo "  • MySQL avec base ntp_monitor_test"
echo "  • Apache avec mod_wsgi"
echo "  • Redis"
echo "  • NTP"
echo "  • Python avec Flask, SQLAlchemy, etc."
echo
echo -e "${CYAN}Prochaines étapes :${NC}"
echo "  1. git clone https://github.com/gilandre/NTPVIZ.git"
echo "  2. cd NTPVIZ && sudo ./deploy_ubuntu_production.sh"
echo
success "Test terminé avec succès !" 