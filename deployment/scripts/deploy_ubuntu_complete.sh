#!/bin/bash
set -e

# ========================================
# SCRIPT DE DÉPLOIEMENT UBUNTU COMPLET
# NTP Monitor Enterprise - Version corrigée
# ========================================

# Configuration des couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/gilandre/NTPVIZ.git"
BRANCH="MacDev"
APP_DIR="/opt/ntp-monitor"
SERVICE_NAME="ntp-monitor"
DB_NAME="ntp_monitor"
DB_USER="ntp_user"
DB_PASS="NTP_Monitor_2025!"

# Fonctions de logging
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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Fonction de vérification des prérequis
check_prerequisites() {
    log_step "Vérification des prérequis système..."
    
    # Vérifier si on est root
    if [[ $EUID -eq 0 ]]; then
        log_error "Ce script ne doit pas être exécuté en tant que root"
        exit 1
    fi
    
    # Vérifier les commandes essentielles
    command -v git >/dev/null 2>&1 || { log_error "git n'est pas installé"; exit 1; }
    command -v python3 >/dev/null 2>&1 || { log_error "python3 n'est pas installé"; exit 1; }
    command -v pip3 >/dev/null 2>&1 || { log_error "pip3 n'est pas installé"; exit 1; }
    
    log_success "Prérequis système vérifiés"
}

# Fonction d'installation des packages système
install_system_packages() {
    log_step "Installation des packages système..."
    
    sudo apt-get update
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        git \
        curl \
        wget \
        mysql-server \
        mysql-client \
        libmysqlclient-dev \
        build-essential \
        pkg-config \
        libssl-dev \
        libffi-dev
    
    log_success "Packages système installés"
}

# Fonction de configuration MySQL
setup_mysql() {
    log_step "Configuration de MySQL..."
    
    # Démarrer MySQL s'il n'est pas démarré
    sudo systemctl start mysql
    sudo systemctl enable mysql
    
    # Créer la base de données et l'utilisateur
    sudo mysql -e "
        CREATE DATABASE IF NOT EXISTS $DB_NAME;
        CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
        GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
        FLUSH PRIVILEGES;
    "
    
    log_success "MySQL configuré"
}

# Fonction de téléchargement du code source
download_source_code() {
    log_step "Téléchargement du code source depuis GitHub..."
    
    # Créer le répertoire de l'application
    sudo mkdir -p $APP_DIR
    sudo chown $USER:$USER $APP_DIR
    
    # Cloner le repository
    if [ -d "$APP_DIR/.git" ]; then
        log_info "Repository existant détecté, mise à jour..."
        cd $APP_DIR
        git fetch origin
        git reset --hard origin/$BRANCH
        git checkout $BRANCH
    else
        log_info "Clonage du repository..."
        git clone -b $BRANCH $REPO_URL $APP_DIR
        cd $APP_DIR
    fi
    
    log_success "Code source téléchargé depuis GitHub"
}

# Fonction de configuration de l'environnement Python
setup_python_environment() {
    log_step "Configuration de l'environnement Python..."
    
    cd $APP_DIR
    
    # Créer l'environnement virtuel
    python3 -m venv .venv
    source .venv/bin/activate
    
    # Mettre à jour pip
    pip install --upgrade pip setuptools wheel
    
    # Installer les dépendances
    pip install -r requirements.txt
    
    log_success "Environnement Python configuré"
}

# Fonction de configuration de l'environnement
setup_environment() {
    log_step "Configuration de l'environnement..."
    
    cd $APP_DIR
    
    # Copier le fichier de configuration
    if [ ! -f ".env" ]; then
        cp env.example .env
    fi
    
    # Configurer pour la production
    sed -i 's/FLASK_ENV=development/FLASK_ENV=production/' .env
    sed -i 's/DEBUG=True/DEBUG=False/' .env
    sed -i 's/HOST=127.0.0.1/HOST=0.0.0.0/' .env
    
    # Vérifier la configuration
    log_info "Configuration .env:"
    grep -E "(FLASK_ENV|DEBUG|HOST|MYSQL)" .env
    
    log_success "Environnement configuré"
}

# Fonction de correction du schéma de base de données
fix_database_schema() {
    log_step "Correction du schéma de base de données..."
    
    cd $APP_DIR
    source .venv/bin/activate
    
    # Exécuter le script de correction du schéma
    python fix_database_schema.py
    
    if [ $? -eq 0 ]; then
        log_success "Schéma de base de données corrigé"
    else
        log_error "Échec de la correction du schéma"
        exit 1
    fi
}

