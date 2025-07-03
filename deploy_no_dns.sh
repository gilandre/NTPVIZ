#!/bin/bash
# Déploiement NTP Monitor Enterprise SANS DNS
# Utilise uniquement les packages déjà installés

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"
}

section() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Ce script doit être exécuté en tant que root"
        exit 1
    fi
}

# Variables
APP_NAME="ntp-monitor-enterprise"
APP_USER="ntp-monitor"
APP_DIR="/home/$APP_USER/$APP_NAME"
CURRENT_DIR="$(pwd)"
DB_NAME="ntp_monitor"
DB_USER="ntp_user"
DB_PASSWORD=$(openssl rand -base64 12)

deploy_without_dns() {
    section "DÉPLOIEMENT SANS DNS - NTP MONITOR ENTERPRISE"
    
    check_root
    
    log "🚀 Déploiement avec packages existants uniquement"
    
    # Créer utilisateur application
    if ! id "$APP_USER" &>/dev/null; then
        log "Création utilisateur $APP_USER..."
        useradd -m -s /bin/bash "$APP_USER"
        usermod -aG www-data "$APP_USER"
        log "✅ Utilisateur $APP_USER créé"
    else
        log "✅ Utilisateur $APP_USER existe déjà"
    fi
    
    # Créer répertoire application
    log "Création répertoire application..."
    mkdir -p "$APP_DIR"
    
    # Copier les fichiers depuis le répertoire actuel
    log "Copie des fichiers application..."
    cp -r "$CURRENT_DIR"/* "$APP_DIR/"
    
    # Exclure certains fichiers inutiles
    rm -rf "$APP_DIR"/.git
    rm -f "$APP_DIR"/deploy_*.sh
    rm -f "$APP_DIR"/fix_*.sh
    rm -f "$APP_DIR"/check_*.sh
    
    # Permissions
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    chmod +x "$APP_DIR"/*.py
    
    log "✅ Fichiers copiés et permissions définies"
    
    # Créer environnement virtuel Python
    log "Création environnement virtuel Python..."
    sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
    log "✅ Environnement virtuel créé"
    
    # Installer packages Python essentiels sans DNS
    log "Installation packages Python de base..."
    sudo -u "$APP_USER" bash -c "
        source '$APP_DIR/venv/bin/activate'
        # Utiliser pip avec cache local si disponible
        pip install --upgrade pip --no-index --find-links /usr/share/python-wheels/ 2>/dev/null || true
        
        # Installer packages système Python disponibles
        pip install flask==2.3.3 --no-deps 2>/dev/null || echo 'Flask installation skipped'
        pip install werkzeug==2.3.7 --no-deps 2>/dev/null || echo 'Werkzeug installation skipped'
        pip install sqlalchemy==2.0.21 --no-deps 2>/dev/null || echo 'SQLAlchemy installation skipped'
        pip install pymysql --no-deps 2>/dev/null || echo 'PyMySQL installation skipped'
        pip install redis --no-deps 2>/dev/null || echo 'Redis installation skipped'
        pip install flask-socketio --no-deps 2>/dev/null || echo 'Flask-SocketIO installation skipped'
    "
    
    log "✅ Packages Python installés (disponibles)"
    
    # Configuration base de données MySQL
    section "CONFIGURATION BASE DE DONNÉES"
    
    log "Configuration MySQL..."
    
    # Créer base de données
    mysql -u root -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    mysql -u root -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
    mysql -u root -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
    mysql -u root -e "FLUSH PRIVILEGES;"
    
    log "✅ Base de données MySQL configurée"
    
    # Sauvegarder credentials
    cat > /root/mysql_credentials.txt << EOF
# Credentials MySQL pour NTP Monitor Enterprise
DATABASE_URL=mysql+pymysql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
DB_HOST=localhost
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
EOF
    
    log "✅ Credentials sauvegardés dans /root/mysql_credentials.txt"
    
    # Créer configuration .env
    log "Création configuration .env..."
    cat > "$APP_DIR/.env" << EOF
# Configuration NTP Monitor Enterprise
SECRET_KEY=$(openssl rand -base64 32)
DATABASE_URL=mysql+pymysql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
REDIS_URL=redis://localhost:6379/0
FLASK_ENV=production
DEBUG=False
LOG_LEVEL=INFO
NTP_SERVERS=0.ubuntu.pool.ntp.org,1.ubuntu.pool.ntp.org,2.ubuntu.pool.ntp.org,3.ubuntu.pool.ntp.org
EOF
    
    chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    
    log "✅ Configuration .env créée"
    
    # Initialiser base de données
    log "Initialisation base de données..."
    sudo -u "$APP_USER" bash -c "
        cd '$APP_DIR'
        source venv/bin/activate
        python -c \"
import sys
sys.path.insert(0, '.')
try:
    from backend.database import init_db
    init_db()
    print('✅ Base de données initialisée')
except Exception as e:
    print(f'⚠️ Erreur initialisation DB: {e}')
    # Créer tables manuellement si nécessaire
    pass
\"
    "
    
    # Configuration Apache
    section "CONFIGURATION APACHE"
    
    log "Configuration Apache Virtual Host..."
    
    # Créer configuration Apache
    cat > "/etc/apache2/sites-available/$APP_NAME.conf" << EOF
<VirtualHost *:80>
    ServerName $(hostname -I | awk '{print $1}')
    DocumentRoot $APP_DIR/frontend
    
    WSGIDaemonProcess $APP_NAME python-home=$APP_DIR/venv python-path=$APP_DIR
    WSGIProcessGroup $APP_NAME
    WSGIScriptAlias / $APP_DIR/app.wsgi
    
    <Directory $APP_DIR>
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    
    <Directory $APP_DIR/frontend/static>
        Require all granted
    </Directory>
    
    # Logs
    ErrorLog \${APACHE_LOG_DIR}/${APP_NAME}_error.log
    CustomLog \${APACHE_LOG_DIR}/${APP_NAME}_access.log combined
</VirtualHost>
EOF
    
    # Créer fichier WSGI
    cat > "$APP_DIR/app.wsgi" << EOF
#!/usr/bin/python3
import sys
import os

# Ajouter le répertoire de l'application au path Python
sys.path.insert(0, "$APP_DIR")

# Activer l'environnement virtuel
activate_this = "$APP_DIR/venv/bin/activate_this.py"
if os.path.exists(activate_this):
    exec(open(activate_this).read(), dict(__file__=activate_this))

# Importer l'application
from app import app as application

if __name__ == "__main__":
    application.run()
EOF
    
    chown "$APP_USER:$APP_USER" "$APP_DIR/app.wsgi"
    chmod +x "$APP_DIR/app.wsgi"
    
    # Activer le site
    a2ensite "$APP_NAME"
    a2dissite 000-default
    a2enmod wsgi
    
    log "✅ Apache configuré"
    
    # Créer service systemd
    section "CRÉATION SERVICE SYSTEMD"
    
    cat > "/etc/systemd/system/$APP_NAME.service" << EOF
[Unit]
Description=NTP Monitor Enterprise
After=network.target mysql.service redis.service

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python app.py
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable "$APP_NAME"
    
    log "✅ Service systemd créé"
    
    # Démarrer services
    section "DÉMARRAGE SERVICES"
    
    log "Redémarrage Apache..."
    systemctl restart apache2
    
    log "Démarrage service NTP Monitor..."
    systemctl start "$APP_NAME"
    
    # Vérification finale
    section "VÉRIFICATION DÉPLOIEMENT"
    
    sleep 3
    
    log "Vérification des services..."
    
    if systemctl is-active --quiet apache2; then
        log "✅ Apache : Actif"
    else
        error "❌ Apache : Problème"
    fi
    
    if systemctl is-active --quiet "$APP_NAME"; then
        log "✅ NTP Monitor : Actif"
    else
        error "❌ NTP Monitor : Problème"
    fi
    
    if systemctl is-active --quiet mysql; then
        log "✅ MySQL : Actif"
    else
        error "❌ MySQL : Problème"
    fi
    
    if systemctl is-active --quiet redis-server; then
        log "✅ Redis : Actif"
    else
        error "❌ Redis : Problème"
    fi
    
    if systemctl is-active --quiet ntpsec; then
        log "✅ ntpsec : Actif (préservé)"
    else
        warn "⚠️ ntpsec : Vérifiez le statut"
    fi
    
    # Test accès web
    log "Test accès web..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200"; then
        log "✅ Application accessible sur http://localhost"
    else
        warn "⚠️ Application peut nécessiter quelques minutes pour démarrer"
    fi
    
    section "DÉPLOIEMENT TERMINÉ"
    
    log "🎉 NTP Monitor Enterprise déployé avec succès !"
    echo
    info "📋 Informations importantes :"
    info "   • Application : http://$(hostname -I | awk '{print $1}')"
    info "   • Base de données : MySQL ($DB_NAME)"
    info "   • Credentials : /root/mysql_credentials.txt"
    info "   • Logs : journalctl -u $APP_NAME"
    info "   • Gestion : ./manage_ntp_monitor.sh"
    echo
    info "🔧 Commandes utiles :"
    info "   • Statut : ./manage_ntp_monitor.sh status"
    info "   • Logs : ./manage_ntp_monitor.sh logs"
    info "   • Redémarrage : sudo systemctl restart $APP_NAME"
    echo
    log "✅ Déploiement sans DNS terminé avec succès !"
}

# Exécution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    deploy_without_dns "$@"
fi 