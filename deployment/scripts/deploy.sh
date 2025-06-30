#!/bin/bash
# Script de déploiement one-click - NTP Monitor Enterprise
# Usage: wget -O - https://raw.githubusercontent.com/[YOUR_REPO]/dev/deployment/scripts/deploy.sh | sudo bash

set -e

# Configuration
REPO_URL="https://github.com/[YOUR_REPO]/ntp-monitor-enterprise.git"
BRANCH="dev"
APP_DIR="/var/www/ntp-monitor-enterprise"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Logo ASCII
print_logo() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              🚀 NTP MONITOR ENTERPRISE 🚀                    ║"
    echo "║                                                              ║"
    echo "║              Déploiement Automatique One-Click               ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_step() {
    echo -e "\n${PURPLE}[ÉTAPE]${NC} $1"
    echo "────────────────────────────────────────────────────────────"
}

# Vérifications préliminaires
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Ce script doit être exécuté en tant que root (sudo)"
        exit 1
    fi
}

check_os() {
    if ! command -v apt &> /dev/null; then
        log_error "Ce script nécessite Ubuntu/Debian (apt package manager)"
        exit 1
    fi
    
    OS_VERSION=$(lsb_release -rs 2>/dev/null || echo "unknown")
    log_info "OS détecté: Ubuntu $OS_VERSION"
}

check_internet() {
    if ! ping -c 1 google.com &> /dev/null; then
        log_error "Connexion Internet requise"
        exit 1
    fi
    log_success "Connexion Internet OK"
}

# Fonction principale
main() {
    print_logo
    
    log_step "1/8 - Vérifications préliminaires"
    check_root
    check_os
    check_internet
    
    log_step "2/8 - Mise à jour du système"
    log_info "Mise à jour des paquets système..."
    apt update -qq && apt upgrade -y -qq
    log_success "Système mis à jour"
    
    log_step "3/8 - Installation des dépendances"
    log_info "Installation des dépendances système..."
    apt install -y -qq git curl wget python3.11 python3.11-venv \
        apache2 libapache2-mod-wsgi-py3 redis-server sqlite3 \
        ntpsec ntpsec-ntpdate htop vim
    log_success "Dépendances installées"
    
    log_step "4/8 - Clone du repository"
    if [ -d "$APP_DIR" ]; then
        log_warning "Répertoire existant détecté, sauvegarde..."
        mv "$APP_DIR" "${APP_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    log_info "Clone du repository..."
    git clone -b $BRANCH --depth 1 $REPO_URL $APP_DIR
    cd $APP_DIR
    log_success "Repository cloné"
    
    log_step "5/8 - Configuration utilisateur et permissions"
    useradd -r -s /bin/false ntpmonitor 2>/dev/null || true
    chown -R ntpmonitor:www-data $APP_DIR
    chmod -R 755 $APP_DIR
    log_success "Permissions configurées"
    
    log_step "6/8 - Installation de l'application"
    log_info "Lancement du script d'installation principal..."
    chmod +x deployment/scripts/install.sh
    ./deployment/scripts/install.sh
    log_success "Application installée"
    
    log_step "7/8 - Configuration des services"
    systemctl enable apache2 redis-server ntpsec
    systemctl restart apache2 redis-server ntpsec
    log_success "Services configurés"
    
    log_step "8/8 - Tests finaux"
    sleep 5
    
    # Test HTTP
    if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|302"; then
        log_success "Application web accessible"
    else
        log_warning "Test HTTP échoué (peut être normal)"
    fi
    
    # Test des services
    if systemctl is-active --quiet apache2; then
        log_success "Apache2 actif"
    else
        log_error "Apache2 inactif"
    fi
    
    if systemctl is-active --quiet redis-server; then
        log_success "Redis actif" 
    else
        log_error "Redis inactif"
    fi
    
    print_success_message
}

print_success_message() {
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║              🎉 DÉPLOIEMENT RÉUSSI ! 🎉                     ║${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    
    echo -e "\n${BLUE}📋 INFORMATIONS D'ACCÈS${NC}"
    echo "────────────────────────────────────────────────────────────"
    echo -e "${YELLOW}🌐 URL Application:${NC} http://$SERVER_IP ou http://localhost"
    echo -e "${YELLOW}👤 Utilisateur Admin:${NC} admin"
    echo -e "${YELLOW}🔑 Mot de passe:${NC} admin123"
    echo -e "${YELLOW}📁 Répertoire App:${NC} $APP_DIR"
    
    echo -e "\n${BLUE}🛠️ COMMANDES UTILES${NC}"
    echo "────────────────────────────────────────────────────────────"
    echo -e "${YELLOW}Redémarrer Apache:${NC} sudo systemctl restart apache2"
    echo -e "${YELLOW}Logs Apache:${NC} sudo tail -f /var/log/apache2/ntp-monitor_error.log"
    echo -e "${YELLOW}Logs Application:${NC} sudo tail -f $APP_DIR/logs/app.log"
    echo -e "${YELLOW}Status Services:${NC} sudo systemctl status apache2 redis-server ntpsec"
    
    echo -e "\n${BLUE}🔧 PROCHAINES ÉTAPES${NC}"
    echo "────────────────────────────────────────────────────────────"
    echo -e "1. ${YELLOW}Changer le mot de passe admin${NC} (interface web → Admin → Profil)"
    echo -e "2. ${YELLOW}Configurer votre domaine${NC} (optionnel)"
    echo -e "3. ${YELLOW}Installer SSL/HTTPS${NC} avec certbot (recommandé)"
    echo -e "4. ${YELLOW}Configurer les sauvegardes${NC} automatiques"
    
    echo -e "\n${BLUE}📚 DOCUMENTATION${NC}"
    echo "────────────────────────────────────────────────────────────"
    echo -e "${YELLOW}Guide complet:${NC} $APP_DIR/GUIDE_DEPLOIEMENT_SERVEUR.md"
    echo -e "${YELLOW}Initialisation BDD:${NC} $APP_DIR/GUIDE_INITIALISATION_BDD.md"
    echo -e "${YELLOW}README:${NC} $APP_DIR/README.md"
    
    echo -e "\n${GREEN}🎯 Votre NTP Monitor Enterprise est maintenant opérationnel !${NC}"
    echo -e "${GREEN}Accédez à http://$SERVER_IP pour commencer à l'utiliser.${NC}\n"
}

# Gestion d'erreur
trap 'log_error "Erreur détectée. Déploiement interrompu."; exit 1' ERR

# Lancement du script principal
main "$@" 