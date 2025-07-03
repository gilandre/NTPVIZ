#!/bin/bash
# ============================================================================
# NTP Monitor Enterprise - Vérification et Installation Simplifiée
# Ubuntu Server 24.04 LTS - Version Robuste
# Version: 2.0.2-simple
# ============================================================================

# PAS de set -e pour éviter les arrêts inattendus
# Gestion d'erreur manuelle et explicite

# Configuration
SCRIPT_VERSION="2.0.2-simple"
MYSQL_DB="ntp_monitor"
MYSQL_USER="ntp_user"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Compteurs
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $1${NC}"
    ((WARNINGS++))
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    ((FAILED_CHECKS++))
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
    ((PASSED_CHECKS++))
}

section() {
    echo -e "\n${WHITE}============================================================================${NC}"
    echo -e "${WHITE}$1${NC}"
    echo -e "${WHITE}============================================================================${NC}\n"
}

# ============================================================================
# VÉRIFICATIONS SYSTÈME
# ============================================================================

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Ce script doit être exécuté en tant que root (sudo)"
        return 1
    fi
    success "Privilèges root confirmés"
    return 0
}

check_ubuntu() {
    if [ -f /etc/os-release ]; then
        source /etc/os-release
        if [[ "$ID" == "ubuntu" ]]; then
            success "Ubuntu détecté: $VERSION_ID"
            return 0
        else
            error "Système non Ubuntu: $ID"
            return 1
        fi
    else
        error "Impossible de détecter le système"
        return 1
    fi
}

check_resources() {
    local mem_mb=$(free -m | awk 'NR==2{print $2}')
    local disk_gb=$(df / | awk 'NR==2{print int($4/1024/1024)}')
    
    if [ "$mem_mb" -lt 1024 ]; then
        error "RAM insuffisante: ${mem_mb}MB (min: 1024MB)"
        return 1
    else
        success "RAM suffisante: ${mem_mb}MB"
    fi
    
    if [ "$disk_gb" -lt 5 ]; then
        error "Disque insuffisant: ${disk_gb}GB (min: 5GB)"
        return 1
    else
        success "Disque suffisant: ${disk_gb}GB"
    fi
    
    return 0
}

# ============================================================================
# INSTALLATION PACKAGES
# ============================================================================

install_packages() {
    section "INSTALLATION DES PACKAGES"
    
    log "Mise à jour des paquets..."
    if apt update; then
        success "Mise à jour réussie"
    else
        error "Échec mise à jour"
        return 1
    fi
    
    log "Installation des packages essentiels..."
    local packages=(
        "curl" "wget" "git" "htop" "vim" "tree" "net-tools" "unzip"
        "software-properties-common" "apt-transport-https" "ca-certificates"
        "gnupg" "lsb-release" "build-essential" "pkg-config" "ufw"
        "python3" "python3-pip" "python3-venv" "python3-dev"
        "python3-setuptools" "python3-wheel"
        "mysql-server" "mysql-client" "libmysqlclient-dev"
        "apache2" "libapache2-mod-wsgi-py3" "apache2-utils"
        "redis-server" "ntp" "ntpdate" "ntpstat"
        "certbot" "python3-certbot-apache" "openssl"
        "psmisc" "lsof"
    )
    
    if apt install -y "${packages[@]}"; then
        success "Packages installés avec succès"
        return 0
    else
        error "Échec installation packages"
        return 1
    fi
}

# ============================================================================
# CONFIGURATION MYSQL
# ============================================================================

