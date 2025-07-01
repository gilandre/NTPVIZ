#!/bin/bash
# Script de déploiement automatique Ubuntu - NTP Monitor Enterprise v2.0.0
# Déploie l'application depuis GitHub vers serveur Ubuntu de production

set -e  # Arrêt immédiat en cas d'erreur

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_NAME="ntp-monitor-enterprise"
APP_USER="ntp-monitor"
APP_DIR="/home/$APP_USER/$APP_NAME"
GITHUB_REPO="https://github.com/gilandre/NTPVIZ.git"
DOMAIN="192.168.10.45"  # CHANGEZ ICI
MYSQL_DB="ntp_monitor"
MYSQL_USER="ntp_user"

# Couleurs pour affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

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

# ============================================================================
# INSTALLATION SYSTÈME
# ============================================================================

install_system_packages() {
    log "🔧 Installation des dépendances système..."
    
    apt update && apt upgrade -y
    apt install -y \
        python3.11 python3.11-venv python3.11-dev \
        python3-pip build-essential \
        mysql-server mysql-client \
        apache2 libapache2-mod-wsgi-py3 \
        redis-server \
        ntp ntpdate \
        git curl wget htop \
        certbot python3-certbot-apache \
        ufw
    
    log "✅ Dépendances système installées"
}

configure_mysql() {
    log "🗄️ Configuration MySQL..."
    
    # Démarrer MySQL
    systemctl enable mysql
    systemctl start mysql
    
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
    log "🔄 Configuration des services..."
    
    # Redis
    systemctl enable redis-server
    systemctl start redis-server
    
    # NTP
    systemctl enable ntp
    systemctl start ntp
    
    # Apache
    systemctl enable apache2
    a2enmod wsgi rewrite ssl headers
    
    log "✅ Services configurés"
}

# ============================================================================
# UTILISATEUR ET APPLICATION
# ============================================================================

create_app_user() {
    log "👤 Création utilisateur application..."
    
    # Créer utilisateur s'il n'existe pas
    if ! id "$APP_USER" &>/dev/null; then
        useradd -m -s /bin/bash $APP_USER
        usermod -aG www-data $APP_USER
        log "✅ Utilisateur $APP_USER créé"
    else
        log "ℹ️ Utilisateur $APP_USER existe déjà"
    fi
}

