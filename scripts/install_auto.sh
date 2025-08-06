#!/bin/bash
# ============================================================================
# install_auto.sh - Installation automatique NTP Monitor Enterprise
# Script d'installation one-click pour Ubuntu 24.04
# Version : 1.0.0
# ============================================================================

set -e

# === CONFIGURATION ===
APP_NAME="NTP Monitor Enterprise"
APP_VERSION="2.1.0"
INSTALL_DIR="/opt/ntp-monitor-enterprise"
VENV_DIR="/opt/ntp-monitor-venv"
APP_USER="ntp-monitor"
DB_NAME="ntp_monitor"
DB_USER="ntp_user"
DB_PASSWORD=""
GITHUB_REPO="https://github.com/gilandre/NTPVIZ.git"

# === COULEURS ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# === FONCTIONS ===
log_info()    { echo -e "${BLUE}ℹ️  $*${NC}"; }
log_success() { echo -e "${GREEN}✅ $*${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $*${NC}"; }
log_error()   { echo -e "${RED}❌ $*${NC}"; }
log_title()   { echo -e "${WHITE}🚀 $*${NC}"; }

# === VÉRIFICATION ROOT ===
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Ce script doit être exécuté avec sudo ou en tant que root"
        exit 1
    fi
}

# === VÉRIFICATION SYSTÈME ===
check_system() {
    log_info "Vérification du système..."
    
    # Vérifier Ubuntu
    if ! grep -q "Ubuntu" /etc/os-release; then
        log_error "Ce script est conçu pour Ubuntu 24.04"
        exit 1
    fi
    
    # Vérifier la version
    local version=$(lsb_release -rs)
    if [[ "$version" != "24.04" ]] && [[ "$version" != "22.04" ]] && [[ "$version" != "20.04" ]]; then
        log_warning "Version Ubuntu non testée : $version"
        read -p "Continuer quand même ? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Vérifier l'espace disque
    local disk_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $disk_space -lt 10485760 ]]; then # 10GB en KB
        log_error "Espace disque insuffisant. Minimum 10GB requis."
        exit 1
    fi
    
    # Vérifier la RAM
    local ram=$(free -m | awk 'NR==2{print $2}')
    if [[ $ram -lt 1800 ]]; then
        log_warning "RAM insuffisante ($ram MB). Minimum 2GB recommandé."
    fi
    
    log_success "Système compatible détecté"
}

# === GÉNÉRATION MOT DE PASSE ===
generate_password() {
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    log_success "Mot de passe base de données généré"
}

# === INSTALLATION PACKAGES ===
install_packages() {
    log_info "Installation des packages système..."
    
    # Mise à jour
    apt update -y
    apt upgrade -y
    
    # Installation packages essentiels
    apt install -y \
        curl wget git vim nano htop tree net-tools unzip \
        build-essential pkg-config software-properties-common \
        python3 python3-pip python3-venv python3-dev \
        mysql-server mysql-client libmysqlclient-dev \
        apache2 libapache2-mod-wsgi-py3 apache2-utils \
        redis-server \
        ntpsec ntpdate ntpstat \
        ufw fail2ban \
        certbot python3-certbot-apache \
        openssl
    
    log_success "Packages installés"
}

# === CONFIGURATION SÉCURITÉ ===
configure_security() {
    log_info "Configuration de la sécurité..."
    
    # Pare-feu
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 123/udp
    ufw --force enable
    
    # Fail2ban
    systemctl enable fail2ban
    systemctl start fail2ban
    
    log_success "Sécurité configurée"
}

# === CONFIGURATION MYSQL ===
configure_mysql() {
    log_info "Configuration de MySQL..."
    
    # Démarrer MySQL
    systemctl enable mysql
    systemctl start mysql
    
    # Sécurisation automatique
    mysql -e "DELETE FROM mysql.user WHERE User='';"
    mysql -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
    mysql -e "DROP DATABASE IF EXISTS test;"
    mysql -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';"
    mysql -e "FLUSH PRIVILEGES;"
    
    # Création base de données et utilisateur
    mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
    mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
    mysql -e "FLUSH PRIVILEGES;"
    
    log_success "MySQL configuré"
}

