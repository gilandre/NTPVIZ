#!/bin/bash
# ============================================================================
# download_and_install.sh - Téléchargement et installation complète
# Script pour télécharger NTP Monitor Enterprise depuis GitHub et l'installer
# ============================================================================

set -e

# === CONFIGURATION ===
APP_NAME="NTP Monitor Enterprise"
APP_VERSION="2.1.0"
GITHUB_USER="gilandre"
GITHUB_REPO="NTPVIZ"
GITHUB_BRANCH="dev"
INSTALL_DIR="/opt/ntp-monitor-enterprise"
VENV_DIR="/opt/ntp-monitor-venv"
APP_USER="ntp-monitor"
DB_NAME="ntp_monitor"
DB_USER="ntp_user"

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

# === NETTOYAGE PRÉALABLE ===
cleanup_previous() {
    log_info "Nettoyage des installations précédentes..."
    
    # Arrêter services s'ils existent
    systemctl stop apache2 2>/dev/null || true
    systemctl stop ntp-monitor 2>/dev/null || true
    
    # Supprimer répertoires existants
    rm -rf "$INSTALL_DIR" "$VENV_DIR" 2>/dev/null || true
    
    # Supprimer configurations Apache
    a2dissite ntp-monitor 2>/dev/null || true
    rm -f /etc/apache2/sites-available/ntp-monitor.conf 2>/dev/null || true
    
    log_success "Nettoyage terminé"
}

