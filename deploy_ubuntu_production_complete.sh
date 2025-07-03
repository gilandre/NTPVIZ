#!/bin/bash
# Script de Déploiement Complet Ubuntu - NTP Monitor Enterprise v2.1.0
# Vérifie les prérequis, préserve ntpsec, utilise MySQL, déploie sur port 80
# Optimisé pour Ubuntu 24.04 avec détection automatique des versions

set -e

# ============================================================================
# CONFIGURATION GLOBALE
# ============================================================================

APP_NAME="ntp-monitor-enterprise"
APP_USER="ntp-monitor"
APP_DIR="/home/$APP_USER/$APP_NAME"
GITHUB_REPO="https://github.com/gilandre/NTPVIZ.git"
GITHUB_BRANCH="dev"
DOMAIN="192.168.10.45"  # Modifiez selon votre IP/domaine
MYSQL_DB="ntp_monitor"
MYSQL_USER="ntp_user"

# Couleurs pour affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables globales
PYTHON_VERSION=""
PYTHON_CMD=""
MYSQL_PASSWORD=""
NTPSEC_INSTALLED=false
NTPSEC_ACTIVE=false
NTPSEC_FUNCTIONAL=false
NTPSEC_HAS_CLIENTS=false

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

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

section() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "❌ Ce script doit être exécuté en tant que root (sudo)"
    fi
}

# ============================================================================
# DÉTECTION ET VÉRIFICATION SYSTÈME
# ============================================================================

detect_python_version() {
    log "🔍 Détection de la version Python disponible..."
    
    # Tester les versions dans l'ordre de préférence
    for version in "3.12" "3.11" "3.10" "3.9"; do
        if command -v python$version &> /dev/null; then
            PYTHON_VERSION=$version
            PYTHON_CMD="python$version"
            log "✅ Python $version détecté et sélectionné"
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

check_ntpsec_status() {
    log "🔍 Vérification de l'état ntpsec actuel..."
    
    # Vérifier si ntpsec est installé
    if command -v ntpq &> /dev/null; then
        log "✅ ntpsec est installé"
        NTPSEC_INSTALLED=true
        
        # Vérifier si le service ntpsec est actif
        if systemctl is-active --quiet ntpsec 2>/dev/null; then
            log "✅ Service ntpsec est actif"
            NTPSEC_ACTIVE=true
            
            # Vérifier si ntpq répond
            if ntpq -c peers &> /dev/null; then
                log "✅ ntpq répond correctement"
                NTPSEC_FUNCTIONAL=true
                
                # Compter les serveurs synchronisés
                SYNC_SERVERS=$(ntpq -c peers 2>/dev/null | grep -c "^[*+]" || echo "0")
                if [ "$SYNC_SERVERS" -gt 0 ]; then
                    log "✅ $SYNC_SERVERS serveur(s) NTP synchronisé(s)"
                else
                    warn "⚠️ Aucun serveur NTP synchronisé actuellement"
                fi
                
                # Vérifier les clients connectés
                CLIENT_CONNECTIONS=$(ss -u -n | grep :123 | wc -l || echo "0")
                if [ "$CLIENT_CONNECTIONS" -gt 0 ]; then
                    log "✅ $CLIENT_CONNECTIONS connexion(s) client(s) NTP détectée(s)"
                    NTPSEC_HAS_CLIENTS=true
                else
                    info "ℹ️ Aucune connexion client active actuellement"
                fi
            else
                warn "⚠️ ntpq ne répond pas correctement"
                NTPSEC_FUNCTIONAL=false
            fi
        else
            warn "⚠️ Service ntpsec inactif"
            NTPSEC_ACTIVE=false
        fi
    else
        info "ℹ️ ntpsec n'est pas installé"
        NTPSEC_INSTALLED=false
    fi
}

check_system_requirements() {
    section "VÉRIFICATION DES PRÉREQUIS SYSTÈME"
    
    log "🔍 Vérification de la distribution..."
    if ! grep -q "Ubuntu" /etc/os-release; then
        warn "⚠️ Cette distribution n'est pas Ubuntu - procédure adaptée"
    fi
    
    log "🔍 Vérification de l'espace disque..."
    AVAILABLE_SPACE=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$AVAILABLE_SPACE" -lt 2 ]; then
        error "❌ Espace disque insuffisant (< 2GB disponible)"
    fi
    log "✅ Espace disque suffisant (${AVAILABLE_SPACE}GB disponible)"
    
    log "🔍 Vérification de la mémoire..."
    AVAILABLE_RAM=$(free -m | grep '^Mem:' | awk '{print $2}')
    if [ "$AVAILABLE_RAM" -lt 512 ]; then
        warn "⚠️ Mémoire faible (${AVAILABLE_RAM}MB) - performance réduite possible"
    fi
    log "✅ Mémoire suffisante (${AVAILABLE_RAM}MB)"
    
    log "🔍 Vérification de la connectivité Internet..."
    if ! ping -c 1 -W 5 8.8.8.8 &> /dev/null; then
        error "❌ Pas de connexion Internet"
    fi
    log "✅ Connexion Internet active"
}

# ============================================================================
# INSTALLATION PACKAGES SYSTÈME
# ============================================================================

install_system_packages() {
    section "INSTALLATION DES PACKAGES SYSTÈME"
    
    log "🔄 Mise à jour des paquets système..."
    apt update && apt upgrade -y
    
    # Détection Python
    detect_python_version
    
    # Installation packages Python selon version détectée
    log "🐍 Installation packages Python ($PYTHON_VERSION)..."
    local python_packages=""
    case "$PYTHON_VERSION" in
        "3.12")
            python_packages="python3.12 python3.12-venv python3.12-dev python3-pip python3-setuptools python3-wheel"
            ;;
        "3.11")
            python_packages="python3.11 python3.11-venv python3.11-dev python3-pip python3-setuptools python3-wheel"
            ;;
        "3.10")
            python_packages="python3.10 python3.10-venv python3.10-dev python3-pip python3-setuptools python3-wheel"
            ;;
        *)
            python_packages="python3 python3-venv python3-dev python3-pip python3-setuptools python3-wheel"
            ;;
    esac
    
    log "🔧 Installation des dépendances système complètes..."
    apt install -y \
        $python_packages \
        build-essential pkg-config \
        mysql-server mysql-client libmysqlclient-dev mysql-common \
        apache2 libapache2-mod-wsgi-py3 apache2-dev apache2-utils \
        redis-server \
        git curl wget htop vim tree net-tools unzip \
        certbot python3-certbot-apache openssl \
        ufw psmisc lsof \
        software-properties-common apt-transport-https ca-certificates gnupg \
        || error "❌ Erreur lors de l'installation des packages système"
    
    log "✅ Packages système installés avec succès"
}

