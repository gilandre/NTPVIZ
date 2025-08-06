#!/bin/bash
set -e

# ========================================
# SCRIPT DE MISE À JOUR DU DÉPLOIEMENT
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

# Fonction de sauvegarde
backup_current_deployment() {
    log_step "Sauvegarde du déploiement actuel..."
    
    if [ -d "$APP_DIR" ]; then
        BACKUP_DIR="/opt/ntp-monitor-backup-$(date +%Y%m%d-%H%M%S)"
        sudo cp -r $APP_DIR $BACKUP_DIR
        log_success "Sauvegarde créée: $BACKUP_DIR"
    else
        log_warning "Aucun déploiement existant trouvé"
    fi
}

# Fonction de mise à jour du code source
update_source_code() {
    log_step "Mise à jour du code source depuis GitHub..."
    
    if [ ! -d "$APP_DIR" ]; then
        log_error "Répertoire de l'application non trouvé: $APP_DIR"
        exit 1
    fi
    
    cd $APP_DIR
    
    # Sauvegarder les fichiers de configuration
    if [ -f ".env" ]; then
        cp .env .env.backup
        log_info "Configuration .env sauvegardée"
    fi
    
    # Mettre à jour depuis GitHub
    git fetch origin
    git reset --hard origin/$BRANCH
    git checkout $BRANCH
    
    # Restaurer la configuration si nécessaire
    if [ -f ".env.backup" ]; then
        cp .env.backup .env
        log_info "Configuration .env restaurée"
    fi
    
    log_success "Code source mis à jour depuis GitHub"
}

# Fonction de mise à jour de l'environnement Python
update_python_environment() {
    log_step "Mise à jour de l'environnement Python..."
    
    cd $APP_DIR
    
    if [ ! -d ".venv" ]; then
        log_error "Environnement virtuel non trouvé"
        exit 1
    fi
    
    source .venv/bin/activate
    
    # Mettre à jour pip
    pip install --upgrade pip setuptools wheel
    
    # Mettre à jour les dépendances
    pip install -r requirements.txt --upgrade
    
    log_success "Environnement Python mis à jour"
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

# Fonction de redémarrage du service
restart_service() {
    log_step "Redémarrage du service..."
    
    # Arrêter le service
    sudo systemctl stop $SERVICE_NAME || true
    
    # Redémarrer le service
    sudo systemctl start $SERVICE_NAME
    
    # Vérifier le statut
    sudo systemctl status $SERVICE_NAME --no-pager
    
    log_success "Service redémarré"
}

# Fonction de vérification de la mise à jour
verify_update() {
    log_step "Vérification de la mise à jour..."
    
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
    
    log_success "Mise à jour vérifiée"
}

# Fonction d'affichage des logs
show_logs() {
    log_step "Affichage des logs récents..."
    
    sudo journalctl -u $SERVICE_NAME -n 20 --no-pager
}

# Fonction de rollback
rollback() {
    log_step "Rollback vers la version précédente..."
    
    # Trouver la sauvegarde la plus récente
    LATEST_BACKUP=$(ls -t /opt/ntp-monitor-backup-* 2>/dev/null | head -1)
    
    if [ -n "$LATEST_BACKUP" ]; then
        log_info "Restauration depuis: $LATEST_BACKUP"
        
        # Arrêter le service
        sudo systemctl stop $SERVICE_NAME || true
        
        # Restaurer la sauvegarde
        sudo rm -rf $APP_DIR
        sudo cp -r $LATEST_BACKUP $APP_DIR
        sudo chown -R $USER:$USER $APP_DIR
        
        # Redémarrer le service
        sudo systemctl start $SERVICE_NAME
        
        log_success "Rollback terminé"
    else
        log_error "Aucune sauvegarde trouvée"
        exit 1
    fi
}

# Fonction principale
main() {
    echo -e "${CYAN}"
    echo "=========================================="
    echo "  MISE À JOUR NTP MONITOR ENTERPRISE"
    echo "  Ubuntu 24.04 - Version corrigée"
    echo "=========================================="
    echo -e "${NC}"
    
    # Exécuter les étapes de mise à jour
    backup_current_deployment
    update_source_code
    update_python_environment
    fix_database_schema
    harmonize_models
    test_application
    restart_service
    verify_update
    
    echo -e "${GREEN}"
    echo "=========================================="
    echo "  MISE À JOUR TERMINÉE AVEC SUCCÈS!"
    echo "=========================================="
    echo -e "${NC}"
    
    # Afficher les commandes utiles
    echo -e "${YELLOW}Commandes utiles:${NC}"
    echo "  Voir les logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "  Redémarrer: sudo systemctl restart $SERVICE_NAME"
    echo "  Statut: sudo systemctl status $SERVICE_NAME"
    echo "  Rollback: $0 rollback"
}

# Gestion des arguments
case "${1:-}" in
    "logs")
        show_logs
        ;;
    "restart")
        restart_service
        ;;
    "status")
        sudo systemctl status $SERVICE_NAME
        ;;
    "test")
        test_application
        ;;
    "rollback")
        rollback
        ;;
    *)
        main
        ;;
esac 