#!/bin/bash
# Script de Vérification des Prérequis - NTP Monitor Enterprise
# Vérifie que le système est prêt pour le déploiement

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables
ERRORS=0
WARNINGS=0

log() {
    echo -e "${GREEN}[✓] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[!] $1${NC}"
    ((WARNINGS++))
}

error() {
    echo -e "${RED}[✗] $1${NC}"
    ((ERRORS++))
}

info() {
    echo -e "${BLUE}[i] $1${NC}"
}

section() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Ce script doit être exécuté en tant que root (sudo)"
        return 1
    fi
    log "Privilèges root : OK"
    return 0
}

check_system() {
    section "VÉRIFICATION SYSTÈME"
    
    # Distribution
    if grep -q "Ubuntu" /etc/os-release; then
        VERSION=$(grep "VERSION_ID" /etc/os-release | cut -d'"' -f2)
        log "Distribution Ubuntu $VERSION détectée"
    else
        DISTRO=$(grep "^ID=" /etc/os-release | cut -d'=' -f2)
        warn "Distribution non-Ubuntu détectée : $DISTRO"
    fi
    
    # Architecture
    ARCH=$(uname -m)
    if [[ "$ARCH" == "x86_64" ]]; then
        log "Architecture x86_64 : OK"
    else
        warn "Architecture non-standard : $ARCH"
    fi
    
    # Kernel
    KERNEL=$(uname -r)
    log "Kernel : $KERNEL"
    
    # Uptime
    UPTIME=$(uptime -p)
    log "Uptime : $UPTIME"
}

check_resources() {
    section "VÉRIFICATION RESSOURCES"
    
    # Espace disque
    DISK_FREE=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
    if [[ $DISK_FREE -ge 5 ]]; then
        log "Espace disque libre : ${DISK_FREE}GB (excellent)"
    elif [[ $DISK_FREE -ge 2 ]]; then
        log "Espace disque libre : ${DISK_FREE}GB (suffisant)"
    else
        error "Espace disque insuffisant : ${DISK_FREE}GB (minimum 2GB requis)"
    fi
    
    # Mémoire
    MEMORY_TOTAL=$(free -m | grep '^Mem:' | awk '{print $2}')
    MEMORY_FREE=$(free -m | grep '^Mem:' | awk '{print $7}')
    if [[ $MEMORY_TOTAL -ge 2048 ]]; then
        log "Mémoire totale : ${MEMORY_TOTAL}MB (excellent)"
    elif [[ $MEMORY_TOTAL -ge 1024 ]]; then
        log "Mémoire totale : ${MEMORY_TOTAL}MB (bon)"
    elif [[ $MEMORY_TOTAL -ge 512 ]]; then
        warn "Mémoire totale : ${MEMORY_TOTAL}MB (minimum)"
    else
        error "Mémoire insuffisante : ${MEMORY_TOTAL}MB (minimum 512MB requis)"
    fi
    
    # CPU
    CPU_CORES=$(nproc)
    CPU_MODEL=$(grep "model name" /proc/cpuinfo | head -1 | cut -d':' -f2 | xargs)
    log "CPU : $CPU_CORES cœur(s) - $CPU_MODEL"
    
    # Load average
    LOAD_AVG=$(uptime | grep -oE "load average: [0-9]+\.?[0-9]*" | cut -d' ' -f3)
    log "Charge système : $LOAD_AVG"
}

check_network() {
    section "VÉRIFICATION RÉSEAU"
    
    # Connectivité Internet
    if ping -c 1 -W 5 8.8.8.8 &> /dev/null; then
        log "Connectivité Internet : OK"
    else
        error "Pas de connexion Internet (requis pour téléchargement)"
    fi
    
    # DNS
    if nslookup google.com &> /dev/null; then
        log "Résolution DNS : OK"
    else
        error "Problème de résolution DNS"
    fi
    
    # Ports
    PORTS_BUSY=""
    for port in 80 443 3306 6379 5000; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            PORTS_BUSY="$PORTS_BUSY $port"
        fi
    done
    
    if [[ -n "$PORTS_BUSY" ]]; then
        warn "Ports déjà utilisés :$PORTS_BUSY (peuvent causer des conflits)"
    else
        log "Ports requis (80, 443, 3306, 6379, 5000) : Libres"
    fi
}