# ============================================================================
# CONFIGURATION NTPSEC
# ============================================================================

configure_ntpsec() {
    section "CONFIGURATION SERVICE TEMPS (NTPSEC)"
    
    check_ntpsec_status
    
    if [[ $NTPSEC_INSTALLED == true && $NTPSEC_FUNCTIONAL == true ]]; then
        log "🎉 ntpsec fonctionne déjà parfaitement !"
        
        if [[ $NTPSEC_HAS_CLIENTS == true ]]; then
            warn "⚠️ ATTENTION: Des clients sont connectés à votre serveur ntpsec"
            warn "⚠️ Préservation de la configuration existante"
            
            # Sauvegarder la configuration ntpsec
            log "💾 Sauvegarde de la configuration ntpsec existante..."
            BACKUP_DIR="/root/ntpsec_backup/$(date +%Y%m%d_%H%M%S)"
            mkdir -p "$BACKUP_DIR"
            
            if [ -f "/etc/ntpsec/ntp.conf" ]; then
                cp /etc/ntpsec/ntp.conf "$BACKUP_DIR/ntp.conf.bak"
            fi
            if [ -f "/etc/ntpsec/ntp.keys" ]; then
                cp /etc/ntpsec/ntp.keys "$BACKUP_DIR/ntp.keys.bak"
                chmod 600 "$BACKUP_DIR/ntp.keys.bak"
            fi
            
            echo "$BACKUP_DIR" > /root/last_ntpsec_backup.txt
            log "✅ Configuration ntpsec sauvegardée dans $BACKUP_DIR"
        fi
        
        # Arrêter les services concurrents
        log "🔄 Vérification des services concurrents..."
        if systemctl is-active --quiet chronyd 2>/dev/null; then
            log "🔄 Arrêt de chrony (conflit avec ntpsec)..."
            systemctl stop chronyd
            systemctl disable chronyd
        fi
        
        if systemctl is-active --quiet systemd-timesyncd 2>/dev/null; then
            log "🔄 Arrêt de systemd-timesyncd (conflit avec ntpsec)..."
            systemctl stop systemd-timesyncd
            systemctl disable systemd-timesyncd
        fi
        
        log "✅ Configuration ntpsec préservée"
        
    else
        # Installer ntpsec si nécessaire
        log "📦 Installation de ntpsec..."
        apt install -y ntpsec ntpsec-utils ntpsec-doc
        
        # Arrêter les services concurrents avant de configurer ntpsec
        systemctl stop chronyd 2>/dev/null || true
        systemctl disable chronyd 2>/dev/null || true
        systemctl stop systemd-timesyncd 2>/dev/null || true
        systemctl disable systemd-timesyncd 2>/dev/null || true
        
        # Configurer et démarrer ntpsec
        systemctl enable ntpsec
        systemctl start ntpsec
        
        log "✅ ntpsec installé et configuré"
    fi
}

