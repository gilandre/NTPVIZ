#!/bin/bash
# ============================================================================
# NTP Monitor Enterprise - Vérification et Installation des Dépendances
# Ubuntu Server 24.04 LTS - Script Holistique
# Version: 2.0.0 - CORRIGÉE
# ============================================================================

set -e

# Configuration
SCRIPT_VERSION="2.0.0-fixed"
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
# VÉRIFICATIONS SYSTÈME
# ============================================================================

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Ce script doit être exécuté en tant que root (sudo)"
        exit 1
    fi
    success "Privilèges root confirmés"
}

check_ubuntu_version() {
    check_start "Version Ubuntu"
    
    if [ ! -f /etc/os-release ]; then
        error "Impossible de détecter la version Ubuntu"
        return 1
    fi
    
    source /etc/os-release
    
    if [[ "$ID" != "ubuntu" ]]; then
        error "Système non Ubuntu détecté: $ID"
        return 1
    fi
    
    case "$VERSION_ID" in
        "24.04"|"24.10")
            success "Version Ubuntu supportée: $VERSION_ID"
            ;;
        "22.04"|"23.04"|"23.10")
            warn "Version Ubuntu ancienne mais compatible: $VERSION_ID"
            ;;
        *)
            error "Version Ubuntu non supportée: $VERSION_ID"
            return 1
            ;;
    esac
}

check_system_resources() {
    check_start "Ressources système"
    
    # RAM
    total_mem=$(free -m | awk 'NR==2{print $2}')
    if [ "$total_mem" -lt 1024 ]; then
        error "RAM insuffisante: ${total_mem}MB (minimum: 1024MB)"
        return 1
    elif [ "$total_mem" -lt 2048 ]; then
        warn "RAM faible: ${total_mem}MB (recommandé: 2048MB+)"
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
# VÉRIFICATIONS PACKAGES
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
    section "VÉRIFICATION PACKAGES SYSTÈME"
    
    local required_packages=(
        # Outils système essentiels
        "curl" "wget" "git" "htop" "vim" "tree" "net-tools" "unzip"
        "software-properties-common" "apt-transport-https" "ca-certificates" 
        "gnupg" "lsb-release" "build-essential" "pkg-config" "ufw"
        
        # Python et dépendances
        "python3" "python3-pip" "python3-venv" "python3-dev" 
        "python3-setuptools" "python3-wheel" "python3-distutils"
        
        # MySQL
        "mysql-server" "mysql-client" "libmysqlclient-dev" "mysql-common"
        
        # Apache et modules
        "apache2" "libapache2-mod-wsgi-py3" "apache2-utils"
        
        # Services réseau
        "redis-server" "ntp" "ntpdate" "ntpstat"
        
        # SSL/TLS et sécurité
        "certbot" "python3-certbot-apache" "openssl"
        
        # Outils de monitoring
        "psmisc" "lsof" "tcpdump" "iftop"
    )
    
    local missing_packages=()
    
    for package in "${required_packages[@]}"; do
        if ! check_package_installed "$package"; then
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -eq 0 ]; then
        success "Tous les packages requis sont installés"
        return 0
    else
        warn "Packages manquants (${#missing_packages[@]}): ${missing_packages[*]}"
        return 1
    fi
}

# ============================================================================
# VÉRIFICATIONS PYTHON
# ============================================================================

check_python_environment() {
    section "VÉRIFICATION PYTHON"
    
    check_start "Version Python"
    if ! command -v python3 &> /dev/null; then
        error "Python 3 non installé"
        return 1
    fi
    
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    python_major=$(echo "$python_version" | cut -d'.' -f1)
    python_minor=$(echo "$python_version" | cut -d'.' -f2)
    
    if [ "$python_major" -lt 3 ] || [ "$python_minor" -lt 11 ]; then
        error "Version Python insuffisante: $python_version (requis: 3.11+)"
        return 1
    else
        success "Version Python OK: $python_version"
    fi
    
    check_start "pip3"
    if ! command -v pip3 &> /dev/null; then
        error "pip3 non installé"
        return 1
    else
        success "pip3 disponible"
    fi
    
    check_start "python3-venv"
    if ! python3 -m venv --help &> /dev/null; then
        error "python3-venv non installé"
        return 1
    else
        success "python3-venv disponible"
    fi
    
    check_start "Modules Python critiques"
    local critical_modules=("sqlite3" "json" "datetime" "threading" "subprocess")
    local modules_ok=true
    
    for module in "${critical_modules[@]}"; do
        if ! python3 -c "import $module" &> /dev/null; then
            error "Module Python $module manquant"
            modules_ok=false
        fi
    done
    
    if [ "$modules_ok" = true ]; then
        success "Modules Python critiques disponibles"
    else
        return 1
    fi
}

