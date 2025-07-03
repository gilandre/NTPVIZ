#!/bin/bash
# Script d'installation rapide NTP Monitor Enterprise pour Ubuntu 24.04
# Version simplifiée - utilise le vérificateur de dépendances simplifié

# Configuration
SCRIPT_URL="https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/dependencies_checker_ubuntu24_simple.sh"
SCRIPT_NAME="dependencies_checker_ubuntu24_simple.sh"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Fonctions
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

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

section() {
    echo -e "\n${WHITE}============================================================================${NC}"
    echo -e "${WHITE}$1${NC}"
    echo -e "${WHITE}============================================================================${NC}\n"
}

check_requirements() {
    log "Vérification des prérequis..."
    
    # Vérifier Ubuntu
    if [ ! -f /etc/os-release ]; then
        error "Impossible de détecter le système d'exploitation"
    fi
    
    source /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        error "Ce script est conçu pour Ubuntu (détecté: $ID)"
    fi
    
    log "Système détecté: Ubuntu $VERSION_ID"
    
    # Vérifier privilèges root
    if [[ $EUID -ne 0 ]]; then
        error "Ce script doit être exécuté en tant que root (sudo)"
    fi
    
    # Vérifier curl/wget
    if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
        log "Installation de curl..."
        apt update && apt install -y curl
    fi
    
    success "Prérequis validés"
}

download_and_run() {
    section "TÉLÉCHARGEMENT ET EXÉCUTION DU SCRIPT"
    
    local temp_dir="/tmp/ntp-monitor-install"
    local script_path="$temp_dir/$SCRIPT_NAME"
    
    # Créer répertoire temporaire
    log "Création du répertoire temporaire..."
    mkdir -p "$temp_dir"
    cd "$temp_dir"
    
    # Télécharger le script
    log "Téléchargement du script depuis GitHub..."
    log "URL: $SCRIPT_URL"
    
    local download_success=false
    
    if command -v curl &> /dev/null; then
        if curl -fsSL "$SCRIPT_URL" -o "$script_path"; then
            download_success=true
        else
            warn "Échec du téléchargement avec curl"
        fi
    fi
    
    if [ "$download_success" = false ] && command -v wget &> /dev/null; then
        if wget -q "$SCRIPT_URL" -O "$script_path"; then
            download_success=true
        else
            warn "Échec du téléchargement avec wget"
        fi
    fi
    
    if [ "$download_success" = false ]; then
        error "Impossible de télécharger le script"
    fi
    
    # Vérifier le téléchargement
    if [ ! -f "$script_path" ] || [ ! -s "$script_path" ]; then
        error "Le script téléchargé est vide ou inexistant"
    fi
    
    local file_size=$(stat -c%s "$script_path" 2>/dev/null || echo "0")
    if [ "$file_size" -lt 1000 ]; then
        error "Le script téléchargé semble incomplet (taille: $file_size octets)"
    fi
    
    success "Script téléchargé avec succès (taille: $file_size octets)"
    
    # Rendre exécutable
    log "Configuration des permissions..."
    chmod +x "$script_path"
    
    # Vérifier le contenu
    if ! head -1 "$script_path" | grep -q "#!/bin/bash"; then
        error "Le fichier téléchargé ne semble pas être un script bash valide"
    fi
    
    # Exécuter le script
    section "EXÉCUTION DU VÉRIFICATEUR DE DÉPENDANCES"
    
    log "Lancement du script de vérification et installation..."
    log "Script: $script_path"
    echo
    
    # Exécuter avec gestion d'erreur
    if bash "$script_path"; then
        success "Script de dépendances exécuté avec succès"
        cleanup_success
    else
        local exit_code=$?
        error "Échec de l'exécution du script (code de sortie: $exit_code)"
    fi
}

cleanup_success() {
    section "NETTOYAGE ET FINALISATION"
    
    log "Nettoyage des fichiers temporaires..."
    cd /
    rm -rf "/tmp/ntp-monitor-install" 2>/dev/null || true
    
    success "Installation terminée avec succès !"
    
    echo -e "\n${CYAN}============================================${NC}"
    echo -e "${CYAN}  NTP MONITOR ENTERPRISE${NC}"
    echo -e "${CYAN}  Installation Ubuntu 24.04 Terminée${NC}"
    echo -e "${CYAN}============================================${NC}"
    echo
    echo -e "${GREEN}✅ Votre serveur Ubuntu 24.04 est maintenant prêt pour NTP Monitor Enterprise !${NC}"
    echo
    echo -e "${CYAN}Prochaines étapes :${NC}"
    echo "  1. Cloner le projet complet :"
    echo "     git clone https://github.com/gilandre/NTPVIZ.git"
    echo "  2. Lancer le déploiement :"
    echo "     cd NTPVIZ && sudo ./deploy_ubuntu_production.sh"
    echo "  3. Accéder à l'interface web"
    echo
    echo -e "${CYAN}Informations importantes :${NC}"
    echo "  • Credentials MySQL : /root/mysql_credentials.txt"
    echo "  • Logs système : journalctl -xe"
    echo "  • Services : systemctl status mysql apache2 redis-server"
    echo
}

main() {
    clear
    section "NTP MONITOR ENTERPRISE - INSTALLATION RAPIDE UBUNTU 24.04"
    
    echo -e "${CYAN}Ce script va :${NC}"
    echo "  1. Vérifier les prérequis système"
    echo "  2. Télécharger le script de dépendances depuis GitHub"
    echo "  3. Exécuter la vérification et installation automatique"
    echo "  4. Préparer votre serveur pour NTP Monitor Enterprise"
    echo
    echo -e "${YELLOW}⚠️  Assurez-vous d'avoir une connexion Internet active${NC}"
    echo
    
    read -p "Continuer l'installation ? (O/n) : " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Oo]$ ]] && [[ ! -z $REPLY ]]; then
        log "Installation annulée par l'utilisateur"
        exit 0
    fi
    
    log "Début de l'installation automatique..."
    echo
    
    # Étapes d'installation
    check_requirements
    download_and_run
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 