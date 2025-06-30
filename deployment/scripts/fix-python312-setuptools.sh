#!/bin/bash
# Script de correction rapide pour les problèmes setuptools Python 3.12
# Usage: wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/fix-python312-setuptools.sh | bash

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 Correction Python 3.12 Setuptools - NTP Monitor Enterprise${NC}\n"

# Configuration
APP_DIR="/var/www/ntp-monitor-enterprise"
VENV_PATH="$APP_DIR/venv"

# Vérifications
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}❌ Répertoire $APP_DIR non trouvé${NC}"
    echo -e "${YELLOW}💡 Suggestion: Lancez d'abord le script de déploiement principal${NC}"
    exit 1
fi

if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ Environnement virtuel $VENV_PATH non trouvé${NC}"
    echo -e "${YELLOW}💡 Suggestion: Relancez le déploiement complet${NC}"
    exit 1
fi

echo -e "${YELLOW}📍 Répertoire application: $APP_DIR${NC}"
echo -e "${YELLOW}🐍 Environnement virtuel: $VENV_PATH${NC}\n"

cd $APP_DIR

echo -e "${YELLOW}🗑️ Nettoyage environnement virtuel...${NC}"
# Nettoyage du cache pip corrompu
sudo -u ntpmonitor ./venv/bin/pip cache purge 2>/dev/null || true

echo -e "${YELLOW}⚙️ Mise à jour des outils de build...${NC}"
# Mise à jour forcée des outils essentiels
sudo -u ntpmonitor ./venv/bin/pip install --force-reinstall --no-cache-dir pip
sudo -u ntpmonitor ./venv/bin/pip install --force-reinstall --no-cache-dir setuptools wheel
sudo -u ntpmonitor ./venv/bin/pip install --force-reinstall --no-cache-dir setuptools-scm build

echo -e "${GREEN}✅ Outils de build mis à jour${NC}"

echo -e "${YELLOW}📦 Installation des dépendances Flask...${NC}"
# Installation des dépendances Flask essentielles
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir Flask==3.0.3
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir Flask-SQLAlchemy==3.1.1
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir SQLAlchemy==2.0.30

echo -e "${YELLOW}📦 Installation des dépendances SocketIO...${NC}"
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir Flask-SocketIO==5.3.4
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir python-socketio==5.8.0
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir python-engineio==4.7.1

echo -e "${YELLOW}📦 Installation des dépendances auth...${NC}"
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir Flask-Login==0.6.2
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir Flask-WTF==1.1.1
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir Flask-Migrate==4.0.4

echo -e "${YELLOW}📦 Installation des dépendances NTP...${NC}"
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir ntplib==0.4.0
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir pytz==2023.3

echo -e "${YELLOW}📦 Installation des dépendances système...${NC}"
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir redis==4.6.0
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir python-dateutil==2.8.2
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir requests==2.31.0
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir psutil==5.9.5
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir python-dotenv==1.0.0

echo -e "${YELLOW}📦 Installation Celery (optionnel)...${NC}"
sudo -u ntpmonitor ./venv/bin/pip install --no-cache-dir celery==5.3.1 || echo -e "${YELLOW}⚠️ Celery optionnel non installé${NC}"

echo -e "${GREEN}✅ Toutes les dépendances installées${NC}"

echo -e "${YELLOW}🧪 Test de l'environnement...${NC}"
if sudo -u ntpmonitor ./venv/bin/python -c "import flask, flask_sqlalchemy, flask_socketio; print('✅ Imports Flask OK')"; then
    echo -e "${GREEN}✅ Environnement Flask fonctionnel${NC}"
else
    echo -e "${RED}❌ Problème avec l'environnement Flask${NC}"
    exit 1
fi

echo -e "${YELLOW}🗃️ Test base de données...${NC}"
if sudo -u ntpmonitor ./venv/bin/python init_database.py check; then
    echo -e "${GREEN}✅ Base de données OK${NC}"
else
    echo -e "${YELLOW}⚠️ Réinitialisation de la base de données...${NC}"
    sudo -u ntpmonitor ./venv/bin/python init_database.py init
fi

echo -e "${YELLOW}🔄 Redémarrage des services...${NC}"
sudo systemctl restart apache2
sudo systemctl restart redis-server

echo -e "\n${GREEN}🎉 CORRECTION TERMINÉE AVEC SUCCÈS !${NC}"

SERVER_IP=$(hostname -I | awk '{print $1}')
echo -e "\n${BLUE}📋 INFORMATIONS D'ACCÈS${NC}"
echo "────────────────────────────────────────────────────────────"
echo -e "${YELLOW}🌐 URL Application:${NC} http://$SERVER_IP"
echo -e "${YELLOW}👤 Utilisateur Admin:${NC} admin"
echo -e "${YELLOW}🔑 Mot de passe:${NC} admin123"

echo -e "\n${BLUE}🛠️ COMMANDES DE DIAGNOSTIC${NC}"
echo "────────────────────────────────────────────────────────────"
echo -e "${YELLOW}Status services:${NC} sudo systemctl status apache2 redis-server"
echo -e "${YELLOW}Logs Apache:${NC} sudo tail -f /var/log/apache2/ntp-monitor_error.log"
echo -e "${YELLOW}Test BDD:${NC} cd $APP_DIR && sudo -u ntpmonitor ./venv/bin/python init_database.py check"

echo -e "\n${GREEN}🚀 Votre NTP Monitor Enterprise devrait maintenant fonctionner !${NC}" 