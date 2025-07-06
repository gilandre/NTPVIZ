#!/usr/bin/env bash
# ============================================================================
# start_ntp_monitor.sh — Démarrage NTP Monitor Enterprise
# Script de démarrage optimisé pour environnement local
# ============================================================================

set -u

# --- COULEURS -----------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# --- CONFIGURATION ------------------------------------------------------------
APP_NAME="NTP Monitor Enterprise"
APP_VERSION="1.0.0"
DEFAULT_HOST="127.0.0.1"
DEFAULT_PORT="5000"
PYTHON_CMD="python3"
ENV_FILE=".env"
VENV_DIR="/opt/ntp-monitor-venv"

# --- FONCTIONS DE LOG --------------------------------------------------------
info()    { echo -e "${BLUE}ℹ️  $*${NC}"; }
success() { echo -e "${GREEN}✅ $*${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $*${NC}"; }
error()   { echo -e "${RED}❌ $*${NC}"; }
title()   { echo -e "${WHITE}$*${NC}"; }

# --- FONCTION DE VÉRIFICATION DES PRÉREQUIS ----------------------------------
check_prerequisites() {
    info "Vérification des prérequis..."
    
    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 n'est pas installé"
        return 1
    fi
    
    local python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    success "Python $python_version détecté"
    
    # Vérifier l'environnement virtuel
    if [ -d "$VENV_DIR" ]; then
        success "Environnement virtuel trouvé: $VENV_DIR"
        PYTHON_CMD="$VENV_DIR/bin/python"
    else
        warning "Environnement virtuel non trouvé, utilisation Python système"
    fi
    
    # Vérifier les services
    local services=("mysql" "redis-server" "apache2" "ntpsec")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            success "Service $service actif"
        else
            warning "Service $service inactif"
        fi
    done
    
    return 0
}

# --- FONCTION DE CONFIGURATION ENVIRONNEMENT --------------------------------
setup_environment() {
    info "Configuration de l'environnement..."
    
    # Créer .env s'il n'existe pas
    if [ ! -f "$ENV_FILE" ]; then
        warning "Fichier .env non trouvé, création depuis .env.example"
        if [ -f ".env.example" ]; then
            cp .env.example .env
            success "Fichier .env créé depuis .env.example"
        else
            info "Création d'un fichier .env de base..."
            cat > .env << 'EOF'
# Configuration NTP Monitor Enterprise
FLASK_ENV=production
SECRET_KEY=ntp-monitor-local-dev-key
DEBUG=false
HOST=127.0.0.1
PORT=5000

# Base de données
DATABASE_URL=mysql+pymysql://root:@localhost/ntp_monitor

# NTP Configuration
DEFAULT_NTP_SERVERS=pool.ntp.org,time.google.com,time.cloudflare.com
LOCAL_NTP_SERVERS=192.168.1.100,10.0.0.50

# Alertes
ALERT_OFFSET_THRESHOLD=100
ALERT_DELAY_THRESHOLD=500

# Redis
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_TO_STDOUT=true
EOF
            success "Fichier .env de base créé"
        fi
    else
        success "Fichier .env trouvé"
    fi
    
    # Créer les répertoires nécessaires
    mkdir -p logs instance
    
    # Charger les variables d'environnement
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' .env | xargs)
        success "Variables d'environnement chargées"
    fi
    
    # Définir les variables par défaut
    export HOST="${HOST:-$DEFAULT_HOST}"
    export PORT="${PORT:-$DEFAULT_PORT}"
    export FLASK_ENV="${FLASK_ENV:-production}"
    export SECRET_KEY="${SECRET_KEY:-ntp-monitor-default-key}"
}

# --- FONCTION DE VÉRIFICATION BASE DE DONNÉES -------------------------------
check_database() {
    info "Vérification de la base de données..."
    
    # Tester la connexion Python
    if $PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')
try:
    from backend.database_manager import DatabaseManager
    db = DatabaseManager()
    if db.test_connection():
        print('✅ Connexion base de données OK')
    else:
        print('❌ Problème connexion base de données')
        sys.exit(1)
except Exception as e:
    print(f'❌ Erreur base de données: {e}')
    sys.exit(1)
" 2>/dev/null; then
        success "Base de données accessible"
        return 0
    else
        warning "Problème avec la base de données"
        return 1
    fi
}

# --- FONCTION DE VÉRIFICATION DES DÉPENDANCES -------------------------------
check_dependencies() {
    info "Vérification des dépendances Python..."
    
    # Vérifier les imports critiques
    local critical_imports=("flask" "sqlalchemy" "redis" "pymysql" "ntplib")
    
    for import_name in "${critical_imports[@]}"; do
        if $PYTHON_CMD -c "import $import_name" 2>/dev/null; then
            success "Module $import_name disponible"
        else
            error "Module $import_name manquant"
            return 1
        fi
    done
    
    return 0
}

