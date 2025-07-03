#!/bin/bash
# ============================================================================
# NTP Monitor Enterprise - Verification et Installation des Dependances
# Ubuntu Server 24.04 LTS - Script Fonctionnel
# Version: 2.1.0
# ============================================================================

set -e

# Configuration
SCRIPT_VERSION="2.1.0"
MYSQL_DB="ntp_monitor"
MYSQL_USER="ntp_user"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

check_start() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')] CHECK: $1${NC}"
    ((TOTAL_CHECKS++))
}

section() {
    echo -e "\n${WHITE}============================================================================${NC}"
    echo -e "${WHITE}$1${NC}"
    echo -e "${WHITE}============================================================================${NC}\n"
}

# ============================================================================
# VERIFICATIONS SYSTEME
# ============================================================================

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Ce script doit etre execute en tant que root (sudo)"
        exit 1
    fi
    success "Privileges root confirmes"
}

check_ubuntu_version() {
    check_start "Version Ubuntu"
    
    if [ ! -f /etc/os-release ]; then
        error "Impossible de detecter la version Ubuntu"
        return 1
    fi
    
    source /etc/os-release
    
    if [[ "$ID" != "ubuntu" ]]; then
        error "Systeme non Ubuntu detecte: $ID"
        return 1
    fi
    
    case "$VERSION_ID" in
        "24.04"|"24.10")
            success "Version Ubuntu supportee: $VERSION_ID"
            ;;
        "22.04"|"23.04"|"23.10")
            warn "Version Ubuntu ancienne mais compatible: $VERSION_ID"
            ;;
        *)
            error "Version Ubuntu non supportee: $VERSION_ID"
            return 1
            ;;
    esac
}

check_system_resources() {
    check_start "Ressources systeme"
    
    # RAM
    total_mem=$(free -m | awk 'NR==2{print $2}')
    if [ "$total_mem" -lt 1024 ]; then
        error "RAM insuffisante: ${total_mem}MB (minimum: 1024MB)"
        return 1
    else
        success "RAM suffisante: ${total_mem}MB"
    fi
    
    # Disque
    disk_space=$(df / | awk 'NR==2{print $4}')
    disk_space_gb=$((disk_space / 1024 / 1024))
    if [ "$disk_space_gb" -lt 5 ]; then
        error "Espace disque insuffisant: ${disk_space_gb}GB (minimum: 5GB)"
        return 1
    else
        success "Espace disque suffisant: ${disk_space_gb}GB"
    fi
}

# ============================================================================
# VERIFICATIONS PACKAGES
# ============================================================================

check_package_installed() {
    local package=$1
    if dpkg -l | grep -q "^ii  $package "; then
        return 0
    else
        return 1
    fi
}

check_all_packages() {
    section "VERIFICATION PACKAGES SYSTEME"
    
    local required_packages=(
        "curl" "wget" "git" "htop" "vim" "tree" "net-tools" "unzip"
        "software-properties-common" "apt-transport-https" "ca-certificates" 
        "gnupg" "lsb-release" "build-essential" "pkg-config" "ufw"
        "python3" "python3-pip" "python3-venv" "python3-dev" 
        "python3-setuptools" "python3-wheel"
        "mysql-server" "mysql-client" "libmysqlclient-dev"
        "apache2" "libapache2-mod-wsgi-py3" "apache2-utils"
        "redis-server" "ntp" "ntpdate"
        "certbot" "python3-certbot-apache" "openssl"
    )
    
    local missing_packages=()
    
    for package in "${required_packages[@]}"; do
        if ! check_package_installed "$package"; then
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -eq 0 ]; then
        success "Tous les packages requis sont installes"
        return 0
    else
        warn "Packages manquants (${#missing_packages[@]}): ${missing_packages[*]}"
        return 1
    fi
}

# ============================================================================
# VERIFICATIONS SERVICES
# ============================================================================

check_service_detailed() {
    local service=$1
    
    if systemctl is-active --quiet "$service"; then
        success "Service $service actif"
        return 0
    elif systemctl is-enabled --quiet "$service" 2>/dev/null; then
        warn "Service $service installe mais arrete"
        return 1
    else
        error "Service $service non installe"
        return 2
    fi
}

