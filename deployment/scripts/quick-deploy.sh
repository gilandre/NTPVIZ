#!/bin/bash
# Script de déploiement ultra-rapide - NTP Monitor Enterprise
# Pour tests et développement uniquement

set -e

# Configuration
REPO_URL="https://github.com/[YOUR_REPO]/ntp-monitor-enterprise.git"
BRANCH="dev"
APP_DIR="/opt/ntp-monitor"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Déploiement ultra-rapide NTP Monitor Enterprise${NC}\n"

# Nettoyage
echo -e "${YELLOW}📦 Préparation...${NC}"
sudo rm -rf $APP_DIR
sudo apt update -qq

# Installation minimale
echo -e "${YELLOW}⚡ Installation express...${NC}"
sudo apt install -y -qq git python3.11 python3.11-venv redis-server

# Clone
echo -e "${YELLOW}📥 Clone du repository...${NC}"
sudo git clone -b $BRANCH --depth 1 $REPO_URL $APP_DIR
cd $APP_DIR

# Installation Python
echo -e "${YELLOW}🐍 Installation des dépendances Python...${NC}"
sudo python3.11 -m venv venv
sudo ./venv/bin/pip install -q --upgrade pip
sudo ./venv/bin/pip install -q -r requirements.txt

# Initialisation BDD
echo -e "${YELLOW}🗃️ Initialisation base de données...${NC}"
sudo ./venv/bin/python init_database.py init

# Démarrage services
echo -e "${YELLOW}🔄 Démarrage des services...${NC}"
sudo systemctl start redis-server
sudo ./venv/bin/python app.py &

sleep 3

SERVER_IP=$(hostname -I | awk '{print $1}')

echo -e "\n${GREEN}✅ Déploiement terminé !${NC}"
echo -e "${GREEN}🌐 Application accessible sur: http://$SERVER_IP:5000${NC}"
echo -e "${GREEN}👤 Admin: admin / admin123${NC}"
echo -e "${GREEN}📁 Répertoire: $APP_DIR${NC}\n"

echo -e "${YELLOW}Pour arrêter: sudo pkill -f 'python app.py'${NC}" 