# ============================================================================
# CONFIGURATION MYSQL
# ============================================================================

configure_mysql() {
    section "CONFIGURATION BASE DE DONNÉES MYSQL"
    
    log "🔄 Configuration MySQL..."
    
    # Démarrer MySQL
    systemctl enable mysql
    systemctl start mysql
    
    # Attendre que MySQL soit prêt
    sleep 5
    
    # Générer mot de passe sécurisé
    MYSQL_PASSWORD=$(openssl rand -base64 16)
    
    # Sécuriser MySQL et créer base
    log "🔒 Sécurisation et configuration MySQL..."
    mysql -u root << EOF
-- Sécurisation de base
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';

-- Création base et utilisateur
CREATE DATABASE IF NOT EXISTS $MYSQL_DB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$MYSQL_USER'@'localhost' IDENTIFIED BY '$MYSQL_PASSWORD';
GRANT ALL PRIVILEGES ON $MYSQL_DB.* TO '$MYSQL_USER'@'localhost';
FLUSH PRIVILEGES;
EOF
    
    # Sauvegarder les credentials
    cat > /root/mysql_credentials.txt << EOF
# Credentials MySQL pour NTP Monitor Enterprise
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=$MYSQL_DB
MYSQL_USER=$MYSQL_USER
MYSQL_PASSWORD=$MYSQL_PASSWORD
EOF
    chmod 600 /root/mysql_credentials.txt
    
    log "✅ MySQL configuré - Credentials sauvés dans /root/mysql_credentials.txt"
}

# ============================================================================
# CONFIGURATION SERVICES SYSTÈME
# ============================================================================

configure_services() {
    section "CONFIGURATION SERVICES SYSTÈME"
    
    log "🔧 Configuration Redis..."
    systemctl daemon-reload
    systemctl enable redis-server
    systemctl start redis-server
    
    if systemctl is-active --quiet redis-server; then
        log "✅ Redis configuré et démarré"
    else
        warn "⚠️ Redis peut avoir des problèmes, mais on continue"
    fi
    
    log "🌐 Configuration Apache..."
    systemctl enable apache2
    a2enmod wsgi rewrite ssl headers expires deflate proxy proxy_http proxy_wstunnel
    systemctl start apache2
    
    log "🔒 Configuration pare-feu..."
    ufw --force enable
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 123/udp  # NTP
    
    log "✅ Services système configurés"
}

# ============================================================================
# DÉPLOIEMENT APPLICATION
# ============================================================================

create_app_user() {
    section "CRÉATION UTILISATEUR APPLICATION"
    
    if ! id "$APP_USER" &>/dev/null; then
        log "👤 Création de l'utilisateur $APP_USER..."
        useradd -m -s /bin/bash $APP_USER
        usermod -aG www-data $APP_USER
        log "✅ Utilisateur $APP_USER créé"
    else
        log "ℹ️ Utilisateur $APP_USER existe déjà"
    fi
}

