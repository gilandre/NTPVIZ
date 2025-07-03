#!/bin/bash
# Test d'installation locale avec le script de dépendances corrigé

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

section() {
    echo -e "\n${WHITE}============================================================================${NC}"
    echo -e "${WHITE}$1${NC}"
    echo -e "${WHITE}============================================================================${NC}\n"
}

main() {
    clear
    section "TEST LOCAL - NTP MONITOR ENTERPRISE UBUNTU 24.04"
    
    log "Vérification des prérequis..."
    
    # Vérifier root
    if [[ $EUID -ne 0 ]]; then
        error "Ce script doit être exécuté en tant que root (sudo)"
    fi
    
    # Vérifier que le script de dépendances corrigé existe
    if [ ! -f "dependencies_checker_ubuntu24_final.sh" ]; then
        error "Script de dépendances non trouvé dans le répertoire courant"
    fi
    
    log "Lancement du script de dépendances corrigé..."
    
    # Exécuter le script local
    if bash ./dependencies_checker_ubuntu24_final.sh; then
        success "Script de dépendances exécuté avec succès"
    else
        local exit_code=$?
        error "Échec de l'exécution du script (code de sortie: $exit_code)"
    fi
    
    success "Test terminé"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 