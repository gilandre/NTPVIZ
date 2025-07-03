#!/bin/bash
# Installation simplifiée NTP Monitor Enterprise pour Ubuntu 24.04

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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
    section "NTP MONITOR ENTERPRISE - INSTALLATION SIMPLIFIÉE UBUNTU 24.04"
    
    log "Vérification des prérequis..."
    
    # Vérifier Ubuntu et root
    if [ ! -f /etc/os-release ]; then
        error "Impossible de détecter le système d'exploitation"
    fi
    
    source /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        error "Ce script est conçu pour Ubuntu (détecté: $ID)"
    fi
    
    if [[ $EUID -ne 0 ]]; then
        error "Ce script doit être exécuté en tant que root (sudo)"
    fi
    
    log "Ubuntu $VERSION_ID détecté"
    
    # Installer curl si nécessaire
    if ! command -v curl &> /dev/null; then
        log "Installation de curl..."
        apt update && apt install -y curl
    fi
    
    # Télécharger le script simplifié
    log "Téléchargement du script d'installation..."
    local temp_dir="/tmp/ntp-install"
    mkdir -p "$temp_dir"
    
    # Utiliser la version simplifiée directement depuis GitHub
    local script_url="https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/dependencies_checker_ubuntu24_simple.sh"
    
    if curl -fsSL "$script_url" -o "$temp_dir/installer.sh"; then
        success "Script téléchargé avec succès"
    else
        error "Impossible de télécharger le script"
    fi
    
    # Vérifier et exécuter
    if [ -f "$temp_dir/installer.sh" ] && [ -s "$temp_dir/installer.sh" ]; then
        chmod +x "$temp_dir/installer.sh"
        log "Lancement de l'installation..."
        
        if bash "$temp_dir/installer.sh"; then
            success "Installation terminée avec succès"
            
            # Nettoyage
            rm -rf "$temp_dir"
            
            section "INSTALLATION TERMINÉE"
            echo -e "${GREEN}🎉 Votre serveur Ubuntu 24.04 est maintenant prêt !${NC}"
            echo
            echo -e "${CYAN}Prochaines étapes :${NC}"
            echo "  1. git clone https://github.com/gilandre/NTPVIZ.git"
            echo "  2. cd NTPVIZ && sudo ./deploy_ubuntu_production.sh"
            echo "  3. Accéder à l'interface web"
            echo
            echo -e "${CYAN}Informations importantes :${NC}"
            echo "  • Credentials MySQL : /root/mysql_credentials.txt"
            echo "  • Services installés : MySQL, Apache, Redis, NTP"
            echo "  • Ports ouverts : 22, 80, 443"
            
        else
            error "Échec de l'installation"
        fi
    else
        error "Script téléchargé invalide"
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 