setup_mysql() {
    section "CONFIGURATION MYSQL"
    
    log "Démarrage MySQL..."
    if systemctl start mysql && systemctl enable mysql; then
        success "MySQL démarré"
    else
        error "Échec démarrage MySQL"
        return 1
    fi
    
    log "Configuration base de données..."
    local mysql_password=$(openssl rand -base64 16)
    
    if mysql -u root << EOF
CREATE DATABASE IF NOT EXISTS $MYSQL_DB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$MYSQL_USER'@'localhost' IDENTIFIED BY '$mysql_password';
GRANT ALL PRIVILEGES ON $MYSQL_DB.* TO '$MYSQL_USER'@'localhost';
FLUSH PRIVILEGES;
EOF
    then
        success "Base de données configurée"
        echo "MYSQL_PASSWORD=$mysql_password" > /root/mysql_credentials.txt
        chmod 600 /root/mysql_credentials.txt
        success "Credentials sauvés: /root/mysql_credentials.txt"
        return 0
    else
        error "Échec configuration MySQL"
        return 1
    fi
}

# ============================================================================
# CONFIGURATION APACHE
# ============================================================================

setup_apache() {
    section "CONFIGURATION APACHE"
    
    log "Démarrage Apache..."
    if systemctl start apache2 && systemctl enable apache2; then
        success "Apache démarré"
    else
        error "Échec démarrage Apache"
        return 1
    fi
    
    log "Activation modules Apache..."
    if a2enmod wsgi rewrite ssl headers; then
        success "Modules Apache activés"
    else
        error "Échec activation modules"
        return 1
    fi
    
    if systemctl reload apache2; then
        success "Apache reconfiguré"
        return 0
    else
        error "Échec reconfiguration Apache"
        return 1
    fi
}

# ============================================================================
# CONFIGURATION SERVICES
# ============================================================================

setup_services() {
    section "CONFIGURATION SERVICES"
    
    # Redis
    log "Configuration Redis..."
    if systemctl start redis-server && systemctl enable redis-server; then
        success "Redis configuré"
    else
        error "Échec Redis"
    fi
    
    # NTP
    log "Configuration NTP..."
    if systemctl start ntp && systemctl enable ntp; then
        success "NTP configuré"
    else
        error "Échec NTP"
    fi
    
    # UFW
    log "Configuration Firewall..."
    if ufw --force enable && ufw allow ssh && ufw allow 80 && ufw allow 443; then
        success "Firewall configuré"
    else
        error "Échec Firewall"
    fi
    
    return 0
}

# ============================================================================
# INSTALLATION PYTHON
# ============================================================================

setup_python() {
    section "CONFIGURATION PYTHON"
    
    log "Mise à jour pip..."
    if python3 -m pip install --upgrade pip; then
        success "pip mis à jour"
    else
        error "Échec mise à jour pip"
        return 1
    fi
    
    log "Installation des packages Python..."
    local python_packages=(
        "Flask==2.3.3" "SQLAlchemy==2.0.21" "PyMySQL==1.1.0" "Redis==5.0.1"
        "ntplib==0.4.0" "psutil==5.9.5" "python-dotenv==1.0.0"
        "flask-sqlalchemy==3.0.5" "flask-login==0.6.2" "werkzeug==2.3.7"
        "flask-socketio==5.3.6" "gunicorn==21.2.0"
    )
    
    if python3 -m pip install "${python_packages[@]}"; then
        success "Packages Python installés"
        return 0
    else
        error "Échec installation Python"
        return 1
    fi
}

# ============================================================================
# TESTS FINAUX
# ============================================================================

run_tests() {
    section "TESTS FINAUX"
    
    local test_results=0
    
    # Test services
    log "Test des services..."
    for service in mysql apache2 redis-server ntp; do
        if systemctl is-active --quiet "$service"; then
            success "Service $service actif"
        else
            error "Service $service inactif"
            ((test_results++))
        fi
    done
    
    # Test Python
    log "Test Python..."
    if python3 -c "import flask, sqlalchemy, pymysql, redis; print('Python OK')" 2>/dev/null; then
        success "Environnement Python OK"
    else
        error "Environnement Python KO"
        ((test_results++))
    fi
    
    # Test réseau
    log "Test réseau..."
    if ping -c 1 -W 5 8.8.8.8 >/dev/null 2>&1; then
        success "Connectivité réseau OK"
    else
        error "Connectivité réseau KO"
        ((test_results++))
    fi
    
    # Test MySQL
    log "Test MySQL..."
    if mysql -u root -e "SHOW DATABASES;" >/dev/null 2>&1; then
        success "MySQL OK"
    else
        error "MySQL KO"
        ((test_results++))
    fi
    
    return $test_results
}

