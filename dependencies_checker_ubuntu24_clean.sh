```bash
#!/bin/bash
# ============================================================================
# NTP Monitor Enterprise - Vérification et Installation Complète des Dépendances
# Ubuntu Server 24.04 LTS - Script Holistique
# Version: 2.0.0
# ============================================================================

# Nettoyage des espaces insécables (NBSP) en espaces ASCII
# (Évite l’erreur “$'\240…': command not found”)
sed -i 's/\xC2\xA0/ /g' "$0"

set -e

# Configuration
SCRIPT_VERSION="2.0.0"
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
# VÉRIFICATION PACKAGES
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
    
    # Liste complète des packages requis
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
# VÉRIFICATION PYTHON
# ============================================================================

check_python_environment() {
    section "VÉRIFICATION PYTHON"
    
    # Version Python
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
    
    # pip
    check_start "pip"
    if ! command -v pip3 &> /dev/null; then
        error "pip3 non installé"
        return 1
    else
        success "pip3 disponible"
    fi
    
    # venv
    check_start "venv"
    if ! python3 -m venv --help &> /dev/null; then
        error "python3-venv non installé"
        return 1
    else
        success "python3-venv disponible"
    fi
    
    # Test dépendances critiques
    check_start "Dépendances Python critiques"
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
# VÉRIFICATION SERVICES
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
        error "Service $service non installé ou non configuré"
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
    
    if [ $services_issues -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# VÉRIFICATION MYSQL
# ============================================================================

check_mysql_detailed() {
    section "VÉRIFICATION MYSQL"
    
    # Serveur MySQL
    check_start "Serveur MySQL"
    if ! command -v mysql &> /dev/null; then
        error "Client MySQL non installé"
        return 1
    fi
    
    if ! systemctl is-active --quiet mysql; then
        error "Serveur MySQL non actif"
        return 1
    fi
    
    # Test connexion
    if mysql -u root -e "SELECT VERSION();" &> /dev/null; then
        mysql_version=$(mysql -u root -e "SELECT VERSION();" 2>/dev/null | tail -1)
        success "MySQL opérationnel: $mysql_version"
    else
        warn "MySQL actif mais connexion root protégée"
    fi
    
    # Vérifier libmysqlclient-dev
    check_start "Headers MySQL"
    if ! dpkg -l | grep -q libmysqlclient-dev; then
        error "Headers MySQL manquants (libmysqlclient-dev)"
        return 1
    else
        success "Headers MySQL installés"
    fi
    
    # Test PyMySQL
    check_start "Driver PyMySQL"
    if python3 -c "import pymysql" &> /dev/null; then
        success "Driver PyMySQL disponible"
    else
        warn "Driver PyMySQL à installer"
    fi
    
    return 0
}

# ============================================================================
# VÉRIFICATION APACHE
# ============================================================================

check_apache_detailed() {
    section "VÉRIFICATION APACHE"
    
    # Apache installé
    check_start "Apache2"
    if ! command -v apache2 &> /dev/null; then
        error "Apache2 non installé"
        return 1
    fi
    
    # Apache actif
    if systemctl is-active --quiet apache2; then
        success "Apache2 actif"
    else
        warn "Apache2 installé mais arrêté"
    fi
    
    # Modules requis
    local required_modules=("wsgi" "rewrite" "ssl" "headers")
    local modules_ok=true
    
    for module in "${required_modules[@]}"; do
        check_start "Module Apache $module"
        if apache2ctl -M 2>/dev/null | grep -q "${module}_module"; then
            success "Module $module activé"
        else
            error "Module $module manquant ou inactif"
            modules_ok=false
        fi
    done
    
    # Test ports
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
# VÉRIFICATION RÉSEAU
# ============================================================================

check_network_detailed() {
    section "VÉRIFICATION RÉSEAU"
    
    # Internet
    check_start "Connexion Internet"
    if ping -c 1 -W 5 8.8.8.8 &> /dev/null; then
        success "Connexion Internet OK"
    else
        error "Pas de connexion Internet"
        return 1
    fi
    
    # DNS
    check_start "Résolution DNS"
    if nslookup google.com &> /dev/null; then
        success "Résolution DNS OK"
    else
        error "Résolution DNS échouée"
        return 1
    fi
    
    # NTP
    check_start "Serveurs NTP"
    if timeout 10 ntpdate -q pool.ntp.org &> /dev/null; then
        success "Serveurs NTP accessibles"
    else
        warn "Serveurs NTP non accessibles"
    fi
    
    # Firewall
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
    
    log "Mise à jour des références packages..."
    apt update -y
    
    log "Mise à jour système..."
    apt upgrade -y
    
    log "Installation packages complets..."
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
    
    log "Démarrage et activation MySQL..."
    systemctl enable mysql
    systemctl start mysql
    
    log "Sécurisation MySQL..."
    mysql -u root << 'EOF'
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
EOF
    
    log "Création base de données et utilisateur..."
    MYSQL_PASSWORD=$(openssl rand -base64 16)
    mysql -u root << EOF
CREATE DATABASE IF NOT EXISTS $MYSQL_DB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$MYSQL_USER'@'localhost' IDENTIFIED BY '$MYSQL_PASSWORD';
GRANT ALL PRIVILEGES ON $MYSQL_DB.* TO '$MYSQL_USER'@'localhost';
FLUSH PRIVILEGES;
EOF
    
    # Sauvegarder credentials
    cat > /root/mysql_credentials.txt << EOF
# Credentials MySQL pour NTP Monitor Enterprise
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=$MYSQL_DB
MYSQL_USER=$MYSQL_USER
MYSQL_PASSWORD=$MYSQL_PASSWORD
EOF
    chmod 600 /root/mysql_credentials.txt
    
    success "MySQL configuré - Credentials sauvés dans /root/mysql_credentials.txt"
}

configure_apache_complete() {
    section "CONFIGURATION APACHE"
    
    log "Démarrage et activation Apache..."
    systemctl enable apache2
    systemctl start apache2
    
    log "Activation modules Apache..."
    a2enmod wsgi
    a2enmod rewrite
    a2enmod ssl
    a2enmod headers
    
    log "Redémarrage Apache..."
    systemctl restart apache2
    
    success "Apache configuré avec modules requis"
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
    ufw allow 123/udp  # NTP
    
    success "Services configurés et démarrés"
}

install_python_packages() {
    section "INSTALLATION DÉPENDANCES PYTHON"
    
    log "Mise à jour pip..."
    python3 -m pip install --upgrade pip setuptools wheel
    
    log "Installation packages Python critiques..."
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
    section "TESTS FINAUX COMPLETS"
    
    local tests_passed=0
    local tests_total=0
    
    # Test MySQL
    ((tests_total++))
    if mysql -u root -e "SELECT VERSION();" &> /dev/null; then
        success "✓ MySQL opérationnel"
        ((tests_passed++))
    else
        error "✗ MySQL non opérationnel"
    fi
    
    # Test Apache
    ((tests_total++))
    if systemctl is-active --quiet apache2 && curl -s http://localhost &> /dev/null; then
        success "✓ Apache opérationnel"
        ((tests_passed++))
    else
        error "✗ Apache non opérationnel"
    fi
    
    # Test Redis
    ((tests_total++))
    if redis-cli ping &> /dev/null; then
        success "✓ Redis opérationnel"
        ((tests_passed++))
    else
        error "✗ Redis non opérationnel"
    fi
    
    # Test NTP
    ((tests_total++))
    if ntpq -p &> /dev/null; then
        success "✓ NTP opérationnel"
        ((tests_passed++))
    else
        warn "⚠ NTP non opérationnel"
    fi
    
    # Test Python avec imports
    ((tests_total++))
    if python3 -c "import flask, sqlalchemy, pymysql, redis, ntplib, psutil; print('Python OK')" &> /dev/null; then
        success "✓ Environnement Python complet"
        ((tests_passed++))
    else
        error "✗ Environnement Python incomplet"
    fi
    
    # Test réseau
    ((tests_total++))
    if ping -c 1 -W 5 8.8.8.8 &> /dev/null; then
        success "✓ Connectivité réseau"
        ((tests_passed++))
    else
        error "✗ Problème connectivité réseau"
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
    section "RAPPORT FINAL D'INSTALLATION"
    
    echo -e "${WHITE}============================================${NC}"
    echo -e "${WHITE}    NTP MONITOR ENTERPRISE${NC}"
    echo -e "${WHITE}    Installation Ubuntu 24.04 LTS${NC}"
    echo -e "${WHITE}============================================${NC}"
    echo
    echo -e "${CYAN}Checks totaux effectués:${NC} $TOTAL_CHECKS"
    echo -e "${GREEN}Succès:${NC} $PASSED_CHECKS"
    echo -e "${RED}Échecs:${NC} $FAILED_CHECKS"
    echo -e "${YELLOW}Avertissements:${NC} $WARNINGS"
    echo
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}🎉 INSTALLATION COMPLÈTE RÉUSSIE !${NC}"
        echo -e "${GREEN}Votre système Ubuntu 24.04 est maintenant prêt pour NTP Monitor Enterprise${NC}"
        echo
        echo -e "${CYAN}🔧 Configuration système:${NC}"
        echo "  ✓ Ubuntu $(lsb_release -rs) installé et à jour"
        echo "  ✓ Python $(python3 --version | cut -d' ' -f2) configuré"
        echo "  ✓ MySQL $(mysql --version | cut -d' ' -f6 | cut -d',' -f1) opérationnel"
        echo "  ✓ Apache $(apache2 -v | head -1 | cut -d ' ' -f3) avec mod_wsgi"
        echo "  ✓ Redis $(redis-server --version | cut -d ' ' -f3) actif"
        echo "  ✓ NTP synchronisé"
        echo "  ✓ Pare-feu UFW configuré"
        echo
        echo -e "${CYAN}📊 Base de données MySQL:${NC}"
        echo "  • Base de données: $MYSQL_DB"
        echo "  • Utilisateur: $MYSQL_USER"
        echo "  • Mot de passe: voir /root/mysql_credentials.txt"
        echo
        echo -e "${CYAN}🌐 Ports configurés:${NC}"
        echo "  • HTTP: 80 (ouvert)"
        echo "  • HTTPS: 443 (ouvert)"
        echo "  • NTP: 123/udp (ouvert)"
        echo "  • SSH: 22 (ouvert)"
        echo
        echo -e "${CYAN}🚀 Prochaines étapes:${NC}"
        echo "  1. Cloner le code NTP Monitor Enterprise"
        echo "  2. Configurer l'application (.env)"
        echo "  3. Déployer avec le script deploy_ubuntu_production.sh"
        echo "  4. Configurer SSL/TLS (certbot)"
        echo "  5. Accéder à l'interface web"
        echo
        echo -e "${CYAN}💡 Commandes utiles:${NC}"
        echo "  • Status services: systemctl status mysql apache2 redis-server"
        echo "  • Logs Apache: tail -f /var/log/apache2/error.log"
        echo "  • Logs MySQL: tail -f /var/log/mysql/error.log"
        echo "  • Test connectivité: curl -I http://localhost"
        echo
    else
        echo -e "${RED}❌ INSTALLATION INCOMPLÈTE${NC}"
        echo -e "${RED}Des erreurs ont été détectées et doivent être corrigées${NC}"
        echo
        echo -e "${YELLOW}⚠  Vérifications à effectuer:${NC}"
        echo "  • Vérifier les logs système: journalctl -xe"
        echo "  • Vérifier l'espace disque: df -h"
        echo "  • Vérifier la RAM: free -h"
        echo "  • Vérifier les services: systemctl --failed"
        echo
        echo -e "${YELLOW}🔧 Actions recommandées:${NC}"
        echo "  1. Corriger les erreurs signalées ci-dessus"
        echo "  2. Relancer ce script: sudo $0"
        echo "  3. Vérifier la configuration réseau"
        echo "  4. Consulter les logs détaillés"
    fi
    
    echo -e "${WHITE}============================================${NC}"
    echo -e "${CYAN}Script version: $SCRIPT_VERSION${NC}"
    echo -e "${CYAN}Rapport généré: $(date)${NC}"
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
    
    # Vérifications système de base
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
    
    # Installation si nécessaire
    if [ "$need_install" = true ]; then
        section "INSTALLATION AUTOMATIQUE REQUISE"
        
        log "Des éléments manquants ont été détectés"
        log "Lancement de l'installation automatique..."
        
        install_missing_packages
        configure_mysql_complete
        configure_apache_complete
        configure_all_services
        install_python_packages
        
        log "Installation terminée, vérification finale..."
        
        # Tests finaux
        if run_comprehensive_tests; then
            success "Tous les tests finaux réussis"
        else
            error "Certains tests finaux ont échoué"
        fi
    else
        log "Système déjà correctement configuré"
        run_comprehensive_tests
    fi
    
    # Rapport final
    generate_final_report
    
    # Code de sortie
    if [ $FAILED_CHECKS -eq 0 ]; then
        log "Script terminé avec succès"
        exit 0
    else
        error "Script terminé avec des erreurs"
        exit 1
    fi
}

# ============================================================================
# EXECUTION
# ============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

