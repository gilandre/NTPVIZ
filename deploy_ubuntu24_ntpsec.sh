#!/bin/bash
# Script de déploiement NTP Monitor Enterprise - Ubuntu 24.04 avec NTPSEC
# Préserve et optimise la configuration ntpsec existante

set -e

# Couleurs pour affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables
APP_NAME="ntp-monitor-enterprise"
APP_USER="ntp-monitor"
APP_DIR="/home/$APP_USER/$APP_NAME"
GITHUB_REPO="https://github.com/gilandre/NTPVIZ.git"
DOMAIN="192.168.10.45"
MYSQL_DB="ntp_monitor"
MYSQL_USER="ntp_user"

# Fonctions utilitaires
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Ce script doit être exécuté en tant que root (sudo)"
    fi
}

detect_python_version() {
    log "🔍 Détection de la version Python disponible..."
    
    # Tester les versions dans l'ordre de préférence
    for version in "3.12" "3.11" "3.10" "3.9"; do
        if command -v python$version &> /dev/null; then
            PYTHON_VERSION=$version
            PYTHON_CMD="python$version"
            log "✅ Python $version détecté et utilisé"
            return 0
        fi
    done
    
    # Fallback vers python3 par défaut
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
        PYTHON_CMD="python3"
        log "✅ Python $PYTHON_VERSION (défaut) utilisé"
        return 0
    fi
    
    error "❌ Aucune version Python compatible trouvée"
}

backup_ntpsec_config() {
    log "💾 Sauvegarde configuration ntpsec existante..."
    
    # Créer répertoire de sauvegarde
    mkdir -p /root/ntpsec_backup/$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="/root/ntpsec_backup/$(date +%Y%m%d_%H%M%S)"
    
    # Sauvegarder configurations existantes
    if [ -f "/etc/ntpsec/ntp.conf" ]; then
        cp /etc/ntpsec/ntp.conf $BACKUP_DIR/ntp.conf.bak
        log "✅ Configuration ntpsec sauvegardée dans $BACKUP_DIR"
    fi
    
    if [ -f "/etc/ntp.conf" ]; then
        cp /etc/ntp.conf $BACKUP_DIR/ntp.conf.legacy.bak
        log "✅ Configuration ntp legacy sauvegardée"
    fi
    
    # Sauvegarder les clés si elles existent
    if [ -f "/etc/ntpsec/ntp.keys" ]; then
        cp /etc/ntpsec/ntp.keys $BACKUP_DIR/ntp.keys.bak
        log "✅ Clés ntpsec sauvegardées"
    fi
    
    echo "$BACKUP_DIR" > /root/last_ntpsec_backup.txt
    log "✅ Sauvegarde terminée dans $BACKUP_DIR"
}

install_system_packages() {
    log "🔧 Installation des dépendances système avec ntpsec..."
    
    # Mise à jour
    apt update && apt upgrade -y
    
    # Détection Python
    detect_python_version
    
    # Installation packages système adaptés
    local python_packages=""
    if [[ "$PYTHON_VERSION" == "3.12" ]]; then
        python_packages="python3 python3-pip python3-venv python3-dev python3-setuptools python3-wheel"
    elif [[ "$PYTHON_VERSION" == "3.11" ]]; then
        python_packages="python3.11 python3.11-pip python3.11-venv python3.11-dev"
    else
        python_packages="python3 python3-pip python3-venv python3-dev python3-setuptools python3-wheel"
    fi
    
    # Installation packages essentiels avec ntpsec
    apt install -y \
        $python_packages \
        build-essential pkg-config \
        mysql-server mysql-client libmysqlclient-dev \
        apache2 libapache2-mod-wsgi-py3 apache2-dev \
        redis-server \
        git curl wget htop vim \
        certbot python3-certbot-apache \
        ufw \
        ntpsec ntpsec-utils ntpsec-doc \
        || error "❌ Erreur lors de l'installation des packages système"
    
    log "✅ Dépendances système installées (avec ntpsec)"
}

configure_mysql() {
    log "🗄️ Configuration MySQL..."
    
    # Démarrer MySQL
    systemctl enable mysql
    systemctl start mysql
    
    # Attendre que MySQL soit prêt
    sleep 5
    
    # Générer mot de passe aléatoire
    MYSQL_PASSWORD=$(openssl rand -base64 16)
    
    # Créer base et utilisateur
    mysql -u root << EOF
CREATE DATABASE IF NOT EXISTS $MYSQL_DB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$MYSQL_USER'@'localhost' IDENTIFIED BY '$MYSQL_PASSWORD';
GRANT ALL PRIVILEGES ON $MYSQL_DB.* TO '$MYSQL_USER'@'localhost';
FLUSH PRIVILEGES;
EOF
    
    # Sauvegarder mot de passe
    echo "MYSQL_PASSWORD=$MYSQL_PASSWORD" > /root/mysql_credentials.txt
    chmod 600 /root/mysql_credentials.txt
    
    log "✅ MySQL configuré - Mot de passe sauvé dans /root/mysql_credentials.txt"
}