# Fonction d'harmonisation des modèles
harmonize_models() {
    log_step "Harmonisation des modèles..."
    
    cd $APP_DIR
    source .venv/bin/activate
    
    # Exécuter le script d'harmonisation
    python harmonize_models.py
    
    if [ $? -eq 0 ]; then
        log_success "Modèles harmonisés"
    else
        log_error "Échec de l'harmonisation des modèles"
        exit 1
    fi
}

# Fonction d'initialisation de la base de données
initialize_database() {
    log_step "Initialisation de la base de données..."
    
    cd $APP_DIR
    source .venv/bin/activate
    
    # Exécuter le script d'initialisation
    python initialiser_database.py
    
    if [ $? -eq 0 ]; then
        log_success "Base de données initialisée"
    else
        log_error "Échec de l'initialisation de la base de données"
        exit 1
    fi
}

# Fonction de test de l'application
test_application() {
    log_step "Test de l'application..."
    
    cd $APP_DIR
    source .venv/bin/activate
    
    # Tester la création de l'application
    python -c "from backend.app import create_app; app = create_app(); print('✅ Application créée avec succès')"
    
    if [ $? -eq 0 ]; then
        log_success "Application testée avec succès"
    else
        log_error "Échec du test de l'application"
        exit 1
    fi
}

# Fonction de configuration du firewall
setup_firewall() {
    log_step "Configuration du firewall..."
    
    # Installer ufw si pas présent
    sudo apt-get install -y ufw
    
    # Configurer le firewall
    sudo ufw allow ssh
    sudo ufw allow 5001/tcp
    sudo ufw --force enable
    
    log_success "Firewall configuré"
}

# Fonction de création du service systemd
create_systemd_service() {
    log_step "Création du service systemd..."
    
    # Créer le fichier de service
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=NTP Monitor Enterprise
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/.venv/bin
ExecStart=$APP_DIR/.venv/bin/python $APP_DIR/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # Recharger systemd et activer le service
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    
    log_success "Service systemd créé"
}

# Fonction de démarrage du service
start_service() {
    log_step "Démarrage du service..."
    
    sudo systemctl start $SERVICE_NAME
    sudo systemctl status $SERVICE_NAME --no-pager
    
    log_success "Service démarré"
}

# Fonction de vérification finale
verify_deployment() {
    log_step "Vérification du déploiement..."
    
    # Vérifier que le service fonctionne
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        log_success "Service actif"
    else
        log_error "Service inactif"
        exit 1
    fi
    
    # Vérifier que l'application répond
    sleep 5
    if curl -s http://localhost:5001/ > /dev/null; then
        log_success "Application accessible"
    else
        log_warning "Application non accessible immédiatement"
    fi
    
    # Afficher les informations de connexion
    log_info "Informations de connexion:"
    log_info "  URL: http://$(hostname -I | awk '{print $1}'):5001"
    log_info "  Utilisateur: admin"
    log_info "  Mot de passe: admin123"
    
    log_success "Déploiement vérifié"
}

# Fonction d'affichage des logs
show_logs() {
    log_step "Affichage des logs récents..."
    
    sudo journalctl -u $SERVICE_NAME -n 20 --no-pager
}

# Fonction principale
main() {
    echo -e "${CYAN}"
    echo "=========================================="
    echo "  DÉPLOIEMENT NTP MONITOR ENTERPRISE"
    echo "  Ubuntu 24.04 - Version corrigée"
    echo "=========================================="
    echo -e "${NC}"
    
    # Exécuter les étapes de déploiement
    check_prerequisites
    install_system_packages
    setup_mysql
    download_source_code
    setup_python_environment
    setup_environment
    fix_database_schema
    harmonize_models
    initialize_database
    test_application
    setup_firewall
    create_systemd_service
    start_service
    verify_deployment
    
    echo -e "${GREEN}"
    echo "=========================================="
    echo "  DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!"
    echo "=========================================="
    echo -e "${NC}"
    
    # Afficher les commandes utiles
    echo -e "${YELLOW}Commandes utiles:${NC}"
    echo "  Voir les logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "  Redémarrer: sudo systemctl restart $SERVICE_NAME"
    echo "  Statut: sudo systemctl status $SERVICE_NAME"
    echo "  Arrêter: sudo systemctl stop $SERVICE_NAME"
}

# Gestion des arguments
case "${1:-}" in
    "logs")
        show_logs
        ;;
    "restart")
        sudo systemctl restart $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME
        ;;
    "status")
        sudo systemctl status $SERVICE_NAME
        ;;
    "test")
        test_application
        ;;
    *)
        main
        ;;
esac 