# === TÉLÉCHARGEMENT DEPUIS GITHUB ===
download_from_github() {
    log_info "Téléchargement depuis GitHub..."
    
    # Vérifier la connectivité GitHub
    if ! curl -s --max-time 10 https://github.com >/dev/null; then
        log_error "Impossible de se connecter à GitHub"
        exit 1
    fi
    
    # Créer répertoire temporaire
    local temp_dir="/tmp/ntp-monitor-download"
    rm -rf "$temp_dir"
    mkdir -p "$temp_dir"
    
    log_info "Téléchargement de l'archive depuis GitHub..."
    
    # Télécharger l'archive ZIP de la branche dev
    local download_url="https://github.com/$GITHUB_USER/$GITHUB_REPO/archive/refs/heads/$GITHUB_BRANCH.zip"
    
    if ! curl -L -o "$temp_dir/source.zip" "$download_url"; then
        log_error "Échec du téléchargement depuis $download_url"
        exit 1
    fi
    
    # Vérifier que le fichier a été téléchargé
    if [ ! -f "$temp_dir/source.zip" ] || [ ! -s "$temp_dir/source.zip" ]; then
        log_error "Fichier téléchargé invalide ou vide"
        exit 1
    fi
    
    log_success "Archive téléchargée : $(du -h "$temp_dir/source.zip" | cut -f1)"
    
    # Extraire l'archive
    log_info "Extraction de l'archive..."
    cd "$temp_dir"
    if ! unzip -q source.zip; then
        log_error "Échec de l'extraction de l'archive"
        exit 1
    fi
    
    # Identifier le répertoire extrait
    local extracted_dir=$(find . -maxdepth 1 -type d -name "*$GITHUB_REPO*" | head -n 1)
    if [ -z "$extracted_dir" ]; then
        log_error "Répertoire extrait non trouvé"
        ls -la "$temp_dir/"
        exit 1
    fi
    
    log_info "Répertoire extrait : $extracted_dir"
    
    # Créer le répertoire d'installation
    mkdir -p "$INSTALL_DIR"
    
    # Déplacer le contenu vers le répertoire d'installation
    log_info "Installation des fichiers..."
    cp -r "$extracted_dir"/* "$INSTALL_DIR/"
    
    # Nettoyer le répertoire temporaire
    rm -rf "$temp_dir"
    
    log_success "Téléchargement terminé"
}

# === VÉRIFICATION DES FICHIERS ===
verify_files() {
    log_info "Vérification des fichiers téléchargés..."
    
    # Afficher la structure
    log_info "Structure du projet :"
    ls -la "$INSTALL_DIR/"
    
    # Vérifier les fichiers critiques
    local critical_files=(
        "app.py"
        "requirements.txt"
        "backend/"
        "frontend/"
        "config/"
    )
    
    local missing_files=()
    for file in "${critical_files[@]}"; do
        if [ ! -e "$INSTALL_DIR/$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        log_error "Fichiers manquants : ${missing_files[*]}"
        log_info "Contenu du répertoire :"
        find "$INSTALL_DIR" -type f | head -20
        exit 1
    fi
    
    log_success "Tous les fichiers critiques sont présents"
}

# === INSTALLATION SYSTÈME ===
install_system_packages() {
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
    
    log_success "Packages système installés"
}

# === CONFIGURATION SÉCURITÉ ===
configure_security() {
    log_info "Configuration de la sécurité..."
    
    # Pare-feu
    ufw --force reset >/dev/null 2>&1
    ufw default deny incoming >/dev/null 2>&1
    ufw default allow outgoing >/dev/null 2>&1
    ufw allow 22/tcp >/dev/null 2>&1
    ufw allow 80/tcp >/dev/null 2>&1
    ufw allow 443/tcp >/dev/null 2>&1
    ufw allow 123/udp >/dev/null 2>&1
    ufw --force enable >/dev/null 2>&1
    
    # Fail2ban
    systemctl enable fail2ban >/dev/null 2>&1
    systemctl start fail2ban
    
    log_success "Sécurité configurée"
}

# === CONFIGURATION MYSQL ===
configure_mysql() {
    log_info "Configuration de MySQL..."
    
    # Démarrer MySQL
    systemctl enable mysql >/dev/null 2>&1
    systemctl start mysql
    
    # Génération mot de passe sécurisé
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # Sécurisation automatique
    mysql -e "DELETE FROM mysql.user WHERE User='';" 2>/dev/null || true
    mysql -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');" 2>/dev/null || true
    mysql -e "DROP DATABASE IF EXISTS test;" 2>/dev/null || true
    mysql -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';" 2>/dev/null || true
    mysql -e "FLUSH PRIVILEGES;" 2>/dev/null || true
    
    # Création base de données et utilisateur
    mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null
    mysql -e "DROP USER IF EXISTS '$DB_USER'@'localhost';" 2>/dev/null || true
    mysql -e "CREATE USER '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';" 2>/dev/null
    mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';" 2>/dev/null
    mysql -e "FLUSH PRIVILEGES;" 2>/dev/null
    
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
    
    # Créer répertoire environnement virtuel
    mkdir -p "$VENV_DIR"
    chown "$APP_USER:$APP_USER" "$INSTALL_DIR" "$VENV_DIR"
}

# === INSTALLATION PYTHON ===
install_python_env() {
    log_info "Configuration environnement Python..."
    
    # Créer environnement virtuel
    sudo -u "$APP_USER" python3 -m venv "$VENV_DIR"
    sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel
    
    # Vérifier que requirements.txt existe
    if [ ! -f "$INSTALL_DIR/requirements.txt" ]; then
        log_error "Fichier requirements.txt manquant"
        log_info "Création du fichier requirements.txt..."
        sudo -u "$APP_USER" tee "$INSTALL_DIR/requirements.txt" > /dev/null << 'REQ_EOF'
# === FRAMEWORK FLASK ===
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-SocketIO==5.3.6
Flask-Login==0.6.3
Flask-WTF==1.1.1
Flask-Migrate==4.0.5
Flask-Cors==4.0.0
Flask-Limiter==3.5.0

# === COMPATIBILITÉ PYTHON 3.12 ===
setuptools>=69.0.2
pip>=23.3.1
wheel>=0.42.0

# === BASE DE DONNÉES ===
SQLAlchemy==2.0.21
PyMySQL==1.1.0
mysqlclient>=2.1.1
alembic==1.12.0

# === WEBSOCKET ET TEMPS RÉEL ===
python-socketio==5.9.0
python-engineio==4.7.1
eventlet==0.33.3
greenlet==2.0.2

# === NTP ET MONITORING ===
ntplib==0.4.0
psutil==5.9.5
requests==2.31.0
urllib3==2.0.4

# === CACHE ET SESSIONS ===
redis==5.0.0
Flask-Session==0.5.0
cachetools==5.3.1

# === SÉCURITÉ ===
Werkzeug==2.3.7
bcrypt==4.0.1
cryptography==41.0.4
PyJWT==2.8.0

# === UTILITAIRES ===
python-dateutil==2.8.2
pytz==2023.3
click==8.1.7
itsdangerous==2.1.2
MarkupSafe==2.1.3
Jinja2==3.1.2

# === DÉVELOPPEMENT ===
python-dotenv==1.0.0
WTForms==3.0.1
email-validator==2.0.0
REQ_EOF
    fi
    
    # Installation des dépendances
    log_info "Installation des dépendances Python..."
    sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
    
    log_success "Environnement Python configuré"
}

# === CONFIGURATION APPLICATION ===
configure_application() {
    log_info "Configuration de l'application..."
    
    # Génération clé secrète
    local secret_key=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)
    
    # Création fichier .env
    sudo -u "$APP_USER" tee "$INSTALL_DIR/.env" > /dev/null << ENV_EOF
# === CONFIGURATION PRODUCTION ===
FLASK_ENV=production
DEBUG=false
SECRET_KEY=$secret_key
HOST=0.0.0.0
PORT=5000

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
ENV_EOF
    
    # Créer répertoires logs
    mkdir -p /var/log/ntp-monitor
    chown "$APP_USER:$APP_USER" /var/log/ntp-monitor
    
    log_success "Application configurée"
}

# === INITIALISATION BASE DE DONNÉES ===
initialize_database() {
    log_info "Initialisation de la base de données..."
    
    cd "$INSTALL_DIR"
    
    # Chercher script d'initialisation
    if [ -f "init_database.py" ]; then
        sudo -u "$APP_USER" "$VENV_DIR/bin/python" init_database.py
    elif [ -f "backend/utils/init_data.py" ]; then
        sudo -u "$APP_USER" "$VENV_DIR/bin/python" backend/utils/init_data.py
    else
        log_warning "Script d'initialisation non trouvé, création basique..."
        # Créer un script d'initialisation basique
        sudo -u "$APP_USER" tee "$INSTALL_DIR/init_basic.py" > /dev/null << 'INIT_EOF'
#!/usr/bin/env python3
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')

db = SQLAlchemy(app)

# Modèles basiques
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class NTPServer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45))
    port = db.Column(db.Integer, default=123)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

def init_db():
    with app.app_context():
        db.create_all()
        
        # Utilisateur admin
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@localhost',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            
        # Serveurs NTP par défaut
        servers = ['pool.ntp.org', 'time.google.com', 'time.cloudflare.com']
        for server in servers:
            if not NTPServer.query.filter_by(hostname=server).first():
                ntp_server = NTPServer(hostname=server)
                db.session.add(ntp_server)
                
        db.session.commit()
        print("✅ Base de données initialisée")

if __name__ == "__main__":
    init_db()
INIT_EOF
        sudo -u "$APP_USER" "$VENV_DIR/bin/python" init_basic.py
    fi
    
    log_success "Base de données initialisée"
}

# === CONFIGURATION APACHE ===
configure_apache() {
    log_info "Configuration d'Apache..."
    
    # Créer fichier WSGI
    sudo -u "$APP_USER" tee "$INSTALL_DIR/app.wsgi" > /dev/null << 'WSGI_EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/opt/ntp-monitor-enterprise')
activate_this = '/opt/ntp-monitor-venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})
from app import app as application
WSGI_EOF
    
    # Configuration Apache
    tee /etc/apache2/sites-available/ntp-monitor.conf > /dev/null << APACHE_EOF
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
APACHE_EOF
    
    # Activer site
    a2ensite ntp-monitor >/dev/null 2>&1
    a2enmod wsgi >/dev/null 2>&1
    a2dissite 000-default >/dev/null 2>&1
    systemctl reload apache2
    
    log_success "Apache configuré"
}

# === DÉMARRAGE SERVICES ===
start_services() {
    log_info "Démarrage des services..."
    
    # Démarrer services
    systemctl enable apache2 mysql redis-server >/dev/null 2>&1
    systemctl start apache2 mysql redis-server
    
    log_success "Services démarrés"
}

# === VÉRIFICATION FINALE ===
verify_installation() {
    log_info "Vérification de l'installation..."
    
    # Vérifier services
    local services=("apache2" "mysql" "redis-server")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log_success "Service $service actif"
        else
            log_error "Service $service inactif"
        fi
    done
    
    # Vérifier interface web
    sleep 5
    if curl -s --max-time 10 http://localhost | grep -q "html\|body\|NTP" 2>/dev/null; then
        log_success "Interface web accessible"
    else
        log_warning "Interface web non accessible - vérifiez les logs"
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
    echo "   • Logs Apache : sudo tail -f /var/log/apache2/ntp-monitor_error.log"
    echo "   • Test direct : cd $INSTALL_DIR && sudo -u $APP_USER $VENV_DIR/bin/python app.py"
    echo "   • Restart     : sudo systemctl restart apache2"
    echo "   • Statut      : sudo systemctl status apache2 mysql redis-server"
    echo
    echo "📚 Documentation :"
    echo "   • Fichiers    : ls -la $INSTALL_DIR/"
    echo "   • Config      : cat $INSTALL_DIR/.env"
    echo "   • Logs        : /var/log/ntp-monitor/"
    echo
    log_success "Installation terminée avec succès ! Accédez à http://$server_ip"
}

# === FONCTION PRINCIPALE ===
main() {
    log_title "🚀 Installation $APP_NAME v$APP_VERSION"
    echo
    log_info "Téléchargement et installation depuis GitHub..."
    echo
    
    check_root
    cleanup_previous
    download_from_github
    verify_files
    install_system_packages
    configure_security
    configure_mysql
    create_user
    install_python_env
    configure_application
    initialize_database
    configure_apache
    start_services
    verify_installation
    show_summary
    
    log_success "🎉 Installation terminée avec succès !"
}

# === GESTION D'ERREURS ===
trap 'log_error "Installation interrompue à la ligne $LINENO"; exit 1' ERR

# === POINT D'ENTRÉE ===
main "$@" 