deploy_application() {
    section "DÉPLOIEMENT APPLICATION DEPUIS GITHUB"
    
    log "📦 Déploiement de l'application..."
    
    sudo -u $APP_USER bash << EOF
set -e

cd /home/$APP_USER

# Clone ou mise à jour depuis GitHub
if [ -d "$APP_NAME" ]; then
    cd $APP_NAME
    git fetch origin
    git pull origin $GITHUB_BRANCH
    log "✅ Application mise à jour depuis GitHub"
else
    git clone -b $GITHUB_BRANCH $GITHUB_REPO $APP_NAME
    cd $APP_NAME
    log "✅ Application clonée depuis GitHub"
fi

# Vérifier les corrections critiques
if grep -q "type: 'category'" frontend/static/js/dashboard.js; then
    echo "✅ Correction Chart.js présente"
else
    echo "⚠️ Correction Chart.js manquante"
fi

if grep -q "sys.stdout.reconfigure(encoding='utf-8')" app.py; then
    echo "✅ Correction UTF-8 présente"
else
    echo "⚠️ Correction UTF-8 manquante"
fi

# Créer environnement virtuel avec version Python détectée
$PYTHON_CMD -m venv venv
source venv/bin/activate

# Installer dépendances
pip install --upgrade pip setuptools wheel

# Créer requirements.txt corrigé pour Ubuntu (sans mod_wsgi)
cat > requirements_ubuntu.txt << 'PYEOF'
# Requirements.txt corrigé pour Ubuntu 24.04
# mod_wsgi installé via apt, pas pip

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

# Sécurité et hachage
bcrypt==4.0.1
cryptography==41.0.4

# Configuration et environnement
python-dotenv==1.0.0

# Gestion des dates
python-dateutil==2.8.2

# Cache et sessions
Flask-Session==0.5.0
redis==5.0.1

# Communication temps réel
Flask-SocketIO==5.3.6
python-socketio==5.8.0

# Validation et utils
validators==0.22.0
click==8.1.7

# Monitoring et logs
psutil==5.9.5
watchdog==3.0.0

# Requests HTTP
requests==2.31.0
urllib3==2.0.7

# Autres utilitaires
packaging==23.1
six==1.16.0
PYEOF

# Installer avec le fichier corrigé
pip install -r requirements_ubuntu.txt

# Créer répertoires
mkdir -p logs instance backups

echo "✅ Application déployée avec succès"
EOF
    
    log "✅ Déploiement application terminé"
}

# ============================================================================
# CONFIGURATION ENVIRONNEMENT
# ============================================================================

configure_environment() {
    section "CONFIGURATION ENVIRONNEMENT PRODUCTION"
    
    log "⚙️ Configuration des variables d'environnement..."
    
    # Récupérer mot de passe MySQL
    MYSQL_PASSWORD=$(grep MYSQL_PASSWORD /root/mysql_credentials.txt | cut -d'=' -f2)
    
    # Générer clé secrète
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    
    # Créer fichier .env
    sudo -u $APP_USER tee $APP_DIR/.env > /dev/null << EOF
# Configuration production NTP Monitor Enterprise v2.1.0
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

# Monitoring et maintenance
MONITORING_INTERVAL=10
MAX_LOG_RETENTION_DAYS=30
AUTO_CLEANUP_ENABLED=true
EOF
    
    chmod 600 $APP_DIR/.env
    
    log "✅ Configuration environnement créée"
}

# ============================================================================
# INITIALISATION BASE DE DONNÉES
# ============================================================================

initialize_database() {
    section "INITIALISATION BASE DE DONNÉES"
    
    log "🗄️ Initialisation de la base de données..."
    
    sudo -u $APP_USER bash << EOF
cd $APP_DIR
source venv/bin/activate
python init_database.py
EOF
    
    log "✅ Base de données initialisée"
}

# ============================================================================
# CONFIGURATION WEB (APACHE + WSGI)
# ============================================================================

