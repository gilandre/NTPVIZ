#!/bin/bash
# ============================================================================
# NTP Monitor Enterprise - Vérification et Installation Complète des Dépendances
# Ubuntu Server 24.04 LTS - Script Holistique
# Version: 2.0.0
# ============================================================================

set -e  # Arrêt immédiat en cas d'erreur

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_VERSION="2.0.0"
REQUIRED_UBUNTU_VERSION="24.04"
REQUIRED_PYTHON_VERSION="3.11"
APP_NAME="ntp-monitor-enterprise"
APP_USER="ntp-monitor"
MYSQL_DB="ntp_monitor"
MYSQL_USER="ntp_user"
WORKING_DIR="/opt/ntp-monitor-enterprise"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Variables globales
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0
INSTALL_NEEDED=()

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
# VÉRIFICATION SYSTÈME
# ============================================================================

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Ce script doit être exécuté en tant que root (sudo)"
        exit 1
    fi
    success "Privilèges root confirmés"
}

check_ubuntu_version() {
    check_start "Vérification version Ubuntu"
    
    if [ ! -f /etc/os-release ]; then
        error "Impossible de détecter la version Ubuntu"
        return 1
    fi
    
    source /etc/os-release
    
    if [[ "$ID" != "ubuntu" ]]; then
        error "Système non Ubuntu détecté: $ID"
        return 1
    fi
    
    version_ok=false
    case "$VERSION_ID" in
        "24.04"|"24.10")
            success "Version Ubuntu supportée: $VERSION_ID"
            version_ok=true
            ;;
        "22.04"|"23.04"|"23.10")
            warn "Version Ubuntu ancienne mais compatible: $VERSION_ID"
            version_ok=true
            ;;
        *)
            error "Version Ubuntu non supportée: $VERSION_ID (requis: 24.04+)"
            ;;
    esac
    
    if [ "$version_ok" = false ]; then
        return 1
    fi
}

check_system_architecture() {
    check_start "Vérification architecture système"
    
    arch=$(uname -m)
    case "$arch" in
        "x86_64"|"amd64")
            success "Architecture supportée: $arch"
            ;;
        "aarch64"|"arm64")
            warn "Architecture ARM détectée: $arch (peut nécessiter des ajustements)"
            ;;
        *)
            error "Architecture non supportée: $arch"
            return 1
            ;;
    esac
}

check_system_resources() {
    check_start "Vérification ressources système"
    
    # Vérifier RAM
    total_mem=$(free -m | awk 'NR==2{print $2}')
    if [ "$total_mem" -lt 1024 ]; then
        error "RAM insuffisante: ${total_mem}MB (minimum: 1024MB)"
        return 1
    elif [ "$total_mem" -lt 2048 ]; then
        warn "RAM faible: ${total_mem}MB (recommandé: 2048MB+)"
    else
        success "RAM suffisante: ${total_mem}MB"
    fi
    
    # Vérifier espace disque
    disk_space=$(df / | awk 'NR==2{print $4}')
    disk_space_gb=$((disk_space / 1024 / 1024))
    if [ "$disk_space_gb" -lt 5 ]; then
        error "Espace disque insuffisant: ${disk_space_gb}GB (minimum: 5GB)"
        return 1
    elif [ "$disk_space_gb" -lt 10 ]; then
        warn "Espace disque faible: ${disk_space_gb}GB (recommandé: 10GB+)"
    else
        success "Espace disque suffisant: ${disk_space_gb}GB"
    fi
}

# ============================================================================
# VÉRIFICATION PACKAGES SYSTÈME
# ============================================================================

check_package_installed() {
    local package=$1
    if dpkg -l | grep -q "^ii  $package "; then
        return 0
    else
        return 1
    fi
}