# ============================================================================
# RAPPORT FINAL
# ============================================================================

generate_report() {
    section "RAPPORT FINAL"
    
    echo -e "${WHITE}============================================${NC}"
    echo -e "${WHITE}    NTP MONITOR ENTERPRISE${NC}"
    echo -e "${WHITE}    Installation Ubuntu 24.04 LTS${NC}"
    echo -e "${WHITE}============================================${NC}"
    echo
    echo -e "${CYAN}Statistiques:${NC}"
    echo -e "${GREEN}  ✓ Succès: $PASSED_CHECKS${NC}"
    echo -e "${RED}  ✗ Échecs: $FAILED_CHECKS${NC}"
    echo -e "${YELLOW}  ⚠ Avertissements: $WARNINGS${NC}"
    echo
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}🎉 INSTALLATION COMPLÈTE RÉUSSIE !${NC}"
        echo -e "${GREEN}Votre système Ubuntu 24.04 est prêt pour NTP Monitor Enterprise${NC}"
        echo
        echo -e "${CYAN}Services configurés:${NC}"
        echo "  • MySQL avec base '$MYSQL_DB' et utilisateur '$MYSQL_USER'"
        echo "  • Apache avec mod_wsgi activé"
        echo "  • Redis opérationnel"
        echo "  • NTP synchronisé"
        echo "  • Firewall UFW configuré (ports 22, 80, 443)"
        echo
        echo -e "${CYAN}Prochaines étapes:${NC}"
        echo "  1. Cloner le projet: git clone https://github.com/gilandre/NTPVIZ.git"
        echo "  2. Déployer l'application: cd NTPVIZ && sudo ./deploy_ubuntu_production.sh"
        echo "  3. Accéder à l'interface web"
        echo
        echo -e "${CYAN}Informations importantes:${NC}"
        echo "  • Credentials MySQL: /root/mysql_credentials.txt"
        echo "  • Logs Apache: /var/log/apache2/error.log"
        echo "  • Status services: systemctl status mysql apache2 redis-server"
        echo
    else
        echo -e "${RED}❌ INSTALLATION INCOMPLÈTE${NC}"
        echo -e "${RED}$FAILED_CHECKS erreurs détectées${NC}"
        echo
        echo -e "${YELLOW}Actions recommandées:${NC}"
        echo "  • Vérifier les logs: journalctl -xe"
        echo "  • Vérifier les services: systemctl --failed"
        echo "  • Relancer le script après correction"
        echo
    fi
    
    echo -e "${WHITE}============================================${NC}"
    echo -e "${CYAN}Script version: $SCRIPT_VERSION${NC}"
    echo -e "${CYAN}Terminé: $(date)${NC}"
    echo -e "${WHITE}============================================${NC}"
}

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

main() {
    clear
    section "NTP MONITOR ENTERPRISE - VÉRIFICATION SYSTÈME UBUNTU 24.04"
    
    log "Démarrage du script de vérification v$SCRIPT_VERSION"
    log "Système détecté: $(lsb_release -ds 2>/dev/null || echo 'Ubuntu/Linux')"
    log "Date: $(date)"
    echo
    
    # Vérifications préliminaires
    if ! check_root; then
        exit 1
    fi
    
    check_ubuntu
    check_resources
    
    # Installation complète
    log "Début de l'installation automatique..."
    echo
    
    install_packages
    setup_mysql
    setup_apache
    setup_services
    setup_python
    
    # Tests finaux
    run_tests
    
    # Rapport final
    generate_report
    
    # Code de sortie
    if [ $FAILED_CHECKS -eq 0 ]; then
        log "Installation terminée avec succès"
        exit 0
    else
        log "Installation terminée avec des erreurs"
        exit 1
    fi
}

# ============================================================================
# EXECUTION
# ============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 