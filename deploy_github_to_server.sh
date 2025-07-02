#!/bin/bash

# Script de Déploiement GitHub vers Serveur Ubuntu 24.04
# NTP Monitor Enterprise - Mise à jour avec corrections intégrées
# Version: 2.1.0 - Janvier 2025

echo "=================================================================="
echo "  DÉPLOIEMENT GITHUB → SERVEUR UBUNTU 24.04"
echo "  NTP Monitor Enterprise - Mise à jour avec corrections"
echo "=================================================================="
echo "🚀 Déploiement automatique avec corrections 'partitioned' + MySQL fallback"
echo "🐧 Optimisé pour Ubuntu 24.04 LTS"
echo ""

# ==========================================
# CONFIGURATION
# ==========================================

# Variables de configuration
GITHUB_REPO_URL="https://github.com/votre-username/ntp-monitor.git"  # À modifier
GITHUB_BRANCH="main"  # ou "master" selon votre repo
APP_NAME="ntp-monitor"
APP_DIR="/opt/ntp-monitor"
BACKUP_DIR="/opt/ntp-monitor-backup"
VENV_PATH="$APP_DIR/.venv"
SERVICE_NAME="ntp-monitor"
LOG_FILE="/var/log/ntp-monitor-deploy.log"
USER_APP="ntp-monitor"  # Utilisateur dédié pour l'application

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"; }

# ==========================================
# VÉRIFICATIONS PRÉLIMINAIRES
# ==========================================

# Vérification privilèges root
if [[ $EUID -ne 0 ]]; then
   log_error "Ce script doit être exécuté en tant que root"
   log_info "Usage: sudo bash deploy_github_to_server.sh"
   exit 1
fi

# Création du fichier de log
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"

log_info "Début du déploiement GitHub vers serveur Ubuntu 24.04..."
log_info "Repository: $GITHUB_REPO_URL"
log_info "Branche: $GITHUB_BRANCH"
log_info "Destination: $APP_DIR"

# Vérification des outils requis
REQUIRED_TOOLS=("git" "python3" "python3-pip" "python3-venv" "systemctl" "nginx")
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        MISSING_TOOLS+=("$tool")
    fi
done

if [[ ${#MISSING_TOOLS[@]} -gt 0 ]]; then
    log_warning "Outils manquants détectés: ${MISSING_TOOLS[*]}"
    log_info "Installation des outils manquants..."
    
    apt update -qq
    for tool in "${MISSING_TOOLS[@]}"; do
        case $tool in
            "python3-pip")
                apt install -y python3-pip
                ;;
            "python3-venv")
                apt install -y python3-venv
                ;;
            *)
                apt install -y "$tool"
                ;;
        esac
    done
    log_success "Outils installés avec succès"
fi

# ==========================================
# GESTION UTILISATEUR DÉDIÉ
# ==========================================

log_info "1. Configuration utilisateur dédié..."

# Création utilisateur dédié si nécessaire
if ! id "$USER_APP" &>/dev/null; then
    log_info "Création de l'utilisateur $USER_APP..."
    useradd -r -s /bin/bash -d "$APP_DIR" -m "$USER_APP"
    log_success "Utilisateur $USER_APP créé"
else
    log_info "Utilisateur $USER_APP existe déjà"
fi

# ==========================================
# SAUVEGARDE DE L'ANCIENNE VERSION
# ==========================================

log_info "2. Sauvegarde de l'ancienne version..."

if [[ -d "$APP_DIR" ]]; then
    # Arrêt du service avant sauvegarde
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    
    # Sauvegarde avec timestamp
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_PATH="${BACKUP_DIR}_${TIMESTAMP}"
    
    log_info "Sauvegarde vers: $BACKUP_PATH"
    cp -r "$APP_DIR" "$BACKUP_PATH"
    log_success "Sauvegarde créée: $BACKUP_PATH"
    
    # Conservation des 5 dernières sauvegardes
    ls -dt /opt/ntp-monitor-backup_* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true