configure_services() {
    log "🔄 Configuration des services avec ntpsec..."
    
    # Configuration Redis
    log "🔧 Configuration Redis..."
    systemctl daemon-reload
    systemctl enable redis-server
    systemctl start redis-server
    
    # Configuration NTPSEC - Préserver la configuration existante
    log "🕐 Configuration ntpsec (préservation configuration existante)..."
    
    # Arrêter chrony s'il est installé et actif
    if systemctl is-active --quiet chronyd 2>/dev/null; then
        log "🔄 Arrêt de chrony (remplacé par ntpsec)"
        systemctl stop chronyd
        systemctl disable chronyd
    fi
    
    # Arrêter systemd-timesyncd s'il est actif
    if systemctl is-active --quiet systemd-timesyncd 2>/dev/null; then
        log "🔄 Arrêt de systemd-timesyncd (remplacé par ntpsec)"
        systemctl stop systemd-timesyncd
        systemctl disable systemd-timesyncd
    fi
    
    # Arrêter ntp legacy s'il est actif
    if systemctl is-active --quiet ntp 2>/dev/null; then
        log "🔄 Arrêt de ntp legacy (remplacé par ntpsec)"
        systemctl stop ntp
        systemctl disable ntp
    fi
    
    # Activer et démarrer ntpsec
    systemctl enable ntpsec
    systemctl start ntpsec
    
    # Vérifier que ntpsec fonctionne
    if systemctl is-active --quiet ntpsec; then
        log "✅ ntpsec configuré et démarré"
    else
        warn "⚠️ Problème avec ntpsec, tentative de redémarrage..."
        systemctl restart ntpsec
    fi
    
    # Configuration Apache
    log "🌐 Configuration Apache..."
    systemctl enable apache2
    a2enmod wsgi rewrite ssl headers
    systemctl start apache2
    
    # Configuration Firewall
    log "🔒 Configuration pare-feu..."
    ufw --force enable
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 123/udp  # NTP
    
    log "✅ Services configurés avec ntpsec"
}

restore_ntpsec_config() {
    log "🔧 Restauration/Configuration ntpsec..."
    
    # Créer répertoire de configuration s'il n'existe pas
    mkdir -p /etc/ntpsec
    
    # Si une sauvegarde existe, restaurer
    if [ -f "/root/last_ntpsec_backup.txt" ]; then
        BACKUP_DIR=$(cat /root/last_ntpsec_backup.txt)
        if [ -f "$BACKUP_DIR/ntp.conf.bak" ]; then
            log "📋 Restauration de la configuration ntpsec existante..."
            cp $BACKUP_DIR/ntp.conf.bak /etc/ntpsec/ntp.conf
            if [ -f "$BACKUP_DIR/ntp.keys.bak" ]; then
                cp $BACKUP_DIR/ntp.keys.bak /etc/ntpsec/ntp.keys
                chmod 600 /etc/ntpsec/ntp.keys
            fi
            log "✅ Configuration ntpsec restaurée"
        fi
    fi
    
    # Créer le répertoire de logs
    mkdir -p /var/log/ntpsec
    chown ntpsec:ntpsec /var/log/ntpsec 2>/dev/null || true
    
    # Redémarrer ntpsec
    systemctl restart ntpsec
    
    log "✅ Configuration ntpsec appliquée"
}

create_app_user() {
    log "👤 Création utilisateur application..."
    
    if ! id "$APP_USER" &>/dev/null; then
        useradd -m -s /bin/bash $APP_USER
        usermod -aG www-data $APP_USER
        log "✅ Utilisateur $APP_USER créé"
    else
        log "ℹ️ Utilisateur $APP_USER existe déjà"
    fi
}

fix_requirements() {
    log "🔧 Correction du fichier requirements.txt..."
    
    # Créer un requirements.txt corrigé pour Ubuntu
    cat > "$APP_DIR/requirements_ubuntu.txt" << 'EOF'
# Requirements.txt corrigé pour Ubuntu 24.04
# mod_wsgi est installé via apt, pas pip

# Framework Flask
Flask==2.3.3
Werkzeug==2.3.7

# Base de données
SQLAlchemy==2.0.21
PyMySQL==1.1.0
Flask-Migrate==4.0.5

# Authentification et formulaires
Flask-Login==0.6.3
Flask-WTF==1.1.1
WTForms==3.0.1

# WebSocket et temps réel
Flask-SocketIO==5.3.6
python-socketio==5.8.0

# Cache et sessions Redis
redis==5.0.1

# Workers et tâches asynchrones
celery==5.3.4

# Monitoring NTP
ntplib==0.4.0
psutil==5.9.5

# Utilitaires
requests==2.31.0
python-dateutil==2.8.2
pytz==2023.3
python-dotenv==1.0.0

# Sécurité
cryptography==41.0.7
bcrypt==4.0.1

# CLI et outils
click==8.1.7
itsdangerous==2.1.2

# Développement
setuptools==68.2.2
wheel==0.41.2
EOF
    
    log "✅ Fichier requirements corrigé créé"
}

