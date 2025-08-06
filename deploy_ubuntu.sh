#!/bin/bash
# Script de déploiement Ubuntu 24.04 - NTP Monitor Enterprise

set -e

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}✅ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

echo "🚀 DÉPLOIEMENT UBUNTU 24.04 - NTP Monitor Enterprise"
echo "=================================================="

# Vérifier les prérequis
log_info "Vérification des prérequis..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv mysql-server

# Configuration environnement
log_info "Configuration de l'environnement..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configuration .env
if [[ ! -f ".env" ]]; then
    cp env.example .env
    sed -i 's/FLASK_ENV=development/FLASK_ENV=production/' .env
    sed -i 's/DEBUG=True/DEBUG=False/' .env
    sed -i 's/HOST=127.0.0.1/HOST=0.0.0.0/' .env
fi

# Initialisation base de données
log_info "Initialisation de la base de données..."
python initialiser_database.py

# Test application
log_info "Test de l'application..."
python -c "from backend.app import create_app; app = create_app(); print('✅ OK')"

log_info "Déploiement terminé!"
log_info "Démarrez avec: python app.py"
log_info "Accédez à: http://localhost:5001"
log_info "Connectez-vous avec: admin/admin123" 