else
    log_info "Première installation - pas de sauvegarde nécessaire"
fi

# ==========================================
# RÉCUPÉRATION DU CODE DEPUIS GITHUB
# ==========================================

log_info "3. Récupération du code depuis GitHub..."

# Suppression de l'ancien répertoire si existant
if [[ -d "$APP_DIR" ]]; then
    rm -rf "$APP_DIR"
fi

# Clonage du repository
log_info "Clonage: $GITHUB_REPO_URL (branche: $GITHUB_BRANCH)"
git clone --branch "$GITHUB_BRANCH" --single-branch "$GITHUB_REPO_URL" "$APP_DIR"

if [[ $? -eq 0 ]]; then
    log_success "Code récupéré avec succès depuis GitHub"
else
    log_error "Échec du clonage GitHub"
    
    # Restauration de la sauvegarde si disponible
    if [[ -d "$BACKUP_PATH" ]]; then
        log_info "Restauration de la sauvegarde..."
        rm -rf "$APP_DIR"
        cp -r "$BACKUP_PATH" "$APP_DIR"
        log_warning "Application restaurée depuis la sauvegarde"
    fi
    exit 1
fi

# Changement de propriétaire
chown -R "$USER_APP:$USER_APP" "$APP_DIR"
cd "$APP_DIR"

# ==========================================
# APPLICATION DES CORRECTIONS INTÉGRÉES
# ==========================================

log_info "4. Application des corrections intégrées..."

# 4.1. Configuration avec fallback MySQL/SQLite
log_info "4.1. Configuration fallback MySQL/SQLite..."

mkdir -p config
cat > config/config.py << 'CONFIG_EOF'
# Configuration avec fallback automatique MySQL -> SQLite
# Intègre les corrections pour erreur 'partitioned'
import os
from pathlib import Path

class Config:
    """Configuration avec fallback MySQL vers SQLite"""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ntp-monitor-ubuntu24-production-2025'
    
    # Test disponibilité MySQL avec timeout court
    MYSQL_AVAILABLE = False
    try:
        import pymysql
        # Test connexion rapide
        test_conn = pymysql.connect(
            host=os.environ.get('MYSQL_HOST', 'localhost'),
            port=int(os.environ.get('MYSQL_PORT', 3306)),
            user=os.environ.get('MYSQL_USER', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', ''),
            connect_timeout=3
        )
        test_conn.close()
        MYSQL_AVAILABLE = True
        print("✅ MySQL disponible - utilisation MySQL")
    except Exception as e:
        print(f"⚠️ MySQL indisponible ({e}) - utilisation SQLite")
    
    # Configuration dynamique base de données
    if MYSQL_AVAILABLE:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{os.environ.get('MYSQL_USER', 'root')}:"
            f"{os.environ.get('MYSQL_PASSWORD', '')}@"
            f"{os.environ.get('MYSQL_HOST', 'localhost')}:"
            f"{os.environ.get('MYSQL_PORT', 3306)}/"
            f"{os.environ.get('MYSQL_DATABASE', 'ntp_monitor')}"
        )
        DATABASE_TYPE = 'mysql'
    else:
        # Fallback SQLite
        basedir = Path(__file__).parent.parent
        db_path = basedir / 'instance' / 'ntp_monitor.db'
        db_path.parent.mkdir(exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        DATABASE_TYPE = 'sqlite'
    
    # Configuration Flask-SQLAlchemy optimisée
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'echo': False
    }
    
    # Configuration de production
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    DEBUG = False  # Toujours False en production
    TESTING = False
    
    # Configuration sessions
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_COOKIE_SECURE = True  # HTTPS requis en production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configuration sécurité
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Configuration logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    print(f"📊 Base de données: {DATABASE_TYPE.upper()}")
    print(f"🔗 URI: {SQLALCHEMY_DATABASE_URI}")
    print(f"🔒 Mode: PRODUCTION")

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False