deploy_application() {
    log "📦 Déploiement de l'application depuis GitHub..."
    
    sudo -u $APP_USER bash << EOF
set -e

cd /home/$APP_USER

# Clone ou mise à jour depuis GitHub
if [ -d "$APP_NAME" ]; then
    cd $APP_NAME
    git fetch origin
    git pull origin dev
    echo "✅ Application mise à jour depuis GitHub"
else
    git clone -b dev $GITHUB_REPO $APP_NAME
    cd $APP_NAME
    echo "✅ Application clonée depuis GitHub"
fi
EOF
    
    # Corriger les requirements après le clone
    fix_requirements
    
    sudo -u $APP_USER bash << EOF
set -e
cd $APP_DIR

# Créer environnement virtuel
$PYTHON_CMD -m venv venv
source venv/bin/activate

# Installer dépendances
pip install --upgrade pip setuptools wheel
pip install -r requirements_ubuntu.txt

# Créer répertoires
mkdir -p logs instance backups

echo "✅ Application déployée"
EOF
    
    log "✅ Déploiement application terminé"
}

configure_environment() {
    log "⚙️ Configuration environnement production..."
    
    # Récupérer mot de passe MySQL
    MYSQL_PASSWORD=$(grep MYSQL_PASSWORD /root/mysql_credentials.txt | cut -d'=' -f2)
    
    # Générer clé secrète
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    
    # Créer fichier .env
    sudo -u $APP_USER tee $APP_DIR/.env > /dev/null << EOF
# Configuration production NTP Monitor Enterprise
FLASK_ENV=production
SECRET_KEY=$SECRET_KEY
DEBUG=false
HOST=0.0.0.0
PORT=5000

# Base de données MySQL
DATABASE_URL=mysql+pymysql://$MYSQL_USER:$MYSQL_PASSWORD@localhost/$MYSQL_DB

# Configuration NTP
DEFAULT_NTP_SERVERS=pool.ntp.org,time.google.com,time.cloudflare.com
LOCAL_NTP_SERVERS=192.168.1.100,10.0.0.50

# Alertes
ALERT_OFFSET_THRESHOLD=100
ALERT_DELAY_THRESHOLD=500
ALERT_EMAIL=admin@$DOMAIN

# Redis et WebSocket
REDIS_URL=redis://localhost:6379/0
SOCKETIO_ASYNC_MODE=threading

# Sécurité
WTF_CSRF_ENABLED=true
SESSION_PERMANENT=false
PERMANENT_SESSION_LIFETIME=3600

# Monitoring NTP - Utiliser ntpsec
NTP_MONITORING_METHOD=ntpsec
NTP_COMMAND=ntpq
NTP_SERVICE=ntpsec
EOF
    
    chmod 600 $APP_DIR/.env
    
    log "✅ Configuration environnement créée avec ntpsec"
}

initialize_database() {
    log "🗄️ Initialisation base de données..."
    
    sudo -u $APP_USER bash << EOF
cd $APP_DIR
source venv/bin/activate
python init_database.py
EOF
    
    log "✅ Base de données initialisée"
}

create_wsgi_file() {
    log "🌐 Création fichier WSGI..."
    
    sudo -u $APP_USER tee $APP_DIR/app.wsgi > /dev/null << 'EOF'
#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Configuration chemins
app_path = Path('/home/ntp-monitor/ntp-monitor-enterprise')
venv_path = app_path / 'venv' / 'lib' / 'python3.12' / 'site-packages'

# Fallback pour autres versions Python
if not venv_path.exists():
    for version in ['3.11', '3.10', '3.9']:
        venv_path = app_path / 'venv' / 'lib' / f'python{version}' / 'site-packages'
        if venv_path.exists():
            break

sys.path.insert(0, str(app_path))
if venv_path.exists():
    sys.path.insert(0, str(venv_path))
os.chdir(str(app_path))

# Charger environnement
from dotenv import load_dotenv
load_dotenv(str(app_path / '.env'))

# Importer application
from app import app as application

if __name__ == "__main__":
    application.run()
EOF
    
    log "✅ Fichier WSGI créé"
}