# ============================================================================
# VÉRIFICATIONS SERVICES
# ============================================================================

check_service_detailed() {
    local service=$1
    
    if systemctl is-active --quiet "$service"; then
        success "Service $service actif"
        return 0
    elif systemctl is-enabled --quiet "$service" 2>/dev/null; then
        warn "Service $service installé mais arrêté"
        return 1
    else
        error "Service $service non installé"
        return 2
    fi
}

check_all_services() {
    section "VÉRIFICATION SERVICES"
    
    local services=("mysql" "apache2" "redis-server" "ntp")
    local services_issues=0
    
    for service in "${services[@]}"; do
        check_start "Service $service"
        if ! check_service_detailed "$service"; then
            ((services_issues++))
        fi
    done
    
    return $services_issues
}

# ============================================================================
# VÉRIFICATIONS MYSQL
# ============================================================================

check_mysql_detailed() {
    section "VÉRIFICATION MYSQL"
    
    check_start "Serveur MySQL"
    if ! command -v mysql &> /dev/null; then
        error "Client MySQL non installé"
        return 1
    fi
    
    if ! systemctl is-active --quiet mysql; then
        error "Serveur MySQL non actif"
        return 1
    fi
    
    if mysql -u root -e "SELECT VERSION();" &> /dev/null; then
        mysql_version=$(mysql -u root -e "SELECT VERSION();" 2>/dev/null | tail -1)
        success "MySQL opérationnel: $mysql_version"
    else
        warn "MySQL actif mais connexion root protégée"
    fi
    
    check_start "Headers MySQL"
    if ! dpkg -l | grep -q libmysqlclient-dev; then
        error "Headers MySQL manquants (libmysqlclient-dev)"
        return 1
    else
        success "Headers MySQL installés"
    fi
    
    check_start "Driver PyMySQL"
    if python3 -c "import pymysql" &> /dev/null; then
        success "Driver PyMySQL disponible"
    else
        warn "Driver PyMySQL à installer"
    fi
    
    return 0
}

# ============================================================================
# VÉRIFICATIONS APACHE
# ============================================================================

check_apache_detailed() {
    section "VÉRIFICATION APACHE"
    
    check_start "Apache2"
    if ! command -v apache2 &> /dev/null; then
        error "Apache2 non installé"
        return 1
    fi
    
    if systemctl is-active --quiet apache2; then
        success "Apache2 actif"
    else
        warn "Apache2 installé mais arrêté"
    fi
    
    local required_modules=("wsgi" "rewrite" "ssl" "headers")
    local modules_ok=true
    
    for module in "${required_modules[@]}"; do
        check_start "Module Apache $module"
        if apache2ctl -M 2>/dev/null | grep -q "${module}_module"; then
            success "Module $module activé"
        else
            error "Module $module manquant"
            modules_ok=false
        fi
    done
    
    check_start "Ports Apache"
    if netstat -tlnp 2>/dev/null | grep -q ":80 "; then
        success "Port 80 en écoute"
    else
        warn "Port 80 non en écoute"
    fi
    
    if [ "$modules_ok" = false ]; then
        return 1
    fi
    
    return 0
}

# ============================================================================
# VÉRIFICATIONS RÉSEAU
# ============================================================================

check_network_detailed() {
    section "VÉRIFICATION RÉSEAU"
    
    check_start "Connexion Internet"
    if ping -c 1 -W 5 8.8.8.8 &> /dev/null; then
        success "Connexion Internet OK"
    else
        error "Pas de connexion Internet"
        return 1
    fi
    
    check_start "Résolution DNS"
    if nslookup google.com &> /dev/null; then
        success "Résolution DNS OK"
    else
        error "Résolution DNS échouée"
        return 1
    fi
    
    check_start "Serveurs NTP"
    if timeout 10 ntpdate -q pool.ntp.org &> /dev/null; then
        success "Serveurs NTP accessibles"
    else
        warn "Serveurs NTP non accessibles"
    fi
    
    check_start "Pare-feu UFW"
    if command -v ufw &> /dev/null; then
        ufw_status=$(ufw status 2>/dev/null | head -1)
        if echo "$ufw_status" | grep -q "Status: active"; then
            success "UFW actif"
        else
            warn "UFW inactif"
        fi
    else
        error "UFW non installé"
        return 1
    fi
    
    return 0
}