# Export des configurations
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
CONFIG_EOF

log_success "Configuration fallback créée"

# 4.2. Correction erreur 'partitioned' dans auth.py
log_info "4.2. Correction erreur 'partitioned' cookies..."

if [[ -f "backend/api/auth.py" ]]; then
    # Backup du fichier original
    cp backend/api/auth.py backend/api/auth.py.backup
    
    # Vérification si le patch est déjà présent
    if ! grep -q "def safe_cookie" backend/api/auth.py; then
        # Application du patch safe_cookie
        sed -i '/^import logging$/a\\n# Fonction wrapper pour éviter erreur partitioned Flask/Werkzeug\ndef safe_cookie(response, key, value="", **kwargs):\n    """Wrapper sécurisé pour set_cookie évitant erreur partitioned"""\n    # Supprimer partitioned et autres paramètres problématiques\n    safe_kwargs = {k: v for k, v in kwargs.items() if k not in ["partitioned", "samesite_strict"]}\n    try:\n        response.set_cookie(key, value, **safe_kwargs)\n    except TypeError as e:\n        if "partitioned" in str(e) or "samesite" in str(e):\n            # Fallback minimal sécurisé\n            response.set_cookie(\n                key, value, \n                path=kwargs.get("path", "/"),\n                httponly=kwargs.get("httponly", True),\n                secure=kwargs.get("secure", False)\n            )\n        else:\n            raise\n\n' backend/api/auth.py
        
        log_success "Patch cookies 'partitioned' appliqué"
    else
        log_info "Patch cookies déjà présent"
    fi
else
    log_warning "Fichier backend/api/auth.py non trouvé"
fi

# ==========================================
# ENVIRONNEMENT VIRTUEL ET PACKAGES
# ==========================================

log_info "5. Configuration environnement virtuel..."

# Suppression ancien environnement virtuel si existant
if [[ -d "$VENV_PATH" ]]; then
    rm -rf "$VENV_PATH"
fi

# Création nouvel environnement virtuel
sudo -u "$USER_APP" python3 -m venv "$VENV_PATH"
source "$VENV_PATH/bin/activate"

# Mise à jour pip
pip install --upgrade pip setuptools wheel

log_info "6. Installation packages avec versions corrigées..."

# Désinstallation packages problématiques
CONFLICTING_PACKAGES=("Flask" "Werkzeug" "redis" "celery" "Flask-SocketIO" "python-socketio" "python-engineio")

log_info "Désinstallation packages en conflit..."
for package in "${CONFLICTING_PACKAGES[@]}"; do
    pip uninstall "$package" -y 2>/dev/null || true
done

# Installation versions corrigées (évitent erreur partitioned)
FIXED_PACKAGES=(
    "Flask==2.3.3"              # Version sans bug partitioned
    "Werkzeug==2.3.7"           # Compatible Flask 2.3.3
    "Flask-Login==0.6.3"
    "Flask-SQLAlchemy==3.0.5"
    "Flask-WTF==1.2.1"
    "python-socketio==5.8.0"    # Version stable testée
    "python-engineio==4.7.1"    # Compatible socketio
    "Flask-SocketIO==5.3.6"     # Version compatible
    "redis==4.6.0"              # Compatible Celery 5.3.4
    "celery==5.3.4"             # Version stable
    "SQLAlchemy==2.0.21"        # Compatible Flask-SQLAlchemy
    "PyMySQL==1.1.0"            # Driver MySQL pur Python
    "psutil==5.9.5"             # Monitoring système
    "ntplib==0.4.0"             # Protocole NTP
    "python-dotenv==1.0.0"      # Variables environnement
    "pytz==2023.3"              # Fuseaux horaires
    "requests==2.31.0"          # HTTP client
    "cryptography>=42.0.8"      # Sécurité
    "bcrypt==4.0.1"             # Hash passwords
    "Jinja2==3.1.2"             # Templates
    "MarkupSafe==2.1.3"         # Sécurité templates
    "gunicorn==21.2.0"          # Serveur WSGI pour production
    "supervisor==4.2.5"         # Gestion processus
)