check_python() {
    section "VÉRIFICATION PYTHON"
    
    # Versions Python disponibles
    PYTHON_VERSIONS=""
    for version in "3.12" "3.11" "3.10" "3.9"; do
        if command -v python$version &> /dev/null; then
            PYTHON_VERSIONS="$PYTHON_VERSIONS $version"
        fi
    done
    
    if [[ -n "$PYTHON_VERSIONS" ]]; then
        log "Versions Python disponibles :$PYTHON_VERSIONS"
        
        # Meilleure version
        BEST_VERSION=$(echo $PYTHON_VERSIONS | tr ' ' '\n' | sort -V | tail -1)
        log "Version recommandée : Python $BEST_VERSION"
        
        # Vérifier pip
        if command -v pip3 &> /dev/null; then
            PIP_VERSION=$(pip3 --version | cut -d' ' -f2)
            log "pip3 version : $PIP_VERSION"
        else
            warn "pip3 non trouvé (sera installé)"
        fi
        
        # Vérifier venv
        if python3 -m venv --help &> /dev/null; then
            log "Module venv : Disponible"
        else
            warn "Module venv manquant (sera installé)"
        fi
    else
        error "Aucune version Python 3.9+ trouvée"
    fi
}

check_existing_services() {
    section "VÉRIFICATION SERVICES EXISTANTS"
    
    # MySQL
    if systemctl list-unit-files | grep -q mysql; then
        if systemctl is-active --quiet mysql; then
            log "MySQL : Installé et actif"
        else
            log "MySQL : Installé mais inactif"
        fi
    else
        info "MySQL : Non installé (sera installé)"
    fi
    
    # Apache
    if systemctl list-unit-files | grep -q apache2; then
        if systemctl is-active --quiet apache2; then
            log "Apache : Installé et actif"
        else
            log "Apache : Installé mais inactif"
        fi
    else
        info "Apache : Non installé (sera installé)"
    fi
    
    # Redis
    if systemctl list-unit-files | grep -q redis; then
        if systemctl is-active --quiet redis-server; then
            log "Redis : Installé et actif"
        else
            log "Redis : Installé mais inactif"
        fi
    else
        info "Redis : Non installé (sera installé)"
    fi
    
    # ntpsec
    if command -v ntpq &> /dev/null; then
        if systemctl is-active --quiet ntpsec; then
            log "ntpsec : Installé et actif"
            
            # Vérifier fonctionnalité
            if ntpq -c peers &> /dev/null; then
                SYNC_COUNT=$(ntpq -c peers 2>/dev/null | grep -c "^[*+]" || echo "0")
                if [[ $SYNC_COUNT -gt 0 ]]; then
                    log "ntpsec : $SYNC_COUNT serveur(s) synchronisé(s)"
                else
                    warn "ntpsec : Aucun serveur synchronisé"
                fi
            else
                warn "ntpsec : Installé mais ne répond pas"
            fi
        else
            warn "ntpsec : Installé mais inactif"
        fi
    else
        info "ntpsec : Non installé (sera installé)"
    fi
    
    # Chrony (conflit potentiel)
    if systemctl is-active --quiet chronyd 2>/dev/null; then
        warn "chrony : Actif (sera désactivé pour éviter conflits avec ntpsec)"
    fi
    
    # systemd-timesyncd (conflit potentiel)
    if systemctl is-active --quiet systemd-timesyncd 2>/dev/null; then
        warn "systemd-timesyncd : Actif (sera désactivé pour éviter conflits avec ntpsec)"
    fi
}

check_git() {
    section "VÉRIFICATION GIT"
    
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version | cut -d' ' -f3)
        log "Git version : $GIT_VERSION"
        
        # Test accès GitHub
        if git ls-remote https://github.com/gilandre/NTPVIZ.git &> /dev/null; then
            log "Accès GitHub : OK"
        else
            error "Impossible d'accéder au repository GitHub"
        fi
    else
        info "Git : Non installé (sera installé)"
    fi
}

check_firewall() {
    section "VÉRIFICATION PARE-FEU"
    
    if command -v ufw &> /dev/null; then
        UFW_STATUS=$(ufw status | grep "Status:" | cut -d' ' -f2)
        log "UFW installé : Status $UFW_STATUS"
        
        if [[ "$UFW_STATUS" == "active" ]]; then
            # Vérifier règles SSH
            if ufw status | grep -q "22/tcp"; then
                log "Règle SSH : Présente"
            else
                warn "Règle SSH : Absente (risque de blocage)"
            fi
        fi
    else
        info "UFW : Non installé (sera installé)"
    fi
    
    # iptables
    if command -v iptables &> /dev/null; then
        IPTABLES_RULES=$(iptables -L | wc -l)
        if [[ $IPTABLES_RULES -gt 10 ]]; then
            warn "iptables : Règles personnalisées détectées ($IPTABLES_RULES lignes)"
        else
            log "iptables : Configuration standard"
        fi
    fi
}

