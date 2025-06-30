#!/bin/bash
# Script d'installation NTP Monitor Enterprise
# Ubuntu 24.04 + Apache 2.4 + mod_wsgi

set -e

# Configuration
APP_NAME="NTP Monitor Enterprise"
APP_DIR="/var/www/ntp-monitor-enterprise"
APACHE_CONF="/etc/apache2/sites-available/ntp-monitor.conf"

# Utiliser la version Python détectée ou détecter automatiquement
if [ -z "$PYTHON_VERSION" ]; then
    if command -v python3.12 &> /dev/null; then
        PYTHON_VERSION="3.12"
        PYTHON_CMD="python3.12"
    elif command -v python3.11 &> /dev/null; then
        PYTHON_VERSION="3.11"
        PYTHON_CMD="python3.11"
    elif command -v python3.10 &> /dev/null; then
        PYTHON_VERSION="3.10"
        PYTHON_CMD="python3.10"
    elif command -v python3.9 &> /dev/null; then
        PYTHON_VERSION="3.9"
        PYTHON_CMD="python3.9"
    elif command -v python3.8 &> /dev/null; then
        PYTHON_VERSION="3.8"
        PYTHON_CMD="python3.8"
    elif command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
        PYTHON_CMD="python3"
    else
        log_error "Aucune version de Python 3 détectée"
        exit 1
    fi
else
    PYTHON_CMD=${PYTHON_CMD:-python$PYTHON_VERSION}
fi

log_info "Utilisation de Python $PYTHON_VERSION ($PYTHON_CMD)"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Ce script doit être exécuté en tant que root (sudo)"
        exit 1
    fi
}

# Vérifications préliminaires
check_root

log_info "Début de l'installation de $APP_NAME"

# 1. Mise à jour du système
log_info "Mise à jour du système..."
apt update && apt upgrade -y

# 2. Installation des dépendances système (si pas déjà fait)
if [ "$1" != "--python-configured" ]; then
    log_info "Installation des dépendances système..."
    
    # Installation des outils de base
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        apache2 \
        apache2-dev \
        libapache2-mod-wsgi-py3 \
        redis-server \
        sqlite3 \
        ntpsec \
        ntpsec-ntpdate \
        git \
        curl \
        vim \
        htop \
        software-properties-common
    
    # Essayer d'installer des versions spécifiques Python
    apt install -y python$PYTHON_VERSION python$PYTHON_VERSION-venv python$PYTHON_VERSION-dev 2>/dev/null || \
    log_warning "Version Python $PYTHON_VERSION spécifique non disponible, utilisation de python3 système"
    
else
    log_info "Dépendances Python déjà configurées, passage à la suite..."
fi

# 3. Configuration des modules Apache
log_info "Configuration des modules Apache..."
a2enmod wsgi
a2enmod rewrite
a2enmod headers
a2enmod expires
a2enmod deflate
a2enmod ssl

# 4. Création de l'utilisateur et du répertoire application
log_info "Création de l'utilisateur et du répertoire application..."
useradd -r -s /bin/false ntpmonitor || true
mkdir -p $APP_DIR
chown ntpmonitor:ntpmonitor $APP_DIR