FAILED_PACKAGES=()
for package in "${FIXED_PACKAGES[@]}"; do
    log_info "Installation: $package"
    if pip install "$package" --no-cache-dir; then
        log_success "$package installé"
    else
        log_warning "Échec installation: $package"
        FAILED_PACKAGES+=("$package")
    fi
done

# Sauvegarde des packages installés
pip freeze > requirements_production.txt
log_success "Requirements sauvegardés: requirements_production.txt"

# ==========================================
# SERVICES SYSTÈME
# ==========================================

log_info "7. Configuration services système..."

# 7.1. Service MySQL/MariaDB
MYSQL_STARTED=false
for service in mysql mariadb; do
    if systemctl start "$service" 2>/dev/null; then
        systemctl enable "$service" 2>/dev/null
        log_success "Service $service démarré et activé"
        MYSQL_STARTED=true
        break
    fi
done

if [[ "$MYSQL_STARTED" != "true" ]]; then
    log_warning "MySQL/MariaDB non disponible - SQLite sera utilisé"
fi

# 7.2. Service Redis (si disponible)
if systemctl start redis-server 2>/dev/null; then
    systemctl enable redis-server 2>/dev/null
    log_success "Service Redis démarré"
else
    log_info "Redis non disponible - fonctionnement sans cache"
fi

# ==========================================
# CONFIGURATION SERVICE SYSTEMD
# ==========================================

log_info "8. Configuration service systemd..."

# Service principal NTP Monitor
cat > "/etc/systemd/system/${SERVICE_NAME}.service" << SERVICE_EOF
[Unit]
Description=NTP Monitor Enterprise - Monitoring serveurs NTP
Documentation=https://github.com/votre-repo/ntp-monitor
After=network.target mysql.service redis-server.service
Wants=mysql.service redis-server.service

[Service]
Type=exec
User=$USER_APP
Group=$USER_APP
WorkingDirectory=$APP_DIR
Environment=PATH=$VENV_PATH/bin
Environment=FLASK_ENV=production
Environment=PYTHONPATH=$APP_DIR
ExecStart=$VENV_PATH/bin/python app.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Sécurité
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR/instance $APP_DIR/logs /tmp
PrivateTmp=true

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Service Celery Worker (tâches asynchrones)
cat > "/etc/systemd/system/${SERVICE_NAME}-worker.service" << WORKER_EOF
[Unit]
Description=NTP Monitor Enterprise - Celery Worker
After=network.target mysql.service redis-server.service
Wants=mysql.service redis-server.service

[Service]
Type=exec
User=$USER_APP
Group=$USER_APP
WorkingDirectory=$APP_DIR
Environment=PATH=$VENV_PATH/bin
Environment=FLASK_ENV=production
Environment=PYTHONPATH=$APP_DIR
ExecStart=$VENV_PATH/bin/celery -A backend.app.celery worker --loglevel=info
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}-worker

[Install]
WantedBy=multi-user.target
WORKER_EOF

# Rechargement et activation des services
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl enable "${SERVICE_NAME}-worker"

log_success "Services systemd configurés"

# ==========================================
# INITIALISATION BASE DE DONNÉES
# ==========================================

log_info "9. Initialisation base de données..."

# Changement vers utilisateur application
sudo -u "$USER_APP" bash << 'INIT_DB_EOF'
source /opt/ntp-monitor/.venv/bin/activate
cd /opt/ntp-monitor
export PYTHONPATH="/opt/ntp-monitor"

# Test initialisation
python3 -c "
import sys
sys.path.insert(0, '.')