check_system_packages() {
    section "VÉRIFICATION PACKAGES SYSTÈME"
    
    # Packages système essentiels
    local essential_packages=(
        "curl"
        "wget"
        "git"
        "htop"
        "vim"
        "software-properties-common"
        "apt-transport-https"
        "ca-certificates"
        "gnupg"
        "lsb-release"
        "build-essential"
        "pkg-config"
        "unzip"
        "tree"
        "net-tools"
        "ufw"
    )
    
    # Packages Python
    local python_packages=(
        "python3"
        "python3-pip"
        "python3-venv"
        "python3-dev"
        "python3-setuptools"
        "python3-wheel"
        "python3-distutils"
        "python3-full"
    )
    
    # Packages MySQL
    local mysql_packages=(
        "mysql-server"
        "mysql-client"
        "libmysqlclient-dev"
        "mysql-common"
    )
    
    # Packages Apache
    local apache_packages=(
        "apache2"
        "libapache2-mod-wsgi-py3"
        "apache2-utils"
    )
    
    # Packages Redis et NTP
    local service_packages=(
        "redis-server"
        "ntp"
        "ntpdate"
        "ntpstat"
    )
    
    # Packages SSL/TLS
    local ssl_packages=(
        "certbot"
        "python3-certbot-apache"
        "openssl"
    )
    
    # Vérifier tous les packages
    local all_packages=(
        "${essential_packages[@]}"
        "${python_packages[@]}"
        "${mysql_packages[@]}"
        "${apache_packages[@]}"
        "${service_packages[@]}"
        "${ssl_packages[@]}"
    )
    
    local missing_packages=()
    
    for package in "${all_packages[@]}"; do
        check_start "Package $package"
        if check_package_installed "$package"; then
            success "Package $package installé"
        else
            error "Package $package manquant"
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        warn "Packages manquants: ${missing_packages[*]}"
        INSTALL_NEEDED+=("system_packages")
    fi
}

# ============================================================================
# VÉRIFICATION PYTHON
# ============================================================================

check_python_version() {
    section "VÉRIFICATION PYTHON"
    
    check_start "Version Python"
    
    # Vérifier Python 3
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
    
    # Vérifier pip
    check_start "Python pip"
    if ! command -v pip3 &> /dev/null; then
        error "pip3 non installé"
        INSTALL_NEEDED+=("python_pip")
    else
        pip_version=$(pip3 --version 2>&1 | cut -d' ' -f2)
        success "pip3 installé: $pip_version"
    fi
    
    # Vérifier venv
    check_start "Python venv"
    if ! python3 -m venv --help &> /dev/null; then
        error "python3-venv non installé"
        INSTALL_NEEDED+=("python_venv")
    else
        success "python3-venv disponible"
    fi
}

check_python_dependencies() {
    check_start "Dépendances Python principales"
    
    # Vérifier les dépendances critiques en Python
    local critical_deps=(
        "flask"
        "sqlalchemy"
        "pymysql"
        "redis"
        "ntplib"
        "psutil"
        "requests"
        "werkzeug"
        "jinja2"
    )
    
    # Créer un environnement virtuel temporaire pour test
    temp_venv="/tmp/test_python_deps"
    if [ -d "$temp_venv" ]; then
        rm -rf "$temp_venv"
    fi
    
    if python3 -m venv "$temp_venv" &> /dev/null; then
        source "$temp_venv/bin/activate"
        
        # Test d'installation des dépendances critiques
        local deps_ok=true
        for dep in "${critical_deps[@]}"; do
            if ! pip install "$dep" &> /dev/null; then
                error "Impossible d'installer $dep"
                deps_ok=false
            fi
        done
        
        deactivate
        rm -rf "$temp_venv"
        
        if [ "$deps_ok" = true ]; then
            success "Dépendances Python critiques installables"
        else
            INSTALL_NEEDED+=("python_dependencies")
        fi
    else
        error "Impossible de créer environnement virtuel de test"
        INSTALL_NEEDED+=("python_venv")
    fi
}

# ============================================================================
# VÉRIFICATION SERVICES
# ============================================================================

check_service_status() {
    local service=$1
    if systemctl is-active --quiet "$service"; then
        success "Service $service actif"
        return 0
    elif systemctl is-enabled --quiet "$service"; then
        warn "Service $service installé mais arrêté"
        return 1
    else
        error "Service $service non installé"
        return 2
    fi
}