# === CRÉATION UTILISATEUR ===
create_user() {
    log_info "Création de l'utilisateur application..."
    
    # Créer utilisateur système
    if ! id "$APP_USER" &>/dev/null; then
        useradd -m -s /bin/bash "$APP_USER"
        log_success "Utilisateur $APP_USER créé"
    else
        log_warning "Utilisateur $APP_USER existe déjà"
    fi
    
    # Créer répertoires
    mkdir -p "$INSTALL_DIR"
    chown "$APP_USER:$APP_USER" "$INSTALL_DIR"
}

# === INSTALLATION APPLICATION ===
install_application() {
    log_info "Installation de l'application..."
    
    # Cloner repository
    sudo -u "$APP_USER" git clone "$GITHUB_REPO" "$INSTALL_DIR"
    
    # Environnement virtuel
    sudo -u "$APP_USER" python3 -m venv "$VENV_DIR"
    sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel
    
    # Installation dépendances
    sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
    
    log_success "Application installée"
}

# === CONFIGURATION APPLICATION ===
configure_application() {
    log_info "Configuration de l'application..."
    
    # Génération clé secrète
    local secret_key=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)
    
    # Création fichier .env
    sudo -u "$APP_USER" tee "$INSTALL_DIR/.env" > /dev/null << EOF
# === CONFIGURATION PRODUCTION ===
FLASK_ENV=production
DEBUG=false
SECRET_KEY=$secret_key
HOST=0.0.0.0
PORT=5001

# === BASE DE DONNÉES ===
DATABASE_URL=mysql+pymysql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME

# === SERVEURS NTP ===
DEFAULT_NTP_SERVERS=pool.ntp.org,time.google.com,time.cloudflare.com
LOCAL_NTP_SERVERS=192.168.1.1,10.0.0.1

# === ALERTES ===
ALERT_OFFSET_THRESHOLD=100
ALERT_DELAY_THRESHOLD=500
ALERT_EMAIL_ENABLED=false

# === REDIS ===
REDIS_URL=redis://localhost:6379/0

# === LOGS ===
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE=/var/log/ntp-monitor/app.log
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5

# === SÉCURITÉ ===
SESSION_PERMANENT=false
PERMANENT_SESSION_LIFETIME=3600
WTF_CSRF_ENABLED=true
BCRYPT_LOG_ROUNDS=12

# === MONITORING ===
MONITORING_INTERVAL=30
MAX_LOG_RETENTION_DAYS=30
AUTO_CLEANUP_ENABLED=true
ENABLE_METRICS=true
EOF
    
    # Créer répertoires logs
    mkdir -p /var/log/ntp-monitor
    chown "$APP_USER:$APP_USER" /var/log/ntp-monitor
    
    # Initialiser base de données
    cd "$INSTALL_DIR"
    sudo -u "$APP_USER" "$VENV_DIR/bin/python" init_database.py
    
    log_success "Application configurée"
}

# === CONFIGURATION APACHE ===
configure_apache() {
    log_info "Configuration d'Apache..."
    
    # Créer fichier WSGI
    sudo -u "$APP_USER" tee "$INSTALL_DIR/app.wsgi" > /dev/null << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Ajouter le chemin de l'application
sys.path.insert(0, '/opt/ntp-monitor-enterprise')

# Activer l'environnement virtuel
activate_this = '/opt/ntp-monitor-venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

# Importer l'application
from app import app as application

if __name__ == "__main__":
    application.run()
EOF
    
    # Configuration Apache
    tee /etc/apache2/sites-available/ntp-monitor.conf > /dev/null << EOF
<VirtualHost *:80>
    ServerName localhost
    DocumentRoot $INSTALL_DIR/frontend/static
    
    WSGIDaemonProcess ntp-monitor \\
        python-home=$VENV_DIR \\
        python-path=$INSTALL_DIR \\
        user=$APP_USER \\
        group=$APP_USER \\
        processes=2 \\
        threads=5
    
    WSGIProcessGroup ntp-monitor
    WSGIScriptAlias / $INSTALL_DIR/app.wsgi
    
    <Directory $INSTALL_DIR>
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    
    Alias /static $INSTALL_DIR/frontend/static
    <Directory $INSTALL_DIR/frontend/static>
        Require all granted
    </Directory>
    
    ErrorLog \${APACHE_LOG_DIR}/ntp-monitor_error.log
    CustomLog \${APACHE_LOG_DIR}/ntp-monitor_access.log combined
</VirtualHost>
EOF
    
    # Activer site
    a2ensite ntp-monitor
    a2enmod wsgi
    a2dissite 000-default
    systemctl reload apache2
    
    log_success "Apache configuré"
}