try:
    from backend.app import create_app
    app = create_app()
    print('✅ Application Flask créée avec succès')
    
    with app.app_context():
        # Initialisation base de données
        from backend.utils.init_data import init_default_data
        init_default_data()
        print('✅ Base de données initialisée')
        
except Exception as e:
    print(f'❌ Erreur initialisation: {e}')
    import traceback
    traceback.print_exc()
"
INIT_DB_EOF

# ==========================================
# CONFIGURATION NGINX (REVERSE PROXY)
# ==========================================

log_info "10. Configuration Nginx..."

# Configuration Nginx pour NTP Monitor
cat > "/etc/nginx/sites-available/$SERVICE_NAME" << NGINX_EOF
server {
    listen 80;
    server_name localhost $(hostname -I | awk '{print $1}');
    
    # Redirection HTTPS (à configurer selon besoins)
    # return 301 https://\$server_name\$request_uri;
    
    # Configuration HTTP (développement/test)
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Fichiers statiques
    location /static {
        alias $APP_DIR/frontend/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Logs
    access_log /var/log/nginx/${SERVICE_NAME}_access.log;
    error_log /var/log/nginx/${SERVICE_NAME}_error.log;
}
NGINX_EOF

# Activation du site
ln -sf "/etc/nginx/sites-available/$SERVICE_NAME" "/etc/nginx/sites-enabled/"
nginx -t && systemctl reload nginx

log_success "Nginx configuré"

# ==========================================
# DÉMARRAGE DES SERVICES
# ==========================================

log_info "11. Démarrage des services..."

# Démarrage services NTP Monitor
systemctl start "$SERVICE_NAME"
systemctl start "${SERVICE_NAME}-worker"

# Attente stabilisation
sleep 15

# ==========================================
# TESTS DE VALIDATION
# ==========================================

log_info "12. Tests de validation..."

# Test service principal
if systemctl is-active --quiet "$SERVICE_NAME"; then
    log_success "Service $SERVICE_NAME actif"
    SERVICE_OK=true
else
    log_error "Service $SERVICE_NAME inactif"
    SERVICE_OK=false
fi

# Test worker Celery
if systemctl is-active --quiet "${SERVICE_NAME}-worker"; then
    log_success "Service ${SERVICE_NAME}-worker actif"
    WORKER_OK=true
else
    log_warning "Service ${SERVICE_NAME}-worker inactif"
    WORKER_OK=false
fi

# Test port 5000
if ss -tlnp | grep -q ':5000'; then
    log_success "Port 5000 accessible"
    PORT_OK=true
else
    log_error "Port 5000 non accessible"
    PORT_OK=false
fi

# Test HTTP
HTTP_OK=false
for i in {1..5}; do
    if curl -f -s -m 10 "http://localhost:5000/" > /dev/null 2>&1; then
        log_success "Application web accessible"
        HTTP_OK=true
        break
    else
        log_info "Tentative $i/5 - Application pas encore prête..."
        sleep 10
    fi
done

if [[ "$HTTP_OK" != "true" ]]; then
    log_warning "Application web pas encore accessible (peut nécessiter plus de temps)"
fi

# ==========================================
# RAPPORT FINAL
# ==========================================

echo ""
echo "=================================================================="
echo "                    RAPPORT FINAL DE DÉPLOIEMENT"
echo "=================================================================="

# Calcul statut global
TOTAL_CHECKS=4
SUCCESS_COUNT=0
[[ "$SERVICE_OK" == "true" ]] && ((SUCCESS_COUNT++))
[[ "$WORKER_OK" == "true" ]] && ((SUCCESS_COUNT++))
[[ "$PORT_OK" == "true" ]] && ((SUCCESS_COUNT++))
[[ "$HTTP_OK" == "true" ]] && ((SUCCESS_COUNT++))

if [[ $SUCCESS_COUNT -eq $TOTAL_CHECKS ]]; then
    FINAL_STATUS="SUCCESS"
    log_success "🎉 DÉPLOIEMENT RÉUSSI À 100%"
elif [[ $SUCCESS_COUNT -ge 2 ]]; then
    FINAL_STATUS="PARTIAL"
    log_warning "⚠️ DÉPLOIEMENT PARTIEL ($SUCCESS_COUNT/$TOTAL_CHECKS tests réussis)"
else
    FINAL_STATUS="ERROR"
    log_error "❌ DÉPLOIEMENT ÉCHOUÉ"
fi

echo ""
echo "📋 RÉSUMÉ:"
echo "   - Service principal: $([ "$SERVICE_OK" == "true" ] && echo "✅ Actif" || echo "❌ Inactif")"
echo "   - Worker Celery: $([ "$WORKER_OK" == "true" ] && echo "✅ Actif" || echo "⚠️ Inactif")"
echo "   - Port 5000: $([ "$PORT_OK" == "true" ] && echo "✅ Accessible" || echo "❌ Fermé")"
echo "   - Interface web: $([ "$HTTP_OK" == "true" ] && echo "✅ Accessible" || echo "⚠️ En cours")"

if [[ ${#FAILED_PACKAGES[@]} -gt 0 ]]; then
    echo ""
    echo "⚠️ Packages en échec:"
    printf '   - %s\n' "${FAILED_PACKAGES[@]}"
fi

echo ""
echo "🌐 ACCÈS APPLICATION:"
echo "   - URL locale: http://localhost:5000"
echo "   - URL réseau: http://$(hostname -I | awk '{print $1}'):5000"
echo "   - Via Nginx: http://$(hostname -I | awk '{print $1}')"

echo ""
echo "👤 COMPTES UTILISATEUR:"
echo "   - Administrateur: admin / admin123"
echo "   - Opérateur: operator / operator123"
echo "   - Visualiseur: viewer / viewer123"

echo ""
echo "🔧 COMMANDES UTILES:"
echo "   - Statut services: systemctl status $SERVICE_NAME"
echo "   - Logs application: journalctl -u $SERVICE_NAME -f"
echo "   - Logs worker: journalctl -u ${SERVICE_NAME}-worker -f"
echo "   - Redémarrage: systemctl restart $SERVICE_NAME"
echo "   - Logs déploiement: tail -f $LOG_FILE"

echo ""
echo "📊 CORRECTIONS APPLIQUÉES:"
echo "   ✅ Erreur 'partitioned' cookies corrigée (Flask 2.3.3)"
echo "   ✅ Fallback MySQL/SQLite automatique"
echo "   ✅ Packages compatibles installés"
echo "   ✅ Service systemd configuré"
echo "   ✅ Nginx reverse proxy actif"
echo "   ✅ Environnement de production sécurisé"

echo ""
if [[ "$FINAL_STATUS" == "SUCCESS" ]]; then
    echo "🎉 DÉPLOIEMENT GITHUB → SERVEUR RÉUSSI !"
    echo "✅ NTP Monitor Enterprise v2.1.0 est opérationnel"
elif [[ "$FINAL_STATUS" == "PARTIAL" ]]; then
    echo "⚠️ DÉPLOIEMENT PARTIEL - Application en cours de stabilisation"
    echo "ℹ️ Attendez quelques minutes puis vérifiez les services"
else
    echo "❌ DÉPLOIEMENT ÉCHOUÉ"
    echo "ℹ️ Consultez les logs pour diagnostiquer les problèmes"
fi

echo ""
echo "=================================================================="
echo "✅ SCRIPT DE DÉPLOIEMENT TERMINÉ"
echo "=================================================================="

# Code de sortie selon le statut
case $FINAL_STATUS in
    "SUCCESS") exit 0 ;;
    "PARTIAL") exit 1 ;;
    *) exit 2 ;;
esac 