create_wsgi_file() {
    section "CRÉATION FICHIER WSGI"
    
    log "🌐 Création du fichier WSGI..."
    
    sudo -u $APP_USER tee $APP_DIR/app.wsgi > /dev/null << EOF
#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Configuration chemins
app_path = Path('$APP_DIR')
venv_path = app_path / 'venv' / 'lib' / 'python$PYTHON_VERSION' / 'site-packages'

# Fallback pour autres versions Python
if not venv_path.exists():
    for version in ['3.12', '3.11', '3.10', '3.9']:
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
    section "CONFIGURATION APACHE POUR PORT 80"
    
    log "🌐 Configuration Apache Virtual Host..."
    
    # Configuration Virtual Host pour port 80
    tee /etc/apache2/sites-available/$APP_NAME.conf > /dev/null << EOF
# NTP Monitor Enterprise - Configuration Apache
# Port 80 - Production

<VirtualHost *:80>
    ServerName $DOMAIN
    ServerAlias www.$DOMAIN localhost
    
    DocumentRoot $APP_DIR
    
    # Configuration WSGI
    WSGIDaemonProcess $APP_NAME python-home=$APP_DIR/venv python-path=$APP_DIR
    WSGIProcessGroup $APP_NAME
    WSGIScriptAlias / $APP_DIR/app.wsgi
    
    # Répertoire principal
    <Directory $APP_DIR>
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    
    # Fichiers statiques
    Alias /static $APP_DIR/frontend/static
    <Directory $APP_DIR/frontend/static>
        Require all granted
        
        # Cache pour les fichiers statiques
        <IfModule mod_expires.c>
            ExpiresActive On
            ExpiresByType text/css "access plus 1 month"
            ExpiresByType application/javascript "access plus 1 month"
            ExpiresByType image/png "access plus 1 month"
            ExpiresByType image/jpg "access plus 1 month"
            ExpiresByType image/jpeg "access plus 1 month"
            ExpiresByType image/gif "access plus 1 month"
            ExpiresByType image/ico "access plus 1 month"
        </IfModule>
    </Directory>
    
    # Logs
    ErrorLog \${APACHE_LOG_DIR}/${APP_NAME}_error.log
    CustomLog \${APACHE_LOG_DIR}/${APP_NAME}_access.log combined
    LogLevel info
    
    # Headers de sécurité
    <IfModule mod_headers.c>
        Header always set X-Content-Type-Options nosniff
        Header always set X-Frame-Options SAMEORIGIN
        Header always set X-XSS-Protection "1; mode=block"
        Header always set Referrer-Policy "strict-origin-when-cross-origin"
    </IfModule>
    
    # Configuration WebSocket (pour SocketIO)
    RewriteEngine On
    RewriteCond %{REQUEST_URI}  ^/socket.io            [NC]
    RewriteCond %{QUERY_STRING} transport=websocket    [NC]
    RewriteRule /(.*)           ws://localhost:5000/$1 [P,L]
    
    ProxyPreserveHost On
    ProxyRequests Off
    ProxyPass /socket.io/ http://localhost:5000/socket.io/
    ProxyPassReverse /socket.io/ http://localhost:5000/socket.io/
    
    # Compression
    <IfModule mod_deflate.c>
        SetOutputFilter DEFLATE
        AddOutputFilterByType DEFLATE text/plain
        AddOutputFilterByType DEFLATE text/html
        AddOutputFilterByType DEFLATE text/xml
        AddOutputFilterByType DEFLATE text/css
        AddOutputFilterByType DEFLATE application/xml
        AddOutputFilterByType DEFLATE application/xhtml+xml
        AddOutputFilterByType DEFLATE application/rss+xml
        AddOutputFilterByType DEFLATE application/javascript
        AddOutputFilterByType DEFLATE application/x-javascript
    </IfModule>
    
    # Empêcher l'accès aux fichiers sensibles
    <FilesMatch "\.(py|pyc|pyo|db|sqlite|log|ini|conf|env)$">
        Require all denied
    </FilesMatch>
    
    <Directory $APP_DIR/backend>
        Require all denied
    </Directory>
    
    <Directory $APP_DIR/config>
        Require all denied
    </Directory>
    
    <Directory $APP_DIR/logs>
        Require all denied
    </Directory>
    
    <Directory $APP_DIR/instance>
        Require all denied
    </Directory>
</VirtualHost>
EOF
    
    # Activer modules Apache nécessaires
    log "🔧 Activation des modules Apache..."
    a2enmod proxy proxy_http proxy_wstunnel
    
    # Désactiver site par défaut et activer le nôtre
    log "🔄 Activation du site NTP Monitor..."
    a2dissite 000-default 2>/dev/null || true
    a2ensite $APP_NAME
    
    # Test configuration
    if apache2ctl configtest; then
        systemctl reload apache2
        log "✅ Apache configuré pour le port 80"
    else
        warn "⚠️ Problème configuration Apache, mais on continue"
    fi
}

# ============================================================================
# SERVICE SYSTEMD
# ============================================================================