# === CONFIGURATION SERVICE ===
configure_service() {
    log_info "Configuration du service systemd..."
    
    tee /etc/systemd/system/ntp-monitor.service > /dev/null << EOF
[Unit]
Description=NTP Monitor Enterprise
After=network.target mysql.service redis.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python app.py
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

[Install]
WantedBy=multi-user.target
EOF
    
    # Activer et démarrer
    systemctl daemon-reload
    systemctl enable ntp-monitor
    systemctl start ntp-monitor
    
    log_success "Service configuré"
}

# === VÉRIFICATION FINALE ===
verify_installation() {
    log_info "Vérification de l'installation..."
    
    # Vérifier services
    local services=("ntp-monitor" "apache2" "mysql" "redis-server" "ntpsec")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log_success "Service $service actif"
        else
            log_error "Service $service inactif"
        fi
    done
    
    # Vérifier interface web
    sleep 5
    if curl -s http://localhost | grep -q "NTP Monitor"; then
        log_success "Interface web accessible"
    else
        log_warning "Interface web non accessible"
    fi
    
    # Vérifier API
    if curl -s http://localhost/api/system/status | grep -q "status"; then
        log_success "API fonctionnelle"
    else
        log_warning "API non fonctionnelle"
    fi
}

# === AFFICHAGE RÉSUMÉ ===
show_summary() {
    local server_ip=$(hostname -I | awk '{print $1}')
    
    log_title "=== INSTALLATION TERMINÉE ==="
    echo
    log_success "🎉 $APP_NAME v$APP_VERSION installé avec succès !"
    echo
    echo "📋 Informations d'accès :"
    echo "   🌐 Interface web : http://$server_ip"
    echo "   👤 Utilisateur   : admin"
    echo "   🔒 Mot de passe  : admin123"
    echo
    echo "⚠️  IMPORTANT : Changez le mot de passe après la première connexion !"
    echo
    echo "📊 Services installés :"
    echo "   • NTP Monitor Enterprise"
    echo "   • Apache Web Server"
    echo "   • MySQL Database"
    echo "   • Redis Cache"
    echo "   • NTP Server (ntpsec)"
    echo
    echo "🔧 Commandes utiles :"
    echo "   • Statut : sudo systemctl status ntp-monitor"
    echo "   • Logs   : sudo journalctl -u ntp-monitor -f"
    echo "   • Restart: sudo systemctl restart ntp-monitor"
    echo
    echo "📚 Documentation :"
    echo "   • Guide : $INSTALL_DIR/README.md"
    echo "   • Config: $INSTALL_DIR/.env"
    echo "   • Logs  : /var/log/ntp-monitor/"
    echo
    log_success "Installation terminée avec succès !"
}

# === FONCTION PRINCIPALE ===
main() {
    log_title "Installation $APP_NAME v$APP_VERSION"
    echo
    log_info "Début de l'installation automatique..."
    
    check_root
    check_system
    generate_password
    install_packages
    configure_security
    configure_mysql
    create_user
    install_application
    configure_application
    configure_apache
    configure_service
    verify_installation
    show_summary
    
    log_success "🚀 Installation terminée avec succès !"
}

# === GESTION D'ERREURS ===
trap 'log_error "Installation interrompue"; exit 1' ERR

# === POINT D'ENTRÉE ===
main "$@" 