# 5. Copie des fichiers de l'application
log_info "Copie des fichiers de l'application..."
if [ -d "/tmp/ntp-monitor-enterprise" ]; then
    cp -r /tmp/ntp-monitor-enterprise/* $APP_DIR/
else
    log_warning "Répertoire source non trouvé, utilisation du répertoire actuel"
    cp -r ./* $APP_DIR/
fi

# 6. Création de l'environnement virtuel Python (si pas déjà fait)
if [ ! -d "$APP_DIR/venv" ]; then
    log_info "Création de l'environnement virtuel Python..."
    cd $APP_DIR
    $PYTHON_CMD -m venv venv
    source venv/bin/activate
    
    # 7. Installation des dépendances Python par étapes
    log_info "Installation des outils de build Python..."
    pip install --upgrade pip setuptools wheel
    pip install --upgrade setuptools-scm build
    log_success "Outils de build installés"
    
    log_info "Installation des dépendances Python essentielles..."
    # Installation des dépendances critiques en premier
    pip install Flask Flask-SQLAlchemy Flask-SocketIO
    pip install Flask-Login Flask-WTF Flask-Migrate
    pip install SQLAlchemy ntplib pytz
    
    log_info "Installation des dépendances avancées..."
    # Installation du reste des dépendances
    pip install redis celery python-dateutil requests psutil python-dotenv
    
    # Installation des dépendances optionnelles (sans échec critique)
    pip install numpy pandas || log_warning "Numpy/Pandas optionnels non installés"
    
    log_success "Toutes les dépendances Python installées"
else
    log_info "Environnement virtuel déjà créé, activation..."
    cd $APP_DIR
    source venv/bin/activate
fi

# 8. Configuration des permissions
log_info "Configuration des permissions..."
chown -R ntpmonitor:www-data $APP_DIR
chmod -R 755 $APP_DIR
chmod -R 644 $APP_DIR/config/*
chmod +x $APP_DIR/app.py
chmod +x $APP_DIR/app.wsgi

# Créer les dossiers nécessaires
mkdir -p $APP_DIR/logs
mkdir -p $APP_DIR/instance
chown -R ntpmonitor:www-data $APP_DIR/logs
chown -R ntpmonitor:www-data $APP_DIR/instance
chmod 775 $APP_DIR/logs
chmod 775 $APP_DIR/instance

# 9. Configuration Apache
log_info "Configuration Apache..."
cp deployment/apache/ntp-monitor.conf $APACHE_CONF

# Adapter les chemins dans la configuration
sed -i "s|/var/www/ntp-monitor-enterprise|$APP_DIR|g" $APACHE_CONF

# Activer le site
a2ensite ntp-monitor.conf
a2dissite 000-default.conf

# 10. Configuration du service Redis
log_info "Configuration du service Redis..."
systemctl enable redis-server
systemctl start redis-server

# 11. Configuration du service NTP
log_info "Configuration du service NTP..."
systemctl enable ntpsec
systemctl start ntpsec

# 12. Initialisation de la base de données (si pas déjà fait)
if [ "$1" != "--python-configured" ]; then
    log_info "Initialisation de la base de données..."
    cd $APP_DIR
    source venv/bin/activate
    
    # Utiliser le script d'initialisation intégré
    python init_database.py init || {
        log_warning "Script init_database.py échoué, utilisation de la méthode alternative..."
        # Méthode alternative
        python3 -c "
from app import create_app
from backend.app import db
from backend.utils.init_data import init_default_data

app = create_app('production')
with app.app_context():
    db.create_all()
    init_default_data()
    print('Base de données initialisée avec succès')
"
    }
else
    log_info "Base de données déjà initialisée, passage à la suite..."
fi

# 13. Configuration du firewall (optionnel)
log_info "Configuration du firewall..."
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow ssh

# 14. Test de la configuration Apache
log_info "Test de la configuration Apache..."
apache2ctl configtest

if [ $? -eq 0 ]; then
    log_success "Configuration Apache valide"
    systemctl restart apache2
    systemctl enable apache2
else
    log_error "Erreur dans la configuration Apache"
    exit 1
fi

# 15. Création d'un service systemd pour les tâches en arrière-plan (optionnel)
log_info "Création du service systemd..."
cat > /etc/systemd/system/ntp-monitor-worker.service << EOF
[Unit]
Description=NTP Monitor Enterprise Worker
After=network.target

[Service]
Type=simple
User=ntpmonitor
Group=www-data
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python app.py worker
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ntp-monitor-worker.service

# 16. Vérifications finales
log_info "Vérifications finales..."

# Test des services
if systemctl is-active --quiet apache2; then
    log_success "Apache2 est actif"
else
    log_error "Apache2 n'est pas actif"
fi

if systemctl is-active --quiet redis-server; then
    log_success "Redis est actif"
else
    log_error "Redis n'est pas actif"
fi

if systemctl is-active --quiet ntpsec; then
    log_success "NTP est actif"
else
    log_error "NTP n'est pas actif"
fi

# Test de connectivité HTTP
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|302"; then
    log_success "Application web accessible"
else
    log_warning "Application web non accessible (normal si configuration SSL uniquement)"
fi

# 17. Affichage des informations finales
log_success "Installation terminée avec succès!"
echo ""
echo -e "${GREEN}=== INFORMATIONS D'ACCÈS ===${NC}"
echo -e "${BLUE}URL Application:${NC} http://localhost ou http://$(hostname -I | awk '{print $1}')"
echo -e "${BLUE}Utilisateur Admin:${NC} admin"
echo -e "${BLUE}Mot de passe Admin:${NC} admin123"
echo ""
echo -e "${GREEN}=== COMMANDES UTILES ===${NC}"
echo -e "${BLUE}Redémarrer Apache:${NC} sudo systemctl restart apache2"
echo -e "${BLUE}Logs Apache:${NC} sudo tail -f /var/log/apache2/ntp-monitor_error.log"
echo -e "${BLUE}Logs Application:${NC} sudo tail -f $APP_DIR/logs/app.log"
echo -e "${BLUE}Status Services:${NC} sudo systemctl status apache2 redis-server ntpsec"
echo ""
echo -e "${GREEN}=== FICHIERS IMPORTANTS ===${NC}"
echo -e "${BLUE}Configuration Apache:${NC} $APACHE_CONF"
echo -e "${BLUE}Répertoire Application:${NC} $APP_DIR"
echo -e "${BLUE}Base de données:${NC} $APP_DIR/ntp_monitor_prod.db"
echo ""
echo -e "${YELLOW}PENSEZ À CHANGER LE MOT DE PASSE ADMINISTRATEUR APRÈS LA PREMIÈRE CONNEXION${NC}"
echo ""
log_success "Installation de $APP_NAME terminée!" 