create_systemd_service() {
    section "CRÉATION SERVICE SYSTEMD"
    
    log "🔧 Création du service systemd..."
    
    tee /etc/systemd/system/$APP_NAME.service > /dev/null << EOF
[Unit]
Description=NTP Monitor Enterprise v2.1.0
Documentation=https://github.com/gilandre/NTPVIZ
After=network.target mysql.service redis.service ntpsec.service
Wants=mysql.service redis.service ntpsec.service

[Service]
Type=simple
User=$APP_USER
Group=www-data
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
Environment=PYTHONPATH=$APP_DIR
ExecStartPre=/bin/sleep 10
ExecStart=$APP_DIR/venv/bin/python app.py
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3
KillMode=mixed
TimeoutStopSec=10

# Sécurité
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$APP_DIR
ProtectHome=true

# Limites de ressources
LimitNOFILE=65536
MemoryLimit=1G

[Install]
WantedBy=multi-user.target
EOF
    
    # Activer et démarrer le service
    systemctl daemon-reload
    systemctl enable $APP_NAME
    systemctl start $APP_NAME
    
    log "✅ Service systemd créé et démarré"
}

# ============================================================================
# VALIDATION ET TESTS
# ============================================================================

validate_deployment() {
    section "VALIDATION DU DÉPLOIEMENT"
    
    log "🔍 Validation des services..."
    
    # Vérifier MySQL
    if systemctl is-active --quiet mysql; then
        log "✅ MySQL actif"
    else
        warn "⚠️ MySQL inactif"
    fi
    
    # Vérifier Redis
    if systemctl is-active --quiet redis-server; then
        log "✅ Redis actif"
    else
        warn "⚠️ Redis inactif"
    fi
    
    # Vérifier ntpsec
    if systemctl is-active --quiet ntpsec; then
        log "✅ ntpsec actif"
    else
        warn "⚠️ ntpsec inactif"
    fi
    
    # Vérifier Apache
    if systemctl is-active --quiet apache2; then
        log "✅ Apache actif"
    else
        warn "⚠️ Apache inactif"
    fi
    
    # Vérifier l'application
    if systemctl is-active --quiet $APP_NAME; then
        log "✅ NTP Monitor Enterprise actif"
    else
        warn "⚠️ NTP Monitor Enterprise inactif"
    fi
    
    # Test accès web
    log "🌐 Test d'accès web..."
    sleep 5
    if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200"; then
        log "✅ Application accessible sur http://localhost"
    else
        warn "⚠️ Application non accessible - vérifiez les logs"
    fi
    
    log "✅ Validation terminée"
}

# ============================================================================
# MONITORING ET MAINTENANCE
# ============================================================================

create_monitoring_script() {
    section "CONFIGURATION MONITORING"
    
    log "📊 Création du script de monitoring..."
    
    tee /home/$APP_USER/monitor_ntp.sh > /dev/null << 'EOF'
#!/bin/bash
# Script de monitoring NTP Monitor Enterprise
# Vérifie les services et effectue la maintenance automatique

LOG_FILE="/home/ntp-monitor/logs/monitoring.log"
mkdir -p "$(dirname "$LOG_FILE")"

log_event() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Vérifier et redémarrer les services si nécessaire
for service in ntp-monitor-enterprise mysql redis-server ntpsec apache2; do
    if ! systemctl is-active --quiet $service; then
        log_event "RESTART: Service $service redémarré"
        systemctl start $service
    fi
done

# Nettoyage des anciens logs
find /home/ntp-monitor/ntp-monitor-enterprise/logs -name "*.log" -mtime +30 -delete 2>/dev/null || true

# Vérifier l'accès web
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200"; then
    log_event "ERROR: Application web inaccessible"
fi

# Vérifier ntpsec
if ! ntpq -c peers &>/dev/null; then
    log_event "ERROR: ntpsec ne répond pas"
fi

# Vérifier MySQL
if ! mysqladmin ping &>/dev/null; then
    log_event "ERROR: MySQL ne répond pas"
fi
EOF
    
    chmod +x /home/$APP_USER/monitor_ntp.sh
    chown $APP_USER:$APP_USER /home/$APP_USER/monitor_ntp.sh
    
    # Cron job pour monitoring automatique
    (crontab -u $APP_USER -l 2>/dev/null; echo "*/15 * * * * /home/$APP_USER/monitor_ntp.sh") | crontab -u $APP_USER -
    
    log "✅ Monitoring automatique configuré (toutes les 15 minutes)"
}