# ============================================================================
# INSTALLATION AUTOMATIQUE
# ============================================================================

install_missing_packages() {
    section "INSTALLATION PACKAGES SYSTÈME"
    
    log "Mise à jour des références..."
    apt update -y
    
    log "Mise à jour du système..."
    apt upgrade -y
    
    log "Installation des packages..."
    apt install -y \
        curl wget git htop vim tree net-tools unzip \
        software-properties-common apt-transport-https ca-certificates gnupg lsb-release \
        build-essential pkg-config ufw \
        python3 python3-pip python3-venv python3-dev python3-setuptools python3-wheel python3-distutils \
        mysql-server mysql-client libmysqlclient-dev mysql-common \
        apache2 libapache2-mod-wsgi-py3 apache2-utils \
        redis-server ntp ntpdate ntpstat \
        certbot python3-certbot-apache openssl \
        psmisc lsof tcpdump iftop
    
    success "Packages système installés"
}

configure_mysql_complete() {
    section "CONFIGURATION MYSQL"
    
    log "Démarrage MySQL..."
    systemctl enable mysql
    systemctl start mysql
    
    log "Sécurisation MySQL..."
    mysql -u root << 'EOFMYSQL'
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
EOFMYSQL
    
    log "Création base de données..."
    MYSQL_PASSWORD=$(openssl rand -base64 16)
    mysql -u root << EOFMYSQL
CREATE DATABASE IF NOT EXISTS $MYSQL_DB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$MYSQL_USER'@'localhost' IDENTIFIED BY '$MYSQL_PASSWORD';
GRANT ALL PRIVILEGES ON $MYSQL_DB.* TO '$MYSQL_USER'@'localhost';
FLUSH PRIVILEGES;
EOFMYSQL
    
    cat > /root/mysql_credentials.txt << EOFCRED
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=$MYSQL_DB
MYSQL_USER=$MYSQL_USER
MYSQL_PASSWORD=$MYSQL_PASSWORD
EOFCRED
    chmod 600 /root/mysql_credentials.txt
    
    success "MySQL configuré - Credentials: /root/mysql_credentials.txt"
}

configure_apache_complete() {
    section "CONFIGURATION APACHE"
    
    log "Configuration Apache..."
    systemctl enable apache2
    systemctl start apache2
    
    log "Activation des modules..."
    a2enmod wsgi rewrite ssl headers
    
    systemctl restart apache2
    
    success "Apache configuré"
}

configure_all_services() {
    section "CONFIGURATION SERVICES"
    
    log "Configuration Redis..."
    systemctl enable redis-server
    systemctl start redis-server
    
    log "Configuration NTP..."
    systemctl enable ntp
    systemctl start ntp
    
    log "Configuration UFW..."
    ufw --force enable
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 123/udp
    
    success "Services configurés"
}