check_all_services() {
    section "VERIFICATION SERVICES"
    
    local services=("mysql" "apache2" "redis-server" "ntp")
    local services_issues=0
    
    for service in "${services[@]}"; do
        check_start "Service $service"
        if ! check_service_detailed "$service"; then
            ((services_issues++))
        fi
    done
    
    if [ $services_issues -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# VERIFICATIONS MYSQL
# ============================================================================

check_mysql_detailed() {
    section "VERIFICATION MYSQL"
    
    check_start "Serveur MySQL"
    if ! command -v mysql &> /dev/null; then
        error "Client MySQL non installe"
        return 1
    fi
    
    if ! systemctl is-active --quiet mysql; then
        error "Serveur MySQL non actif"
        return 1
    fi
    
    if mysql -u root -e "SELECT VERSION();" &> /dev/null; then
        mysql_version=$(mysql -u root -e "SELECT VERSION();" 2>/dev/null | tail -1)
        success "MySQL operationnel: $mysql_version"
    else
        warn "MySQL actif mais connexion root protegee"
    fi
    
    return 0
}

# ============================================================================
# VERIFICATIONS PYTHON
# ============================================================================

check_python_environment() {
    section "VERIFICATION PYTHON"
    
    check_start "Version Python"
    if ! command -v python3 &> /dev/null; then
        error "Python 3 non installe"
        return 1
    fi
    
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    python_major=$(echo "$python_version" | cut -d'.' -f1)
    python_minor=$(echo "$python_version" | cut -d'.' -f2)
    
    if [ "$python_major" -lt 3 ] || [ "$python_minor" -lt 9 ]; then
        error "Version Python insuffisante: $python_version (requis: 3.9+)"
        return 1
    else
        success "Version Python OK: $python_version"
    fi
    
    check_start "pip3"
    if ! command -v pip3 &> /dev/null; then
        error "pip3 non installe"
        return 1
    else
        success "pip3 disponible"
    fi
    
    return 0
}

# ============================================================================
# VERIFICATIONS APACHE
# ============================================================================

check_apache_detailed() {
    section "VERIFICATION APACHE"
    
    check_start "Apache2"
    if ! command -v apache2 &> /dev/null; then
        error "Apache2 non installe"
        return 1
    fi
    
    if systemctl is-active --quiet apache2; then
        success "Apache2 actif"
    else
        warn "Apache2 installe mais arrete"
    fi
    
    return 0
}

# ============================================================================
# VERIFICATIONS RESEAU
# ============================================================================

check_network_detailed() {
    section "VERIFICATION RESEAU"
    
    check_start "Connexion Internet"
    if ping -c 1 -W 5 8.8.8.8 &> /dev/null; then
        success "Connexion Internet OK"
    else
        error "Pas de connexion Internet"
        return 1
    fi
    
    check_start "Pare-feu UFW"
    if command -v ufw &> /dev/null; then
        success "UFW installe"
    else
        error "UFW non installe"
        return 1
    fi
    
    return 0
}

# ============================================================================
# INSTALLATION AUTOMATIQUE
# ============================================================================

install_missing_packages() {
    section "INSTALLATION PACKAGES SYSTEME"
    
    log "Mise a jour des references..."
    apt update -y
    
    log "Installation des packages..."
    apt install -y \
        curl wget git htop vim tree net-tools unzip \
        software-properties-common apt-transport-https ca-certificates gnupg lsb-release \
        build-essential pkg-config ufw \
        python3 python3-pip python3-venv python3-dev python3-setuptools python3-wheel \
        mysql-server mysql-client libmysqlclient-dev \
        apache2 libapache2-mod-wsgi-py3 apache2-utils \
        redis-server ntp ntpdate \
        certbot python3-certbot-apache openssl
    
    success "Packages systeme installes"
}

configure_mysql_complete() {
    section "CONFIGURATION MYSQL"
    
    log "Demarrage MySQL..."
    systemctl enable mysql
    systemctl start mysql
    
    log "Creation base de donnees..."
    MYSQL_PASSWORD=$(openssl rand -base64 16)
    mysql -u root << 'EOFMYSQL'
CREATE DATABASE IF NOT EXISTS ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'ntp_user'@'localhost' IDENTIFIED BY 'temp_password';
GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_user'@'localhost';
FLUSH PRIVILEGES;
EOFMYSQL
    
    mysql -u root -e "ALTER USER 'ntp_user'@'localhost' IDENTIFIED BY '$MYSQL_PASSWORD';"
    
    echo "MYSQL_PASSWORD=$MYSQL_PASSWORD" > /root/mysql_credentials.txt
    chmod 600 /root/mysql_credentials.txt
    
    success "MySQL configure - Credentials: /root/mysql_credentials.txt"
}

configure_apache_complete() {
    section "CONFIGURATION APACHE"
    
    systemctl enable apache2
    systemctl start apache2
    
    a2enmod wsgi rewrite ssl headers
    systemctl restart apache2
    
    success "Apache configure avec modules requis"
}

configure_all_services() {
    section "CONFIGURATION SERVICES"
    
    systemctl enable redis-server
    systemctl start redis-server
    
    systemctl enable ntp
    systemctl start ntp
    
    ufw --force enable
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 123/udp
    
    success "Services configures - Ports ouverts: 22, 80, 443, 123"
}

install_python_packages() {
    section "INSTALLATION PYTHON"
    
    log "Mise a jour pip..."
    python3 -m pip install --upgrade pip
    
    log "Installation Flask et dependances..."
    python3 -m pip install Flask==2.3.3
    python3 -m pip install Flask-SQLAlchemy==3.0.5
    python3 -m pip install Flask-SocketIO==5.3.6
    python3 -m pip install Flask-Login==0.6.3
    python3 -m pip install Flask-WTF==1.2.1
    python3 -m pip install SQLAlchemy==2.0.21
    python3 -m pip install PyMySQL==1.1.0
    python3 -m pip install redis==5.0.1
    python3 -m pip install ntplib==0.4.0
    python3 -m pip install psutil==5.9.5
    python3 -m pip install requests==2.31.0
    python3 -m pip install Werkzeug==2.3.7
    python3 -m pip install bcrypt==4.0.1
    python3 -m pip install python-socketio==5.8.0
    python3 -m pip install gunicorn==21.2.0
    python3 -m pip install python-dotenv==1.0.0
    python3 -m pip install cryptography
    python3 -m pip install pytz
    python3 -m pip install python-dateutil
    
    success "Dependances Python installees"
}

# ============================================================================
# TESTS FINAUX
# ============================================================================

run_comprehensive_tests() {
    section "TESTS FINAUX"
    
    local tests_passed=0
    local tests_total=0
    
    ((tests_total++))
    if mysql -u root -e "SELECT VERSION();" &> /dev/null; then
        success "Test MySQL: REUSSI"
        ((tests_passed++))
    else
        error "Test MySQL: ECHEC"
    fi
    
    ((tests_total++))
    if systemctl is-active --quiet apache2; then
        success "Test Apache: REUSSI"
        ((tests_passed++))
    else
        error "Test Apache: ECHEC"
    fi
    
    ((tests_total++))
    if systemctl is-active --quiet redis-server; then
        success "Test Redis: REUSSI"
        ((tests_passed++))
    else
        error "Test Redis: ECHEC"
    fi
    
    ((tests_total++))
    if python3 -c "import flask, sqlalchemy, pymysql, redis" &> /dev/null; then
        success "Test Python: REUSSI"
        ((tests_passed++))
    else
        error "Test Python: ECHEC"
    fi
    
    ((tests_total++))
    if ping -c 1 -W 5 8.8.8.8 &> /dev/null; then
        success "Test Reseau: REUSSI"
        ((tests_passed++))
    else
        error "Test Reseau: ECHEC"
    fi
    
    log "BILAN TESTS: $tests_passed/$tests_total reussis"
    
    if [ "$tests_passed" -eq "$tests_total" ]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# RAPPORT FINAL
# ============================================================================

generate_final_report() {
    section "RAPPORT FINAL"
    
    echo -e "${WHITE}============================================${NC}"
    echo -e "${WHITE}    NTP MONITOR ENTERPRISE${NC}"
    echo -e "${WHITE}    Installation Ubuntu 24.04 LTS${NC}"
    echo -e "${WHITE}============================================${NC}"
    echo
    echo -e "${CYAN}Checks effectues:${NC} $TOTAL_CHECKS"
    echo -e "${GREEN}Succes:${NC} $PASSED_CHECKS"
    echo -e "${RED}Echecs:${NC} $FAILED_CHECKS"
    echo -e "${YELLOW}Avertissements:${NC} $WARNINGS"
    echo
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}INSTALLATION COMPLETE ET REUSSIE !${NC}"
        echo -e "${GREEN}Systeme Ubuntu 24.04 pret pour NTP Monitor Enterprise${NC}"
        echo
        echo -e "${CYAN}Configuration systeme:${NC}"
        echo "  - Ubuntu $(lsb_release -rs) configure"
        echo "  - Python $(python3 --version | cut -d' ' -f2) installe"
        echo "  - MySQL operationnel avec base ntp_monitor"
        echo "  - Apache avec mod_wsgi active"
        echo "  - Redis actif pour cache/sessions"
        echo "  - NTP synchronise"
        echo "  - Pare-feu UFW configure"
        echo
        echo -e "${CYAN}Base de donnees MySQL:${NC}"
        echo "  - Base: ntp_monitor"
        echo "  - Utilisateur: ntp_user"
        echo "  - Mot de passe: voir /root/mysql_credentials.txt"
        echo
        echo -e "${CYAN}Ports configures:${NC}"
        echo "  - HTTP: 80 (ouvert)"
        echo "  - HTTPS: 443 (ouvert)"
        echo "  - NTP: 123/udp (ouvert)"
        echo "  - SSH: 22 (ouvert)"
        echo
        echo -e "${CYAN}Prochaines etapes:${NC}"
        echo "  1. Telecharger le code NTP Monitor Enterprise"
        echo "  2. Configurer le fichier .env avec les credentials MySQL"
        echo "  3. Lancer le script deploy_ubuntu_production.sh"
        echo "  4. Configurer SSL/TLS avec certbot"
        echo "  5. Acceder a l'interface web"
        echo
        echo -e "${CYAN}Commandes utiles:${NC}"
        echo "  - Status services: systemctl status mysql apache2 redis-server"
        echo "  - Logs Apache: tail -f /var/log/apache2/error.log"
        echo "  - Logs MySQL: tail -f /var/log/mysql/error.log"
        echo "  - Test web: curl -I http://localhost"
        echo "  - Credentials MySQL: cat /root/mysql_credentials.txt"
        echo
    else
        echo -e "${RED}INSTALLATION INCOMPLETE${NC}"
        echo -e "${RED}$FAILED_CHECKS erreurs detectees qui doivent etre corrigees${NC}"
        echo
        echo -e "${YELLOW}Actions recommandees:${NC}"
        echo "  1. Corriger les erreurs signalees ci-dessus"
        echo "  2. Relancer le script: sudo $0"
        echo "  3. Verifier les logs systeme: journalctl -xe"
        echo "  4. Verifier espace disque: df -h"
        echo "  5. Verifier memoire: free -h"
        echo "  6. Verifier connexion reseau: ping 8.8.8.8"
        echo
    fi
    
    echo -e "${WHITE}============================================${NC}"
    echo -e "${CYAN}Script version: $SCRIPT_VERSION${NC}"
    echo -e "${CYAN}Rapport genere: $(date)${NC}"
    echo -e "${WHITE}============================================${NC}"
}

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

main() {
    clear
    section "NTP MONITOR ENTERPRISE - VERIFICATEUR UBUNTU 24.04"
    
    log "Demarrage du script v$SCRIPT_VERSION"
    log "Systeme detecte: $(lsb_release -ds 2>/dev/null || echo 'Linux')"
    log "Date/Heure: $(date)"
    log "Utilisateur: $(whoami)"
    echo
    
    # Verifications de base obligatoires
    check_root
    check_ubuntu_version
    check_system_resources
    
    # Verifications detaillees
    local need_install=false
    
    if ! check_all_packages; then
        need_install=true
    fi
    
    if ! check_python_environment; then
        need_install=true
    fi
    
    if ! check_all_services; then
        need_install=true
    fi
    
    if ! check_mysql_detailed; then
        need_install=true
    fi
    
    if ! check_apache_detailed; then
        need_install=true
    fi
    
    if ! check_network_detailed; then
        need_install=true
    fi
    
    # Installation automatique si necessaire
    if [ "$need_install" = true ]; then
        section "INSTALLATION AUTOMATIQUE REQUISE"
        
        log "Des elements manquants ont ete detectes"
        log "Demarrage de l'installation automatique..."
        echo
        
        install_missing_packages
        configure_mysql_complete
        configure_apache_complete
        configure_all_services
        install_python_packages
        
        log "Installation terminee - Lancement des tests finaux..."
        echo
        
        if run_comprehensive_tests; then
            success "Tous les tests finaux ont reussi"
        else
            error "Certains tests finaux ont echoue"
        fi
    else
        log "Systeme deja correctement configure"
        log "Execution des tests de verification..."
        echo
        run_comprehensive_tests
    fi
    
    # Rapport final
    generate_final_report
    
    # Code de sortie
    if [ $FAILED_CHECKS -eq 0 ]; then
        log "Script termine avec succes - Systeme pret !"
        exit 0
    else
        error "Script termine avec des erreurs - Verifications necessaires"
        exit 1
    fi
}

# ============================================================================
# EXECUTION DU SCRIPT
# ============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 