# ============================================================================
# AFFICHAGE FINAL
# ============================================================================

display_final_info() {
    section "DÉPLOIEMENT TERMINÉ AVEC SUCCÈS"
    
    echo
    echo "🎉 NTP Monitor Enterprise v2.1.0 déployé avec succès !"
    echo
    echo "=============================================="
    echo "  INFORMATIONS DE CONNEXION"
    echo "=============================================="
    echo
    echo "🌐 URL Application: http://$DOMAIN"
    echo "🌐 URL Locale: http://localhost"
    echo
    echo "👤 Connexion par défaut:"
    echo "   - Utilisateur: admin"
    echo "   - Mot de passe: admin123"
    echo
    echo "=============================================="
    echo "  CONFIGURATION TECHNIQUE"
    echo "=============================================="
    echo
    echo "🐍 Version Python: $PYTHON_VERSION"
    echo "🗄️ Base de données: MySQL ($MYSQL_DB)"
    echo "🕐 Service temps: ntpsec (préservé)"
    echo "🌐 Serveur web: Apache (port 80)"
    echo "📊 Cache: Redis"
    echo "🔧 WSGI: mod_wsgi (système)"
    echo
    echo "=============================================="
    echo "  COMMANDES DE GESTION"
    echo "=============================================="
    echo
    echo "🔧 Gestion du service:"
    echo "   sudo systemctl status $APP_NAME"
    echo "   sudo systemctl restart $APP_NAME"
    echo "   sudo systemctl stop $APP_NAME"
    echo
    echo "📋 Visualisation des logs:"
    echo "   sudo journalctl -u $APP_NAME -f"
    echo "   sudo tail -f /var/log/apache2/${APP_NAME}_error.log"
    echo
    echo "🕐 Vérification ntpsec:"
    echo "   sudo systemctl status ntpsec"
    echo "   ntpq -c peers"
    echo "   ntpq -c associations"
    echo
    echo "🗄️ Gestion MySQL:"
    echo "   sudo mysql -u root"
    echo "   mysql -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DB"
    echo
    echo "=============================================="
    echo "  FICHIERS IMPORTANTS"
    echo "=============================================="
    echo
    echo "📁 Application: $APP_DIR"
    echo "⚙️ Configuration: $APP_DIR/.env"
    echo "🔑 Credentials MySQL: /root/mysql_credentials.txt"
    echo "🌐 Site Apache: /etc/apache2/sites-available/$APP_NAME.conf"
    echo "🔧 Service: /etc/systemd/system/$APP_NAME.service"
    echo "📊 Monitoring: /home/$APP_USER/monitor_ntp.sh"
    echo
    echo "=============================================="
    echo "  DÉPANNAGE"
    echo "=============================================="
    echo
    echo "Si l'application ne répond pas:"
    echo "1. Vérifiez les logs: sudo journalctl -u $APP_NAME -f"
    echo "2. Vérifiez Apache: sudo systemctl status apache2"
    echo "3. Vérifiez MySQL: sudo systemctl status mysql"
    echo "4. Vérifiez Redis: sudo systemctl status redis-server"
    echo "5. Test connectivité: curl -I http://localhost"
    echo
    echo "=============================================="
    
    log "🎉 Installation terminée - Accédez à http://$DOMAIN"
}

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

main() {
    clear
    section "DÉPLOIEMENT NTP MONITOR ENTERPRISE v2.1.0"
    
    log "🚀 Début du déploiement sur Ubuntu avec ntpsec et MySQL"
    
    # Vérifications préalables
    check_root
    check_system_requirements
    
    # Configuration système
    install_system_packages
    configure_ntpsec
    configure_mysql
    configure_services
    
    # Déploiement application
    create_app_user
    deploy_application
    configure_environment
    initialize_database
    
    # Configuration web
    create_wsgi_file
    configure_apache
    create_systemd_service
    
    # Finalisation
    create_monitoring_script
    validate_deployment
    display_final_info
    
    log "🎉 Déploiement terminé avec succès !"
}

# ============================================================================
# EXÉCUTION
# ============================================================================

# Vérifier si le script est appelé directement
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 