configure_apache() {
    log "🌐 Configuration Apache..."
    
    # Configuration Virtual Host
    tee /etc/apache2/sites-available/$APP_NAME.conf > /dev/null << EOF
<VirtualHost *:80>
    ServerName $DOMAIN
    ServerAlias www.$DOMAIN
    
    DocumentRoot $APP_DIR
    
    WSGIDaemonProcess $APP_NAME python-home=$APP_DIR/venv python-path=$APP_DIR
    WSGIProcessGroup $APP_NAME
    WSGIScriptAlias / $APP_DIR/app.wsgi
    
    <Directory $APP_DIR>
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    
    Alias /static $APP_DIR/frontend/static
    <Directory $APP_DIR/frontend/static>
        Require all granted
    </Directory>
    
    ErrorLog \${APACHE_LOG_DIR}/${APP_NAME}_error.log
    CustomLog \${APACHE_LOG_DIR}/${APP_NAME}_access.log combined
</VirtualHost>
EOF
    
    # Activer site
    a2dissite 000-default 2>/dev/null || true
    a2ensite $APP_NAME
    
    # Test configuration
    if apache2ctl configtest; then
        systemctl reload apache2
        log "✅ Apache configuré"
    else
        warn "⚠️ Problème configuration Apache"
    fi
}

create_systemd_service() {
    log "🔧 Création service systemd..."
    
    tee /etc/systemd/system/$APP_NAME.service > /dev/null << EOF
[Unit]
Description=NTP Monitor Enterprise
After=network.target mysql.service redis.service ntpsec.service
Wants=mysql.service redis.service ntpsec.service

[Service]
Type=simple
User=$APP_USER
Group=www-data
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python app.py
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
EOF
    
    # Activer service
    systemctl daemon-reload
    systemctl enable $APP_NAME
    systemctl start $APP_NAME
    
    log "✅ Service systemd créé et démarré"
}

validate_deployment() {
    log "🧪 Validation du déploiement ntpsec..."
    
    # Test services
    for service in $APP_NAME apache2 mysql redis-server; do
        if systemctl is-active --quiet $service; then
            log "✅ Service $service actif"
        else
            warn "⚠️ Service $service inactif"
        fi
    done
    
    # Test ntpsec
    if systemctl is-active --quiet ntpsec; then
        log "✅ Service ntpsec actif"
        
        # Test fonctionnement ntpsec
        if command -v ntpq &> /dev/null; then
            if ntpq -c peers &> /dev/null; then
                log "✅ ntpq répond correctement"
            else
                warn "⚠️ ntpq ne répond pas correctement"
            fi
        else
            warn "⚠️ Commande ntpq non disponible"
        fi
    else
        warn "⚠️ Service ntpsec inactif"
    fi
    
    # Test accès local
    sleep 10
    if curl -s http://localhost > /dev/null; then
        log "✅ Application accessible localement"
    else
        warn "⚠️ Application non accessible localement"
    fi
    
    log "✅ Validation terminée"
}

display_final_info() {
    log "🎉 Déploiement terminé avec succès !"
    
    echo
    echo "=============================================="
    echo "  NTP MONITOR ENTERPRISE - UBUNTU 24.04"
    echo "           AVEC NTPSEC"
    echo "=============================================="
    echo
    echo "🌐 URL Application: http://$DOMAIN"
    echo "🐍 Version Python: $PYTHON_VERSION"
    echo "🕐 Service temps: ntpsec (configuration préservée)"
    echo "📊 Cache: Redis"
    echo "🔧 mod_wsgi: Système"
    echo
    echo "👤 Connexion par défaut:"
    echo "   - Administrateur: admin / admin123"
    echo
    echo "🔧 Gestion:"
    echo "   - Service: sudo systemctl status $APP_NAME"
    echo "   - Logs: sudo journalctl -u $APP_NAME -f"
    echo
    echo "🕐 ntpsec:"
    echo "   - Service: sudo systemctl status ntpsec"
    echo "   - Configuration: /etc/ntpsec/ntp.conf"
    echo "   - Commandes: ntpq -c peers"
    echo
    echo "=============================================="
}

# Fonction principale
main() {
    log "🚀 Début déploiement NTP Monitor Enterprise sur Ubuntu 24.04 avec ntpsec"
    
    check_root
    
    # Sauvegarder configuration existante
    backup_ntpsec_config
    
    # Installation et configuration
    install_system_packages
    configure_mysql
    configure_services
    
    # Restaurer/configurer ntpsec
    restore_ntpsec_config
    
    # Application
    create_app_user
    deploy_application
    configure_environment
    initialize_database
    
    # Web
    create_wsgi_file
    configure_apache
    create_systemd_service
    
    # Tests finaux
    validate_deployment
    display_final_info
    
    log "🎉 Déploiement Ubuntu 24.04 avec ntpsec terminé !"
}

# Exécution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 