# --- FONCTION DE DÉMARRAGE DE L'APPLICATION ----------------------------------
start_application() {
    info "Démarrage de l'application..."
    
    # Afficher les informations de démarrage
    title "================================================================"
    title "  🚀 $APP_NAME v$APP_VERSION"
    title "================================================================"
    
    # Informations de connexion
    local url="http://${HOST}:${PORT}"
    info "📡 Serveur web: $url"
    info "🔐 Identifiants par défaut:"
    info "   - Utilisateur: admin"
    info "   - Mot de passe: admin123"
    info "🔄 Mode: $FLASK_ENV"
    
    # Afficher les services actifs
    info "📊 Services actifs:"
    if systemctl is-active --quiet mysql 2>/dev/null; then
        info "   - MySQL: ✅ Actif"
    else
        info "   - MySQL: ❌ Inactif"
    fi
    
    if systemctl is-active --quiet redis-server 2>/dev/null; then
        info "   - Redis: ✅ Actif"
    else
        info "   - Redis: ❌ Inactif"
    fi
    
    if systemctl is-active --quiet ntpsec 2>/dev/null; then
        info "   - NTP (ntpsec): ✅ Actif"
    else
        info "   - NTP (ntpsec): ❌ Inactif"
    fi
    
    title "================================================================"
    info "🌐 Accès web: $url"
    info "🛑 Arrêt: Ctrl+C"
    title "================================================================"
    
    # Démarrer l'application
    export FLASK_APP="app.py"
    export FLASK_RUN_HOST="$HOST"
    export FLASK_RUN_PORT="$PORT"
    
    # Changer vers le répertoire de l'application
    cd "$(dirname "$0")"
    
    # Démarrer avec gestion des erreurs
    if [ "$FLASK_ENV" == "development" ]; then
        info "🔄 Mode développement - rechargement automatique activé"
        $PYTHON_CMD app.py
    else
        info "🚀 Mode production - démarrage optimisé"
        $PYTHON_CMD app.py
    fi
}

# --- FONCTION DE NETTOYAGE ---------------------------------------------------
cleanup() {
    info "Arrêt de l'application..."
    # Nettoyage si nécessaire
    exit 0
}

# --- FONCTION D'AIDE ---------------------------------------------------------
show_help() {
    title "================================================================"
    title "  $APP_NAME - Script de Démarrage"
    title "================================================================"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help         Afficher cette aide"
    echo "  -c, --check        Vérifier les prérequis uniquement"
    echo "  -d, --dev          Mode développement"
    echo "  -p, --port PORT    Port personnalisé (défaut: 5000)"
    echo "  --host HOST        Host personnalisé (défaut: 127.0.0.1)"
    echo "  --no-checks        Ignorer les vérifications"
    echo
    echo "Exemples:"
    echo "  $0                 Démarrage normal"
    echo "  $0 -c              Vérifier les prérequis"
    echo "  $0 -d              Mode développement"
    echo "  $0 -p 8080         Démarrer sur le port 8080"
    echo "  $0 --host 0.0.0.0  Écouter sur toutes les interfaces"
    echo
}

# --- FONCTION PRINCIPALE -----------------------------------------------------
main() {
    # Gestion des signaux
    trap cleanup SIGINT SIGTERM
    
    # Variables par défaut
    local mode="production"
    local run_checks=true
    local check_only=false
    
    # Parse des arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--check)
                check_only=true
                shift
                ;;
            -d|--dev)
                mode="development"
                shift
                ;;
            -p|--port)
                DEFAULT_PORT="$2"
                shift 2
                ;;
            --host)
                DEFAULT_HOST="$2"
                shift 2
                ;;
            --no-checks)
                run_checks=false
                shift
                ;;
            *)
                error "Option inconnue: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Configuration initiale
    export FLASK_ENV="$mode"
    
    # Vérifications
    if [ "$run_checks" = true ]; then
        if ! check_prerequisites; then
            error "Vérification des prérequis échouée"
            exit 1
        fi
        
        if ! check_dependencies; then
            error "Dépendances manquantes"
            exit 1
        fi
    fi
    
    # Configuration environnement
    setup_environment
    
    # Vérification base de données
    if [ "$run_checks" = true ]; then
        if ! check_database; then
            warning "Base de données non accessible - l'application pourrait ne pas fonctionner correctement"
        fi
    fi
    
    # Mode vérification uniquement
    if [ "$check_only" = true ]; then
        success "Toutes les vérifications sont terminées"
        exit 0
    fi
    
    # Démarrage de l'application
    start_application
}

# --- POINT D'ENTRÉE ---------------------------------------------------------
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 