install_python_packages() {
    section "INSTALLATION PYTHON"
    
    log "Mise à jour pip..."
    python3 -m pip install --upgrade pip setuptools wheel
    
    log "Installation des packages Python..."
    python3 -m pip install \
        Flask==2.3.3 \
        Flask-SQLAlchemy==3.0.5 \
        Flask-SocketIO==5.3.6 \
        Flask-Login==0.6.3 \
        Flask-WTF==1.2.1 \
        SQLAlchemy==2.0.21 \
        PyMySQL==1.1.0 \
        redis==5.0.1 \
        ntplib==0.4.0 \
        psutil==5.9.5 \
        requests==2.31.0 \
        Werkzeug==2.3.7 \
        bcrypt==4.0.1 \
        python-socketio==5.8.0 \
        gunicorn==21.2.0 \
        python-dotenv==1.0.0 \
        cryptography \
        pytz \
        python-dateutil \
        pandas \
        numpy
    
    success "Dépendances Python installées"
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
        success "✓ MySQL opérationnel"
        ((tests_passed++))
    else
        error "✗ MySQL non opérationnel"
    fi
    
    ((tests_total++))
    if systemctl is-active --quiet apache2; then
        success "✓ Apache opérationnel"
        ((tests_passed++))
    else
        error "✗ Apache non opérationnel"
    fi
    
    ((tests_total++))
    if redis-cli ping &> /dev/null; then
        success "✓ Redis opérationnel"
        ((tests_passed++))
    else
        error "✗ Redis non opérationnel"
    fi
    
    ((tests_total++))
    if ntpq -p &> /dev/null; then
        success "✓ NTP opérationnel"
        ((tests_passed++))
    else
        warn "⚠ NTP non opérationnel"
    fi
    
    ((tests_total++))
    if python3 -c "import flask, sqlalchemy, pymysql, redis, ntplib, psutil" &> /dev/null; then
        success "✓ Python complet"
        ((tests_passed++))
    else
        error "✗ Python incomplet"
    fi
    
    ((tests_total++))
    if ping -c 1 -W 5 8.8.8.8 &> /dev/null; then
        success "✓ Réseau OK"
        ((tests_passed++))
    else
        error "✗ Réseau KO"
    fi
    
    log "Tests réussis: $tests_passed/$tests_total"
    
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
    echo -e "${CYAN}Checks effectués:${NC} $TOTAL_CHECKS"
    echo -e "${GREEN}Succès:${NC} $PASSED_CHECKS"
    echo -e "${RED}Échecs:${NC} $FAILED_CHECKS"
    echo -e "${YELLOW}Avertissements:${NC} $WARNINGS"
    echo
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}🎉 INSTALLATION RÉUSSIE !${NC}"
        echo -e "${GREEN}Système Ubuntu 24.04 prêt pour NTP Monitor Enterprise${NC}"
        echo
        echo -e "${CYAN}🔧 Configuration:${NC}"
        echo "  ✓ Ubuntu $(lsb_release -rs) à jour"
        echo "  ✓ Python $(python3 --version | cut -d' ' -f2)"
        echo "  ✓ MySQL opérationnel"
        echo "  ✓ Apache avec mod_wsgi"
        echo "  ✓ Redis actif"
        echo "  ✓ NTP synchronisé"
        echo "  ✓ UFW configuré"
        echo
        echo -e "${CYAN}📊 Base de données:${NC}"
        echo "  • DB: $MYSQL_DB"
        echo "  • User: $MYSQL_USER"
        echo "  • Pass: /root/mysql_credentials.txt"
        echo
        echo -e "${CYAN}🌐 Ports:${NC}"
        echo "  • HTTP: 80"
        echo "  • HTTPS: 443"
        echo "  • NTP: 123/udp"
        echo "  • SSH: 22"
        echo
        echo -e "${CYAN}🚀 Prochaines étapes:${NC}"
        echo "  1. Cloner NTP Monitor Enterprise"
        echo "  2. Configurer .env"
        echo "  3. Lancer deploy_ubuntu_production.sh"
        echo "  4. Configurer SSL (certbot)"
        echo "  5. Accéder à l'interface web"
        echo
    else
        echo -e "${RED}❌ INSTALLATION INCOMPLÈTE${NC}"
        echo -e "${RED}Erreurs détectées à corriger${NC}"
        echo
        echo -e "${YELLOW}🔧 Actions:${NC}"
        echo "  1. Corriger les erreurs ci-dessus"
        echo "  2. Relancer: sudo $0"
        echo "  3. Vérifier logs: journalctl -xe"
        echo "  4. Vérifier réseau et ressources"
    fi
    
    echo -e "${WHITE}============================================${NC}"
    echo -e "${CYAN}Script v$SCRIPT_VERSION - $(date)${NC}"
    echo -e "${WHITE}============================================${NC}"
}

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

main() {
    clear
    section "NTP MONITOR ENTERPRISE - VÉRIFICATION UBUNTU 24.04"
    
    log "Script v$SCRIPT_VERSION"
    log "Système: $(lsb_release -ds 2>/dev/null || echo 'Ubuntu/Linux')"
    log "Date: $(date)"
    
    # Vérifications de base
    check_root
    check_ubuntu_version
    check_system_resources
    
    # Vérifications détaillées
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
    
    # Installation automatique si nécessaire
    if [ "$need_install" = true ]; then
        section "INSTALLATION AUTOMATIQUE"
        
        log "Éléments manquants détectés"
        log "Démarrage installation automatique..."
        
        install_missing_packages
        configure_mysql_complete
        configure_apache_complete
        configure_all_services
        install_python_packages
        
        log "Installation terminée"
        
        if run_comprehensive_tests; then
            success "Tests finaux réussis"
        else
            error "Tests finaux échoués"
        fi
    else
        log "Système correctement configuré"
        run_comprehensive_tests
    fi
    
    generate_final_report
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        log "Script terminé avec succès"
        exit 0
    else
        error "Script terminé avec erreurs"
        exit 1
    fi
}

# ============================================================================
# EXÉCUTION
# ============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 