check_permissions() {
    section "VÉRIFICATION PERMISSIONS"
    
    # Répertoires système
    DIRS_TO_CHECK=("/etc" "/var/log" "/home" "/opt")
    for dir in "${DIRS_TO_CHECK[@]}"; do
        if [[ -w "$dir" ]]; then
            log "Écriture dans $dir : OK"
        else
            error "Impossible d'écrire dans $dir"
        fi
    done
    
    # Capacité à créer utilisateurs
    if command -v useradd &> /dev/null; then
        log "Création utilisateurs : OK"
    else
        error "Commande useradd manquante"
    fi
    
    # Capacité à gérer services
    if command -v systemctl &> /dev/null; then
        log "Gestion services systemd : OK"
    else
        error "systemctl manquant"
    fi
}

display_summary() {
    section "RÉSUMÉ"
    
    echo
    if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}🎉 SYSTÈME PRÊT POUR LE DÉPLOIEMENT${NC}"
        echo -e "${GREEN}   Aucun problème détecté${NC}"
        echo
        echo -e "${BLUE}📋 Prochaines étapes :${NC}"
        echo -e "${BLUE}   1. Exécuter : chmod +x deploy_ubuntu_production_complete.sh${NC}"
        echo -e "${BLUE}   2. Lancer : sudo ./deploy_ubuntu_production_complete.sh${NC}"
        
    elif [[ $ERRORS -eq 0 ]]; then
        echo -e "${YELLOW}⚠️  SYSTÈME PRÊT AVEC AVERTISSEMENTS${NC}"
        echo -e "${YELLOW}   $WARNINGS avertissement(s) détecté(s)${NC}"
        echo -e "${YELLOW}   Le déploiement peut continuer mais surveillez les logs${NC}"
        echo
        echo -e "${BLUE}📋 Prochaines étapes :${NC}"
        echo -e "${BLUE}   1. Exécuter : chmod +x deploy_ubuntu_production_complete.sh${NC}"
        echo -e "${BLUE}   2. Lancer : sudo ./deploy_ubuntu_production_complete.sh${NC}"
        
    else
        echo -e "${RED}❌ SYSTÈME NON PRÊT${NC}"
        echo -e "${RED}   $ERRORS erreur(s) et $WARNINGS avertissement(s) détecté(s)${NC}"
        echo -e "${RED}   Corrigez les erreurs avant de continuer${NC}"
        echo
        echo -e "${BLUE}📋 Actions recommandées :${NC}"
        echo -e "${BLUE}   1. Corriger les erreurs listées ci-dessus${NC}"
        echo -e "${BLUE}   2. Relancer ce script de vérification${NC}"
        echo -e "${BLUE}   3. Puis déployer avec deploy_ubuntu_production_complete.sh${NC}"
    fi
    
    echo
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  STATISTIQUES${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo -e "${GREEN}  Vérifications réussies : $(($(grep -c "✓" <<< "$(cat /tmp/check_output 2>/dev/null)") || 0))${NC}"
    echo -e "${YELLOW}  Avertissements : $WARNINGS${NC}"
    echo -e "${RED}  Erreurs : $ERRORS${NC}"
    echo -e "${BLUE}============================================${NC}"
}

main() {
    clear
    section "VÉRIFICATION PRÉREQUIS NTP MONITOR ENTERPRISE"
    
    echo -e "${BLUE}Ce script vérifie si votre système Ubuntu est prêt pour le déploiement${NC}"
    echo -e "${BLUE}de NTP Monitor Enterprise v2.1.0${NC}"
    echo
    
    # Rediriger sortie pour comptage
    exec 1> >(tee /tmp/check_output)
    
    check_root
    check_system
    check_resources
    check_network
    check_python
    check_existing_services
    check_git
    check_firewall
    check_permissions
    
    # Restaurer sortie normale
    exec 1>&1
    
    display_summary
    
    # Nettoyage
    rm -f /tmp/check_output
    
    # Code de sortie
    if [[ $ERRORS -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
}

# Exécution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 