check_services() {
    section "VÉRIFICATION SERVICES"
    
    # Services requis
    local required_services=(
        "mysql"
        "apache2"
        "redis-server"
        "ntp"
        "ufw"
    )
    
    local services_need_install=()
    local services_need_start=()
    
    for service in "${required_services[@]}"; do
        check_start "Service $service"
        case $(check_service_status "$service"; echo $?) in
            0) ;; # Service actif - OK
            1) services_need_start+=("$service") ;;
            2) services_need_install+=("$service") ;;
        esac
    done
    
    if [ ${#services_need_install[@]} -gt 0 ]; then
        warn "Services à installer: ${services_need_install[*]}"
        INSTALL_NEEDED+=("services")
    fi
    
    if [ ${#services_need_start[@]} -gt 0 ]; then
        warn "Services à démarrer: ${services_need_start[*]}"
        INSTALL_NEEDED+=("start_services")
    fi
}

# ============================================================================
# VÉRIFICATION BASE DE DONNÉES
# ============================================================================

check_mysql_server() {
    section "VÉRIFICATION MYSQL"
    
    check_start "Serveur MySQL"
    
    if ! command -v mysql &> /dev/null; then
        error "Client MySQL non installé"
        INSTALL_NEEDED+=("mysql_client")
        return 1
    fi
    
    # Vérifier si MySQL est actif
    if ! systemctl is-active --quiet mysql; then
        error "MySQL non actif"
        INSTALL_NEEDED+=("mysql_service")
        return 1
    fi
    
    # Test de connexion
    if mysql -u root -e "SELECT VERSION();" &> /dev/null; then
        mysql_version=$(mysql -u root -e "SELECT VERSION();" 2>/dev/null | tail -1)
        success "MySQL actif: $mysql_version"
    else
        warn "MySQL actif mais connexion root échouée (mot de passe requis)"
    fi
    
    # Vérifier la base de données
    check_start "Base de données $MYSQL_DB"
    if mysql -u root -e "USE $MYSQL_DB;" &> /dev/null; then
        success "Base de données $MYSQL_DB existe"
    else
        warn "Base de données $MYSQL_DB à créer"
        INSTALL_NEEDED+=("mysql_database")
    fi
}

check_mysql_python_driver() {
    check_start "Driver MySQL Python"
    
    # Vérifier si les headers MySQL sont installés
    if ! dpkg -l | grep -q libmysqlclient-dev; then
        error "Headers MySQL manquants (libmysqlclient-dev)"
        INSTALL_NEEDED+=("mysql_headers")
        return 1
    fi
    
    # Test import pymysql
    if python3 -c "import pymysql" &> /dev/null; then
        success "Driver PyMySQL disponible"
    else
        warn "Driver PyMySQL à installer"
        INSTALL_NEEDED+=("mysql_python_driver")
    fi
}

# ============================================================================
# VÉRIFICATION APACHE
# ============================================================================

check_apache_server() {
    section "VÉRIFICATION APACHE"
    
    check_start "Serveur Apache"
    
    if ! command -v apache2 &> /dev/null; then
        error "Apache2 non installé"
        INSTALL_NEEDED+=("apache2")
        return 1
    fi
    
    # Vérifier si Apache est actif
    if systemctl is-active --quiet apache2; then
        success "Apache2 actif"
    else
        warn "Apache2 installé mais arrêté"
        INSTALL_NEEDED+=("apache2_service")
    fi
    
    # Vérifier mod_wsgi
    check_start "Module mod_wsgi"
    if apache2ctl -M 2>/dev/null | grep -q wsgi; then
        success "mod_wsgi activé"
    else
        warn "mod_wsgi à activer"
        INSTALL_NEEDED+=("apache2_wsgi")
    fi
    
    # Vérifier les autres modules requis
    local required_modules=("rewrite" "ssl" "headers")
    for module in "${required_modules[@]}"; do
        check_start "Module Apache $module"
        if apache2ctl -M 2>/dev/null | grep -q "$module"; then
            success "Module $module activé"
        else
            warn "Module $module à activer"
            INSTALL_NEEDED+=("apache2_modules")
        fi
    done
}

check_apache_ports() {
    check_start "Ports Apache"
    
    # Vérifier port 80
    if netstat -tlnp 2>/dev/null | grep -q ":80 "; then
        success "Port 80 en écoute"
    else
        warn "Port 80 non en écoute"
    fi
    
    # Vérifier port 443
    if netstat -tlnp 2>/dev/null | grep -q ":443 "; then
        success "Port 443 en écoute"
    else
        warn "Port 443 non en écoute (SSL optionnel)"
    fi
}

# ============================================================================
# VÉRIFICATION RÉSEAU ET SÉCURITÉ
# ============================================================================

check_network_connectivity() {
    section "VÉRIFICATION RÉSEAU"
    
    # Test connexion Internet
    check_start "Connexion Internet"
    if ping -c 1 8.8.8.8 &> /dev/null; then
        success "Connexion Internet OK"
    else
        error "Pas de connexion Internet"
        return 1
    fi
    
    # Test résolution DNS
    check_start "Résolution DNS"
    if nslookup google.com &> /dev/null; then
        success "Résolution DNS OK"
    else
        error "Résolution DNS échouée"
        return 1
    fi
    
    # Test NTP
    check_start "Serveurs NTP"
    if ntpdate -q pool.ntp.org &> /dev/null; then
        success "Serveurs NTP accessibles"
    else
        warn "Serveurs NTP non accessibles"
    fi
}

check_firewall() {
    check_start "Pare-feu UFW"
    
    if ! command -v ufw &> /dev/null; then
        error "UFW non installé"
        INSTALL_NEEDED+=("ufw")
        return 1
    fi
    
    ufw_status=$(ufw status 2>/dev/null | head -1)
    if echo "$ufw_status" | grep -q "Status: active"; then
        success "UFW actif"
    else
        warn "UFW inactif"
        INSTALL_NEEDED+=("ufw_config")
    fi
}

# ============================================================================
# INSTALLATION AUTOMATIQUE
# ============================================================================

update_system() {
    log "Mise à jour du système..."
    apt update -y
    apt upgrade -y
    success "Système mis à jour"
}

install_system_packages() {
    log "Installation des packages système..."
    
    # Packages essentiels
    local all_packages=(
        # Outils système
        "curl" "wget" "git" "htop" "vim" "tree" "net-tools" "unzip"
        "software-properties-common" "apt-transport-https" "ca-certificates" "gnupg" "lsb-release"
        "build-essential" "pkg-config" "ufw"
        
        # Python
        "python3" "python3-pip" "python3-venv" "python3-dev" "python3-setuptools" 
        "python3-wheel" "python3-distutils" "python3-full"
        
        # MySQL
        "mysql-server" "mysql-client" "libmysqlclient-dev" "mysql-common"
        
        # Apache
        "apache2" "libapache2-mod-wsgi-py3" "apache2-utils"
        
        # Services
        "redis-server" "ntp" "ntpdate" "ntpstat"
        
        # SSL/TLS
        "certbot" "python3-certbot-apache" "openssl"
    )
    
    apt install -y "${all_packages[@]}"
    success "Packages système installés"
}

configure_mysql() {
    log "Configuration MySQL..."
    
    # Démarrer MySQL
    systemctl enable mysql
    systemctl start mysql
    
    # Sécuriser MySQL (automatique)
    mysql -u root << EOF
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
EOF
    
    # Créer base de données et utilisateur
    MYSQL_PASSWORD=$(openssl rand -base64 16)
    mysql -u root << EOF
CREATE DATABASE IF NOT EXISTS $MYSQL_DB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$MYSQL_USER'@'localhost' IDENTIFIED BY '$MYSQL_PASSWORD';
GRANT ALL PRIVILEGES ON $MYSQL_DB.* TO '$MYSQL_USER'@'localhost';
FLUSH PRIVILEGES;
EOF
    
    # Sauvegarder mot de passe
    echo "MYSQL_PASSWORD=$MYSQL_PASSWORD" > /root/mysql_credentials.txt
    chmod 600 /root/mysql_credentials.txt
    
    success "MySQL configuré - Mot de passe sauvé dans /root/mysql_credentials.txt"
}

configure_apache() {
    log "Configuration Apache..."
    
    # Démarrer Apache
    systemctl enable apache2
    systemctl start apache2
    
    # Activer modules
    a2enmod wsgi rewrite ssl headers
    
    # Redémarrer Apache
    systemctl restart apache2
    
    success "Apache configuré"
}

configure_services() {
    log "Configuration des services..."
    
    # Redis
    systemctl enable redis-server
    systemctl start redis-server
    
    # NTP
    systemctl enable ntp
    systemctl start ntp
    
    # UFW
    ufw --force enable
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    success "Services configurés"
}

install_python_dependencies() {
    log "Installation des dépendances Python..."
    
    # Mettre à jour pip
    python3 -m pip install --upgrade pip setuptools wheel
    
    # Installer les dépendances critiques
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
        python-socketio==5.8.0 \
        gunicorn==21.2.0 \
        python-dotenv==1.0.0
    
    success "Dépendances Python installées"
}

# ============================================================================
# TESTS FINAUX
# ============================================================================

run_final_tests() {
    section "TESTS FINAUX"
    
    # Test connexion MySQL
    check_start "Test connexion MySQL"
    if mysql -u root -e "SELECT VERSION();" &> /dev/null; then
        success "MySQL opérationnel"
    else
        error "MySQL non opérationnel"
    fi
    
    # Test Apache
    check_start "Test Apache"
    if systemctl is-active --quiet apache2; then
        success "Apache opérationnel"
    else
        error "Apache non opérationnel"
    fi
    
    # Test Redis
    check_start "Test Redis"
    if redis-cli ping &> /dev/null; then
        success "Redis opérationnel"
    else
        error "Redis non opérationnel"
    fi
    
    # Test NTP
    check_start "Test NTP"
    if ntpq -p &> /dev/null; then
        success "NTP opérationnel"
    else
        warn "NTP non opérationnel"
    fi
    
    # Test Python
    check_start "Test environnement Python"
    if python3 -c "import flask, sqlalchemy, pymysql, redis; print('OK')" &> /dev/null; then
        success "Environnement Python opérationnel"
    else
        error "Environnement Python non opérationnel"
    fi
}

# ============================================================================
# RAPPORT FINAL
# ============================================================================

generate_report() {
    section "RAPPORT FINAL"
    
    echo -e "${WHITE}============================================${NC}"
    echo -e "${WHITE}    RAPPORT D'INSTALLATION COMPLET${NC}"
    echo -e "${WHITE}============================================${NC}"
    echo
    echo -e "${CYAN}Checks totaux:${NC} $TOTAL_CHECKS"
    echo -e "${GREEN}Succès:${NC} $PASSED_CHECKS"
    echo -e "${RED}Échecs:${NC} $FAILED_CHECKS"
    echo -e "${YELLOW}Avertissements:${NC} $WARNINGS"
    echo
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}✅ INSTALLATION COMPLÈTE RÉUSSIE !${NC}"
        echo -e "${GREEN}Votre système est prêt pour NTP Monitor Enterprise${NC}"
        echo
        echo -e "${CYAN}Prochaines étapes:${NC}"
        echo "1. Déployer l'application NTP Monitor"
        echo "2. Configurer le domaine/IP"
        echo "3. Configurer SSL/TLS (optionnel)"
        echo "4. Accéder à l'interface web"
        echo
        echo -e "${CYAN}Informations de connexion MySQL:${NC}"
        echo "- Base de données: $MYSQL_DB"
        echo "- Utilisateur: $MYSQL_USER"
        echo "- Mot de passe: voir /root/mysql_credentials.txt"
    else
        echo -e "${RED}❌ INSTALLATION INCOMPLÈTE${NC}"
        echo -e "${RED}Veuillez corriger les erreurs signalées${NC}"
        echo
        echo -e "${YELLOW}Éléments nécessitant attention:${NC}"
        for item in "${INSTALL_NEEDED[@]}"; do
            echo "- $item"
        done
    fi
    
    echo
    echo -e "${WHITE}============================================${NC}"
}

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

main() {
    section "NTP MONITOR ENTERPRISE - VÉRIFICATION COMPLÈTE"
    echo -e "${CYAN}Version du script: $SCRIPT_VERSION${NC}"
    echo -e "${CYAN}Système cible: Ubuntu Server 24.04 LTS${NC}"
    echo -e "${CYAN}Date: $(date)${NC}"
    
    # Vérifications préliminaires
    check_root
    check_ubuntu_version
    check_system_architecture
    check_system_resources
    
    # Vérifications détaillées
    check_system_packages
    check_python_version
    check_python_dependencies
    check_services
    check_mysql_server
    check_mysql_python_driver
    check_apache_server
    check_apache_ports
    check_network_connectivity
    check_firewall
    
    # Installation si nécessaire
    if [ ${#INSTALL_NEEDED[@]} -gt 0 ]; then
        section "INSTALLATION AUTOMATIQUE"
        
        log "Éléments à installer: ${INSTALL_NEEDED[*]}"
        
        update_system
        install_system_packages
        configure_mysql
        configure_apache
        configure_services
        install_python_dependencies
        
        # Tests après installation
        run_final_tests
    fi
    
    # Rapport final
    generate_report
    
    # Code de sortie
    if [ $FAILED_CHECKS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# ============================================================================
# EXÉCUTION
# ============================================================================

# Vérifier si le script est appelé directement
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 