deploy_application() {
    log "📦 Déploiement de l'application depuis GitHub..."
    
    # Changer vers utilisateur app
    sudo -u $APP_USER bash << EOF
set -e

# Aller dans le répertoire home
cd /home/$APP_USER

# Clone ou mise à jour depuis GitHub
if [ -d "$APP_NAME" ]; then
    cd $APP_NAME
    git fetch origin
    git pull origin main
    echo "✅ Application mise à jour depuis GitHub"
else
    git clone $GITHUB_REPO
    cd $APP_NAME
    echo "✅ Application clonée depuis GitHub"
fi

# Vérifier les corrections
if grep -q "type: 'category'" frontend/static/js/dashboard.js; then
    echo "✅ Correction Chart.js présente"
else
    echo "❌ Correction Chart.js manquante"
    exit 1
fi

if grep -q "sys.stdout.reconfigure(encoding='utf-8')" app.py; then
    echo "✅ Correction UTF-8 présente"
else
    echo "❌ Correction UTF-8 manquante"
    exit 1
fi

# Créer environnement virtuel
python3.11 -m venv venv
source venv/bin/activate

# Installer dépendances
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Créer répertoires
mkdir -p logs instance backups

echo "✅ Application déployée avec succès"
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

# Monitoring
MONITORING_INTERVAL=10
MAX_LOG_RETENTION_DAYS=30
AUTO_CLEANUP_ENABLED=true
EOF
    
    # Sécuriser le fichier
    chmod 600 $APP_DIR/.env
    
    log "✅ Configuration environnement créée"
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

# ============================================================================
# CONFIGURATION WEB
# ============================================================================

create_wsgi_file() {
    log "🌐 Création fichier WSGI..."
    
    sudo -u $APP_USER tee $APP_DIR/app.wsgi > /dev/null << 'EOF'
#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Configuration chemins
app_path = Path('/home/ntp-monitor/ntp-monitor-enterprise')
venv_path = app_path / 'venv' / 'lib' / 'python3.11' / 'site-packages'

sys.path.insert(0, str(app_path))
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
    
    # Headers sécurité
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    Header always set X-XSS-Protection "1; mode=block"
</VirtualHost>
EOF
    
    # Activer site
    a2dissite 000-default
    a2ensite $APP_NAME
    
    # Test configuration
    apache2ctl configtest
    systemctl reload apache2
    
    log "✅ Apache configuré"
}

create_systemd_service() {
    log "🔧 Création service systemd..."
    
    tee /etc/systemd/system/$APP_NAME.service > /dev/null << EOF
[Unit]
Description=NTP Monitor Enterprise
After=network.target mysql.service redis.service
Wants=mysql.service redis.service

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

# ============================================================================
# SÉCURITÉ
# ============================================================================

configure_firewall() {
    log "🔒 Configuration pare-feu..."
    
    ufw --force enable
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    log "✅ Pare-feu configuré"
}

setup_ssl() {
    log "🔐 Configuration SSL avec Let's Encrypt..."
    
    if [[ "$DOMAIN" != "votre-domaine.com" ]]; then
        certbot --apache -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
        log "✅ SSL configuré"
    else
        warn "⚠️ Domaine non configuré - SSL ignoré"
    fi
}

set_permissions() {
    log "🔒 Configuration permissions..."
    
    chown -R $APP_USER:www-data $APP_DIR
    chmod -R 755 $APP_DIR
    chmod 600 $APP_DIR/.env
    chmod -R 664 $APP_DIR/logs
    
    log "✅ Permissions configurées"
}

# ============================================================================
# SURVEILLANCE
# ============================================================================

create_monitoring_script() {
    log "📊 Création script de monitoring..."
    
    tee /home/$APP_USER/monitor.sh > /dev/null << 'EOF'
#!/bin/bash
# Monitoring automatique NTP Monitor Enterprise

# Vérifier services
for service in ntp-monitor-enterprise apache2 mysql redis-server; do
    if ! systemctl is-active --quiet $service; then
        echo "$(date): Redémarrage $service" >> /home/ntp-monitor/logs/monitoring.log
        systemctl start $service
    fi
done

# Nettoyage logs anciens
find /home/ntp-monitor/ntp-monitor-enterprise/logs -name "*.log" -mtime +30 -delete

# Test accès web
if ! curl -s http://localhost > /dev/null; then
    echo "$(date): Application inaccessible" >> /home/ntp-monitor/logs/monitoring.log
fi
EOF
    
    chmod +x /home/$APP_USER/monitor.sh
    chown $APP_USER:$APP_USER /home/$APP_USER/monitor.sh
    
    # Cron job monitoring
    (crontab -u $APP_USER -l 2>/dev/null; echo "*/15 * * * * /home/$APP_USER/monitor.sh") | crontab -u $APP_USER -
    
    log "✅ Monitoring automatique configuré"
}

# ============================================================================
# VALIDATION ET TESTS
# ============================================================================

validate_deployment() {
    log "🧪 Validation du déploiement..."
    
    # Test services
    for service in $APP_NAME apache2 mysql redis-server; do
        if systemctl is-active --quiet $service; then
            log "✅ Service $service actif"
        else
            error "❌ Service $service inactif"
        fi
    done
    
    # Test accès local
    sleep 5
    if curl -s http://localhost > /dev/null; then
        log "✅ Application accessible localement"
    else
        warn "⚠️ Application non accessible localement"
    fi
    
    # Test base de données
    if mysql -u $MYSQL_USER -p$(grep MYSQL_PASSWORD /root/mysql_credentials.txt | cut -d'=' -f2) -e "USE $MYSQL_DB; SHOW TABLES;" | grep -q "user"; then
        log "✅ Base de données opérationnelle"
    else
        warn "⚠️ Problème base de données"
    fi
    
    log "✅ Validation terminée"
}

display_final_info() {
    log "🎉 Déploiement terminé avec succès !"
    
    echo
    echo "=============================================="
    echo "    NTP MONITOR ENTERPRISE - PRODUCTION"
    echo "=============================================="
    echo
    echo "🌐 URL Application: http://$DOMAIN"
    if [[ "$DOMAIN" != "votre-domaine.com" ]]; then
        echo "🔒 URL HTTPS: https://$DOMAIN"
    fi
    echo
    echo "👤 Connexion par défaut:"
    echo "   - Administrateur: admin / admin123"
    echo "   - Opérateur: operator / operator123"
    echo "   - Visualiseur: viewer / viewer123"
    echo
    echo "🔧 Gestion:"
    echo "   - Service: sudo systemctl status $APP_NAME"
    echo "   - Logs: sudo journalctl -u $APP_NAME -f"
    echo "   - Apache: /var/log/apache2/${APP_NAME}_error.log"
    echo
    echo "🗄️ Base de données:"
    echo "   - Utilisateur: $MYSQL_USER"
    echo "   - Mot de passe: voir /root/mysql_credentials.txt"
    echo
    echo "⚠️ IMPORTANT:"
    echo "   - Changez les mots de passe par défaut"
    echo "   - Configurez vos serveurs NTP locaux"
    echo "   - Surveillez les logs régulièrement"
    echo
    echo "=============================================="
}

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

main() {
    log "🚀 Début déploiement NTP Monitor Enterprise sur Ubuntu"
    
    check_root
    
    # Vérifications préalables
    if [[ "$GITHUB_REPO" == *"VOTRE_USERNAME"* ]]; then
        error "❌ Veuillez modifier GITHUB_REPO avec votre URL GitHub"
    fi
    
    # Installation et configuration
    install_system_packages
    configure_mysql
    configure_services
    configure_firewall
    
    # Application
    create_app_user
    deploy_application
    configure_environment
    initialize_database
    
    # Web
    create_wsgi_file
    configure_apache
    create_systemd_service
    
    # Sécurité
    setup_ssl
    set_permissions
    
    # Monitoring
    create_monitoring_script
    
    # Tests finaux
    validate_deployment
    display_final_info
    
    log "🎉 Déploiement Ubuntu terminé avec succès !"
}

# ============================================================================
# EXÉCUTION
# ============================================================================

# Vérifier si le script est appelé directement
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 